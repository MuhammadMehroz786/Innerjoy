# Inner Joy Studio - Conversation Flow Diagram

## Complete Customer Journey Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEW CUSTOMER ARRIVES                          │
│              (From Facebook Ad → WhatsApp)                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  B1 Z1: ASK NAME                                                 │
│  "Hi 🌸 I'm Ineke from InnerJoy! Can you share your name?"      │
│  → Update 24hr window                                            │
│  → Store in Google Sheets                                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  B1 Z2: SEND ZOOM LINK                                           │
│  "Here's your Zoom link + timeslot options (A-E)"                │
│  → Store firstName in Respond.io                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
           ┌─────────┴──────────┐
           │                    │
      RESPONDS?             NO RESPONSE
           │                    │
           ▼                    ▼
    ┌──────────┐         ┌─────────────┐
    │  TREE 1  │         │   TREE 2    │
    │  NORMAL  │         │ (T+2 hours) │
    └──────────┘         └─────────────┘


═══════════════════════════════════════════════════════════════════
                         TREE 1: NORMAL FLOW
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  CUSTOMER CHOOSES TIMESLOT (A, B, C, D, or E)                    │
│  → Detect letter in message                                      │
│  → Calculate next session datetime                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  B1 Z2a1: CONFIRM TIMESLOT                                       │
│  "Perfect! Your spot is saved for [Day] at [Time]"               │
│  → Update chosen_timeslot in Respond.io                          │
│  → Update Google Sheets with session_datetime                    │
│  → Schedule reminder jobs                                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  REMINDER SEQUENCE BEGINS                                        │
│  (APScheduler runs every 5 minutes to check)                     │
└─────────────────────────────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
   T-12h         T-60min         T-10min
      │              │              │
      ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ REMINDER │   │ REMINDER │   │ REMINDER │
│    1     │   │    2     │   │    3     │
├──────────┤   ├──────────┤   ├──────────┤
│"Session  │   │"Starts   │   │"Starts   │
│tomorrow" │   │in 1 hour"│   │in 10 min"│
│          │   │          │   │          │
│Optional: │   │With Zoom │   │With Zoom │
│Send 👍   │   │link      │   │link      │
│if no     │   │          │   │          │
│thumbs up │   │          │   │          │
│yet       │   │          │   │          │
└──────────┘   └──────────┘   └──────────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   CHECK 24HR WINDOW    │
        │  Before each message   │
        └────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION HAPPENS                               │
│            (Customer joins Zoom preview)                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
   T+5min        T+20min         T+2h
      │              │              │
      ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ SALES S1 │   │ SHAKE-UP │   │ SALES S2 │
├──────────┤   ├──────────┤   ├──────────┤
│"Join for │   │"8/10     │   │"Trial or │
│$80/3mo"  │   │members   │   │Membership│
│          │   │progressing│   │options"  │
│Membership│   │Social    │   │          │
│offer     │   │proof     │   │$12 trial │
│          │   │          │   │$80 member│
└──────────┘   └──────────┘   └──────────┘


═══════════════════════════════════════════════════════════════════
                  TREE 2: NO TIMESLOT SELECTED
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  NO TIMESLOT CHOSEN WITHIN 2 HOURS                               │
│  → Switch tree_type to "Tree2" in Google Sheets                  │
│  → APScheduler monitors hourly                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  T+22h: TREE2 SALES MESSAGE 1                                    │
│  "I noticed you haven't picked a time yet..."                    │
│  → Re-engagement attempt                                         │
│  → Show timeslot options again                                   │
│  → Include Zoom link                                             │
│  → Check 24hr window before sending                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
           ┌─────────┴──────────┐
           │                    │
      RESPONDS?             NO RESPONSE
           │                    │
           ▼                    ▼
    Back to Tree 1       Continue Tree 2
    (if timeslot           (wait 1.5h)
     selected)                  │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  T+23.5h: TREE2 SALES MESSAGE 2                                  │
