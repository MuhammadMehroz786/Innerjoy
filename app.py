"""
Inner Joy Studio WhatsApp Automation
Main Flask Application
"""
import logging
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import pytz

from config import Config
from services.respond_api import RespondAPI
from services.google_sheets import GoogleSheetsService
from services.message_handler import MessageHandler
from services.reminder_scheduler import ReminderScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('innerjoy_automation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize services
api = RespondAPI()
try:
    sheets = GoogleSheetsService() if Config.GOOGLE_SHEETS_ID else None
except Exception as e:
    logger.warning(f"Google Sheets not available: {e}")
    sheets = None
message_handler = MessageHandler()
try:
    scheduler = ReminderScheduler()
except Exception as e:
    logger.warning(f"Scheduler not available: {e}")
    scheduler = None


@app.before_request
def log_request():
    """Log all incoming requests"""
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")


@app.route('/')
def index():
    """Home page with dashboard"""
    return render_template('dashboard.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Inner Joy Studio Automation'
    })


@app.route('/webhook/respond', methods=['POST'])
def webhook_respond():
    """
    Webhook endpoint for Make.com → Flask
    Receives incoming WhatsApp messages from Make.com

    Expected format from Make.com:
    {
        "event_type": "message.received",
        "Contact": {
            "Contact ID": "339593905",
            "First Name": "Mehroz",
            "Phone No.": "+923273626526",
            ...
        },
        "Message": {
            "Message": {
                "Type": "text",
                "Text": "hey"
            },
            ...
        }
    }
    """
    try:
        # Log raw data for debugging
        raw_data = request.get_data(as_text=True)
        raw_bytes = request.get_data()
        logger.info(f"Raw webhook data from Make.com: {raw_data}")
        logger.info(f"Raw bytes length: {len(raw_bytes)}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Content-Length: {request.content_length}")

        # Try to parse JSON
        try:
            data = request.get_json(force=True)
        except Exception as json_error:
            # If JSON parsing fails, try to fix common issues from Make.com
            logger.warning(f"Initial JSON parse failed, attempting to fix: {json_error}")
            try:
                import json
                import re

                # Fix literal newlines in JSON string values
                # Replace unescaped newlines with escaped ones
                # This regex finds strings and escapes newlines within them
                def fix_newlines_in_strings(match):
                    string_content = match.group(0)
                    # Replace literal newlines with \n
                    fixed = string_content.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    return fixed

                # Fix the JSON by escaping control characters in string values
                fixed_data = raw_data
                # Simple approach: replace all literal newlines with escaped newlines
                # Be careful not to break the JSON structure itself
                fixed_data = fixed_data.replace('\\n', '\\\\n')  # First, protect already escaped newlines
                fixed_data = fixed_data.replace('\n', '\\n')      # Then escape literal newlines
                fixed_data = fixed_data.replace('\\\\n', '\\n')  # Restore the protected ones
                fixed_data = fixed_data.replace('\r', '\\r')      # Escape carriage returns
                fixed_data = fixed_data.replace('\t', '\\t')      # Escape tabs

                data = json.loads(fixed_data)
                logger.info("Successfully parsed JSON after fixing newlines")
            except Exception as retry_error:
                logger.error(f"JSON parse error (final): {retry_error}")
                logger.error(f"Error type: {type(retry_error).__name__}")
                logger.error(f"Content-Type: {request.content_type}")
                logger.error(f"Raw data (first 500 chars): {raw_data[:500]}")
                logger.error(f"Raw bytes (hex, first 100): {raw_bytes[:100].hex()}")
                return jsonify({
                    'error': 'Invalid JSON format',
                    'details': str(retry_error),
                    'content_type': request.content_type,
                    'data_preview': raw_data[:200]
                }), 400

        if not data:
            logger.warning("Received empty webhook data")
            return jsonify({'error': 'No data received'}), 400

        logger.info(f"Parsed webhook data from Make.com: {data}")

        # Extract event type (Make.com format uses "event_type")
        event_type = data.get('event_type', data.get('event'))

        if event_type == 'message.received':
            # Transform Make.com format to internal format
            transformed_data = _transform_makecom_to_internal(data)

            # Process incoming message
            success = message_handler.process_message(transformed_data)

            if success:
                return jsonify({'status': 'processed', 'message': 'Message processed successfully'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'Failed to process'}), 500

        else:
            logger.info(f"Unhandled event type: {event_type}")
            return jsonify({'status': 'ignored', 'event': event_type}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def _transform_makecom_to_internal(make_data: dict) -> dict:
    """
    Transform Make.com webhook format to internal message handler format
    Supports multiple Make.com output formats

    Args:
        make_data: Data from Make.com

    Returns:
        Transformed data for message_handler
    """
    try:
        # Check if data is already in simple format (from Make.com HTTP module)
        if 'contact' in make_data and 'message' in make_data:
            # Simple format from Make.com HTTP module
            contact_info = make_data.get('contact', {})
            message_info = make_data.get('message', {})

            contact_id = contact_info.get('id', '')
            phone = contact_info.get('phone', '')
            first_name = contact_info.get('firstName', contact_info.get('first_name', ''))
            message_text = message_info.get('text', '')

            # Extract custom fields and tags (if present in Make.com payload)
            custom_fields = contact_info.get('customFields', contact_info.get('custom_fields', {}))
            tags = contact_info.get('tags', [])

            internal_format = {
                'event': 'message.received',
                'contact': {
                    'id': contact_id,
                    'phone': phone,
                    'firstName': first_name,
                    'lastName': contact_info.get('lastName', contact_info.get('last_name', '')),
                    'customFields': custom_fields,
                    'tags': tags
                },
                'message': {
                    'id': message_info.get('id', ''),
                    'type': message_info.get('type', 'text'),
                    'text': message_text,
                    'timestamp': message_info.get('timestamp', ''),
                    'context': message_info.get('context', {})
                },
                'channel': make_data.get('channel', {})
            }

            logger.info(f"Transformed Make.com data (simple format) - Contact: {contact_id}, Phone: {phone}, Text: {message_text}")
            return internal_format

        # Complex format from Make.com Respond.io module
        else:
            contact_info = make_data.get('Contact', {})
            contact_id = contact_info.get('Contact ID', '')
            first_name = contact_info.get('First Name', '')
            phone = contact_info.get('Phone No.', '')

            message_info = make_data.get('Message', {})
            message_content = message_info.get('Message', {})
            message_text = message_content.get('Text', '')
            message_type = message_content.get('Type', 'text')

            # Extract custom fields and tags from Make.com complex format
            # Make.com might send custom fields as separate keys
            custom_fields = {}
            tags = []

            # Look for custom field keys in contact_info
            for key, value in contact_info.items():
                # Skip standard fields
                if key not in ['Contact ID', 'First Name', 'Last Name', 'Phone No.', 'Email']:
                    # This is likely a custom field
                    custom_fields[key] = value

            # Check if tags exist in specific field
            if 'Tags' in contact_info:
                tags = contact_info.get('Tags', [])
                if isinstance(tags, str):
                    # If tags come as comma-separated string, split them
                    tags = [t.strip() for t in tags.split(',')]

            internal_format = {
                'event': 'message.received',
                'contact': {
                    'id': contact_id,
                    'phone': phone,
                    'firstName': first_name,
                    'lastName': contact_info.get('Last Name', ''),
                    'customFields': custom_fields,
                    'tags': tags
                },
                'message': {
                    'id': message_info.get('ID', ''),
                    'type': message_type,
                    'text': message_text,
                    'timestamp': message_info.get('Timestamp', ''),
                    'context': message_content.get('Context', {})
                },
                'channel': make_data.get('Channel', {})
            }

            logger.info(f"Transformed Make.com data (complex format) - Contact: {contact_id}, Phone: {phone}, Text: {message_text}, CustomFields: {list(custom_fields.keys())}, Tags: {tags}")
            return internal_format

    except Exception as e:
        logger.error(f"Error transforming Make.com data: {e}", exc_info=True)
        raise


@app.route('/api/send-test', methods=['POST'])
def send_test_message():
    """
    Send a test message to a contact
    Body: { "contact_id": "...", "message": "..." }
    """
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        message = data.get('message')

        if not contact_id or not message:
            return jsonify({'error': 'Missing contact_id or message'}), 400

        # Check 72-hour window
        if not api.check_72hr_window(contact_id):
            return jsonify({
                'error': 'Contact is outside 72-hour messaging window'
            }), 400

        # Send message
        result = api.send_message(contact_id, message)

        return jsonify({
            'status': 'sent',
            'contact_id': contact_id,
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"Error sending test message: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """
    Get all contacts from Google Sheets
    """
    try:
        if not sheets:
            return jsonify({'error': 'Google Sheets not configured', 'contacts': []}), 200

        contacts = sheets.get_all_contacts()

        return jsonify({
            'count': len(contacts),
            'contacts': contacts
        }), 200

    except Exception as e:
        logger.error(f"Error getting contacts: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/contact/<contact_id>', methods=['GET'])
def get_contact(contact_id):
    """
    Get a specific contact's information
    """
    try:
        # Get from Google Sheets
        sheet_data = sheets.get_contact(contact_id)

        # Get from Respond.io
        respond_data = api.get_contact(contact_id)

        return jsonify({
            'sheet_data': sheet_data,
            'respond_data': respond_data
        }), 200

    except Exception as e:
        logger.error(f"Error getting contact {contact_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get system statistics
    """
    try:
        if not sheets:
            return jsonify({
                'total_contacts': 0,
                'with_timeslot': 0,
                'without_timeslot': 0,
                'thumbs_up_count': 0,
                'members': 0,
                'source_distribution': {'facebook_ads': 0, 'website': 0},
                'timeslot_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0},
                'timestamp': datetime.now().isoformat(),
                'note': 'Google Sheets not configured'
            }), 200

        contacts = sheets.get_all_contacts()

        # Calculate statistics
        total_contacts = len(contacts)
        with_timeslot = len([c for c in contacts if c.get('chosen_timeslot')])
        without_timeslot = total_contacts - with_timeslot
        thumbs_up_count = len([c for c in contacts if c.get('thumbs_up') == 'Yes'])
        members = len([c for c in contacts if c.get('member_status') in ['trial', 'member']])

        # Count by source
        facebook_ads_count = len([c for c in contacts if c.get('contact_source') == 'facebook_ads'])
        website_count = len([c for c in contacts if c.get('contact_source') == 'website'])

        # Count by timeslot
        timeslot_counts = {}
        for slot in ['A', 'B', 'C', 'D']:
            timeslot_counts[slot] = len([c for c in contacts if c.get('chosen_timeslot') == slot])

        return jsonify({
            'total_contacts': total_contacts,
            'with_timeslot': with_timeslot,
            'without_timeslot': without_timeslot,
            'thumbs_up_count': thumbs_up_count,
            'members': members,
            'source_distribution': {
                'facebook_ads': facebook_ads_count,
                'website': website_count
            },
            'timeslot_distribution': timeslot_counts,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/trigger-reminder', methods=['POST'])
def trigger_reminder():
    """
    Manually trigger reminder check
    """
    try:
        if not scheduler:
            return jsonify({'error': 'Scheduler not configured'}), 400

        scheduler.trigger_manual_reminder_check()

        return jsonify({
            'status': 'triggered',
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error triggering reminder: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/send-reminder', methods=['POST'])
def send_specific_reminder():
    """
    Send a specific reminder to a contact
    Body: { "contact_id": "...", "reminder_type": "12h|60min|10min" }
    """
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        reminder_type = data.get('reminder_type')

        if not contact_id or not reminder_type:
            return jsonify({'error': 'Missing contact_id or reminder_type'}), 400

        if reminder_type not in ['12h', '60min', '10min']:
            return jsonify({'error': 'Invalid reminder_type'}), 400

        success = message_handler.send_reminder(contact_id, reminder_type)

        if success:
            return jsonify({
                'status': 'sent',
                'contact_id': contact_id,
                'reminder_type': reminder_type
            }), 200
        else:
            return jsonify({
                'status': 'failed',
                'message': 'Could not send reminder (check logs)'
            }), 500

    except Exception as e:
        logger.error(f"Error sending reminder: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-attendance', methods=['POST'])
def update_attendance():
    """
    Update attendance status for a contact
    Body: { "contact_id": "...", "attended": "Yes|NoShow" }
    """
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        attended = data.get('attended')

        if not contact_id or not attended:
            return jsonify({'error': 'Missing contact_id or attended'}), 400

        # Update in Google Sheets
        success = sheets.update_contact(contact_id, {'attended': attended})

        if success:
            return jsonify({
                'status': 'updated',
                'contact_id': contact_id,
                'attended': attended
            }), 200
        else:
            return jsonify({'status': 'failed'}), 500

    except Exception as e:
        logger.error(f"Error updating attendance: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-member-status', methods=['POST'])
def update_member_status():
    """
    Update member status for a contact
    Body: { "contact_id": "...", "status": "prospect|trial|member" }
    """
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        status = data.get('status')

        if not contact_id or not status:
            return jsonify({'error': 'Missing contact_id or status'}), 400

        # Update in Google Sheets (primary database)
        # Note: Skipping Respond.io field update to avoid 400 errors with phone:+number format
        sheets.update_contact(contact_id, {'member_status': status})

        # If becoming a member, send welcome message
        if status in ['trial', 'member']:
            # Get contact info from sheets to get first_name
            contact_data = sheets.get_contact(contact_id) if sheets else {}
            first_name = contact_data.get('first_name', 'there')

            # Choose template based on status
            if status == 'trial':
                template_key = 'B1_M1A1'
                # For trial, we'd need trial_start and trial_end dates
                # For now, use full membership template
                template_key = 'B1_M1'
            else:
                template_key = 'B1_M1'

            welcome_message = Config.get_message_templates()[template_key].format(
                name=first_name,
                member_zoom_link=Config.ZOOM_MEMBER_LINK,
                youtube_playlist_link=Config.YOUTUBE_PLAYLIST_LINK
            )

            # Check 72-hour window before sending
            if api.check_72hr_window(contact_id):
                api.send_message(contact_id, welcome_message, channel_id=Config.RESPOND_CHANNEL_ID)
                logger.info(f"Sent welcome message to new {status}: {contact_id}")

        return jsonify({
            'status': 'updated',
            'contact_id': contact_id,
            'member_status': status
        }), 200

    except Exception as e:
        logger.error(f"Error updating member status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/initialize-sheets', methods=['POST'])
def initialize_sheets():
    """
    Initialize Google Sheets with headers
    """
    try:
        sheets.initialize_sheet()

        return jsonify({
            'status': 'initialized',
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error initializing sheets: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def init_app():
    """Initialize the application"""
    try:
        # Validate configuration (only check required fields)
        if not Config.RESPOND_API_KEY:
            raise ValueError("Missing required: RESPOND_API_KEY")
        logger.info("Configuration validated successfully")

        # Try to initialize Google Sheets (optional for testing)
        try:
            if Config.GOOGLE_SHEETS_ID:
                sheets.initialize_sheet()
                logger.info("Google Sheets initialized")
            else:
                logger.warning("Google Sheets not configured - will skip sheet operations")
        except Exception as e:
            logger.warning(f"Google Sheets initialization failed (continuing without it): {e}")

        # Start scheduler
        if scheduler:
            scheduler.start()
            logger.info("Reminder scheduler started")
        else:
            logger.warning("Scheduler not available - skipping")

        logger.info("Application initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    # Initialize app
    init_app()

    # Run Flask app
    port = Config.PORT
    debug = Config.DEBUG

    logger.info(f"Starting Inner Joy Studio Automation on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
