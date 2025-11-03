"""
Reminder Scheduler Service
Manages automated reminder sending using APScheduler
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from config import Config
from services.respond_api import RespondAPI
from services.google_sheets import GoogleSheetsService
from services.message_handler import MessageHandler
from services.message_poller import SimpleMessagePoller

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Manages scheduled reminders and automated messages"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=Config.TIMEZONE)
        self.api = RespondAPI()
        try:
            self.sheets = GoogleSheetsService() if Config.GOOGLE_SHEETS_ID else None
        except:
            self.sheets = None
        self.message_handler = MessageHandler()
        self.message_poller = SimpleMessagePoller()
        self.timezone = pytz.timezone(Config.TIMEZONE)

    def start(self):
        """Start the scheduler"""
        # Poll for new messages every 10 seconds (webhook alternative)
        self.scheduler.add_job(
            func=self.message_poller.poll_once,
            trigger=IntervalTrigger(seconds=10),
            id='poll_messages',
            name='Poll for new messages (webhook alternative)',
            replace_existing=True
        )

        # Check reminders every 5 minutes
        self.scheduler.add_job(
            func=self.check_reminders,
            trigger=IntervalTrigger(minutes=5),
            id='check_reminders',
            name='Check and send reminders',
            replace_existing=True
        )

        # Check for Tree 2 messages every hour
        self.scheduler.add_job(
            func=self.check_tree2_messages,
            trigger=IntervalTrigger(hours=1),
            id='check_tree2',
            name='Check Tree 2 sales messages',
            replace_existing=True
        )

        # Monday CSV processing (every Monday at 10 AM)
        self.scheduler.add_job(
            func=self.monday_processing,
            trigger=CronTrigger(day_of_week='mon', hour=10, minute=0),
            id='monday_processing',
            name='Monday CSV processing',
            replace_existing=True
        )

        # Friday re-invites (every Friday at 14:00)
        self.scheduler.add_job(
            func=self.friday_reinvites,
            trigger=CronTrigger(day_of_week='fri', hour=14, minute=0),
            id='friday_reinvites',
            name='Friday re-invites',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Reminder scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Reminder scheduler stopped")

    def check_reminders(self):
        """
        Check all contacts and send reminders if needed
        Called every 5 minutes
        """
        logger.info("Checking reminders...")

        try:
            # Get all contacts from Google Sheets
            if not self.sheets:
                logger.debug("Skipping reminder check - Google Sheets not configured")
                return

            contacts = self.sheets.get_all_contacts()

            now = datetime.now(self.timezone)

            for contact in contacts:
                contact_id = contact.get('contact_id')
                chosen_timeslot = contact.get('chosen_timeslot')
                session_datetime_str = contact.get('session_datetime')

                # Skip if no timeslot chosen
                if not chosen_timeslot or not session_datetime_str:
                    continue

                # Parse session datetime
                try:
                    session_datetime = datetime.fromisoformat(session_datetime_str)
                    if session_datetime.tzinfo is None:
                        session_datetime = self.timezone.localize(session_datetime)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid session datetime for {contact_id}")
                    continue

                # Skip if session is in the past
                if session_datetime < now:
                    continue

                # Calculate time until session
                time_until_session = (session_datetime - now).total_seconds() / 60  # in minutes

                # Check and send 12-hour reminder
                if (720 <= time_until_session <= 725 and
                    contact.get('reminder_12h_sent') != 'Yes'):
                    logger.info(f"Sending 12h reminder to {contact_id}")
                    self.message_handler.send_reminder(contact_id, '12h')

                # Check and send 60-minute reminder
                elif (60 <= time_until_session <= 65 and
                      contact.get('reminder_60min_sent') != 'Yes'):
                    logger.info(f"Sending 60min reminder to {contact_id}")
                    self.message_handler.send_reminder(contact_id, '60min')

                # Check and send 10-minute reminder
                elif (10 <= time_until_session <= 15 and
                      contact.get('reminder_10min_sent') != 'Yes'):
                    logger.info(f"Sending 10min reminder to {contact_id}")
                    self.message_handler.send_reminder(contact_id, '10min')

            logger.info("Reminder check completed")

        except Exception as e:
            logger.error(f"Error checking reminders: {e}", exc_info=True)

    def check_tree2_messages(self):
        """
        Check for contacts who need Tree 2 messages
        (no timeslot chosen within 2 hours)
        """
        logger.info("Checking Tree 2 messages...")

        try:
            if not self.sheets:
                logger.debug("Skipping Tree 2 check - Google Sheets not configured")
                return

            contacts = self.sheets.get_all_contacts()
            now = datetime.now(self.timezone)

            for contact in contacts:
                contact_id = contact.get('contact_id')
                chosen_timeslot = contact.get('chosen_timeslot')
                registration_time_str = contact.get('registration_time')
                tree_type = contact.get('tree_type', 'Tree1')

                # Skip if already chose timeslot
                if chosen_timeslot:
                    continue

                # Parse registration time
                try:
                    registration_time = datetime.fromisoformat(registration_time_str)
                    if registration_time.tzinfo is None:
                        registration_time = self.timezone.localize(registration_time)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid registration time for {contact_id}")
                    continue

                # Calculate hours since registration
                hours_since_reg = (now - registration_time).total_seconds() / 3600

                # After 2 hours without timeslot, switch to Tree 2
                if hours_since_reg >= 2 and tree_type == 'Tree1':
                    logger.info(f"Switching {contact_id} to Tree 2")
                    self.sheets.update_contact(contact_id, {'tree_type': 'Tree2'})

                # Tree 2 Sales Message 1 (T+22h)
                if (Config.TREE2_SALES_1 <= hours_since_reg < Config.TREE2_SALES_1 + 1 and
                    tree_type == 'Tree2'):
                    logger.info(f"Sending Tree 2 sales message 1 to {contact_id}")

                    # Check 24hr window and send
                    if self.api.check_24hr_window(contact_id):
                        contact_info = self.api.get_contact(contact_id)
                        custom_fields = contact_info.get('customFields', {})
                        first_name = custom_fields.get(Config.CUSTOM_FIELDS['FIRST_NAME'], 'there')

                        message = Config.get_message_templates()['TREE2_SALES_1'].format(
                            name=first_name,
                            zoom_link=Config.ZOOM_PREVIEW_LINK
                        )
                        self.api.send_message(contact_id, message)

                # Tree 2 Sales Message 2 (T+23.5h)
                elif (Config.TREE2_SALES_2 <= hours_since_reg < Config.TREE2_SALES_2 + 1 and
                      tree_type == 'Tree2'):
                    logger.info(f"Sending Tree 2 sales message 2 to {contact_id}")

                    if self.api.check_24hr_window(contact_id):
                        contact_info = self.api.get_contact(contact_id)
                        custom_fields = contact_info.get('customFields', {})
                        first_name = custom_fields.get(Config.CUSTOM_FIELDS['FIRST_NAME'], 'there')

                        message = Config.get_message_templates()['TREE2_SALES_2'].format(
                            name=first_name
                        )
                        self.api.send_message(contact_id, message)

            logger.info("Tree 2 check completed")

        except Exception as e:
            logger.error(f"Error checking Tree 2 messages: {e}", exc_info=True)

    def monday_processing(self):
        """
        Monday CSV processing
        Download Zoom attendee list, categorize contacts, update sheets
        """
        logger.info("Running Monday processing...")

        # This is a placeholder - actual implementation would:
        # 1. Download Zoom attendee CSV
        # 2. Match with registered contacts
        # 3. Mark as attended/NoShow
        # 4. Tag contacts for Friday re-invites

        try:
            if not self.sheets:
                logger.debug("Skipping Monday processing - Google Sheets not configured")
                return

            contacts = self.sheets.get_all_contacts()

            for contact in contacts:
                contact_id = contact.get('contact_id')
                session_datetime_str = contact.get('session_datetime')
                attended = contact.get('attended')

                if not session_datetime_str:
                    continue

                # Parse session datetime
                try:
                    session_datetime = datetime.fromisoformat(session_datetime_str)
                    if session_datetime.tzinfo is None:
                        session_datetime = self.timezone.localize(session_datetime)
                except (ValueError, TypeError):
                    continue

                # Check if session was last weekend
                now = datetime.now(self.timezone)
                days_since_session = (now - session_datetime).days

                if 1 <= days_since_session <= 7 and not attended:
                    # This contact had a session last week but attendance not marked
                    # In real implementation, check against Zoom CSV

                    # For now, just log
                    logger.info(f"Contact {contact_id} needs attendance verification")

                    # Could auto-tag as NoShow and prepare for Friday re-invite
                    # self.api.add_tag(contact_id, 'NoShow')
                    # self.sheets.update_contact(contact_id, {'attended': 'NoShow'})

            logger.info("Monday processing completed")

        except Exception as e:
            logger.error(f"Error in Monday processing: {e}", exc_info=True)

    def friday_reinvites(self):
        """
        Friday re-invites for NoShow and NoSales contacts
        """
        logger.info("Sending Friday re-invites...")

        try:
            if not self.sheets:
                logger.debug("Skipping Friday re-invites - Google Sheets not configured")
                return

            contacts = self.sheets.get_all_contacts()

            for contact in contacts:
                contact_id = contact.get('contact_id')
                attended = contact.get('attended')
                member_status = contact.get('member_status')

                # Re-invite NoShow contacts
                if attended == 'NoShow':
                    if self.api.check_24hr_window(contact_id):
                        contact_info = self.api.get_contact(contact_id)
                        custom_fields = contact_info.get('customFields', {})
                        first_name = custom_fields.get(Config.CUSTOM_FIELDS['FIRST_NAME'], 'there')

                        message = Config.get_message_templates()['NOSHOW_REINVITE'].format(
                            name=first_name,
                            zoom_link=Config.ZOOM_PREVIEW_LINK
                        )
                        self.api.send_message(contact_id, message)
                        logger.info(f"Sent NoShow re-invite to {contact_id}")

                # Re-invite NoSales contacts (attended but didn't become member)
                elif attended == 'Yes' and member_status == 'prospect':
                    # Check if it's been a week since session
                    session_datetime_str = contact.get('session_datetime')
                    if session_datetime_str:
                        try:
                            session_datetime = datetime.fromisoformat(session_datetime_str)
                            if session_datetime.tzinfo is None:
                                session_datetime = self.timezone.localize(session_datetime)

                            days_since = (datetime.now(self.timezone) - session_datetime).days

                            if days_since >= 7:
                                if self.api.check_24hr_window(contact_id):
                                    contact_info = self.api.get_contact(contact_id)
                                    custom_fields = contact_info.get('customFields', {})
                                    first_name = custom_fields.get(
                                        Config.CUSTOM_FIELDS['FIRST_NAME'], 'there'
                                    )

                                    message = Config.get_message_templates()['NOSALES_REINVITE'].format(
                                        name=first_name,
                                        zoom_link=Config.ZOOM_PREVIEW_LINK
                                    )
                                    self.api.send_message(contact_id, message)
                                    logger.info(f"Sent NoSales re-invite to {contact_id}")

                        except (ValueError, TypeError):
                            continue

            logger.info("Friday re-invites completed")

        except Exception as e:
            logger.error(f"Error in Friday re-invites: {e}", exc_info=True)

    def trigger_manual_reminder_check(self):
        """Manually trigger reminder check (for testing/admin)"""
        logger.info("Manual reminder check triggered")
        self.check_reminders()