│  "Last call! I'm here if you change your mind..."                │
│  → Final engagement attempt                                      │
│  → Offer free resources as alternative                           │
│  → Check 24hr window before sending                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
           ┌─────────┴──────────┐
           │                    │
      RESPONDS?             NO RESPONSE
           │                    │
           ▼                    ▼
    Back to Tree 1         Mark as cold lead
    (if timeslot           (Keep in sheets
     selected)              for reference)


═══════════════════════════════════════════════════════════════════
                    MONDAY CSV PROCESSING
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  EVERY MONDAY 10 AM                                              │
│  → Download Zoom attendee CSV for last weekend                   │
│  → Match with contacts in Google Sheets                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
   ATTENDED      NO SHOW        NO RECORD
      │              │              │
      ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ MARK AS  │   │ MARK AS  │   │  NEEDS   │
│ "ATTENDED"│   │ "NOSHOW" │   │  MANUAL  │
│          │   │          │   │  REVIEW  │
│Tag:      │   │Tag:      │   │          │
│Attended  │   │NoShow    │   │          │
└──────────┘   └──────────┘   └──────────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  UPDATE GOOGLE SHEETS                                            │
│  → Set attended field                                            │
│  → Prepare for Friday re-invite if needed                        │
└─────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
                      FRIDAY RE-INVITES
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  EVERY FRIDAY 2 PM                                               │
│  → Check Google Sheets for NoShow and NoSales                    │
│  → APScheduler triggers job                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
   NO SHOW      NO SALES      MEMBERS
(registered    (attended    (already
but didn't     but didn't    converted)
 attend)       convert)          │
      │              │             │
      ▼              ▼             ▼
┌──────────┐   ┌──────────┐   Skip them
│ RE-INVITE│   │ RE-INVITE│
│ MESSAGE  │   │ MESSAGE  │
├──────────┤   ├──────────┤
│"Missed   │   │"Join     │
│you!      │   │again or  │
│New times │   │ready to  │
│this      │   │become    │
│weekend"  │   │member?"  │
│          │   │          │
│+ Timeslot│   │+ Options │
│  options │   │          │
└──────────┘   └──────────┘


═══════════════════════════════════════════════════════════════════
                    PAYMENT & MEMBERSHIP FLOW
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  CUSTOMER DECIDES TO JOIN                                        │
│  → Sends payment screenshot                                      │
│  → Or indicates interest in trial/membership                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  MANUAL VERIFICATION (Admin)                                     │
│  → Admin checks payment screenshot                               │
│  → Admin uses dashboard API to update status                     │
│  POST /api/update-member-status                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
   TRIAL          MEMBER        REJECTED
      │              │              │
      ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ WELCOME  │   │ WELCOME  │   │  FOLLOW  │
│ MESSAGE  │   │ MESSAGE  │   │    UP    │
├──────────┤   ├──────────┤   ├──────────┤
│"Welcome! │   │"Welcome  │   │Manual    │
│Trial     │   │to Inner  │   │outreach  │
│started"  │   │Joy!"     │   │          │
│          │   │          │   │          │
│+ Member  │   │+ Member  │   │          │
│  Zoom    │   │  Zoom    │   │          │
│  link    │   │  link    │   │          │
└──────────┘   └──────────┘   └──────────┘
      │              │
      └──────────────┼──────────────┐
                     │              │
                     ▼              ▼
           Update Google Sheets  Update Respond.io
           member_status         member_status field
           payment_verified      Add "Member" tag


═══════════════════════════════════════════════════════════════════
                  24-HOUR WINDOW MANAGEMENT
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  EVERY INCOMING MESSAGE                                          │
│  → Webhook receives message.received event                       │
│  → Update last_24hr_window_start to NOW                          │
│  → Store in Respond.io custom field                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  BEFORE SENDING ANY MESSAGE                                      │
│  1. Get last_24hr_window_start                                   │
│  2. Calculate time elapsed                                       │
│  3. Check if < 24 hours                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
           ┌─────────┴──────────┐
           │                    │
        Within 24h          Outside 24h
           │                    │
           ▼                    ▼
      Send message        DON'T SEND
      successfully        Log warning
                          Wait for customer
                          to message first


