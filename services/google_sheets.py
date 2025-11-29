"""
Google Sheets Integration Service
Handles data logging and tracking in Google Sheets using Service Account
Supports multi-sheet structure for Inner Joy flow automation
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import base64
import os
import uuid

import gspread
from google.oauth2.service_account import Credentials

from config import Config

logger = logging.getLogger(__name__)


class GoogleSheetsError(Exception):
    """Custom exception for Google Sheets errors"""
    pass


class GoogleSheetsService:
    """Manages Google Sheets operations for contact tracking using Service Account"""

    def __init__(self):
        self.spreadsheet_id = Config.GOOGLE_SHEETS_ID
        self.client = None
        self.spreadsheet = None
        self.sheets = {}  # Cache for sheet objects
        self._authenticate()
        self._init_sheets()

    def _authenticate(self):
        """Authenticate with Google Sheets API using Service Account"""
        try:
            # Define the required scopes
            scopes = ['https://www.googleapis.com/auth/spreadsheets']

            # Check if credentials are provided as base64 environment variable (Railway)
            google_service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

            if google_service_account_json:
                # Decode base64 and load JSON credentials
                logger.info("Loading credentials from GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
                try:
                    decoded_json = base64.b64decode(google_service_account_json).decode('utf-8')
                    credentials_info = json.loads(decoded_json)
                    creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
                    logger.info("Successfully loaded credentials from base64 environment variable")
                except Exception as e:
                    logger.error(f"Failed to decode base64 credentials: {e}")
                    raise GoogleSheetsError(f"Failed to decode base64 credentials: {e}")
            else:
                # Fall back to file-based credentials (local development)
                logger.info(f"Loading credentials from file: {Config.GOOGLE_CREDENTIALS_FILE}")
                creds = Credentials.from_service_account_file(
                    Config.GOOGLE_CREDENTIALS_FILE,
                    scopes=scopes
                )

            # Authorize the client
            self.client = gspread.authorize(creds)

            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)

            logger.info("Successfully authenticated with Google Sheets using Service Account")

        except FileNotFoundError:
            logger.error(f"Credentials file not found: {Config.GOOGLE_CREDENTIALS_FILE}")
            raise GoogleSheetsError(f"Credentials file not found: {Config.GOOGLE_CREDENTIALS_FILE}")
        except Exception as error:
            logger.error(f"Failed to authenticate with Google Sheets: {error}")
            raise GoogleSheetsError(f"Authentication failed: {error}")

    def _init_sheets(self):
        """Initialize access to all required sheets"""
        try:
            # Get or create each sheet
            sheet_names = ['Contacts', 'Scheduled_Messages', 'Message_Log', 'CSV_Processing', 'Config']

            existing_sheets = {ws.title: ws for ws in self.spreadsheet.worksheets()}

            for sheet_name in sheet_names:
                if sheet_name in existing_sheets:
                    self.sheets[sheet_name] = existing_sheets[sheet_name]
                else:
                    # Create the sheet
                    self.sheets[sheet_name] = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
                    logger.info(f"Created new sheet: {sheet_name}")

            logger.info(f"Initialized {len(self.sheets)} sheets")

        except Exception as error:
            logger.error(f"Failed to initialize sheets: {error}")
            raise GoogleSheetsError(f"Sheet initialization failed: {error}")

    def initialize_sheet(self):
        """Initialize all sheets with headers if not already set"""
        try:
            # Contacts sheet headers
            contacts_headers = [
                'contact_id', 'phone', 'first_name', 'contact_source', 'current_tree', 'current_step',
                'registration_time', 'chosen_timeslot', 'session_datetime',
                'last_inbound_msg_time', 'window_expires_at', 'thumbs_up_received',
                'payment_status', 'member_type', 'trial_start', 'trial_end',
                'attended_status', 'csv_follow_up_group', 'tier2_approved', 'last_updated'
            ]

            # Scheduled_Messages sheet headers
            scheduled_headers = [
                'message_id', 'contact_id', 'message_code', 'scheduled_send_time',
                'status', 'sent_at', 'trigger_type', 'created_at'
            ]

            # Message_Log sheet headers
            log_headers = [
                'log_id', 'contact_id', 'timestamp', 'direction', 'message_code',
                'message_content', 'window_valid'
            ]

            # CSV_Processing sheet headers
            csv_headers = [
                'contact_id', 'first_name', 'weekend_date', 'zoom_attended',
                'attendance_count', 'sales_status', 'follow_up_group', 'follow_up_sent_date'
            ]

            # Config sheet headers
            config_headers = ['key', 'value']

            # Initialize each sheet
            sheets_config = {
                'Contacts': contacts_headers,
                'Scheduled_Messages': scheduled_headers,
                'Message_Log': log_headers,
                'CSV_Processing': csv_headers,
                'Config': config_headers
            }

            for sheet_name, headers in sheets_config.items():
                sheet = self.sheets[sheet_name]
                existing_headers = sheet.row_values(1) if sheet.row_count > 0 else []

                if not existing_headers or existing_headers[0] == '':
                    # Write headers
                    sheet.update('A1', [headers])
                    logger.info(f"Initialized {sheet_name} sheet with headers")
                else:
                    logger.info(f"{sheet_name} sheet already initialized")

            # Initialize config sheet with default values
            self._init_config_sheet()

            logger.info("All sheets initialized successfully")

        except Exception as error:
            logger.error(f"Failed to initialize sheets: {error}")
            raise GoogleSheetsError(f"Sheet initialization failed: {error}")

    def _append_row_safe(self, sheet, row_data):
        """
        Safely append a row to a sheet using update() instead of append_row()
        This is a workaround for append_row() silently failing

        Args:
            sheet: The worksheet object
            row_data: List of values to append
        """
        try:
            # Get current row count
            all_values = sheet.get_all_values()
            next_row_num = len(all_values) + 1

            # Calculate range (A to last column needed)
            num_cols = len(row_data)
            end_col = chr(64 + num_cols)  # A=65, so 64+1=A, 64+2=B, etc.
            range_name = f'A{next_row_num}:{end_col}{next_row_num}'

            # Use update() with RAW value input option
            sheet.update(range_name=range_name, values=[row_data], value_input_option='RAW')

            return True
        except Exception as e:
            logger.error(f"Failed to append row: {e}")
            return False

    def _init_config_sheet(self):
        """Initialize Config sheet with default system variables"""
        try:
            config_sheet = self.sheets['Config']
            existing_rows = config_sheet.get_all_values()

            # Default config values
            defaults = {
                'zoom_link_preview': Config.ZOOM_PREVIEW_LINK,
                'zoom_link_members': Config.ZOOM_MEMBER_LINK,
                'membership_link': Config.MEMBERSHIP_LINK,
                'trial_link': Config.TRIAL_LINK,
                'registration_link': Config.REGISTRATION_LINK,
                'timezone': Config.TIMEZONE,
                'tier2_approved': 'No'  # Important: Controls Friday follow-ups
            }

            # If only headers exist, add defaults
            if len(existing_rows) <= 1:
                rows_to_add = [[key, value] for key, value in defaults.items()]
                # Use safe append for each row
                for row in rows_to_add:
                    self._append_row_safe(config_sheet, row)
                logger.info("Initialized Config sheet with default values")

        except Exception as error:
            logger.warning(f"Could not initialize config values: {error}")

    # ==================== CONTACTS SHEET ====================

    def add_contact(self, contact_data: Dict[str, Any]) -> bool:
        """
        Add a new contact to the Contacts sheet

        Args:
            contact_data: Dictionary with contact information

        Returns:
            True if successful, False otherwise
        """
        try:
            row = [
                contact_data.get('contact_id', ''),
                contact_data.get('phone', ''),
                contact_data.get('first_name', ''),
                contact_data.get('contact_source', 'facebook_ads'),  # Default to facebook_ads
                contact_data.get('current_tree', 'Tree1'),
                contact_data.get('current_step', 'B1_Z1'),
                contact_data.get('registration_time', datetime.now().isoformat()),
                contact_data.get('chosen_timeslot', ''),
                contact_data.get('session_datetime', ''),
                contact_data.get('last_inbound_msg_time', datetime.now().isoformat()),
                contact_data.get('window_expires_at', ''),
                contact_data.get('thumbs_up_received', 'No'),
                contact_data.get('payment_status', 'None'),
                contact_data.get('member_type', ''),
                contact_data.get('trial_start', ''),
                contact_data.get('trial_end', ''),
                contact_data.get('attended_status', ''),
                contact_data.get('csv_follow_up_group', ''),
                contact_data.get('tier2_approved', 'No'),
                datetime.now().isoformat()
            ]

            success = self._append_row_safe(self.sheets['Contacts'], row)
            if success:
                logger.info(f"Added contact {contact_data.get('contact_id')} ({contact_data.get('contact_source', 'facebook_ads')}) to Contacts sheet")
            return success

        except Exception as error:
            logger.error(f"Failed to add contact: {error}")
            return False

    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing contact's information

        Args:
            contact_id: Contact ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            row_index = self._find_contact_row(contact_id)

            if row_index is None:
                logger.warning(f"Contact {contact_id} not found in sheet")
                return False

            # Map field names to column numbers (1-indexed)
            field_columns = {
                'phone': 2,
                'first_name': 3,
                'contact_source': 4,
                'current_tree': 5,
                'current_step': 6,
                'registration_time': 7,
                'chosen_timeslot': 8,
                'session_datetime': 9,
                'last_inbound_msg_time': 10,
                'window_expires_at': 11,
                'thumbs_up_received': 12,
                'payment_status': 13,
                'member_type': 14,
                'trial_start': 15,
                'trial_end': 16,
                'attended_status': 17,
                'csv_follow_up_group': 18,
                'tier2_approved': 19,
                'last_updated': 20
            }

            # Update last_updated timestamp
            updates['last_updated'] = datetime.now().isoformat()

            # Update each field
            for field, value in updates.items():
                if field in field_columns:
                    col_index = field_columns[field]
                    self.sheets['Contacts'].update_cell(row_index, col_index, value)

            logger.info(f"Updated contact {contact_id} in sheet")
            return True

        except Exception as error:
            logger.error(f"Failed to update contact: {error}")
            return False

    def _find_contact_row(self, contact_id: str) -> Optional[int]:
        """
        Find the row number for a given contact ID in Contacts sheet

        Args:
            contact_id: Contact ID to find

        Returns:
            Row number (1-indexed) or None if not found
        """
        try:
            contact_ids = self.sheets['Contacts'].col_values(1)

            for i, cid in enumerate(contact_ids):
                if cid == contact_id:
                    return i + 1

            return None

        except Exception as error:
            logger.error(f"Failed to find contact row: {error}")
            return None

    def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get contact information from the Contacts sheet

        Args:
            contact_id: Contact ID to retrieve

        Returns:
            Dictionary with contact data or None if not found
        """
        try:
            row_index = self._find_contact_row(contact_id)

            if row_index is None:
                return None

            row = self.sheets['Contacts'].row_values(row_index)

            contact_data = {
                'contact_id': row[0] if len(row) > 0 else '',
                'phone': row[1] if len(row) > 1 else '',
                'first_name': row[2] if len(row) > 2 else '',
                'contact_source': row[3] if len(row) > 3 else 'facebook_ads',
                'current_tree': row[4] if len(row) > 4 else 'Tree1',
                'current_step': row[5] if len(row) > 5 else '',
                'registration_time': row[6] if len(row) > 6 else '',
                'chosen_timeslot': row[7] if len(row) > 7 else '',
                'session_datetime': row[8] if len(row) > 8 else '',
                'last_inbound_msg_time': row[9] if len(row) > 9 else '',
                'window_expires_at': row[10] if len(row) > 10 else '',
                'thumbs_up_received': row[11] if len(row) > 11 else 'No',
                'payment_status': row[12] if len(row) > 12 else 'None',
                'member_type': row[13] if len(row) > 13 else '',
                'trial_start': row[14] if len(row) > 14 else '',
                'trial_end': row[15] if len(row) > 15 else '',
                'attended_status': row[16] if len(row) > 16 else '',
                'csv_follow_up_group': row[17] if len(row) > 17 else '',
                'tier2_approved': row[18] if len(row) > 18 else 'No',
                'last_updated': row[19] if len(row) > 19 else ''
            }

            return contact_data

        except Exception as error:
            logger.error(f"Failed to get contact: {error}")
            return None

    def get_all_contacts(self) -> List[Dict[str, Any]]:
        """
        Get all contacts from the Contacts sheet

        Returns:
            List of contact dictionaries
        """
        try:
            all_rows = self.sheets['Contacts'].get_all_values()[1:]  # Skip header
            contacts = []

            for row in all_rows:
                if not row or not row[0]:
                    continue

                contact_data = {
                    'contact_id': row[0] if len(row) > 0 else '',
                    'phone': row[1] if len(row) > 1 else '',
                    'first_name': row[2] if len(row) > 2 else '',
                    'contact_source': row[3] if len(row) > 3 else 'facebook_ads',
                    'current_tree': row[4] if len(row) > 4 else 'Tree1',
                    'current_step': row[5] if len(row) > 5 else '',
                    'registration_time': row[6] if len(row) > 6 else '',
                    'chosen_timeslot': row[7] if len(row) > 7 else '',
                    'session_datetime': row[8] if len(row) > 8 else '',
                    'last_inbound_msg_time': row[9] if len(row) > 9 else '',
                    'window_expires_at': row[10] if len(row) > 10 else '',
                    'thumbs_up_received': row[11] if len(row) > 11 else 'No',
                    'payment_status': row[12] if len(row) > 12 else 'None',
                    'member_type': row[13] if len(row) > 13 else '',
                    'trial_start': row[14] if len(row) > 14 else '',
                    'trial_end': row[15] if len(row) > 15 else '',
                    'attended_status': row[16] if len(row) > 16 else '',
                    'csv_follow_up_group': row[17] if len(row) > 17 else '',
                    'tier2_approved': row[18] if len(row) > 18 else 'No',
                    'last_updated': row[19] if len(row) > 19 else ''
                }

                contacts.append(contact_data)

            logger.info(f"Retrieved {len(contacts)} contacts from sheet")
            return contacts

        except Exception as error:
            logger.error(f"Failed to get all contacts: {error}")
            return []

    # ==================== SCHEDULED MESSAGES ====================

    def schedule_message(self, message_data: Dict[str, Any]) -> str:
        """
        Add a message to the scheduled messages queue

        Args:
            message_data: Dictionary with message details

        Returns:
            Message ID if successful, empty string otherwise
        """
        try:
            message_id = message_data.get('message_id', str(uuid.uuid4()))

            row = [
                message_id,
                message_data.get('contact_id', ''),
                message_data.get('message_code', ''),
                message_data.get('scheduled_send_time', ''),
                message_data.get('status', 'pending'),
                message_data.get('sent_at', ''),
                message_data.get('trigger_type', ''),
                datetime.now().isoformat()
            ]

            success = self._append_row_safe(self.sheets['Scheduled_Messages'], row)
            if success:
                logger.info(f"Scheduled message {message_data.get('message_code')} for {message_data.get('contact_id')} at {message_data.get('scheduled_send_time')}")
                return message_id
            else:
                logger.error(f"Failed to schedule message {message_data.get('message_code')}")
                return ''

        except Exception as error:
            logger.error(f"Failed to schedule message: {error}")
            return ''

    def get_pending_messages(self) -> List[Dict[str, Any]]:
        """
        Get all pending scheduled messages

        Returns:
            List of pending message dictionaries
        """
        try:
            all_rows = self.sheets['Scheduled_Messages'].get_all_values()[1:]
            pending_messages = []

            for row in all_rows:
                if not row or len(row) < 5:
                    continue

                status = row[4] if len(row) > 4 else ''
                if status == 'pending':
                    message_data = {
                        'message_id': row[0],
                        'contact_id': row[1] if len(row) > 1 else '',
                        'message_code': row[2] if len(row) > 2 else '',
                        'scheduled_send_time': row[3] if len(row) > 3 else '',
                        'status': status,
                        'sent_at': row[5] if len(row) > 5 else '',
                        'trigger_type': row[6] if len(row) > 6 else '',
                        'created_at': row[7] if len(row) > 7 else ''
                    }
                    pending_messages.append(message_data)

            return pending_messages

        except Exception as error:
            logger.error(f"Failed to get pending messages: {error}")
            return []

    def update_message_status(self, message_id: str, status: str, sent_at: str = None) -> bool:
        """
        Update the status of a scheduled message

        Args:
            message_id: Message ID to update
            status: New status ('pending', 'sent', 'failed', 'cancelled')
            sent_at: Timestamp when sent (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the message row
            message_ids = self.sheets['Scheduled_Messages'].col_values(1)

            for i, mid in enumerate(message_ids):
                if mid == message_id:
                    row_index = i + 1
                    self.sheets['Scheduled_Messages'].update_cell(row_index, 5, status)

                    if sent_at:
                        self.sheets['Scheduled_Messages'].update_cell(row_index, 6, sent_at)

                    logger.info(f"Updated message {message_id} status to {status}")
                    return True

            logger.warning(f"Message {message_id} not found")
            return False

        except Exception as error:
            logger.error(f"Failed to update message status: {error}")
            return False

    def cancel_scheduled_messages(self, contact_id: str, message_codes: List[str] = None) -> bool:
        """
        Cancel scheduled messages for a contact (e.g., when they switch trees)

        Args:
            contact_id: Contact ID
            message_codes: List of message codes to cancel (None = cancel all pending)

        Returns:
            True if successful
        """
        try:
            all_rows = self.sheets['Scheduled_Messages'].get_all_values()

            for i, row in enumerate(all_rows[1:], start=2):  # Skip header, start at row 2
                if not row or len(row) < 5:
                    continue

                row_contact_id = row[1]
                row_message_code = row[2] if len(row) > 2 else ''
                row_status = row[4]

                # Check if this message should be cancelled
                if (row_contact_id == contact_id and
                    row_status == 'pending' and
                    (message_codes is None or row_message_code in message_codes)):

                    self.sheets['Scheduled_Messages'].update_cell(i, 5, 'cancelled')
                    logger.info(f"Cancelled message {row_message_code} for {contact_id}")

            return True

        except Exception as error:
            logger.error(f"Failed to cancel messages: {error}")
            return False

    # ==================== MESSAGE LOG ====================

    def log_message(self, log_data: Dict[str, Any]) -> bool:
        """
        Log a message to the Message_Log sheet

        Args:
            log_data: Dictionary with log information

        Returns:
            True if successful
        """
        try:
            log_id = log_data.get('log_id', str(uuid.uuid4()))

            row = [
                log_id,
                log_data.get('contact_id', ''),
                log_data.get('timestamp', datetime.now().isoformat()),
                log_data.get('direction', ''),  # 'inbound' or 'outbound'
                log_data.get('message_code', ''),
                log_data.get('message_content', ''),
                log_data.get('window_valid', 'Yes')
            ]

            success = self._append_row_safe(self.sheets['Message_Log'], row)
            return success

        except Exception as error:
            logger.warning(f"Failed to log message: {error}")
            return False

    # ==================== CSV PROCESSING ====================

    def add_csv_record(self, csv_data: Dict[str, Any]) -> bool:
        """
        Add a CSV processing record

        Args:
            csv_data: Dictionary with CSV data

        Returns:
            True if successful
        """
        try:
            row = [
                csv_data.get('contact_id', ''),
                csv_data.get('first_name', ''),
                csv_data.get('weekend_date', ''),
                csv_data.get('zoom_attended', 'No'),
                csv_data.get('attendance_count', '0'),
                csv_data.get('sales_status', 'No Sale'),
                csv_data.get('follow_up_group', ''),  # 'Attended_NoSales' or 'NoShow'
                csv_data.get('follow_up_sent_date', '')
            ]

            success = self._append_row_safe(self.sheets['CSV_Processing'], row)
            if success:
                logger.info(f"Added CSV record for {csv_data.get('contact_id')}")
            return success

        except Exception as error:
            logger.error(f"Failed to add CSV record: {error}")
            return False

    def get_follow_up_contacts(self, group: str) -> List[Dict[str, Any]]:
        """
        Get contacts for Friday follow-up by group

        Args:
            group: 'Attended_NoSales' or 'NoShow'

        Returns:
            List of contact dictionaries
        """
        try:
            all_rows = self.sheets['CSV_Processing'].get_all_values()[1:]
            contacts = []

            for row in all_rows:
                if not row or len(row) < 7:
                    continue

                follow_up_group = row[6] if len(row) > 6 else ''
                follow_up_sent = row[7] if len(row) > 7 else ''

                if follow_up_group == group and not follow_up_sent:
                    contact_data = {
                        'contact_id': row[0],
                        'first_name': row[1] if len(row) > 1 else '',
                        'weekend_date': row[2] if len(row) > 2 else '',
                        'zoom_attended': row[3] if len(row) > 3 else '',
                        'attendance_count': row[4] if len(row) > 4 else '',
                        'sales_status': row[5] if len(row) > 5 else '',
                        'follow_up_group': follow_up_group
                    }
                    contacts.append(contact_data)

            return contacts

        except Exception as error:
            logger.error(f"Failed to get follow-up contacts: {error}")
            return []

    # ==================== CONFIG ====================

    def get_config_value(self, key: str) -> Optional[str]:
        """
        Get a configuration value from Config sheet

        Args:
            key: Config key

        Returns:
            Config value or None
        """
        try:
            all_rows = self.sheets['Config'].get_all_values()[1:]

            for row in all_rows:
                if row and row[0] == key:
                    return row[1] if len(row) > 1 else None

            return None

        except Exception as error:
            logger.error(f"Failed to get config value: {error}")
            return None

    def set_config_value(self, key: str, value: str) -> bool:
        """
        Set a configuration value in Config sheet

        Args:
            key: Config key
            value: Config value

        Returns:
            True if successful
        """
        try:
            config_keys = self.sheets['Config'].col_values(1)

            for i, k in enumerate(config_keys):
                if k == key:
                    row_index = i + 1
                    self.sheets['Config'].update_cell(row_index, 2, value)
                    logger.info(f"Updated config {key} = {value}")
                    return True

            # Key not found, add new row
            success = self._append_row_safe(self.sheets['Config'], [key, value])
            if success:
                logger.info(f"Added config {key} = {value}")
            return success

        except Exception as error:
            logger.error(f"Failed to set config value: {error}")
            return False

    def log_activity(self, contact_id: str, activity: str):
        """
        Log an activity for debugging/tracking

        Args:
            contact_id: Contact ID
            activity: Description of the activity
        """
        logger.info(f"Activity for {contact_id}: {activity}")
