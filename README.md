# Inner Joy Studio - WhatsApp Automation System

A complete WhatsApp automation system for managing customer registration, session scheduling, reminders, and payment follow-ups for Inner Joy Studio's wellness coaching business.

## Features

- **Automated Conversation Flows**: Handles customer registration, timeslot selection, and confirmations
- **24-Hour Window Compliance**: Respects WhatsApp's messaging window restrictions
- **Automated Reminders**: Sends reminders at T-12h, T-60min, and T-10min before sessions
- **Sales Message Sequences**: Automated follow-ups after sessions to convert prospects to members
- **Google Sheets Integration**: Tracks all customer data and interactions
- **Web Dashboard**: Monitor contacts, stats, and system activity
- **Respond.io API Integration**: Full WhatsApp Business API integration
- **Scheduled Jobs**: Automated reminder checks, Monday processing, Friday re-invites

## System Architecture

```
innerjoy_automation/
├── app.py                      # Main Flask application
├── config.py                   # Configuration and settings
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create from .env.example)
├── Procfile                    # Heroku deployment config
├── runtime.txt                 # Python version for Heroku
├── services/
│   ├── __init__.py
│   ├── respond_api.py          # Respond.io API wrapper
│   ├── message_handler.py      # Message processing logic
│   ├── reminder_scheduler.py   # APScheduler jobs
│   └── google_sheets.py        # Google Sheets integration
├── templates/
│   └── dashboard.html          # Web dashboard UI
└── static/
    └── style.css              # Dashboard styles
```

## Prerequisites

1. **Python 3.10+**
2. **Respond.io Account** with WhatsApp Business API
3. **Google Cloud Project** with Sheets API enabled
4. **Google Sheet** for data tracking

## Installation

### 1. Clone or Download the Project

```bash
cd /path/to/innerjoy_automation
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
# Respond.io API Configuration
RESPOND_API_KEY=your_respond_io_api_key_here
RESPOND_API_URL=https://api.respond.io/v2

# Google Sheets Configuration
GOOGLE_SHEETS_ID=your_google_sheet_id_here
GOOGLE_CREDENTIALS_FILE=credentials.json

# Webhook Configuration
WEBHOOK_SECRET=your_webhook_secret_here

# Flask Configuration
FLASK_ENV=development
FLASK_SECRET_KEY=your_flask_secret_key_here
PORT=5000

# Timezone Configuration
TIMEZONE=Asia/Bangkok

# Zoom Configuration
ZOOM_PREVIEW_LINK=https://us02web.zoom.us/j/82349172983
ZOOM_MEMBER_LINK=your_member_zoom_link_here

# Pricing Configuration
MEMBERSHIP_PRICE=80
TRIAL_PRICE=12
```

### 5. Set Up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google Sheets API**
4. Create credentials (OAuth 2.0 Client ID for Desktop App)
5. Download credentials and save as `credentials.json` in project root
6. Create a Google Sheet for tracking (note the Sheet ID from the URL)

### 6. Configure Respond.io Custom Fields

In your Respond.io workspace, create these custom fields:

- `firstName` (Text)
- `chosen_timeslot` (Dropdown: A, B, C, D, E)
- `last_24hr_window_start` (Text)
- `thumbs_up_received` (Dropdown: Yes, No)
- `member_status` (Dropdown: prospect, trial, member)
- `reminder_12h_sent` (Dropdown: Yes, No)
- `reminder_60min_sent` (Dropdown: Yes, No)
- `reminder_10min_sent` (Dropdown: Yes, No)

## Running the Application

### Development Mode

```bash
python app.py
```

The application will start on `http://localhost:5000`

### First Run - Initialize Google Sheets

On first run, you'll need to authenticate with Google:

1. The app will open a browser window
2. Log in with your Google account
3. Grant permissions to access Google Sheets
4. A `token.json` file will be created

Then initialize the sheet structure:

```bash
curl -X POST http://localhost:5000/api/initialize-sheets
```

### Access the Dashboard

Open your browser and go to:
```
http://localhost:5000
```

## Setting Up Webhooks

### Configure Respond.io Webhook

1. Go to Respond.io Settings > Webhooks
2. Create a new webhook
3. Set URL to: `https://your-domain.com/webhook/respond`
4. Enable event: `message.received`
5. Set webhook secret (use the same in your `.env`)

### Testing Webhooks Locally

Use ngrok to expose your local server:

```bash
ngrok http 5000
```

Use the ngrok URL for webhook configuration during development.

## API Endpoints

### Health Check
```
GET /health
```

### Dashboard
```
GET /
```

### Webhook
```
POST /webhook/respond
```

### Stats
```
GET /api/stats
```

### Contacts
```
GET /api/contacts
GET /api/contact/<contact_id>
```

### Send Test Message
```
POST /api/send-test
Body: {
  "contact_id": "...",
  "message": "..."
}
```

### Trigger Reminder Check
```
POST /api/trigger-reminder
```

### Update Attendance
```
POST /api/update-attendance
Body: {
  "contact_id": "...",
  "attended": "Yes|NoShow"
}
```

### Update Member Status
```
POST /api/update-member-status
Body: {
  "contact_id": "...",
  "status": "prospect|trial|member"
}
```

