"""Check Mehroz's data in Google Sheets"""
from services.google_sheets import GoogleSheetsService

sheets = GoogleSheetsService()
contact = sheets.get_contact('phone:+923273626526')

if contact:
    print('Mehroz in Google Sheets:')
    print(f"  Name: {contact.get('first_name')}")
    print(f"  Phone: {contact.get('whatsapp_number')}")
    print(f"  Timeslot: {contact.get('chosen_timeslot')}")
    print(f"  Session Time: {contact.get('session_datetime')}")
    print(f"  Reminders sent:")
    print(f"    12h: {contact.get('reminder_12h_sent')}")
    print(f"    60min: {contact.get('reminder_60min_sent')}")
    print(f"    10min: {contact.get('reminder_10min_sent')}")
else:
    print('Mehroz not found in Google Sheets')
