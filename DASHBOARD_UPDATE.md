# Dashboard Update - Lead Source Tracking

## ✅ Changes Implemented

### 1. **Dashboard UI** (`templates/dashboard.html`)

#### Added: Lead Sources Section
A new section displays the breakdown of leads by source:

- **📱 Facebook Ads** (Blue card)
  - Shows count of Facebook Ads leads
  - Label: "72-hour window"

- **🌐 Website** (Green card)
  - Shows count of Website leads
  - Label: "24-hour window"

#### Updated: Timeslot Labels
Fixed timeslot labels to match new 4-slot configuration (A-D):

| Slot | Label |
|------|-------|
| A | Sat 15:30 |
| B | Sat 19:30-21:30 (walk-in) |
| C | Sun 15:30 |
| D | Sun 19:30-21:30 (walk-in) |

**Removed**: Slot E (no longer exists in new configuration)

#### Updated: JavaScript Stats Fetching
The `refreshStats()` function now:
- Fetches `source_distribution` from `/api/stats`
- Updates Facebook Ads lead count (`#facebook-leads`)
- Updates Website lead count (`#website-leads`)
- Handles 4 timeslots (A-D) instead of 5 (A-E)

---

### 2. **CSS Styling** (`static/style.css`)

#### Added: Lead Source Card Colors

```css
/* Lead Source Cards */
.source-facebook {
    background: linear-gradient(135deg, #4267B2 0%, #3b5998 100%);
}

.source-website {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.stat-label {
    font-size: 0.85em;
    margin-top: 10px;
    opacity: 0.85;
}
```

**Visual Design**:
- Facebook Ads: Facebook blue gradient
- Website: Green/teal gradient
- Both cards show clear visual distinction

---

### 3. **Backend API** (`app.py`)

**Already Implemented** ✅ (from previous dual-flow update)

The `/api/stats` endpoint already returns:

```json
{
  "total_contacts": 150,
  "with_timeslot": 120,
  "without_timeslot": 30,
  "members": 25,
  "source_distribution": {
    "facebook_ads": 120,
    "website": 30
  },
  "timeslot_distribution": {
    "A": 35,
    "B": 40,
    "C": 25,
    "D": 20
  },
  "timestamp": "2025-11-27T12:00:00"
}
```

---

## 🎨 Dashboard Preview

### Layout Order
1. **Stats Cards** (Row 1)
   - Total Contacts
   - With Timeslot
   - Without Timeslot
   - Members

2. **Lead Sources** (Row 2) ⭐ NEW
   - 📱 Facebook Ads (72h window)
   - 🌐 Website (24h window)

3. **Timeslot Distribution** (Updated to 4 slots)
   - A, B, C, D

4. **Quick Actions**
   - Refresh Stats
   - Trigger Reminder Check
   - View All Contacts
   - Send Test Message

5. **Recent Contacts Table**

6. **Activity Log**

---

## 📊 Data Flow

### Source Detection (Message-Based Trigger)
```python
# Priority 1: Check stored source (existing contacts)
if contact_source_exists:
    return stored_source

# Priority 2: Check message text trigger (Website)
if 'free Zoom preview link' in message.text:
    return 'website'  # 24h window

# Priority 3: Default to Facebook Ads
return 'facebook_ads'  # 72h window
```

### Google Sheets Storage
- Field: `contact_source` (Column D)
- Values: `"facebook_ads"` or `"website"`
- Locked on first message (never changes)

### Dashboard Display
- Fetches stats every 30 seconds (auto-refresh)
- Manual refresh via "Refresh Stats" button
- Real-time updates when contacts are added

---

## 🚀 How to Use

### Access Dashboard
```
http://localhost:5000/
```

### View Stats
The dashboard automatically displays:
- Total leads by source
- Conversion rates
- Timeslot preferences
- Member status

### Monitor Lead Sources
- **Facebook Ads** card shows all leads without "free Zoom preview link" trigger
- **Website** card shows all leads with "free Zoom preview link" trigger
- Both update in real-time as new contacts arrive

---

## 🔍 Future Enhancement Note

**Recommended Upgrade**: Use WhatsApp referral object for more accurate tracking

When ready, you can implement the referral-based detection:

```python
# Check for referral object in webhook
referral = message.context.referral
if referral and referral.source_type == 'ad':
    return 'facebook_ads'  # More accurate!
```

**Benefits**:
- No reliance on message text
- Track specific ad campaigns
- Get ad creative metadata
- More reliable attribution

**Requirements**:
- Check if Respond.io passes `context.referral` through
- Verify Make.com transformation includes referral object
- Enable attribution in WhatsApp Business settings

---

## ✅ Testing Checklist

- [x] Dashboard loads successfully
- [x] Lead source cards display correctly
- [x] Facebook Ads count shows blue card
- [x] Website count shows green card
- [x] Timeslot distribution shows 4 slots (A-D)
- [x] Auto-refresh works every 30 seconds
- [x] Manual refresh button works
- [x] Stats API returns source_distribution
- [x] CSS styling applied correctly

---

**Status**: ✅ Complete and Ready for Use

**Date**: November 28, 2025

**Trigger Phrase**: `"free Zoom preview link"`
