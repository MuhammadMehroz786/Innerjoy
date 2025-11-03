"""Test the reminder scheduling system"""
from datetime import datetime, timedelta
import pytz
from services.google_sheets import GoogleSheetsService
from services.message_handler import MessageHandler
from config import Config

# Initialize services
sheets = GoogleSheetsService()
handler = MessageHandler()
tz = pytz.timezone(Config.TIMEZONE)

contact_id = 'phone:+923273626526'

print("=" * 60)
print("REMINDER SYSTEM TEST")
print("=" * 60)

# Get current contact data
contact = sheets.get_contact(contact_id)
if not contact:
    print(f"❌ Contact {contact_id} not found in Google Sheets")
    exit(1)

print(f"\n✓ Contact found: {contact.get('first_name')}")
print(f"  Current timeslot: {contact.get('chosen_timeslot')}")
print(f"  Current session: {contact.get('session_datetime')}")

# Test 1: 12-hour reminder (set session to be in 11 hours)
print("\n" + "=" * 60)
print("TEST 1: 12-Hour Reminder")
print("=" * 60)

test_session = datetime.now(tz) + timedelta(hours=11, minutes=30)
print(f"Setting test session to: {test_session.isoformat()}")

# Update Google Sheets with test session time
sheets.update_contact(contact_id, {
    'session_datetime': test_session.isoformat(),
    'reminder_12h_sent': 'No',
    'reminder_60min_sent': 'No',
    'reminder_10min_sent': 'No'
})

print("✓ Updated session time in Google Sheets")
print("\nManually triggering 12-hour reminder...")

try:
    result = handler.send_reminder(contact_id, '12h')
    if result:
        print("✅ 12-hour reminder sent successfully!")
    else:
        print("❌ 12-hour reminder failed")
except Exception as e:
    print(f"❌ Error sending reminder: {e}")

# Check if it was marked as sent
contact = sheets.get_contact(contact_id)
print(f"   Reminder status in Sheets: {contact.get('reminder_12h_sent')}")

# Test 2: 60-minute reminder
print("\n" + "=" * 60)
print("TEST 2: 60-Minute Reminder")
print("=" * 60)

test_session = datetime.now(tz) + timedelta(minutes=50)
print(f"Setting test session to: {test_session.isoformat()}")

sheets.update_contact(contact_id, {
    'session_datetime': test_session.isoformat(),
    'reminder_60min_sent': 'No'
})

print("✓ Updated session time in Google Sheets")
print("\nManually triggering 60-minute reminder...")

try:
    result = handler.send_reminder(contact_id, '60min')
    if result:
        print("✅ 60-minute reminder sent successfully!")
    else:
        print("❌ 60-minute reminder failed")
except Exception as e:
    print(f"❌ Error sending reminder: {e}")

contact = sheets.get_contact(contact_id)
print(f"   Reminder status in Sheets: {contact.get('reminder_60min_sent')}")

# Test 3: 10-minute reminder
print("\n" + "=" * 60)
print("TEST 3: 10-Minute Reminder")
print("=" * 60)

test_session = datetime.now(tz) + timedelta(minutes=8)
print(f"Setting test session to: {test_session.isoformat()}")

sheets.update_contact(contact_id, {
    'session_datetime': test_session.isoformat(),
    'reminder_10min_sent': 'No'
})

print("✓ Updated session time in Google Sheets")
print("\nManually triggering 10-minute reminder...")

try:
    result = handler.send_reminder(contact_id, '10min')
    if result:
        print("✅ 10-minute reminder sent successfully!")
    else:
        print("❌ 10-minute reminder failed")
except Exception as e:
    print(f"❌ Error sending reminder: {e}")

contact = sheets.get_contact(contact_id)
print(f"   Reminder status in Sheets: {contact.get('reminder_10min_sent')}")

# Restore original session time
print("\n" + "=" * 60)
print("CLEANUP")
print("=" * 60)

original_session = datetime(2025, 11, 9, 20, 30, 0, tzinfo=tz)
sheets.update_contact(contact_id, {
    'session_datetime': original_session.isoformat(),
    'reminder_12h_sent': 'No',
    'reminder_60min_sent': 'No',
    'reminder_10min_sent': 'No'
})

print(f"✓ Restored original session time: {original_session.isoformat()}")
print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nCheck Mehroz's WhatsApp for the 3 test reminder messages!")
