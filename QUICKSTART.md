# Quick Start Guide - Inner Joy Studio Automation

Get up and running in 10 minutes!

## Step 1: Install Dependencies (2 minutes)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Configure Environment (3 minutes)

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:
   - Get Respond.io API key from: Settings > API Keys
   - Get Google Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
   - Generate a random webhook secret

## Step 3: Set Up Google Sheets (3 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "Google Sheets API"
4. Create credentials: OAuth 2.0 Client ID (Desktop)
5. Download and save as `credentials.json`

## Step 4: Configure Respond.io (2 minutes)

In Respond.io, create these custom fields:

| Field Name | Type | Options |
|------------|------|---------|
| firstName | Text | - |
| chosen_timeslot | Dropdown | A, B, C, D, E |
| last_24hr_window_start | Text | - |
| thumbs_up_received | Dropdown | Yes, No |
| member_status | Dropdown | prospect, trial, member |
| reminder_12h_sent | Dropdown | Yes, No |
| reminder_60min_sent | Dropdown | Yes, No |
| reminder_10min_sent | Dropdown | Yes, No |

## Step 5: Run the Application

```bash
# Start the app
python app.py
```

Visit: `http://localhost:5000`

## Step 6: Initialize Google Sheets

```bash
curl -X POST http://localhost:5000/api/initialize-sheets
```

## Step 7: Set Up Webhook (for testing)

1. Install ngrok: `brew install ngrok` (or download from ngrok.com)
2. Run: `ngrok http 5000`
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. In Respond.io:
   - Go to Settings > Webhooks
   - Create new webhook
   - URL: `https://abc123.ngrok.io/webhook/respond`
   - Event: `message.received`
   - Save

## Test It!

1. Send a message to your WhatsApp Business number
2. Watch the dashboard update
3. Check the activity log
4. Verify Google Sheets is updated

## Common Issues

### "Google credentials not found"
- Make sure `credentials.json` is in the project root
- Check the file name is exactly `credentials.json`

### "Respond.io API error"
- Verify API key is correct
- Check custom fields are created
- Ensure API key has proper permissions

### "Webhook not receiving messages"
- Check ngrok is running
- Verify webhook URL in Respond.io
- Look for errors in terminal logs

## Next Steps

1. Test the full conversation flow
2. Review message templates in `config.py`
3. Customize timeslots if needed
4. Set up production deployment (see README.md)

## Quick Commands

```bash
# Start app
python app.py

# View logs
tail -f innerjoy_automation.log

# Test reminder check
curl -X POST http://localhost:5000/api/trigger-reminder

# Get stats
curl http://localhost:5000/api/stats

# Send test message
curl -X POST http://localhost:5000/api/send-test \
  -H "Content-Type: application/json" \
  -d '{"contact_id":"CONTACT_ID","message":"Test message"}'
```

## Support

Check the full README.md for detailed documentation.

Happy automating!