═══════════════════════════════════════════════════════════════════
                      SPECIAL SCENARIOS
═══════════════════════════════════════════════════════════════════

SCENARIO 1: Customer sends 👍 (Thumbs Up)
─────────────────────────────────────────
┌─────────────────────────────────────────┐
│ Detect 👍 in message                    │
│ → Update thumbs_up_received = "Yes"    │
│ → Future reminders won't ask for 👍    │
│ → Shows confirmed in Google Sheets     │
└─────────────────────────────────────────┘

SCENARIO 2: Customer changes timeslot
──────────────────────────────────────
┌─────────────────────────────────────────┐
│ New letter detected (A/B/C/D/E)        │
│ → Override previous timeslot           │
│ → Recalculate session_datetime         │
│ → Reset reminder flags                 │
│ → Send new confirmation                │
└─────────────────────────────────────────┘

SCENARIO 3: Outside 24hr window
────────────────────────────────
┌─────────────────────────────────────────┐
│ Automated message scheduled             │
│ → Check window before sending           │
│ → If outside: Log + Skip                │
│ → Retry when customer messages again    │
│ → Dashboard shows warning               │
└─────────────────────────────────────────┘

SCENARIO 4: Customer asks general question
───────────────────────────────────────────
┌─────────────────────────────────────────┐
│ Message doesn't match any flow          │
│ → Update 24hr window                    │
│ → Log in Google Sheets                  │
│ → System acknowledges silently          │
│ → (Manual response via Respond.io)      │
└─────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
                    DATA FLOW SUMMARY
═══════════════════════════════════════════════════════════════════

Customer Message
      │
      ▼
Respond.io Webhook
      │
      ▼
Flask app.py → /webhook/respond
      │
      ▼
MessageHandler.process_message()
      │
      ├──→ Update 24hr window in Respond.io
      ├──→ Log to Google Sheets
      ├──→ Process conversation flow
      └──→ Send appropriate response
                │
                ▼
        RespondAPI.send_message()
                │
                ├──→ Check 24hr window
                ├──→ Send via Respond.io API
                └──→ Update tracking fields
                        │
                        ▼
                  Success/Failure
                        │
                        ▼
                  Log activity
                        │
                        ▼
                  Update Dashboard


═══════════════════════════════════════════════════════════════════

This flow ensures:
✓ No message sent outside 24-hour window
✓ Every interaction tracked in Google Sheets
✓ Automated reminders sent at perfect times
✓ Sales messages delivered strategically
✓ Re-engagement for cold leads
✓ Complete customer journey automation

═══════════════════════════════════════════════════════════════════
```

## Key Decision Points

1. **Name received?** → Store and move to timeslot selection
2. **Timeslot chosen?** → Tree 1 (normal) vs Tree 2 (no response)
3. **Within 24hr window?** → Send vs Wait
4. **Thumbs up received?** → Adjust future reminders
5. **Attended session?** → Sales vs Re-invite flow
6. **Payment verified?** → Welcome as member

## Timing Reference

| Event | Timing | Notes |
|-------|--------|-------|
| Ask Name | Immediately | On first contact |
| Send Zoom | Immediately | After name received |
| Tree 2 Switch | T+2h | If no timeslot |
| Reminder 1 | T-12h | Before session |
| Reminder 2 | T-60min | Before session |
| Reminder 3 | T-10min | Before session |
| Sales S1 | T+5min | After session |
| Sales Shake-up | T+20min | After session |
| Sales S2 | T+2h | After session |
| Tree2 Sales 1 | T+22h | From registration |
| Tree2 Sales 2 | T+23.5h | From registration |
| Monday Check | Mon 10 AM | Weekly |
| Friday Re-invite | Fri 2 PM | Weekly |

---

**This visual guide helps understand the complete customer journey through the Inner Joy Studio automation system.**