## Conversation Flows

### Tree 1 (Normal Flow)

1. **B1 Z1 - Ask Name**: Customer arrives, system asks for first name
2. **B1 Z2 - Send Zoom Link**: System sends Zoom link and timeslot options
3. **B1 Z2a1 - Confirm Timeslot**: Customer chooses slot, system confirms
4. **Reminder Sequence**:
   - T-12h: First reminder (with optional thumbs up request)
   - T-60min: Second reminder
   - T-10min: Final reminder
5. **Sales Messages**:
   - T+5min: Membership offer ($80)
   - T+20min: Social proof message
   - T+2h: Trial + Membership offer

### Tree 2 (No Timeslot Response)

If customer doesn't choose timeslot within 2 hours:
- T+22h: Re-engagement message with timeslot options
- T+23.5h: Last call message

### Scheduled Jobs

- **Reminder Check**: Every 5 minutes
- **Tree 2 Check**: Every hour
- **Monday Processing**: Every Monday at 10 AM
- **Friday Re-invites**: Every Friday at 2 PM

## Deployment

### Heroku Deployment

1. Install Heroku CLI
2. Create a new Heroku app:
```bash
heroku create innerjoy-automation
```

3. Set environment variables:
```bash
heroku config:set RESPOND_API_KEY=your_key
heroku config:set GOOGLE_SHEETS_ID=your_sheet_id
# ... set all other variables
```

4. Upload Google credentials:
```bash
# Method 1: Store as base64 in env var
cat credentials.json | base64 | heroku config:set GOOGLE_CREDENTIALS_BASE64=

# Method 2: Use Heroku config vars (simpler)
heroku config:set GOOGLE_CREDENTIALS="$(cat credentials.json)"
```

5. Deploy:
```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

6. Scale the dyno:
```bash
heroku ps:scale web=1
```

7. View logs:
```bash
heroku logs --tail
```

### Other Platforms

The application can be deployed to:
- **Railway**: Similar to Heroku
- **Render**: Free tier available
- **AWS EC2/ECS**: For more control
- **DigitalOcean**: App Platform or Droplet

## Google Sheets Structure

The system creates a sheet with these columns:

| Column | Description |
|--------|-------------|
| contact_id | Respond.io contact ID |
| whatsapp_number | Customer phone number |
| first_name | Customer's first name |
| registration_time | When they first contacted |
| chosen_timeslot | Selected timeslot (A-E) |
| session_datetime | Calculated session time |
| last_message_time | Last message timestamp |
| thumbs_up | Confirmation received (Yes/No) |
| reminder_12h_sent | 12h reminder sent (Yes/No) |
| reminder_60min_sent | 60min reminder sent (Yes/No) |
| reminder_10min_sent | 10min reminder sent (Yes/No) |
| attended | Session attendance status |
| member_status | prospect/trial/member |
| payment_verified | Payment confirmed (Yes/No) |
| tree_type | Tree1 or Tree2 |
| last_updated | Last update timestamp |

## Timeslot Configuration

| Code | Day | Time (UTC+7) |
|------|-----|--------------|
| A | Saturday | 15:30 |
| B | Saturday | 20:30 |
| C | Sunday | 06:30 |
| D | Sunday | 15:30 |
| E | Sunday | 20:30 |

## Troubleshooting

### Google Sheets Authentication Issues

If you get authentication errors:
1. Delete `token.json`
2. Restart the application
3. Re-authenticate when prompted

### 24-Hour Window Violations

If messages aren't sending:
- Check the `last_24hr_window_start` field
- Verify customer sent a message recently
- Use the dashboard to monitor window status

### Respond.io API Errors

Check:
1. API key is valid
2. Custom fields are created correctly
3. Webhook is receiving events (check logs)

### Scheduler Not Running

Verify:
- Application is running (not just gunicorn worker)
- Check logs for scheduler initialization
- Use `/api/trigger-reminder` to manually trigger

## Logging

Logs are written to:
- Console (stdout)
- `innerjoy_automation.log` file

View logs in real-time:
```bash
tail -f innerjoy_automation.log
```

## Security Considerations

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use HTTPS** in production - Protect webhook data
3. **Validate webhook signatures** - Implement in production
4. **Rate limiting** - Add rate limiting for API endpoints
5. **Input validation** - Already implemented for critical flows

## Support & Maintenance

### Regular Tasks

- **Weekly**: Review Google Sheets for accuracy
- **Monthly**: Check and clear old logs
- **Quarterly**: Review and update message templates
- **As needed**: Update timeslots for holidays

### Monitoring

- Check dashboard daily for stats
- Monitor activity log for errors
- Review Google Sheets for data integrity

## Future Enhancements

Potential improvements:
- Payment gateway integration (auto-verify payments)
- SMS backup for critical reminders
- Advanced analytics dashboard
- Multi-language support
- CRM integration
- Email notifications for admin

## License

Proprietary - Inner Joy Studio

## Contact

For support or questions about the system, contact the Inner Joy Studio technical team.

---

**Version**: 1.0.0
**Last Updated**: 2024
**Built with**: Flask, Respond.io API, Google Sheets API, APScheduler
