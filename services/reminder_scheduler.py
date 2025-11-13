"""
Reminder Scheduler Service
Manages automated message sending using APScheduler
Processes Scheduled_Messages queue from Google Sheets
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
            logger.warning("Google Sheets not available - scheduler will not function")
        self.message_handler = MessageHandler()
        self.timezone = pytz.timezone(Config.TIMEZONE)
        self.templates = Config.get_message_templates()

    def start(self):
        """Start the scheduler"""
        if not self.sheets:
            logger.warning("Cannot start scheduler - Google Sheets not available")
            return

        # Process scheduled messages every 1 minute
        self.scheduler.add_job(
            func=self.process_scheduled_messages,
            trigger=IntervalTrigger(minutes=1),
            id='process_scheduled_messages',
            name='Process scheduled messages from queue',
            replace_existing=True
        )

        # Monday CSV processing (every Monday at 10:00 AM)
        self.scheduler.add_job(
            func=self.monday_csv_processing,
            trigger=CronTrigger(day_of_week='mon', hour=10, minute=0),
            id='monday_processing',
            name='Monday CSV processing',
            replace_existing=True
        )

        # Friday re-invites (every Friday at 18:00 - 6 PM)
        self.scheduler.add_job(
            func=self.friday_reinvites,
            trigger=CronTrigger(day_of_week='fri', hour=18, minute=0),
            id='friday_reinvites',
            name='Friday re-invites (B1 NoSales & NoShow)',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Reminder scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Reminder scheduler stopped")

    # ==================== SCHEDULED MESSAGE PROCESSING ====================

    def process_scheduled_messages(self):
        """
        Process all pending scheduled messages
        Checks Scheduled_Messages sheet and sends messages that are due
        Called every 1 minute
        """
        try:
            if not self.sheets:
                return

            # Get all pending messages
            pending_messages = self.sheets.get_pending_messages()

            if not pending_messages:
                logger.debug("No pending messages to process")
                return

            now = datetime.now(self.timezone)
            logger.info(f"Checking {len(pending_messages)} pending messages...")

            for msg in pending_messages:
                try:
                    message_id = msg.get('message_id')
                    contact_id = msg.get('contact_id')
                    message_code = msg.get('message_code')
                    scheduled_send_time_str = msg.get('scheduled_send_time')

                    if not scheduled_send_time_str:
                        logger.warning(f"Message {message_id} has no scheduled_send_time")
                        continue

                    # Parse scheduled time
                    scheduled_time = datetime.fromisoformat(scheduled_send_time_str)
                    if scheduled_time.tzinfo is None:
                        scheduled_time = self.timezone.localize(scheduled_time)

                    # Check if it's time to send
                    if now >= scheduled_time:
                        logger.info(f"Sending scheduled message {message_code} to {contact_id}")
                        success = self._send_scheduled_message(contact_id, message_code)

                        # Update status
                        if success:
                            self.sheets.update_message_status(
                                message_id,
                                'sent',
                                now.isoformat()
                            )
                        else:
                            self.sheets.update_message_status(
                                message_id,
                                'failed',
                                now.isoformat()
                            )

                except Exception as e:
                    logger.error(f"Error processing message {msg.get('message_id')}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in process_scheduled_messages: {e}", exc_info=True)

    def _send_scheduled_message(self, contact_id: str, message_code: str) -> bool:
        """
        Send a scheduled message based on message code

        Args:
            contact_id: Contact ID
            message_code: Message code (e.g., 'B1_R1', 'B1_S1', 'B2_RA')

        Returns:
            True if sent successfully
        """
        try:
            # Get contact from sheets
            sheet_contact = self.sheets.get_contact(contact_id)

            if not sheet_contact:
                logger.warning(f"Cannot send {message_code} to {contact_id}: not found")
                return False

            first_name = sheet_contact.get('first_name', 'there')
            chosen_timeslot = sheet_contact.get('chosen_timeslot')
            current_tree = sheet_contact.get('current_tree', 'Tree1')

            # Check 72-hour window
            window_expires_at = sheet_contact.get('window_expires_at')
            if window_expires_at:
                expires = datetime.fromisoformat(window_expires_at)
                now = datetime.now(self.timezone)
                if now > expires:
                    logger.warning(f"Cannot send {message_code} to {contact_id}: outside 72hr window")
                    return False

            # Route to appropriate handler based on message code
            if message_code in ['B1_R1', 'B1_R2', 'B1_R3']:
                return self._send_tree1_reminder(contact_id, message_code, first_name, chosen_timeslot)

            elif message_code in ['B1_S1', 'B1_SHAKEUP', 'B1_S2', 'B1_S3']:
                return self._send_tree1_sales(contact_id, message_code, first_name)

            elif message_code == 'B2_RA':
                return self._send_tree2_ra(contact_id, first_name, current_tree)

            elif message_code == 'B2_RB':
                return self._send_tree2_rb(contact_id, first_name)

            elif message_code in ['B2_S1', 'B2_S2']:
                return self._send_tree2_sales(contact_id, message_code, first_name)

            else:
                logger.error(f"Unknown message code: {message_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending scheduled message {message_code}: {e}", exc_info=True)
            return False

    # ==================== TREE 1 MESSAGE SENDERS ====================

    def _send_tree1_reminder(self, contact_id: str, message_code: str, first_name: str, chosen_timeslot: str) -> bool:
        """
        Send Tree 1 reminder (B1_R1, B1_R2, B1_R3)

        Args:
            contact_id: Contact ID
            message_code: Message code
            first_name: User's first name
            chosen_timeslot: Chosen timeslot (A-E)

        Returns:
            True if sent successfully
        """
        try:
            if not chosen_timeslot:
                logger.warning(f"Cannot send {message_code} to {contact_id}: no timeslot chosen")
                return False

            # Get timeslot display
            timeslot_display = Config.get_timeslot_display(chosen_timeslot)

            # Get template
            if message_code not in self.templates:
                logger.error(f"Template not found: {message_code}")
                return False

            message = self.templates[message_code].format(
                name=first_name,
                timeslot=timeslot_display,
                zoom_link=Config.ZOOM_PREVIEW_LINK
            )

            # Send message
            self.api.send_message(contact_id, message)

            # Log
            self.sheets.log_message({
                'contact_id': contact_id,
                'timestamp': datetime.now(self.timezone).isoformat(),
                'direction': 'outbound',
                'message_code': message_code,
                'message_content': message[:500],
                'window_valid': 'Yes'
            })

            logger.info(f"Sent {message_code} to {contact_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending {message_code}: {e}")
            return False

    def _send_tree1_sales(self, contact_id: str, message_code: str, first_name: str) -> bool:
        """
        Send Tree 1 sales message (B1_S1, B1_SHAKEUP, B1_S2)

        Args:
            contact_id: Contact ID
            message_code: Message code
            first_name: User's first name

        Returns:
            True if sent successfully
        """
        try:
            # Get template
            if message_code not in self.templates:
                logger.error(f"Template not found: {message_code}")
                return False

            message = self.templates[message_code].format(
                name=first_name,
                membership_link=Config.MEMBERSHIP_LINK,
                trial_link=Config.TRIAL_LINK
            )

            # Send message
            self.api.send_message(contact_id, message)

            # Log
            self.sheets.log_message({
                'contact_id': contact_id,
                'timestamp': datetime.now(self.timezone).isoformat(),
                'direction': 'outbound',
                'message_code': message_code,
                'message_content': message[:500],
                'window_valid': 'Yes'
            })

            logger.info(f"Sent {message_code} to {contact_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending {message_code}: {e}")
            return False

    # ==================== TREE 2 MESSAGE SENDERS ====================

    def _send_tree2_ra(self, contact_id: str, first_name: str, current_tree: str) -> bool:
        """
        Send B2 Ra - First Tree 2 reminder to choose timeslot
        Only sends if user is still in Tree 1 and hasn't chosen a timeslot

        Args:
            contact_id: Contact ID
            first_name: User's first name
            current_tree: Current tree (should be Tree1)

        Returns:
            True if sent successfully
        """
        try:
            # Check if they already chose a timeslot or moved to Tree 2
            sheet_contact = self.sheets.get_contact(contact_id)
            if not sheet_contact:
                return False

            chosen_timeslot = sheet_contact.get('chosen_timeslot')

            # If they already chose a timeslot, cancel this message
            if chosen_timeslot:
                logger.info(f"Skipping B2_RA for {contact_id} - timeslot already chosen")
                return False

            # Move to Tree 2
            self.sheets.update_contact(contact_id, {
                'current_tree': 'Tree2',
                'current_step': 'B2_RA'
            })

            # Send B2_RA
            message = self.templates['B2_RA'].format(
                name=first_name,
                zoom_link=Config.ZOOM_PREVIEW_LINK
            )

            self.api.send_message(contact_id, message)

            # Log
            self.sheets.log_message({
                'contact_id': contact_id,
                'timestamp': datetime.now(self.timezone).isoformat(),
                'direction': 'outbound',
                'message_code': 'B2_RA',
                'message_content': message[:500],
                'window_valid': 'Yes'
            })

            # Schedule B2_RB (2 hours later)
            now = datetime.now(self.timezone)
            rb_time = now + timedelta(hours=2)

            self.sheets.schedule_message({
                'contact_id': contact_id,
                'message_code': 'B2_RB',
                'scheduled_send_time': rb_time.isoformat(),
                'status': 'pending',
                'trigger_type': 'tree2_followup'
            })

            # Schedule B2_S1 (Sunday 16:00) and B2_S2 (Monday 9:00)
            now = datetime.now(self.timezone)

            # Calculate next Sunday 16:00
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0 and now.hour >= 16:
                days_until_sunday = 7  # Next week's Sunday
            next_sunday = now.date() + timedelta(days=days_until_sunday)
            s1_time = self.timezone.localize(datetime.combine(next_sunday, datetime.min.time().replace(hour=16, minute=0)))

            # Calculate next Monday 9:00
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and now.hour >= 9:
                days_until_monday = 7  # Next week's Monday
            next_monday = now.date() + timedelta(days=days_until_monday)
            s2_time = self.timezone.localize(datetime.combine(next_monday, datetime.min.time().replace(hour=9, minute=0)))

            self.sheets.schedule_message({
                'contact_id': contact_id,
                'message_code': 'B2_S1',
                'scheduled_send_time': s1_time.isoformat(),
                'status': 'pending',
                'trigger_type': 'tree2_sales_sunday'
            })

            self.sheets.schedule_message({
                'contact_id': contact_id,
                'message_code': 'B2_S2',
                'scheduled_send_time': s2_time.isoformat(),
                'status': 'pending',
                'trigger_type': 'tree2_sales_monday'
            })

            logger.info(f"Sent B2_RA to {contact_id}, moved to Tree 2")
            return True

        except Exception as e:
            logger.error(f"Error sending B2_RA: {e}")
            return False

    def _send_tree2_rb(self, contact_id: str, first_name: str) -> bool:
        """
        Send B2 Rb - Second Tree 2 reminder to choose timeslot

        Args:
            contact_id: Contact ID
            first_name: User's first name

        Returns:
            True if sent successfully
        """
        try:
            # Check if they already chose a timeslot
            sheet_contact = self.sheets.get_contact(contact_id)
            if not sheet_contact:
                return False

            chosen_timeslot = sheet_contact.get('chosen_timeslot')

            # If they already chose a timeslot, cancel this message
            if chosen_timeslot:
                logger.info(f"Skipping B2_RB for {contact_id} - timeslot already chosen")
                return False

            # Send B2_RB
            message = self.templates['B2_RB'].format(
                name=first_name,
                zoom_link=Config.ZOOM_PREVIEW_LINK
            )

            self.api.send_message(contact_id, message)

            # Log
            self.sheets.log_message({
                'contact_id': contact_id,
                'timestamp': datetime.now(self.timezone).isoformat(),
                'direction': 'outbound',
                'message_code': 'B2_RB',
                'message_content': message[:500],
                'window_valid': 'Yes'
            })

            logger.info(f"Sent B2_RB to {contact_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending B2_RB: {e}")
            return False

    def _send_tree2_sales(self, contact_id: str, message_code: str, first_name: str) -> bool:
        """
        Send Tree 2 sales message (B2_S1, B2_S2)

        Args:
            contact_id: Contact ID
            message_code: Message code
            first_name: User's first name

        Returns:
            True if sent successfully
        """
        try:
            # Check if they already chose a timeslot or became member
            sheet_contact = self.sheets.get_contact(contact_id)
            if not sheet_contact:
                return False

            chosen_timeslot = sheet_contact.get('chosen_timeslot')
            payment_status = sheet_contact.get('payment_status', 'None')

            # If they already chose a timeslot or paid, cancel this message
            if chosen_timeslot or payment_status != 'None':
                logger.info(f"Skipping {message_code} for {contact_id} - already converted")
                return False

            # Get template
            if message_code not in self.templates:
                logger.error(f"Template not found: {message_code}")
                return False

            message = self.templates[message_code].format(
                name=first_name,
                membership_link=Config.MEMBERSHIP_LINK,
                trial_link=Config.TRIAL_LINK
            )

            # Send message
            self.api.send_message(contact_id, message)

            # Log
            self.sheets.log_message({
                'contact_id': contact_id,
                'timestamp': datetime.now(self.timezone).isoformat(),
                'direction': 'outbound',
                'message_code': message_code,
                'message_content': message[:500],
                'window_valid': 'Yes'
            })

            logger.info(f"Sent {message_code} to {contact_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending {message_code}: {e}")
            return False

    # ==================== MONDAY CSV PROCESSING ====================

    def monday_csv_processing(self):
        """
        Monday CSV processing
        Download/process Zoom attendance CSV and categorize contacts
        This is a placeholder - actual CSV processing logic needs to be implemented
        """
        logger.info("Running Monday CSV processing...")

        try:
            if not self.sheets:
                logger.warning("Cannot run CSV processing - Google Sheets not available")
                return

            # TODO: Implement actual CSV processing logic
            # 1. Download Zoom attendee CSV (manually or via API)
            # 2. Match attendees with contacts in Contacts sheet
            # 3. Mark as 'Attended' or 'NoShow'
            # 4. Check payment status (manual from Ruul screenshot)
            # 5. Add to CSV_Processing sheet with follow_up_group:
            #    - 'Attended_NoSales' for those who attended but didn't buy
            #    - 'NoShow' for those who registered but didn't attend

            logger.info("CSV processing completed (placeholder)")

        except Exception as e:
            logger.error(f"Error in Monday CSV processing: {e}", exc_info=True)

    # ==================== FRIDAY RE-INVITES ====================

    def friday_reinvites(self):
        """
        Friday re-invites for NoShow and NoSales contacts
        Only sends if Tier 2 is approved in Config sheet
        """
        logger.info("Running Friday re-invites...")

        try:
            if not self.sheets:
                logger.warning("Cannot run Friday re-invites - Google Sheets not available")
                return

            # Check if Tier 2 is approved
            tier2_approved = self.sheets.get_config_value('tier2_approved')

            if tier2_approved != 'Yes':
                logger.info("Tier 2 not approved yet - skipping Friday re-invites")
                logger.info("To enable: Set 'tier2_approved' = 'Yes' in Config sheet")
                return

            # Get NoShow contacts
            noshow_contacts = self.sheets.get_follow_up_contacts('NoShow')
            logger.info(f"Found {len(noshow_contacts)} NoShow contacts")

            for contact in noshow_contacts:
                try:
                    contact_id = contact.get('contact_id')
                    first_name = contact.get('first_name', 'there')

                    # Check 72-hour window
                    sheet_contact = self.sheets.get_contact(contact_id)
                    if not sheet_contact:
                        continue

                    window_expires_at = sheet_contact.get('window_expires_at')
                    if window_expires_at:
                        expires = datetime.fromisoformat(window_expires_at)
                        now = datetime.now(self.timezone)
                        if now > expires:
                            logger.warning(f"Cannot send NoShow reinvite to {contact_id}: outside 72hr window")
                            continue

                    # Send B1_NOSHOW
                    message = self.templates['B1_NOSHOW'].format(
                        name=first_name,
                        zoom_link=Config.ZOOM_PREVIEW_LINK
                    )

                    self.api.send_message(contact_id, message)

                    # Log
                    self.sheets.log_message({
                        'contact_id': contact_id,
                        'timestamp': datetime.now(self.timezone).isoformat(),
                        'direction': 'outbound',
                        'message_code': 'B1_NOSHOW',
                        'message_content': message[:500],
                        'window_valid': 'Yes'
                    })

                    logger.info(f"Sent NoShow re-invite to {contact_id}")

                except Exception as e:
                    logger.error(f"Error sending NoShow re-invite: {e}")
                    continue

            # Get NoSales contacts (attended but didn't buy)
            nosales_contacts = self.sheets.get_follow_up_contacts('Attended_NoSales')
            logger.info(f"Found {len(nosales_contacts)} NoSales contacts")

            for contact in nosales_contacts:
                try:
                    contact_id = contact.get('contact_id')
                    first_name = contact.get('first_name', 'there')

                    # Check 72-hour window
                    sheet_contact = self.sheets.get_contact(contact_id)
                    if not sheet_contact:
                        continue

                    window_expires_at = sheet_contact.get('window_expires_at')
                    if window_expires_at:
                        expires = datetime.fromisoformat(window_expires_at)
                        now = datetime.now(self.timezone)
                        if now > expires:
                            logger.warning(f"Cannot send NoSales reinvite to {contact_id}: outside 72hr window")
                            continue

                    # Send B1_NOSALES
                    message = self.templates['B1_NOSALES'].format(
                        name=first_name,
                        zoom_link=Config.ZOOM_PREVIEW_LINK,
                        membership_link=Config.MEMBERSHIP_LINK
                    )

                    self.api.send_message(contact_id, message)

                    # Log
                    self.sheets.log_message({
                        'contact_id': contact_id,
                        'timestamp': datetime.now(self.timezone).isoformat(),
                        'direction': 'outbound',
                        'message_code': 'B1_NOSALES',
                        'message_content': message[:500],
                        'window_valid': 'Yes'
                    })

                    logger.info(f"Sent NoSales re-invite to {contact_id}")

                except Exception as e:
                    logger.error(f"Error sending NoSales re-invite: {e}")
                    continue

            logger.info("Friday re-invites completed")

        except Exception as e:
            logger.error(f"Error in Friday re-invites: {e}", exc_info=True)

    def trigger_manual_reminder_check(self):
        """Manually trigger scheduled message processing (for testing/admin)"""
        logger.info("Manual scheduled message check triggered")
        self.process_scheduled_messages()
