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
        self.channel_id = None  # Store channel ID from webhook

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
            channel = webhook_data.get('channel', {})

            contact_id = contact.get('id')
            phone = contact.get('phone')

            # Extract channel ID (required for sending messages via Respond.io)
            # Use channel from webhook if available, otherwise use configured channel ID
            channel_id_raw = channel.get('id') if isinstance(channel, dict) else Config.RESPOND_CHANNEL_ID
            # Convert to integer (Respond.io API requires integer, not string)
            self.channel_id = int(channel_id_raw) if channel_id_raw else None
            logger.info(f"Channel ID: {self.channel_id}")

            # IMPORTANT: Make.com sends its own internal contact ID, NOT Respond.io contact ID
            # Always use phone number format for Respond.io API
            contact_identifier = f"phone:{phone}" if phone else contact_id

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

            # ===== CHECK IF EXISTING CONTACT =====
            # Get contact from sheets first to check if source is already determined
            sheet_contact = self._safe_sheets_operation(
                lambda: self.sheets.get_contact(contact_identifier) if self.sheets else None
            )

            # ===== DETECT OR RETRIEVE CONTACT SOURCE =====
            if sheet_contact and sheet_contact.get('contact_source'):
                # Existing contact - use stored source (never re-detect)
                contact_source = sheet_contact.get('contact_source')
                logger.info(f"✓ Existing contact - using stored source: {contact_source}")
            else:
                # New contact - detect source from first message
                contact_source = self._detect_contact_source(webhook_data)
                logger.info(f"✓ New contact - detected source: {contact_source}")

            # ===== RESET MESSAGING WINDOW =====
            # Every inbound message resets the messaging window (Meta WhatsApp Policy)
            # Window duration depends on source: 72h for Facebook Ads, 24h for Website
            self._reset_window(contact_identifier, contact_source)

            if not sheet_contact:
                # New contact - Start Tree 1 Flow: B1 Z1
                logger.info(f"New contact {contact_identifier}, starting Tree 1")
                return self._handle_new_contact(contact_identifier, phone, message_text, contact_source=contact_source, contact_data=contact)
            else:
                # Existing contact - Route based on current state
                logger.info(f"Existing contact {contact_identifier}, current tree: {sheet_contact.get('current_tree')}, step: {sheet_contact.get('current_step')}")
                return self._handle_existing_contact(contact_identifier, sheet_contact, message_text)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return False

    def _detect_contact_source(self, webhook_data: Dict) -> str:
        """
        Detect the contact source from webhook data

        DETECTION LOGIC:
        1. Check if custom field 'contact_source' is already set (existing contact)
        2. Check if message contains Facebook Ads trigger text
           → If YES: Facebook Ads source (72-hour window)
        3. Default to Website/Outside Lead (24-hour window)

        Args:
            webhook_data: Webhook payload from Respond.io

        Returns:
            Contact source ('facebook_ads' or 'website')
        """
        try:
            contact = webhook_data.get('contact', {})
            message = webhook_data.get('message', {})

            # ===== PRIORITY 1: Check if source already set (existing contact) =====
            custom_fields = contact.get('customFields', {}) if isinstance(contact, dict) else {}
            source_field = custom_fields.get('contact_source', '')

            if source_field in [Config.SOURCE_FACEBOOK_ADS, Config.SOURCE_WEBSITE]:
                logger.info(f"✓ Source already set: {source_field}")
                return source_field

            # ===== PRIORITY 2: Check message text for Facebook Ads trigger =====
            message_text = message.get('text', '') if isinstance(message, dict) else ''

            # Check for Facebook Ads trigger (case-insensitive)
            if Config.FACEBOOK_ADS_TRIGGER_MESSAGE.lower() in message_text.lower():
                logger.info(f"✓ Facebook Ads trigger detected: '{Config.FACEBOOK_ADS_TRIGGER_MESSAGE}'")
                logger.info("→ Source: facebook_ads (72-hour window - VERIFIED)")
                return Config.SOURCE_FACEBOOK_ADS

            # ===== DEFAULT: Website/Outside Lead (24-hour window) =====
            # All contacts without Facebook Ads trigger default to website (24h window)
            logger.info("✓ No Facebook Ads trigger found")
            logger.info("→ Source: website/outside lead (24-hour window - DEFAULT)")
            return Config.SOURCE_WEBSITE

        except Exception as e:
            logger.warning(f"Error detecting contact source: {e}")
            # Default to Website (24h window - conservative approach)
            logger.info("→ Defaulting to website due to error")
            return Config.SOURCE_WEBSITE

    def _reset_window(self, contact_identifier: str, contact_source: str):
        """
        Reset the messaging window for a contact (Meta WhatsApp Policy)
        Called on EVERY inbound message

        Window duration depends on contact source:
        - Facebook Ads: 72-hour window
        - Website/FB Page: 24-hour window

        Args:
            contact_identifier: Contact identifier
            contact_source: Contact source ('facebook_ads' or 'website')
        """
        try:
            now = datetime.now(self.timezone)
            window_hours = Config.get_window_duration(contact_source)
            window_expires_at = now + timedelta(hours=window_hours)

            # Update in sheets
            self._safe_sheets_operation(
                lambda: self.sheets.update_contact(contact_identifier, {
                    'last_inbound_msg_time': now.isoformat(),
                    'window_expires_at': window_expires_at.isoformat(),
                    'contact_source': contact_source
                }) if self.sheets else None
            )

            # Update in Respond.io (optional - custom field may not exist)
            try:
                self.api.update_window(contact_identifier, window_hours)
            except Exception as e:
                logger.debug(f"Could not update window in Respond.io: {e}")

            logger.info(f"Reset {window_hours}h window for {contact_identifier} ({contact_source}), expires: {window_expires_at}")

        except Exception as e:
            logger.warning(f"Failed to reset window: {e}")

    # ==================== NEW CONTACT FLOW ====================

    def _handle_new_contact(self, contact_identifier: str, phone: str, message_text: str, contact_source: str = None, contact_data: dict = None) -> bool:
        """
        Handle a brand new contact
        This triggers B1 Z1 (asking for name) if they haven't been added to sheets yet

        Args:
            contact_identifier: Contact identifier
            phone: Phone number
            message_text: Their first message
            contact_source: Contact source ('facebook_ads' or 'website')
            contact_data: Optional contact data from webhook (e.g., Make.com)

        Returns:
            True if handled successfully
        """
        try:
            # Default to website if not provided (conservative 24h window)
            if not contact_source:
                contact_source = Config.SOURCE_WEBSITE

            # Calculate window expiry based on source
            now = datetime.now(self.timezone)
            window_hours = Config.get_window_duration(contact_source)
            window_expires_at = now + timedelta(hours=window_hours)

            # Add to sheets with placeholder name
            # We'll get their actual name in the next message
            self._safe_sheets_operation(
                lambda: self.sheets.add_contact({
                    'contact_id': contact_identifier,
                    'phone': phone,
                    'first_name': 'Pending',  # Placeholder until they provide name
                    'current_tree': 'Tree1',
                    'current_step': 'B1_Z1',  # Waiting for name
                    'registration_time': now.isoformat(),
                    'last_inbound_msg_time': now.isoformat(),
                    'window_expires_at': window_expires_at.isoformat(),
                    'contact_source': contact_source
                }) if self.sheets else None
            )

            # Log their first message
            self._log_message(contact_identifier, message_text, 'inbound', 'FIRST_CONTACT')

            # Send B1 Z1 - Ask for name (using appropriate template based on source)
            self._send_b1_z1(contact_identifier, contact_source)

            logger.info(f"New contact {contact_identifier} added ({contact_source}, {window_hours}h window), sent B1_Z1")
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

            # Check if we're waiting for their name (B1_Z1 response)
            if current_step == 'B1_Z1':
                logger.info(f"Receiving name from {contact_identifier}")
                return self._handle_name_response(contact_identifier, message_text)

            # Check if we're waiting for day selection (B1_Z2 response)
            message_upper = message_text.upper().strip()
            if current_step == 'B1_Z2':
                if message_upper in ['S', 'U']:
                    logger.info(f"Day selection detected: {message_upper}")
                    return self._handle_day_selection(contact_identifier, sheet_contact, message_upper)
                else:
                    # Invalid day selection - send helpful error message
                    logger.warning(f"Invalid day selection from {contact_identifier}: '{message_text}'")
                    return self._handle_invalid_day_selection(contact_identifier, message_text)

            # Check if we're waiting for time selection (B1_Z2A response)
            if current_step == 'B1_Z2A':
                if message_upper in ['A', 'B', 'C', 'D', 'E']:
                    logger.info(f"Time selection detected: {message_upper}")
                    return self._handle_time_selection(contact_identifier, sheet_contact, message_upper)
                else:
                    # Invalid time selection - send helpful error message
                    logger.warning(f"Invalid time selection from {contact_identifier}: '{message_text}'")
                    return self._handle_invalid_time_selection(contact_identifier, message_text)

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

    def _send_b1_z1(self, contact_identifier: str, contact_source: str = None):
        """
        Send B1 Z1 - Ask for name
        All contacts now use the same message (24h window for all)

        Args:
            contact_identifier: Contact identifier
            contact_source: Contact source ('facebook_ads' or 'website')
        """
        try:
            # All contacts now get the same B1_Z1 message
            message = self.templates['B1_Z1']
            template_code = 'B1_Z1'

            self.api.send_message(contact_identifier, message, channel_id=self.channel_id)
            self._log_message(contact_identifier, message, 'outbound', template_code)

            logger.info(f"Sent {template_code} to {contact_identifier} ({contact_source})")

        except Exception as e:
            logger.error(f"Error sending B1_Z1: {e}")

    def _handle_name_response(self, contact_identifier: str, message_text: str) -> bool:
        """
        Handle response to B1_Z1 (name question)
        Extract name and send B1_Z2 with Zoom link

        Args:
            contact_identifier: Contact identifier
            message_text: User's response (their name)

        Returns:
            True if handled successfully
        """
        try:
            # Extract first name from their message
            first_name = self._extract_first_name(message_text)
            logger.info(f"Extracted name: {first_name}")

            # Update contact in sheets
            self._safe_sheets_operation(
                lambda: self.sheets.update_contact(contact_identifier, {
                    'first_name': first_name,
                    'current_step': 'B1_Z2'
                }) if self.sheets else None
            )

            # Log their name response
            self._log_message(contact_identifier, message_text, 'inbound', 'NAME_RESPONSE')

            # Send B1 Z2 - Zoom link + ask timeslot
            self._send_b1_z2(contact_identifier, first_name)

            # Schedule B2 Ra (fallback to Tree 2) in 2 hours if no timeslot chosen
            self._schedule_tree2_fallback(contact_identifier, hours=2)

            logger.info(f"Received name '{first_name}' from {contact_identifier}, sent B1_Z2")
            return True

        except Exception as e:
            logger.error(f"Error handling name response: {e}", exc_info=True)
            return False

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
                zoom_link=Config.ZOOM_PREVIEW_LINK,
                zoom_download_link=Config.ZOOM_DOWNLOAD_LINK
            )

            self.api.send_message(contact_identifier, message, channel_id=self.channel_id)
            self._log_message(contact_identifier, message, 'outbound', 'B1_Z2')

            logger.info(f"Sent B1_Z2 to {contact_identifier}")

        except Exception as e:
            logger.error(f"Error sending B1_Z2: {e}")

    def _handle_day_selection(self, contact_identifier: str, sheet_contact: Dict, day_code: str) -> bool:
        """
        Handle day selection (S or U)
        This is Step 1 of two-step selection

        Args:
            contact_identifier: Contact identifier
            sheet_contact: Contact data from sheets
            day_code: Selected day (S or U)

        Returns:
            True if handled successfully
        """
        try:
            first_name = sheet_contact.get('first_name', 'there')

            # Save selected day to sheets
            self._safe_sheets_operation(
                lambda: self.sheets.update_contact(contact_identifier, {
                    'selected_day': day_code,
                    'current_step': 'B1_Z2A'  # Move to time selection step
                }) if self.sheets else None
            )

            # Log the day selection
            self._log_message(contact_identifier, day_code, 'inbound', 'DAY_SELECT')

            # Send B1_Z2A - Ask for time
            message = self.templates['B1_Z2A']
            self.api.send_message(contact_identifier, message, channel_id=self.channel_id)
            self._log_message(contact_identifier, message, 'outbound', 'B1_Z2A')

            logger.info(f"Day {day_code} selected for {contact_identifier}, sent B1_Z2A")
            return True

        except Exception as e:
            logger.error(f"Error handling day selection: {e}", exc_info=True)
            return False

    def _handle_time_selection(self, contact_identifier: str, sheet_contact: Dict, time_code: str) -> bool:
        """
        Handle time selection (A, B, C, D, or E)
        This is Step 2 of two-step selection
        Combines with previously selected day to form full timeslot code

        Args:
            contact_identifier: Contact identifier
            sheet_contact: Contact data from sheets
            time_code: Selected time (A, B, C, D, E)

        Returns:
            True if handled successfully
        """
        try:
            first_name = sheet_contact.get('first_name', 'there')
            selected_day = sheet_contact.get('selected_day', 'S')  # Default to Saturday if not found

            # Combine day + time to form full timeslot code (e.g., "SA", "UB")
            full_timeslot = selected_day + time_code

            # Validate the combined timeslot exists
            if full_timeslot not in Config.TIME_SLOTS:
                logger.error(f"Invalid timeslot combination: {full_timeslot}")
                return False

            # Now proceed with the standard timeslot confirmation flow
            return self._handle_timeslot_selection(contact_identifier, sheet_contact, full_timeslot)

        except Exception as e:
            logger.error(f"Error handling time selection: {e}", exc_info=True)
            return False

    def _handle_invalid_day_selection(self, contact_identifier: str, invalid_input: str) -> bool:
        """
        Handle invalid day selection (user didn't send S or U)
        Send helpful error message and keep them in B1_Z2 step

        Args:
            contact_identifier: Contact identifier
            invalid_input: What the user actually sent

        Returns:
            True if handled successfully
        """
        try:
            # Log the invalid input
            self._log_message(contact_identifier, invalid_input, 'inbound', 'INVALID_DAY')

            # Send helpful error message
            error_message = """I didn't quite catch that 🌸

Please choose your preferred day:

S = Saturday
U = Sunday

Reply with just S or U"""

            self.api.send_message(contact_identifier, error_message, channel_id=self.channel_id)
            self._log_message(contact_identifier, error_message, 'outbound', 'ERROR_INVALID_DAY')

            # Keep them in B1_Z2 step (don't change current_step)
            logger.info(f"Sent invalid day error message to {contact_identifier}")
            return True

        except Exception as e:
            logger.error(f"Error handling invalid day selection: {e}", exc_info=True)
            return False

    def _handle_invalid_time_selection(self, contact_identifier: str, invalid_input: str) -> bool:
        """
        Handle invalid time selection (user didn't send A-E)
        Send helpful error message and keep them in B1_Z2A step

        Args:
            contact_identifier: Contact identifier
            invalid_input: What the user actually sent

        Returns:
            True if handled successfully
        """
        try:
            # Log the invalid input
            self._log_message(contact_identifier, invalid_input, 'inbound', 'INVALID_TIME')

            # Send helpful error message
            error_message = """I didn't quite catch that 🌸

Please choose your preferred time (UTC+7):

A = 15:30
B = 19:30
C = 20:00
D = 20:30
E = 21:00

Reply with just A, B, C, D or E"""

            self.api.send_message(contact_identifier, error_message, channel_id=self.channel_id)
            self._log_message(contact_identifier, error_message, 'outbound', 'ERROR_INVALID_TIME')

            # Keep them in B1_Z2A step (don't change current_step)
            logger.info(f"Sent invalid time error message to {contact_identifier}")
            return True

        except Exception as e:
            logger.error(f"Error handling invalid time selection: {e}", exc_info=True)
            return False

    def _handle_timeslot_selection(self, contact_identifier: str, sheet_contact: Dict, timeslot: str) -> bool:
        """
        Handle final timeslot selection (after day+time combination)
        This is B1 Z2a1 - Confirm slot + send invite card

        Args:
            contact_identifier: Contact identifier
            sheet_contact: Contact data from sheets
            timeslot: Full timeslot code (SA, SB, SC, SD, SE, UA, UB, UC, UD, UE)

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
            self.api.send_message(contact_identifier, confirmation_message, channel_id=self.channel_id)
            self._log_message(contact_identifier, confirmation_message, 'outbound', 'B1_Z2A1')

            # Send B1 Z2a2 - Forward invite card
            invite_card = self.templates['B1_Z2A2'].format(
                timeslot=timeslot_display,
                registration_link=Config.REGISTRATION_LINK or 'https://your-landing-page.com',
                sender_name=first_name
            )
            self.api.send_message(contact_identifier, invite_card, channel_id=self.channel_id)
            self._log_message(contact_identifier, invite_card, 'outbound', 'B1_Z2A2')

            # Schedule all Tree 1 timed messages
            self._schedule_tree1_messages(contact_identifier, session_datetime)

            logger.info(f"Confirmed timeslot {timeslot} for {contact_identifier}, scheduled reminders and sales messages")
            return True

        except Exception as e:
            logger.error(f"Error handling timeslot selection: {e}", exc_info=True)
            return False

    def _calculate_next_session(self, timeslot: str) -> datetime:
        """
        Calculate the next session datetime for a given timeslot

        Args:
            timeslot: Timeslot letter (A, B, C, D)

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
            self.api.send_message(contact_identifier, message, channel_id=self.channel_id)
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
