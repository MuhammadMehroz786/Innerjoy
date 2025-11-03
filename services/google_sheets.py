"""
Google Sheets Integration Service
Handles data logging and tracking in Google Sheets using Service Account
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

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
        self.sheet = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Sheets API using Service Account"""
        try:
            # Define the required scopes
            scopes = ['https://www.googleapis.com/auth/spreadsheets']

            # Load credentials from service account file
            creds = Credentials.from_service_account_file(
                Config.GOOGLE_CREDENTIALS_FILE,
                scopes=scopes
            )

            # Authorize the client
            self.client = gspread.authorize(creds)

            # Open the spreadsheet
            self.sheet = self.client.open_by_key(self.spreadsheet_id).sheet1

            logger.info("Successfully authenticated with Google Sheets using Service Account")

        except FileNotFoundError:
            logger.error(f"Credentials file not found: {Config.GOOGLE_CREDENTIALS_FILE}")
            raise GoogleSheetsError(f"Credentials file not found: {Config.GOOGLE_CREDENTIALS_FILE}")
        except Exception as error:
            logger.error(f"Failed to authenticate with Google Sheets: {error}")
            raise GoogleSheetsError(f"Authentication failed: {error}")

    def initialize_sheet(self):
        """Initialize the spreadsheet with headers if not already set"""
        headers = [
            'contact_id',
            'whatsapp_number',
            'first_name',
            'registration_time',
            'chosen_timeslot',
            'session_datetime',
            'last_message_time',
            'thumbs_up',
            'reminder_12h_sent',
            'reminder_60min_sent',
            'reminder_10min_sent',
            'attended',
            'member_status',
            'payment_verified',
            'tree_type',
            'last_updated'
        ]

        try:
            # Check if headers already exist
            existing_headers = self.sheet.row_values(1)

            if not existing_headers or existing_headers[0] == '':
                # Write headers
                self.sheet.update('A1:P1', [headers])
                logger.info("Initialized Google Sheets with headers")
            else:
                logger.info("Google Sheets already initialized")

        except Exception as error:
            logger.error(f"Failed to initialize sheet: {error}")
            raise GoogleSheetsError(f"Sheet initialization failed: {error}")

    def add_contact(self, contact_data: Dict[str, Any]) -> bool:
        """
        Add a new contact to the sheet

        Args:
            contact_data: Dictionary with contact information

        Returns:
            True if successful, False otherwise
        """
        try:
            row = [
                contact_data.get('contact_id', ''),
                contact_data.get('whatsapp_number', ''),
                contact_data.get('first_name', ''),
                contact_data.get('registration_time', datetime.now().isoformat()),
                contact_data.get('chosen_timeslot', ''),
                contact_data.get('session_datetime', ''),
                contact_data.get('last_message_time', datetime.now().isoformat()),
                contact_data.get('thumbs_up', 'No'),
                contact_data.get('reminder_12h_sent', 'No'),
                contact_data.get('reminder_60min_sent', 'No'),
                contact_data.get('reminder_10min_sent', 'No'),
                contact_data.get('attended', ''),
                contact_data.get('member_status', 'prospect'),
                contact_data.get('payment_verified', 'No'),
                contact_data.get('tree_type', 'Tree1'),
                datetime.now().isoformat()
            ]

            self.sheet.append_row(row)
            logger.info(f"Added contact {contact_data.get('contact_id')} to sheet")
            return True

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
            # Find the row for this contact
            row_index = self._find_contact_row(contact_id)

            if row_index is None:
                logger.warning(f"Contact {contact_id} not found in sheet")
                return False

            # Map field names to column numbers (1-indexed)
            field_columns = {
                'whatsapp_number': 2,
                'first_name': 3,
                'registration_time': 4,
                'chosen_timeslot': 5,
                'session_datetime': 6,
                'last_message_time': 7,
                'thumbs_up': 8,
                'reminder_12h_sent': 9,
                'reminder_60min_sent': 10,
                'reminder_10min_sent': 11,
                'attended': 12,
                'member_status': 13,
                'payment_verified': 14,
                'tree_type': 15,
                'last_updated': 16
            }

            # Update last_updated timestamp
            updates['last_updated'] = datetime.now().isoformat()

            # Update each field
            for field, value in updates.items():
                if field in field_columns:
                    col_index = field_columns[field]
                    self.sheet.update_cell(row_index, col_index, value)

            logger.info(f"Updated contact {contact_id} in sheet")
            return True

        except Exception as error:
            logger.error(f"Failed to update contact: {error}")
            return False

    def _find_contact_row(self, contact_id: str) -> Optional[int]:
        """
        Find the row number for a given contact ID

        Args:
            contact_id: Contact ID to find

        Returns:
            Row number (1-indexed) or None if not found
        """
        try:
            # Get all contact IDs from column A
            contact_ids = self.sheet.col_values(1)

            for i, cid in enumerate(contact_ids):
                if cid == contact_id:
                    return i + 1  # 1-indexed

            return None

        except Exception as error:
            logger.error(f"Failed to find contact row: {error}")
            return None

    def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get contact information from the sheet

        Args:
            contact_id: Contact ID to retrieve

        Returns:
            Dictionary with contact data or None if not found
        """
        try:
            row_index = self._find_contact_row(contact_id)

            if row_index is None:
                return None

            row = self.sheet.row_values(row_index)

            # Map to dictionary
            contact_data = {
                'contact_id': row[0] if len(row) > 0 else '',
                'whatsapp_number': row[1] if len(row) > 1 else '',
                'first_name': row[2] if len(row) > 2 else '',
                'registration_time': row[3] if len(row) > 3 else '',
                'chosen_timeslot': row[4] if len(row) > 4 else '',
                'session_datetime': row[5] if len(row) > 5 else '',
                'last_message_time': row[6] if len(row) > 6 else '',
                'thumbs_up': row[7] if len(row) > 7 else 'No',
                'reminder_12h_sent': row[8] if len(row) > 8 else 'No',
                'reminder_60min_sent': row[9] if len(row) > 9 else 'No',
                'reminder_10min_sent': row[10] if len(row) > 10 else 'No',
                'attended': row[11] if len(row) > 11 else '',
                'member_status': row[12] if len(row) > 12 else 'prospect',
                'payment_verified': row[13] if len(row) > 13 else 'No',
                'tree_type': row[14] if len(row) > 14 else 'Tree1',
                'last_updated': row[15] if len(row) > 15 else ''
            }

            return contact_data

        except Exception as error:
            logger.error(f"Failed to get contact: {error}")
            return None

    def get_all_contacts(self) -> List[Dict[str, Any]]:
        """
        Get all contacts from the sheet

        Returns:
            List of contact dictionaries
        """
        try:
            # Get all rows except the header
            all_rows = self.sheet.get_all_values()[1:]  # Skip header row
            contacts = []

            for row in all_rows:
                if not row or not row[0]:  # Skip empty rows
                    continue

                contact_data = {
                    'contact_id': row[0] if len(row) > 0 else '',
                    'whatsapp_number': row[1] if len(row) > 1 else '',
                    'first_name': row[2] if len(row) > 2 else '',
                    'registration_time': row[3] if len(row) > 3 else '',
                    'chosen_timeslot': row[4] if len(row) > 4 else '',
                    'session_datetime': row[5] if len(row) > 5 else '',
                    'last_message_time': row[6] if len(row) > 6 else '',
                    'thumbs_up': row[7] if len(row) > 7 else 'No',
                    'reminder_12h_sent': row[8] if len(row) > 8 else 'No',
                    'reminder_60min_sent': row[9] if len(row) > 9 else 'No',
                    'reminder_10min_sent': row[10] if len(row) > 10 else 'No',
                    'attended': row[11] if len(row) > 11 else '',
                    'member_status': row[12] if len(row) > 12 else 'prospect',
                    'payment_verified': row[13] if len(row) > 13 else 'No',
                    'tree_type': row[14] if len(row) > 14 else 'Tree1',
                    'last_updated': row[15] if len(row) > 15 else ''
                }

                contacts.append(contact_data)

            logger.info(f"Retrieved {len(contacts)} contacts from sheet")
            return contacts

        except Exception as error:
            logger.error(f"Failed to get all contacts: {error}")
            return []

    def log_activity(self, contact_id: str, activity: str):
        """
        Log an activity for debugging/tracking

        Args:
            contact_id: Contact ID
            activity: Description of the activity
        """
        logger.info(f"Activity for {contact_id}: {activity}")
