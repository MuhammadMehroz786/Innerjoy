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
    Webhook endpoint for Respond.io
    Receives incoming WhatsApp messages
    """
    try:
        # Log raw data for debugging
        raw_data = request.get_data(as_text=True)
        logger.info(f"Raw webhook data (FULL): {raw_data}")  # Log ALL data

        # Try to parse JSON with fallback
        try:
            data = request.get_json(force=True)
        except Exception as json_error:
            logger.error(f"JSON parse error: {json_error}")
            logger.error(f"Content-Type: {request.content_type}")
            logger.error(f"Raw data: {raw_data}")
            return jsonify({'error': 'Invalid JSON format'}), 400

        if not data:
            logger.warning("Received empty webhook data")
            return jsonify({'error': 'No data received'}), 400

        logger.info(f"Parsed webhook data (FULL): {data}")
        logger.info(f"All keys in data: {list(data.keys())}")
        if 'contact' in data:
            logger.info(f"All contact keys: {list(data['contact'].keys())}")
        if 'message' in data:
            logger.info(f"All message keys: {list(data['message'].keys())}")

        # Verify webhook secret if configured
        if Config.WEBHOOK_SECRET:
            signature = request.headers.get('X-Webhook-Signature')
            # Add signature verification logic here if needed

        # Extract event type
        event_type = data.get('event')

        if event_type == 'message.received':
            # Process incoming message
            success = message_handler.process_message(data)

            if success:
                return jsonify({'status': 'processed'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'Failed to process'}), 500

        else:
            logger.info(f"Unhandled event type: {event_type}")
            return jsonify({'status': 'ignored', 'event': event_type}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


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

        # Check 24-hour window
        if not api.check_24hr_window(contact_id):
            return jsonify({
                'error': 'Contact is outside 24-hour messaging window'
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
                'timeslot_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0},
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

        # Count by timeslot
        timeslot_counts = {}
        for slot in ['A', 'B', 'C', 'D', 'E']:
            timeslot_counts[slot] = len([c for c in contacts if c.get('chosen_timeslot') == slot])

        return jsonify({
            'total_contacts': total_contacts,
            'with_timeslot': with_timeslot,
            'without_timeslot': without_timeslot,
            'thumbs_up_count': thumbs_up_count,
            'members': members,
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

        # Update in Respond.io
        api.update_contact_field(
            contact_id,
            Config.CUSTOM_FIELDS['MEMBER_STATUS'],
            status
        )

        # Update in Google Sheets
        sheets.update_contact(contact_id, {'member_status': status})

        # If becoming a member, send welcome message
        if status in ['trial', 'member']:
            contact = api.get_contact(contact_id)
            custom_fields = contact.get('customFields', {})
            first_name = custom_fields.get(Config.CUSTOM_FIELDS['FIRST_NAME'], 'there')

            welcome_message = Config.get_message_templates()['PAYMENT_RECEIVED'].format(
                name=first_name,
                member_zoom_link=Config.ZOOM_MEMBER_LINK
            )

            if api.check_24hr_window(contact_id):
                api.send_message(contact_id, welcome_message)

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
