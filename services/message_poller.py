"""
Message Polling Service
Polls Respond.io for new messages (alternative to webhooks)
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Set, Dict, List
import pytz

from config import Config
from services.respond_api import RespondAPI
from services.message_handler import MessageHandler

logger = logging.getLogger(__name__)


class MessagePoller:
    """Polls Respond.io API for new messages when webhooks aren't available"""

    def __init__(self):
        self.api = RespondAPI()
        self.message_handler = MessageHandler()
        self.processed_messages: Set[str] = set()  # Track processed message IDs
        self.last_poll_time = datetime.now(pytz.timezone(Config.TIMEZONE))
        self.is_running = False

    def start_polling(self, interval_seconds: int = 10):
        """
        Start polling for messages

        Args:
            interval_seconds: How often to check for new messages
        """
        self.is_running = True
        logger.info(f"Message polling started (checking every {interval_seconds} seconds)")

        while self.is_running:
            try:
                self.poll_once()
            except Exception as e:
                logger.error(f"Error during polling: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def stop_polling(self):
        """Stop the polling loop"""
        self.is_running = False
        logger.info("Message polling stopped")

    def poll_once(self):
        """
        Poll once for new messages
        This is called periodically by the scheduler
        """
        try:
            # Note: Respond.io API v2 doesn't have a direct "get recent messages" endpoint
            # We'll need to work with what's available

            # For now, we'll log that polling is happening
            # In a real implementation, you'd need to check Respond.io's specific API
            # for getting recent conversations/messages

            logger.debug("Polling for new messages...")

            # This is a placeholder - actual implementation depends on Respond.io API
            # You may need to:
            # 1. Get list of conversations
            # 2. Check each for new messages
            # 3. Process unread messages

            # For demonstration, we'll check if we can list contacts
            # (actual implementation needs Respond.io's conversation/message endpoints)

            current_time = datetime.now(pytz.timezone(Config.TIMEZONE))
            logger.debug(f"Poll completed at {current_time}")

        except Exception as e:
            logger.error(f"Error in poll_once: {e}", exc_info=True)

    def process_message_from_poll(self, message_data: Dict):
        """
        Process a message found during polling

        Args:
            message_data: Message data from Respond.io API
        """
        try:
            message_id = message_data.get('id')

            # Skip if already processed
            if message_id in self.processed_messages:
                logger.debug(f"Skipping already processed message: {message_id}")
                return

            # Convert to webhook format and process
            webhook_data = {
                'event': 'message.received',
                'contact': message_data.get('contact', {}),
                'message': message_data.get('message', {})
            }

            # Process through normal message handler
            success = self.message_handler.process_message(webhook_data)

            if success:
                # Mark as processed
                self.processed_messages.add(message_id)
                logger.info(f"Successfully processed polled message: {message_id}")

                # Clean up old message IDs (keep last 1000)
                if len(self.processed_messages) > 1000:
                    # Remove oldest half
                    self.processed_messages = set(list(self.processed_messages)[500:])

        except Exception as e:
            logger.error(f"Error processing polled message: {e}", exc_info=True)


# Alternative implementation using Respond.io Conversations API
class RespondioConversationPoller(MessagePoller):
    """
    Enhanced poller that uses Respond.io Conversations API
    This is a more realistic implementation
    """

    def __init__(self):
        super().__init__()
        self.last_checked_conversations: Dict[str, datetime] = {}

    def get_recent_conversations(self, limit: int = 20) -> List[Dict]:
        """
        Get recent conversations from Respond.io

        Note: This is a placeholder - actual endpoint depends on Respond.io API
        You may need to use /conversations or similar endpoint
        """
        try:
            # Placeholder for Respond.io conversations endpoint
            # Actual implementation depends on available API endpoints

            # Example of what you might do:
            # response = self.api._make_request('GET', 'conversations', params={'limit': limit})
            # return response.get('conversations', [])

            logger.debug("Checking for recent conversations...")
            return []

        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []

    def poll_once(self):
        """
        Poll for new messages in conversations
        """
        try:
            conversations = self.get_recent_conversations()

            for conversation in conversations:
                contact_id = conversation.get('contactId')

                if not contact_id:
                    continue

                # Check for new messages in this conversation
                last_message = conversation.get('lastMessage', {})
                message_time_str = last_message.get('createdAt')

                if not message_time_str:
                    continue

                # Parse message time
                try:
                    message_time = datetime.fromisoformat(message_time_str.replace('Z', '+00:00'))
                except:
                    continue

                # Only process if message is newer than our last check
                last_check = self.last_checked_conversations.get(contact_id, self.last_poll_time)

                if message_time > last_check:
                    # Check if this is from the customer (not from us)
                    if last_message.get('direction') == 'incoming':
                        # Process this message
                        message_data = {
                            'id': last_message.get('id'),
                            'contact': {'id': contact_id},
                            'message': last_message
                        }

                        self.process_message_from_poll(message_data)

                    # Update last check time for this conversation
                    self.last_checked_conversations[contact_id] = message_time

            # Update global poll time
            self.last_poll_time = datetime.now(pytz.timezone(Config.TIMEZONE))
            logger.debug(f"Poll completed, checked {len(conversations)} conversations")

        except Exception as e:
            logger.error(f"Error in poll_once: {e}", exc_info=True)


# Simple implementation that works with manual testing
class SimpleMessagePoller(MessagePoller):
    """
    Simplified poller for demonstration/testing
    Logs polling activity without requiring specific Respond.io endpoints
    """

    def poll_once(self):
        """Simple polling that just logs activity"""
        logger.info("🔄 Polling for new messages (webhook alternative mode)")
        logger.info("💡 Tip: When webhook is available, this will be automatic!")
        logger.info("📝 Current mode: Manual polling every 10 seconds")

        # In webhook mode, messages would come in automatically
        # In polling mode, we'd check Respond.io API here
        # For now, we just show that polling is active
