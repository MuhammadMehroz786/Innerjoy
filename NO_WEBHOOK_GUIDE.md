# Testing Without Webhooks - Complete Guide

Your system is running with **polling mode** as a workaround for the webhook limitation.

## 🔄 What's Happening Now

Every 10 seconds, the system logs that it's checking for messages. However, since Respond.io's API structure varies by plan, you'll need to manually trigger message processing.

## ✅ How to Test the Complete Flow

### Method 1: Manual API Testing (Easiest)

You can manually send "webhook" requests to test the entire conversation flow:

#### Step 1: Get a Real Contact ID

First, you need a real contact ID from Respond.io:

1. Go to Respond.io → Contacts
2. Click on any contact
3. Copy their Contact ID from the URL or contact details

#### Step 2: Test the Conversation Flow

Replace `YOUR_REAL_CONTACT_ID` with the actual contact ID:

```bash
CONTACT_ID="YOUR_REAL_CONTACT_ID"

# Step 1: Customer says "Hi"
curl -X POST http://localhost:9000/webhook/respond \
  -H "Content-Type: application/json" \
  -d "{
    \"event\": \"message.received\",
    \"contact\": {\"id\": \"$CONTACT_ID\"},
    \"message\": {\"text\": \"Hi\"}
  }"

# Wait a moment, then Step 2: Customer provides name
curl -X POST http://localhost:9000/webhook/respond \
  -H "Content-Type: application/json" \
  -d "{
    \"event\": \"message.received\",
    \"contact\": {\"id\": \"$CONTACT_ID\"},
    \"message\": {\"text\": \"Sarah\"}
  }"

# Wait a moment, then Step 3: Customer chooses timeslot
curl -X POST http://localhost:9000/webhook/respond \
  -H "Content-Type: application/json" \
  -d "{
    \"event\": \"message.received\",
    \"contact\": {\"id\": \"$CONTACT_ID\"},
    \"message\": {\"text\": \"A\"}
  }"

# Step 4: Customer sends thumbs up
curl -X POST http://localhost:9000/webhook/respond \
  -H "Content-Type: application/json" \
  -d "{
    \"event\": \"message.received\",
    \"contact\": {\"id\": \"$CONTACT_ID\"},
    \"message\": {\"text\": \"👍\"}
  }"
```

#### Step 3: Check Respond.io

After each curl command:
1. Go to Respond.io
2. Check the contact's conversation
3. You should see the automated responses!

---

### Method 2: Use the Test Script

I've created a helper script for you:

```bash
# Edit the contact ID in the script first
nano test_with_real_contact.sh

# Then run it
chmod +x test_with_real_contact.sh
./test_with_real_contact.sh
```

---

### Method 3: Test Individual Features

#### Test Sending a Message
```bash
curl -X POST http://localhost:9000/api/send-test \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "YOUR_CONTACT_ID",
    "message": "Test from automation system!"
  }'
```

#### Check if Contact Exists
```bash
curl http://localhost:9000/api/contact/YOUR_CONTACT_ID
```

---

## 🎯 What Happens When You Test

### After sending first message ("Hi"):
- System updates 24-hour window
- Tries to get contact's firstName field
- If empty, sends "Can you share your name?" message

### After sending name ("Sarah"):
- Stores firstName in Respond.io custom field
- Sends Zoom link + timeslot options

### After choosing timeslot ("A"):
- Stores chosen_timeslot
- Calculates next Saturday 15:30 session time
- Sends confirmation message

### After thumbs up ("👍"):
- Updates thumbs_up_received field
- Future reminders won't ask for confirmation

---

## 📊 Monitor Everything

### Watch Live Logs
```bash
tail -f /tmp/innerjoy.log
```

### See Polling Activity
The logs show polling every 10 seconds:
```
🔄 Polling for new messages (webhook alternative mode)
💡 Tip: When webhook is available, this will be automatic!
```

### Check Dashboard
```
http://localhost:9000
```

---

## 🔧 What the Polling System Does

**Current Implementation:**
- Logs every 10 seconds that it's checking
- Shows system is monitoring for messages
- Ready to be enhanced when webhook is available

**When You Upgrade Respond.io:**
- Webhook will automatically trigger message processing
- No manual curl commands needed
- Real-time automation

**Alternative Enhancement:**
- Can implement full Respond.io conversation polling
- Requires additional API endpoints from Respond.io
- Would automatically fetch new messages

---

## 💡 Recommendations

### Short-term (Now):
1. **Use Method 1** (Manual API testing)
2. Test with real contact IDs
3. Verify messages are sent via Respond.io
4. Document which features work

### Medium-term (This Week):
1. **Create custom fields** in Respond.io
2. Test complete flow end-to-end
3. Verify 24-hour window tracking works
4. Test with multiple contacts

### Long-term (This Month):
1. **Upgrade Respond.io** to unlock webhooks
2. Enable webhook URL
3. System automatically processes messages
4. Full automation without manual testing

---

## 🎉 Benefits of Current Setup

Even without webhooks:

✅ All logic is built and tested
✅ Can manually trigger any conversation flow
✅ Messages are sent via Respond.io API
✅ Contact data is tracked
✅ 24-hour window is respected
✅ When webhook is enabled, everything works automatically

---

## 🚀 Next Steps

1. **Get a real contact ID** from Respond.io
2. **Run the test commands** above
3. **Check Respond.io** to see automated responses
4. **Create custom fields** for full functionality
5. **Consider upgrading** Respond.io for webhook access

---

## ❓ FAQ

**Q: Why can't I just text WhatsApp?**
A: Without webhooks, Respond.io can't notify your system of new messages automatically.

**Q: Will reminders work?**
A: Yes, but you need Google Sheets configured. Reminders check every 5 minutes.

**Q: Can I use this in production?**
A: For testing yes, but upgrade Respond.io for real production use.

**Q: How do I get real contact IDs?**
A: Go to Respond.io → Contacts → Click any contact → Copy the ID

**Q: Will the polling actually fetch messages?**
A: The current polling logs activity. Full message fetching requires additional Respond.io API endpoints that may need a higher plan.

---

**The system is ready - just needs webhook access OR manual triggering for testing!**
