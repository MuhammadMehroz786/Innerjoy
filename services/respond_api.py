"""
Respond.io API Wrapper Service
Handles all interactions with the Respond.io API
"""
import requests
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)


class RespondAPIError(Exception):
    """Custom exception for Respond.io API errors"""
    pass


class RespondAPI:
    """Wrapper for Respond.io API operations"""

    def __init__(self):
        self.api_key = Config.RESPOND_API_KEY
        self.base_url = Config.RESPOND_API_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                      max_retries: int = 3) -> Dict:
        """
        Make HTTP request to Respond.io API with retry logic

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request payload
            max_retries: Maximum number of retry attempts

        Returns:
            API response as dictionary

        Raises:
            RespondAPIError: If request fails after all retries
        """
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=self.headers, timeout=30)
                elif method.upper() == 'POST':
                    response = requests.post(url, headers=self.headers, json=data, timeout=30)
                elif method.upper() == 'PUT':
                    response = requests.put(url, headers=self.headers, json=data, timeout=30)
                elif method.upper() == 'DELETE':
                    response = requests.delete(url, headers=self.headers, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json() if response.content else {}

            except requests.exceptions.RequestException as e:
                logger.warning(f"API request failed (attempt {attempt + 1}/{max_retries}): {e}")

                if attempt == max_retries - 1:
                    logger.error(f"API request failed after {max_retries} attempts: {e}")
                    raise RespondAPIError(f"Failed to make API request: {e}")

        return {}

    def get_contact(self, contact_id: str) -> Dict:
        """
        Get contact details by ID

        Args:
            contact_id: Respond.io contact ID

        Returns:
            Contact information
        """
        logger.info(f"Fetching contact: {contact_id}")
        contact = self._make_request('GET', f'contact/{contact_id}')

        # Debug logging
        logger.info(f"Contact API response - firstName: {contact.get('firstName')}, keys: {list(contact.keys())}")

        # Convert custom_fields array to customFields object for easier access
        if 'custom_fields' in contact and isinstance(contact['custom_fields'], list):
            custom_fields_dict = {}
            for field in contact['custom_fields']:
                if isinstance(field, dict) and 'name' in field:
                    custom_fields_dict[field['name']] = field.get('value')
            contact['customFields'] = custom_fields_dict
            logger.info(f"Converted customFields: {list(custom_fields_dict.keys())}")

        return contact

    def get_contact_by_phone(self, phone: str) -> Dict:
        """
        Get contact details by phone number

        Args:
            phone: Phone number in E.164 format (e.g. +923273626526)

        Returns:
            Contact information
        """
        logger.info(f"Fetching contact by phone: {phone}")
        return self._make_request('GET', f'contact/phone:{phone}')

    def update_contact_field(self, contact_id: str, field_name: str, value: Any) -> Dict:
        """
        Update a custom field for a contact

        Args:
            contact_id: Respond.io contact ID
            field_name: Name of the custom field
            value: Value to set

        Returns:
            Updated contact information
        """
        logger.info(f"Updating contact {contact_id} field '{field_name}' to '{value}'")

        # Use Respond.io's custom_fields array format
        payload = {
            'custom_fields': [
                {"name": field_name, "value": value}
            ]
        }

        return self._make_request('PUT', f'contact/{contact_id}', payload)

    def update_contact_fields(self, contact_id: str, fields: Dict[str, Any]) -> Dict:
        """
        Update multiple custom fields for a contact

        Args:
            contact_id: Respond.io contact ID
            fields: Dictionary of field names and values

        Returns:
            Updated contact information
        """
        logger.info(f"Updating contact {contact_id} with fields: {fields}")

        # Convert dict to Respond.io's custom_fields array format
        custom_fields_array = [{"name": name, "value": value} for name, value in fields.items()]

        payload = {
            'custom_fields': custom_fields_array
        }

        logger.info(f"Sending payload: {payload}")
        return self._make_request('PUT', f'contact/{contact_id}', payload)

    def send_message(self, contact_identifier: str, message: str) -> Dict:
        """
        Send a WhatsApp message to a contact

        Args:
            contact_identifier: Respond.io contact ID or phone:+1234567890
            message: Message text to send

        Returns:
            Message send response
        """
        logger.info(f"Sending message to contact {contact_identifier}")

        payload = {
            'message': {
                'type': 'text',
                'text': message
            }
        }

        return self._make_request('POST', f'contact/{contact_identifier}/message', payload)

    def send_message_by_phone(self, phone: str, message: str, channel_id: str = None) -> Dict:
        """
        Send a WhatsApp message to a contact by phone number

        Args:
            phone: Phone number in E.164 format
            message: Message text to send
            channel_id: Optional channel ID (WhatsApp Business channel)

        Returns:
            Message send response
        """
        logger.info(f"Sending message to phone {phone}")

        payload = {
            'message': {
                'type': 'text',
                'text': message
            }
        }

        if channel_id:
            payload['channelId'] = channel_id

        return self._make_request('POST', f'contact/phone:{phone}/message', payload)

    def add_tag(self, contact_id: str, tag: str) -> Dict:
        """
        Add a tag to a contact

        Args:
            contact_id: Respond.io contact ID
            tag: Tag name to add

        Returns:
            API response
        """
        logger.info(f"Adding tag '{tag}' to contact {contact_id}")

        payload = {
            'tag': tag
        }

        return self._make_request('POST', f'contact/{contact_id}/tag', payload)

    def remove_tag(self, contact_id: str, tag: str) -> Dict:
        """
        Remove a tag from a contact

        Args:
            contact_id: Respond.io contact ID
            tag: Tag name to remove

        Returns:
            API response
        """
        logger.info(f"Removing tag '{tag}' from contact {contact_id}")

        return self._make_request('DELETE', f'contact/{contact_id}/tag/{tag}')

    def get_contact_field(self, contact_id: str, field_name: str) -> Optional[Any]:
        """
        Get a specific custom field value from a contact

        Args:
            contact_id: Respond.io contact ID
            field_name: Name of the custom field

        Returns:
            Field value or None if not found
        """
        try:
            contact = self.get_contact(contact_id)
            custom_fields = contact.get('customFields', {})
            return custom_fields.get(field_name)
        except RespondAPIError as e:
            logger.error(f"Failed to get field '{field_name}' for contact {contact_id}: {e}")
            return None

    def check_24hr_window(self, contact_id: str) -> bool:
        """
        Check if contact is within 24-hour messaging window

        Args:
            contact_id: Respond.io contact ID

        Returns:
            True if within window, False otherwise
        """
        last_window_start = self.get_contact_field(
            contact_id,
            Config.CUSTOM_FIELDS['LAST_24HR_WINDOW']
        )

        if not last_window_start:
            logger.warning(f"No 24hr window timestamp for contact {contact_id}")
            return False

        try:
            window_start = datetime.fromisoformat(last_window_start)
            time_elapsed = (datetime.now() - window_start).total_seconds()

            within_window = time_elapsed < Config.WINDOW_24H_SECONDS

            if not within_window:
                logger.warning(
                    f"Contact {contact_id} is outside 24hr window "
                    f"(elapsed: {time_elapsed/3600:.2f} hours)"
                )

            return within_window

        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing window timestamp for contact {contact_id}: {e}")
            return False

    def update_24hr_window(self, contact_id: str) -> Dict:
        """
        Update the 24-hour window timestamp for a contact
        Called when contact sends a message

        Args:
            contact_id: Respond.io contact ID

        Returns:
            Updated contact information
        """
        timestamp = datetime.now().isoformat()
        logger.info(f"Updating 24hr window for contact {contact_id} to {timestamp}")

        return self.update_contact_field(
            contact_id,
            Config.CUSTOM_FIELDS['LAST_24HR_WINDOW'],
            timestamp
        )

    def send_message_with_window_check(self, contact_id: str, message: str) -> bool:
        """
        Send message only if within 24-hour window

        Args:
            contact_id: Respond.io contact ID
            message: Message text to send

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.check_24hr_window(contact_id):
            logger.error(f"Cannot send message to {contact_id}: outside 24hr window")
            return False

        try:
            self.send_message(contact_id, message)
            return True
        except RespondAPIError as e:
            logger.error(f"Failed to send message to {contact_id}: {e}")
            return False
