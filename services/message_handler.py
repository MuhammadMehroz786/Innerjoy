"""
Message Handler Service
Processes incoming messages and manages conversation flows
Implements Tree 1 and Tree 2 logic with exact flow from specification
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import pytz

from config import Config
from services.respond_api import RespondAPI
from services.google_sheets import GoogleSheetsService

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles incoming WhatsApp messages and conversation flows"""

    def __init__(self):
        self.api = RespondAPI()
        try:
            self.sheets = GoogleSheetsService() if Config.GOOGLE_SHEETS_ID else None
        except:
            self.sheets = None
            logger.warning("Google Sheets not available - will skip sheet operations")
        self.templates = Config.get_message_templates()
        self.timezone = pytz.timezone(Config.TIMEZONE)

    def _safe_sheets_operation(self, operation, *args, **kwargs):
        """Safely execute a Google Sheets operation"""
        if not self.sheets:
            logger.debug("Skipping sheets operation (not configured)")
            return None
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Sheets operation failed: {e}")
            return None

    def process_message(self, webhook_data: Dict) -> bool:
        """
        Process incoming webhook message from Respond.io
        This is the main entry point for all incoming messages

        Args:
            webhook_data: Webhook payload from Respond.io

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            # Extract message data
            message = webhook_data.get('message', {})
            contact = webhook_data.get('contact', {})
            contact_id = contact.get('id')
            phone = contact.get('phone')

            # Use contact ID as primary identifier (required for Respond.io API)
            contact_identifier = contact_id if contact_id else f"phone:{phone}"

            if not contact_identifier:
                logger.error("No contact identifier (phone or ID) in webhook data")
                return False

            logger.info(f"Processing message from: {contact_identifier}")

            # Get message text
            message_text = message.get('text', '').strip()

            if not message_text:
                logger.info(f"Non-text message from {contact_identifier}, ignoring")
                return True

            logger.info(f"Message content: {message_text}")

            # ===== 72-HOUR WINDOW RESET =====
            # Every inbound message resets the 72-hour window (Meta WhatsApp Policy)
            self._reset_72hr_window(contact_identifier)

            # Get or create contact in sheets
            sheet_contact = self._safe_sheets_operation(
                lambda: self.sheets.get_contact(contact_identifier) if self.sheets else None
            )

            if not sheet_contact:
                # New contact - Start Tree 1 Flow: B1 Z1
                logger.info(f"New contact {contact_identifier}, starting Tree 1")
                return self._handle_new_contact(contact_identifier, phone, message_text, contact_data=contact)
            else:
                # Existing contact - Route based on current state
                logger.info(f"Existing contact {contact_identifier}, current tree: {sheet_contact.get('current_tree')}, step: {sheet_contact.get('current_step')}")
                return self._handle_existing_contact(contact_identifier, sheet_contact, message_text)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return False

    def _reset_72hr_window(self, contact_identifier: str):
        """
        Reset the 72-hour window for a contact (Meta WhatsApp Policy)
        Called on EVERY inbound message

        Args:
            contact_identifier: Contact identifier
        """
        try:
            now = datetime.now(self.timezone)
            window_expires_at = now + timedelta(hours=72)  # 72 hours = 3 days

            # Update in sheets
            self._safe_sheets_operation(
                lambda: self.sheets.update_contact(contact_identifier, {
                    'last_inbound_msg_time': now.isoformat(),
                    'window_expires_at': window_expires_at.isoformat()
                }) if self.sheets else None
            )

            # Update in Respond.io (optional - custom field may not exist)
            try:
                self.api.update_72hr_window(contact_identifier)
            except Exception as e:
                logger.debug(f"Could not update 72hr window in Respond.io: {e}")

            logger.info(f"Reset 72hr window for {contact_identifier}, expires: {window_expires_at}")

        except Exception as e:
            logger.warning(f"Failed to reset 72hr window: {e}")

    # ==================== NEW CONTACT FLOW ====================

    def _handle_new_contact(self, contact_identifier: str, phone: str, message_text: str, contact_data: dict = None) -> bool:
        """
        Handle a brand new contact
        This triggers B1 Z1 (asking for name) if they haven't been added to sheets yet

        Args:
            contact_identifier: Contact identifier
            phone: Phone number
            message_text: Their first message
            contact_data: Optional contact data from webhook (e.g., Make.com)

        Returns:
            True if handled successfully
        """
        try:
            # Try to get first name from contact data (Make.com), otherwise extract from message
            if contact_data and contact_data.get('firstName'):
                first_name = contact_data.get('firstName')
                logger.info(f"Using first name from contact data: {first_name}")
            else:
                # Extract first name from their message
                first_name = self._extract_first_name(message_text)
                logger.info(f"Extracted first name from message: {first_name}")

            # Add to sheets
            now = datetime.now(self.timezone)
            self._safe_sheets_operation(
                lambda: self.sheets.add_contact({
                    'contact_id': contact_identifier,
                    'phone': phone,
                    'first_name': first_name,
                    'current_tree': 'Tree1',
                    'current_step': 'B1_Z2',  # Moving to Z2 after getting name
                    'registration_time': now.isoformat(),
                    'last_inbound_msg_time': now.isoformat(),
                    'window_expires_at': (now + timedelta(hours=72)).isoformat()  # 72-hour window
                }) if self.sheets else None
            )

            # Log message
            self._log_message(contact_identifier, message_text, 'inbound', 'B1_Z1')

            # Send B1 Z2 - Zoom link + ask timeslot
            self._send_b1_z2(contact_identifier, first_name)

            # Schedule B2 Ra (fallback to Tree 2) in 2 hours if no timeslot chosen
            self._schedule_tree2_fallback(contact_identifier, hours=2)

            logger.info(f"New contact {contact_identifier} ({first_name}) added, sent B1_Z2")
            return True

        except Exception as e:
            logger.error(f"Error handling new contact: {e}", exc_info=True)
            return False

    def _extract_first_name(self, message_text: str) -> str:
        """
        Extract first name from message text

        Args:
            message_text: Message from user

        Returns:
            First name (capitalized)
        """
        # Take first word and capitalize
        words = message_text.strip().split()
        if words:
            first_name = words[0].strip().capitalize()
            # Validate it's a real name (not just emoji)
            if any(c.isalpha() for c in first_name):
                return first_name

        return "there"  # Default if can't extract

    # ==================== EXISTING CONTACT FLOW ====================

    def _handle_existing_contact(self, contact_identifier: str, sheet_contact: Dict, message_text: str) -> bool:
        """
        Handle message from existing contact
        Routes based on current tree and step

        Args:
            contact_identifier: Contact identifier
            sheet_contact: Contact data from sheets
            message_text: Their message

        Returns:
            True if handled successfully
        """
        try:
            current_tree = sheet_contact.get('current_tree', 'Tree1')
            current_step = sheet_contact.get('current_step', '')
            first_name = sheet_contact.get('first_name', 'there')

            # Check if they sent thumbs up
            if message_text.strip() == '👍':
                self._handle_thumbs_up(contact_identifier)
                # Don't process further - thumbs up is just acknowledgment
                return True

            # Check if this is a timeslot selection (A-E)
            message_upper = message_text.upper().strip()
            if message_upper in ['A', 'B', 'C', 'D', 'E']:
                logger.info(f"Timeslot selection detected: {message_upper}")
                return self._handle_timeslot_selection(contact_identifier, sheet_contact, message_upper)

            # Check if they said "I already attended" (Tree 2 re-entry)
            if 'already attended' in message_text.lower():
                logger.info(f"User {contact_identifier} said they already attended, sending B1_S1")
                return self._handle_already_attended(contact_identifier, first_name)

            # Otherwise, just acknowledge (they're in the flow, no action needed)
            logger.info(f"General message from {contact_identifier}, acknowledging")
            self._log_message(contact_identifier, message_text, 'inbound', 'GENERAL')
            return True

        except Exception as e:
            logger.error(f"Error handling existing contact: {e}", exc_info=True)
            return False

    # ==================== TREE 1 FLOW - MESSAGE SENDING ====================

    def _send_b1_z2(self, contact_identifier: str, first_name: str):
        """
        Send B1 Z2 - Zoom link + ask timeslot

        Args:
            contact_identifier: Contact identifier
            first_name: User's first name
        """
        try:
            message = self.templates['B1_Z2'].format(
                name=first_name,
                zoom_link=Config.ZOOM_PREVIEW_LINK
            )

            self.api.send_message(contact_identifier, message)
            self._log_message(contact_identifier, message, 'outbound', 'B1_Z2')

            logger.info(f"Sent B1_Z2 to {contact_identifier}")

        except Exception as e:
            logger.error(f"Error sending B1_Z2: {e}")

    def _handle_timeslot_selection(self, contact_identifier: str, sheet_contact: Dict, timeslot: str) -> bool:
        """
        Handle timeslot selection (A, B, C, D, or E)
        This is B1 Z2a1 - Confirm slot + send invite card

        Args:
            contact_identifier: Contact identifier
            sheet_contact: Contact data from sheets
            timeslot: Selected timeslot (A, B, C, D, E)

        Returns:
            True if handled successfully
        """
        try:
            first_name = sheet_contact.get('first_name', 'there')
            current_tree = sheet_contact.get('current_tree', 'Tree1')

            # Calculate session datetime
            session_datetime = self._calculate_next_session(timeslot)

            # If switching from Tree 2, cancel Tree 2 scheduled messages
            if current_tree == 'Tree2':
                logger.info(f"Contact {contact_identifier} switching from Tree 2 to Tree 1")
                self._safe_sheets_operation(
                    lambda: self.sheets.cancel_scheduled_messages(
                        contact_identifier,
                        ['B2_RA', 'B2_RB', 'B2_S1', 'B2_S2']
                    ) if self.sheets else None
                )

            # Update contact in sheets
            self._safe_sheets_operation(
                lambda: self.sheets.update_contact(contact_identifier, {
                    'current_tree': 'Tree1',
                    'current_step': 'B1_Z2A1',
                    'chosen_timeslot': timeslot,
                    'session_datetime': session_datetime.isoformat()
                }) if self.sheets else None
            )

            # Log the timeslot selection
            self._log_message(contact_identifier, timeslot, 'inbound', 'TIMESLOT_SELECT')

            # Send B1 Z2a1 - Confirmation
            timeslot_display = Config.get_timeslot_display(timeslot)
            confirmation_message = self.templates['B1_Z2A1'].format(
                name=first_name,
                timeslot=timeslot_display
            )
            self.api.send_message(contact_identifier, confirmation_message)
            self._log_message(contact_identifier, confirmation_message, 'outbound', 'B1_Z2A1')

            # Send B1 Z2a2 - Forward invite card
            invite_card = self.templates['B1_Z2A2'].format(
                timeslot=timeslot_display,
                registration_link=Config.REGISTRATION_LINK or 'https://your-landing-page.com',
                sender_name=first_name
            )
            self.api.send_message(contact_identifier, invite_card)
            self._log_message(contact_identifier, invite_card, 'outbound', 'B1_Z2A2')

            # Schedule all Tree 1 timed messages
            self._schedule_tree1_messages(contact_identifier, session_datetime)

            logger.info(f"Confirmed timeslot {timeslot} for {contact_identifier}, scheduled reminders and sales messages")
            return True

        except Exception as e:
            logger.error(f"Error handling timeslot selection: {e}", exc_info=True)
            return False

    def _handle_thumbs_up(self, contact_identifier: str):
        """
        Handle thumbs up confirmation
        Updates tracking but doesn't change messages

        Args:
            contact_identifier: Contact identifier
        """
        try:
            logger.info(f"Received thumbs up from {contact_identifier}")

            # Update in sheets
            self._safe_sheets_operation(
                lambda: self.sheets.update_contact(contact_identifier, {
                    'thumbs_up_received': 'Yes'
                }) if self.sheets else None
            )

            # Log
            self._log_message(contact_identifier, '👍', 'inbound', 'THUMBS_UP')

        except Exception as e:
            logger.warning(f"Error handling thumbs up: {e}")

    def _calculate_next_session(self, timeslot: str) -> datetime:
        """
        Calculate the next session datetime for a given timeslot

        Args:
            timeslot: Timeslot letter (A, B, C, D, E)

        Returns:
            Next session datetime
        """
        slot_info = Config.TIME_SLOTS[timeslot]
        target_day = slot_info['day_num']  # 5 for Saturday, 6 for Sunday
        session_time = slot_info['time']

        # Get current time in configured timezone
        now = datetime.now(self.timezone)

        # Calculate days until target day
        days_ahead = target_day - now.weekday()

        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7

        # If it's the target day but past the session time, go to next week
        if days_ahead == 0 and now.time() > session_time:
            days_ahead = 7

        # Calculate session datetime
        session_date = now.date() + timedelta(days=days_ahead)
        session_datetime = datetime.combine(session_date, session_time)
        session_datetime = self.timezone.localize(session_datetime)

        return session_datetime

    # ==================== SCHEDULING ====================

    def _schedule_tree1_messages(self, contact_identifier: str, session_datetime: datetime):
        """
        Schedule all Tree 1 timed messages after timeslot is chosen
        - B1 R1 (T-12h)
        - B1 R2 (T-60min)
        - B1 R3 (T-10min)
        - B1 S1 (T+5min after session)
        - B1 Shake-up (T+20min after session)
        - B1 S2 (T+2h after session)
        - B1 S3 (Sun/Mon morning 9:00 AM)

        Args:
            contact_identifier: Contact identifier
            session_datetime: Session datetime
        """
        try:
            # Reminder messages
            r1_time = session_datetime - timedelta(hours=12)
            r2_time = session_datetime - timedelta(minutes=60)
            r3_time = session_datetime - timedelta(minutes=10)

            # Sales messages (after session ends, assume 30min session)
            session_end = session_datetime + timedelta(minutes=30)
            s1_time = session_end + timedelta(minutes=5)
            shakeup_time = session_end + timedelta(minutes=20)
            s2_time = session_end + timedelta(hours=2)

            # B1 S3 - Next morning (Sunday or Monday) at 9:00 AM
            # Calculate next day at 9:00 AM
            next_day = session_datetime.date() + timedelta(days=1)
            s3_time = self.timezone.localize(datetime.combine(next_day, datetime.min.time().replace(hour=9, minute=0)))

            messages_to_schedule = [
                {'code': 'B1_R1', 'time': r1_time, 'trigger': 'reminder_12h'},
                {'code': 'B1_R2', 'time': r2_time, 'trigger': 'reminder_60min'},
                {'code': 'B1_R3', 'time': r3_time, 'trigger': 'reminder_10min'},
                {'code': 'B1_S1', 'time': s1_time, 'trigger': 'sales_post_session'},
                {'code': 'B1_SHAKEUP', 'time': shakeup_time, 'trigger': 'sales_shakeup'},
                {'code': 'B1_S2', 'time': s2_time, 'trigger': 'sales_followup'},
                {'code': 'B1_S3', 'time': s3_time, 'trigger': 'sales_morning'}
            ]

            for msg in messages_to_schedule:
                self._safe_sheets_operation(
                    lambda m=msg: self.sheets.schedule_message({
                        'contact_id': contact_identifier,
                        'message_code': m['code'],
                        'scheduled_send_time': m['time'].isoformat(),
                        'status': 'pending',
                        'trigger_type': m['trigger']
                    }) if self.sheets else None
                )

            logger.info(f"Scheduled {len(messages_to_schedule)} Tree 1 messages for {contact_identifier}")

        except Exception as e:
            logger.error(f"Error scheduling Tree 1 messages: {e}")

    def _schedule_tree2_fallback(self, contact_identifier: str, hours: float):
        """
        Schedule B2 Ra (Tree 2 fallback) if no timeslot chosen within X hours

        Args:
            contact_identifier: Contact identifier
            hours: Hours to wait before sending
        """
        try:
            now = datetime.now(self.timezone)
            send_time = now + timedelta(hours=hours)

            self._safe_sheets_operation(
                lambda: self.sheets.schedule_message({
                    'contact_id': contact_identifier,
                    'message_code': 'B2_RA',
                    'scheduled_send_time': send_time.isoformat(),
                    'status': 'pending',
                    'trigger_type': 'tree2_fallback'
                }) if self.sheets else None
            )

            logger.info(f"Scheduled B2_RA for {contact_identifier} at {send_time}")

        except Exception as e:
            logger.warning(f"Error scheduling Tree 2 fallback: {e}")

    # ==================== TREE 2 RE-ENTRY ====================

    def _handle_already_attended(self, contact_identifier: str, first_name: str) -> bool:
        """
        Handle "I already attended" response from Tree 2
        Send B1 S1 (first sales message) and move back to Tree 1

        Args:
            contact_identifier: Contact identifier
            first_name: User's first name

        Returns:
            True if handled successfully
        """
        try:
            # Update to Tree 1
            self._safe_sheets_operation(
                lambda: self.sheets.update_contact(contact_identifier, {
                    'current_tree': 'Tree1',
                    'current_step': 'B1_S1'
                }) if self.sheets else None
            )

            # Send B1 S1
            message = self.templates['B1_S1'].format(
                name=first_name,
                membership_link=Config.MEMBERSHIP_LINK
            )
            self.api.send_message(contact_identifier, message)
            self._log_message(contact_identifier, message, 'outbound', 'B1_S1')

            # Schedule remaining sales messages
            now = datetime.now(self.timezone)
            shakeup_time = now + timedelta(minutes=15)  # 15 min after S1
            s2_time = now + timedelta(hours=1, minutes=45)  # ~2 hours after S1

            self._safe_sheets_operation(
                lambda: self.sheets.schedule_message({
                    'contact_id': contact_identifier,
                    'message_code': 'B1_SHAKEUP',
                    'scheduled_send_time': shakeup_time.isoformat(),
                    'status': 'pending',
                    'trigger_type': 'sales_shakeup'
                }) if self.sheets else None
            )

            self._safe_sheets_operation(
                lambda: self.sheets.schedule_message({
                    'contact_id': contact_identifier,
                    'message_code': 'B1_S2',
                    'scheduled_send_time': s2_time.isoformat(),
                    'status': 'pending',
                    'trigger_type': 'sales_followup'
                }) if self.sheets else None
            )

            logger.info(f"Sent B1_S1 to {contact_identifier} (already attended)")
            return True

        except Exception as e:
            logger.error(f"Error handling already attended: {e}")
            return False

    # ==================== MESSAGE LOGGING ====================

    def _log_message(self, contact_identifier: str, message_content: str, direction: str, message_code: str):
        """
        Log a message to Message_Log sheet

        Args:
            contact_identifier: Contact identifier
            message_content: Message text
            direction: 'inbound' or 'outbound'
            message_code: Message code (e.g., 'B1_Z2', 'B1_R1')
        """
        try:
            self._safe_sheets_operation(
                lambda: self.sheets.log_message({
                    'contact_id': contact_identifier,
                    'timestamp': datetime.now(self.timezone).isoformat(),
                    'direction': direction,
                    'message_code': message_code,
                    'message_content': message_content[:500],  # Truncate to 500 chars
                    'window_valid': 'Yes'
                }) if self.sheets else None
            )
        except Exception as e:
            logger.debug(f"Could not log message: {e}")

    # ==================== MANUAL MESSAGE SENDING (FOR API ENDPOINTS) ====================

    def send_reminder(self, contact_id: str, reminder_type: str) -> bool:
        """
        Manually send a reminder message (called by scheduler or API)

        Args:
            contact_id: Contact ID
            reminder_type: Type of reminder ('R1', 'R2', 'R3')

        Returns:
            True if sent successfully
        """
        try:
            # Get contact from sheets
            sheet_contact = self._safe_sheets_operation(
                lambda: self.sheets.get_contact(contact_id) if self.sheets else None
            )

            if not sheet_contact:
                logger.warning(f"Cannot send reminder to {contact_id}: not found")
                return False

            first_name = sheet_contact.get('first_name', 'there')
            chosen_timeslot = sheet_contact.get('chosen_timeslot')

            if not chosen_timeslot:
                logger.warning(f"Cannot send reminder to {contact_id}: no timeslot chosen")
                return False

            # Check 72-hour window
            window_expires_at = sheet_contact.get('window_expires_at')
            if window_expires_at:
                expires = datetime.fromisoformat(window_expires_at)
                now = datetime.now(self.timezone)
                if now > expires:
                    logger.warning(f"Cannot send reminder to {contact_id}: outside 72hr window")
                    return False

            # Get timeslot display
            timeslot_display = Config.get_timeslot_display(chosen_timeslot)

            # Select template
            template_key = f'B1_{reminder_type}'
            if template_key not in self.templates:
                logger.error(f"Unknown reminder type: {reminder_type}")
                return False

            message = self.templates[template_key].format(
                name=first_name,
                timeslot=timeslot_display,
                zoom_link=Config.ZOOM_PREVIEW_LINK
            )

            # Send message
            self.api.send_message(contact_id, message)
            self._log_message(contact_id, message, 'outbound', template_key)

            logger.info(f"Sent {reminder_type} reminder to {contact_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending reminder: {e}", exc_info=True)
            return False

    def send_sales_message(self, contact_id: str, sales_type: str) -> bool:
        """
        Manually send a sales message (called by scheduler or API)

        Args:
            contact_id: Contact ID
            sales_type: Type of sales message ('S1', 'SHAKEUP', 'S2')

        Returns:
            True if sent successfully
        """
        try:
            # Get contact from sheets
            sheet_contact = self._safe_sheets_operation(
                lambda: self.sheets.get_contact(contact_id) if self.sheets else None
            )

            if not sheet_contact:
                logger.warning(f"Cannot send sales message to {contact_id}: not found")
                return False

            first_name = sheet_contact.get('first_name', 'there')

            # Check 72-hour window
            window_expires_at = sheet_contact.get('window_expires_at')
            if window_expires_at:
                expires = datetime.fromisoformat(window_expires_at)
                now = datetime.now(self.timezone)
                if now > expires:
                    logger.warning(f"Cannot send sales message to {contact_id}: outside 72hr window")
                    return False

            # Select template
            template_key = f'B1_{sales_type}'
            if template_key not in self.templates:
                logger.error(f"Unknown sales message type: {sales_type}")
                return False

            message = self.templates[template_key].format(
                name=first_name,
                membership_link=Config.MEMBERSHIP_LINK,
                trial_link=Config.TRIAL_LINK
            )

            # Send message
            self.api.send_message(contact_id, message)
            self._log_message(contact_id, message, 'outbound', template_key)

            logger.info(f"Sent {sales_type} sales message to {contact_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending sales message: {e}", exc_info=True)
            return False
