"""
Message Handler Service
Processes incoming messages and manages conversation flows
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

    def _is_valid_name(self, name: str) -> bool:
        """
        Check if a name is valid (not just emoji or placeholder)

        Args:
            name: The name to validate

        Returns:
            True if valid name, False if emoji/placeholder
        """
        if not name:
            return False

        # Remove whitespace
        name = name.strip()

        if not name:
            return False

        # Check if name contains at least one alphabetic character
        # This filters out emoji-only names like "😊"
        has_alpha = any(c.isalpha() for c in name)

        return has_alpha

    def _safe_sheets_operation(self, operation, *args, **kwargs):
        """Safely execute a Google Sheets operation"""
        if not self.sheets:
            logger.debug("Skipping sheets operation (not configured)")
            return
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Sheets operation failed: {e}")

    def process_message(self, webhook_data: Dict) -> bool:
        """
        Process incoming webhook message from Respond.io

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

            # Prefer phone number over contact ID (since UI ID doesn't work with API)
            contact_identifier = f"phone:{phone}" if phone else contact_id

            if not contact_identifier:
                logger.error("No contact identifier (phone or ID) in webhook data")
                return False

            logger.info(f"Using contact identifier: {contact_identifier}")

            # Update 24-hour window (optional - custom field may not exist yet)
            try:
                self.api.update_24hr_window(contact_identifier)
            except Exception as e:
                logger.warning(f"Could not update 24hr window (custom field may not exist): {e}")

            # Get message text
            message_text = message.get('text', '').strip()

            if not message_text:
                logger.info(f"Non-text message from {contact_identifier}, ignoring")
                return True

            logger.info(f"Processing message from {contact_identifier}: {message_text}")

            # Get contact's current state
            contact_info = self.api.get_contact(contact_identifier)
            custom_fields = contact_info.get('customFields', {})

            # firstName is a standard field, not a custom field
            first_name = contact_info.get('firstName') or custom_fields.get(Config.CUSTOM_FIELDS['FIRST_NAME'])
            chosen_timeslot = custom_fields.get(Config.CUSTOM_FIELDS['CHOSEN_TIMESLOT'])
            thumbs_up = custom_fields.get(Config.CUSTOM_FIELDS['THUMBS_UP'])

            # Validate that firstName is a real name (not emoji/placeholder)
            has_valid_name = self._is_valid_name(first_name)

            # Debug logging
            logger.info(f"Contact state - firstName: '{first_name}', has_valid_name: {has_valid_name}, chosen_timeslot: '{chosen_timeslot}', thumbs_up: '{thumbs_up}'")

            # Route to appropriate handler based on conversation state

            # Check if this is a timeslot selection (A-E) - handle immediately
            message_upper = message_text.upper().strip()
            if message_upper in ['A', 'B', 'C', 'D', 'E']:
                # This is a timeslot selection (new or changing)
                display_name = first_name if has_valid_name else "there"
                logger.info(f"Timeslot selection detected: {message_upper}")
                return self._handle_timeslot_selection(contact_identifier, message_text, display_name)

            # Check Google Sheets to see if contact has been welcomed before
            sheet_contact = self._safe_sheets_operation(
                lambda: self.sheets.get_contact(contact_identifier) if self.sheets else None
            )

            # If contact exists in Sheets, they've been welcomed - just acknowledge
            if sheet_contact:
                logger.info(f"Contact {contact_identifier} exists in Sheets, acknowledging message")
                # Check if they sent thumbs up
                if message_text == '👍' and thumbs_up != 'Yes':
                    return self._handle_thumbs_up(contact_identifier)
                # General conversation - just acknowledge
                return True

            # New contact not in Sheets - send welcome and add them
            logger.info(f"New contact not in Sheets, sending welcome")
            display_name = first_name if has_valid_name else "there"

            # Add to Google Sheets first
            if not phone:
                phone = contact_info.get('phone', '')

            self._safe_sheets_operation(
                lambda: self.sheets.add_contact({
                    'contact_id': contact_identifier,
                    'whatsapp_number': phone,
                    'first_name': display_name,
                    'registration_time': datetime.now().isoformat()
                }) if self.sheets else None
            )

            # Send welcome message with Zoom link and timeslot options
            zoom_message = self.templates['SEND_ZOOM_LINK'].format(
                name=display_name,
                zoom_link=Config.ZOOM_PREVIEW_LINK
            )
            self.api.send_message(contact_identifier, zoom_message)
            logger.info(f"Sent welcome and Zoom link to {contact_identifier}")
            return True

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return False

    def _ask_for_name(self, contact_identifier: str) -> bool:
        """
        Ask new contact for their name (Step 1 of new contact flow)

        Args:
            contact_identifier: Contact identifier (phone:+xxx or ID)

        Returns:
            True if handled successfully
        """
        logger.info(f"New contact {contact_identifier}, asking for name")

        # Mark that we've asked for their name
        try:
            self.api.update_contact_field(
                contact_identifier,
                Config.CUSTOM_FIELDS['NAME_REQUESTED'],
                'Yes'
            )
        except Exception as e:
            logger.warning(f"Could not save name_requested to custom field: {e}")

        # Send ASK_NAME template
        self.api.send_message(contact_identifier, self.templates['ASK_NAME'])

        logger.info(f"Asked {contact_identifier} for their name")
        return True

    def _handle_name_received(self, contact_identifier: str, message_text: str, phone: str = None) -> bool:
        """
        Handle name received from new contact (Step 2 of new contact flow)

        Args:
            contact_identifier: Contact identifier (phone:+xxx or ID)
            message_text: The name provided by the user
            phone: Phone number if available

        Returns:
            True if handled successfully
        """
        logger.info(f"Received name from {contact_identifier}: {message_text}")

        # Extract first name (take first word, capitalize)
        first_name = message_text.split()[0].strip().capitalize()

        # Update contact with first name (optional - custom field may not exist yet)
        try:
            self.api.update_contact_field(
                contact_identifier,
                Config.CUSTOM_FIELDS['FIRST_NAME'],
                first_name
            )
        except Exception as e:
            logger.warning(f"Could not save firstName to custom field: {e}")

        # Log to Google Sheets
        if not phone:
            contact_data = self.api.get_contact(contact_identifier)
            phone = contact_data.get('phone', '')

        self._safe_sheets_operation(
            lambda: self.sheets.add_contact({
                'contact_id': contact_identifier,
                'whatsapp_number': phone,
                'first_name': first_name,
                'registration_time': datetime.now().isoformat()
            }) if self.sheets else None
        )

        # Send Zoom link message (B1 Z2)
        zoom_message = self.templates['SEND_ZOOM_LINK'].format(
            name=first_name,
            zoom_link=Config.ZOOM_PREVIEW_LINK
        )

        self.api.send_message(contact_identifier, zoom_message)

        logger.info(f"Sent Zoom link to {contact_identifier} ({first_name})")
        return True

    def _handle_timeslot_selection(self, contact_identifier: str, message_text: str,
                                   first_name: str) -> bool:
        """
        Handle timeslot selection (A, B, C, D, or E)

        Args:
            contact_identifier: Contact identifier
            message_text: Message from user
            first_name: User's first name

        Returns:
            True if handled successfully
        """
        # Extract timeslot letter (A, B, C, D, or E)
        # Match only standalone letters or with minimal surrounding text
        message_upper = message_text.upper().strip()
        timeslot = None

        # First check if message is exactly a single letter
        if message_upper in ['A', 'B', 'C', 'D', 'E']:
            timeslot = message_upper
        else:
            # Check for letter with common surrounding characters (e.g., "A)", "(B", "C.")
            import re
            for slot in ['A', 'B', 'C', 'D', 'E']:
                # Match slot at word boundary or with punctuation
                pattern = rf'\b{slot}\b|^{slot}[\)\.]|[\(\[]{slot}[\)\]]?'
                if re.search(pattern, message_upper):
                    timeslot = slot
                    break

        if not timeslot:
            logger.info(f"No valid timeslot in message from {contact_identifier}: '{message_text}'")
            # Send a friendly reminder about valid options
            reminder = f"I didn't quite catch that, {first_name}! 😊\n\nPlease reply with just the letter of your preferred time:\nA, B, C, D, or E"
            self.api.send_message(contact_identifier, reminder)
            return True

        # Get timeslot info
        slot_info = Config.TIME_SLOTS[timeslot]

        # Calculate next session datetime
        session_datetime = self._calculate_next_session(timeslot)

        # Update contact fields (optional - custom fields may not exist yet)
        try:
            self.api.update_contact_field(
                contact_identifier,
                Config.CUSTOM_FIELDS['CHOSEN_TIMESLOT'],
                timeslot
            )
        except Exception as e:
            logger.warning(f"Could not save timeslot to custom field: {e}")

        # Update Google Sheets
        self._safe_sheets_operation(
            lambda: self.sheets.update_contact(contact_identifier, {
                'chosen_timeslot': timeslot,
                'session_datetime': session_datetime.isoformat()
            }) if self.sheets else None
        )

        # Send confirmation message (B1 Z2a1)
        confirmation_message = self.templates['CONFIRM_TIMESLOT'].format(
            day=slot_info['day'],
            time=slot_info['time'].strftime('%H:%M'),
            zoom_link=Config.ZOOM_PREVIEW_LINK
        )

        self.api.send_message(contact_identifier, confirmation_message)

        logger.info(f"Confirmed timeslot {timeslot} for {contact_identifier}")
        return True

    def _handle_thumbs_up(self, contact_identifier: str) -> bool:
        """
        Handle thumbs up confirmation

        Args:
            contact_identifier: Contact identifier

        Returns:
            True if handled successfully
        """
        logger.info(f"Received thumbs up from {contact_identifier}")

        # Update contact field (optional - custom field may not exist yet)
        try:
            self.api.update_contact_field(
                contact_identifier,
                Config.CUSTOM_FIELDS['THUMBS_UP'],
                'Yes'
            )
        except Exception as e:
            logger.warning(f"Could not save thumbs_up to custom field: {e}")

        # Update Google Sheets
        self._safe_sheets_operation(
            lambda: self.sheets.update_contact(contact_identifier, {'thumbs_up': 'Yes'}) if self.sheets else None
        )

        return True

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

    def send_reminder(self, contact_id: str, reminder_type: str) -> bool:
        """
        Send a reminder message to a contact

        Args:
            contact_id: Contact ID
            reminder_type: Type of reminder ('12h', '60min', '10min')

        Returns:
            True if sent successfully
        """
        try:
            # Get contact info from Google Sheets (source of truth)
            sheet_contact = self._safe_sheets_operation(
                lambda: self.sheets.get_contact(contact_id) if self.sheets else None
            )

            if not sheet_contact:
                logger.warning(f"Cannot send reminder to {contact_id}: not found in Google Sheets")
                return False

            # Get data from Sheets
            first_name = sheet_contact.get('first_name')
            chosen_timeslot = sheet_contact.get('chosen_timeslot')
            thumbs_up = sheet_contact.get('thumbs_up')

            # Validate
            if not self._is_valid_name(first_name) or not chosen_timeslot:
                logger.warning(f"Cannot send reminder to {contact_id}: missing info (firstName: {first_name}, timeslot: {chosen_timeslot})")
                return False

            # Check 24-hour window
            if not self.api.check_24hr_window(contact_id):
                logger.warning(f"Cannot send reminder to {contact_id}: outside 24hr window")
                return False

            # Get session time
            slot_info = Config.TIME_SLOTS[chosen_timeslot]
            session_time = slot_info['time'].strftime('%H:%M')

            # Select appropriate message template
            if reminder_type == '12h':
                if thumbs_up == 'Yes':
                    template = self.templates['REMINDER_12H_NO_THUMBS']
                else:
                    template = self.templates['REMINDER_12H_WITH_THUMBS']

                message = template.format(
                    name=first_name,
                    time=session_time,
                    zoom_link=Config.ZOOM_PREVIEW_LINK
                )

                # Mark as sent
                self.api.update_contact_field(
                    contact_id,
                    Config.CUSTOM_FIELDS['REMINDER_12H'],
                    'Yes'
                )
                self._safe_sheets_operation(
                    lambda: self.sheets.update_contact(contact_id, {'reminder_12h_sent': 'Yes'}) if self.sheets else None
                )

            elif reminder_type == '60min':
                message = self.templates['REMINDER_60MIN'].format(
                    name=first_name,
                    time=session_time,
                    zoom_link=Config.ZOOM_PREVIEW_LINK
                )

                self.api.update_contact_field(
                    contact_id,
                    Config.CUSTOM_FIELDS['REMINDER_60MIN'],
                    'Yes'
                )
                self._safe_sheets_operation(
                    lambda: self.sheets.update_contact(contact_id, {'reminder_60min_sent': 'Yes'}) if self.sheets else None
                )

            elif reminder_type == '10min':
                message = self.templates['REMINDER_10MIN'].format(
                    name=first_name,
                    time=session_time,
                    zoom_link=Config.ZOOM_PREVIEW_LINK
                )

                self.api.update_contact_field(
                    contact_id,
                    Config.CUSTOM_FIELDS['REMINDER_10MIN'],
                    'Yes'
                )
                self._safe_sheets_operation(
                    lambda: self.sheets.update_contact(contact_id, {'reminder_10min_sent': 'Yes'}) if self.sheets else None
                )

            else:
                logger.error(f"Unknown reminder type: {reminder_type}")
                return False

            # Send the message
            self.api.send_message(contact_id, message)
            logger.info(f"Sent {reminder_type} reminder to {contact_id}")

            return True

        except Exception as e:
            logger.error(f"Error sending reminder to {contact_id}: {e}", exc_info=True)
            return False

    def send_sales_message(self, contact_id: str, sales_type: str) -> bool:
        """
        Send a sales message to a contact

        Args:
            contact_id: Contact ID
            sales_type: Type of sales message ('S1', 'SHAKEUP', 'S2', etc.)

        Returns:
            True if sent successfully
        """
        try:
            # Check 24-hour window
            if not self.api.check_24hr_window(contact_id):
                logger.warning(f"Cannot send sales message to {contact_id}: outside 24hr window")
                return False

            # Get contact info
            contact = self.api.get_contact(contact_id)
            custom_fields = contact.get('customFields', {})
            first_name = custom_fields.get(Config.CUSTOM_FIELDS['FIRST_NAME'], 'there')

            # Select message template
            template_key = f'SALES_{sales_type}' if sales_type in ['S1', 'S2'] else sales_type

            if template_key not in self.templates:
                logger.error(f"Unknown sales message type: {sales_type}")
                return False

            message = self.templates[template_key].format(name=first_name)

            # Send the message
            self.api.send_message(contact_id, message)
            logger.info(f"Sent {sales_type} sales message to {contact_id}")

            return True

        except Exception as e:
            logger.error(f"Error sending sales message to {contact_id}: {e}", exc_info=True)
            return False
