# Inner Joy Studio - Localhost Access Guide

Your WhatsApp automation system is running on **http://localhost:9000**

## 🌐 Web Pages

### Main Dashboard
```
http://localhost:9000
```
- View statistics (total contacts, conversions, etc.)
- See timeslot distribution
- Monitor activity log
- Send test messages
- Trigger manual reminders

### Health Check
```
http://localhost:9000/health
```
- Verify system is running
- Check timestamp

## 🔌 API Endpoints

### View Statistics
```bash
curl http://localhost:9000/api/stats
```

### View All Contacts
```bash
curl http://localhost:9000/api/contacts
```

### Get Specific Contact
```bash
curl http://localhost:9000/api/contact/CONTACT_ID
```

### Send Test Message
```bash
curl -X POST http://localhost:9000/api/send-test \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "YOUR_CONTACT_ID",
    "message": "Test message"
  }'
```

### Trigger Reminder Check
```bash
curl -X POST http://localhost:9000/api/trigger-reminder
```

### Update Member Status
```bash
curl -X POST http://localhost:9000/api/update-member-status \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "YOUR_CONTACT_ID",
    "status": "member"
  }'
```

### Webhook Endpoint (for Respond.io)
```
http://localhost:9000/webhook/respond
```
**Note:** This won't work from localhost. You need ngrok or production URL.

## 📊 Current Status

**Port:** 9000
**Environment:** Development
**Respond.io API:** ✅ Connected
**Google Sheets:** ⚠️ Not configured (optional)
**Scheduler:** ⚠️ Disabled (needs Google Sheets)

## 🧪 Testing Locally

### Test the Dashboard
1. Open http://localhost:9000
2. Click "Refresh Stats"
3. Try "Send Test Message" (needs real contact ID)
4. View activity log

### Test API Endpoints
```bash
# Check health
curl http://localhost:9000/health

# View stats
curl http://localhost:9000/api/stats

# View contacts
curl http://localhost:9000/api/contacts
```

### Test with Mock Data
```bash
# Run the test script (will fail API calls but shows flow)
./test_conversation.sh
```

## 🚀 To Test with Real WhatsApp

You need to expose localhost to the internet:

### Option 1: ngrok (Recommended for Testing)
```bash
# Install ngrok (already done)
# Get authtoken from https://dashboard.ngrok.com
ngrok config add-authtoken YOUR_TOKEN
ngrok http 9000

# Then configure webhook in Respond.io with ngrok URL
```

### Option 2: Deploy to Production
```bash
# Deploy to Heroku/Railway/Render
# Use production URL for webhook
```

## 📝 Logs

### View Live Logs
```bash
tail -f /tmp/innerjoy.log
```

### View Recent Activity
```bash
tail -50 /tmp/innerjoy.log
```

## 🛑 Control Commands

### Check if Running
```bash
curl http://localhost:9000/health
```

### Stop the App
```bash
pkill -f "python app.py"
```

### Restart the App
```bash
python app.py > /tmp/innerjoy.log 2>&1 &
```

### Check Port
```bash
lsof -ti:9000
```

## 💡 Quick Tips

1. **Dashboard is read-only** without Google Sheets - stats will show 0
2. **Test messages require real contact IDs** from Respond.io
3. **Webhook only works** when publicly accessible (ngrok or production)
4. **All message templates** are in config.py
5. **Logs show everything** - check /tmp/innerjoy.log for debugging

## 🎯 Next Steps

To actually test with WhatsApp messages:

1. **Set up ngrok** to expose localhost
2. **Configure webhook** in Respond.io
3. **Create custom fields** in Respond.io
4. **Send WhatsApp message** to your business number
5. **Watch it work!**

---

**System Running:** ✅
**Port:** 9000
**Access:** http://localhost:9000
**Logs:** /tmp/innerjoy.log
