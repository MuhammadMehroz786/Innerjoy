"""Check real Mehroz's contact data"""
from services.respond_api import RespondAPI
import json

api = RespondAPI()

# This is the original Mehroz
contact_id = "phone:+923273626526"
contact = api.get_contact(contact_id)

print("Mehroz's contact data:")
print(f"  firstName: {contact.get('firstName')}")
print(f"  phone: {contact.get('phone')}")

print(f"\nRaw custom_fields array:")
print(json.dumps(contact.get('custom_fields', []), indent=2))

custom_fields = contact.get('customFields', {})
print(f"\nConverted customFields dict:")
print(f"  name_requested: {custom_fields.get('name_requested')}")
print(f"  chosen_timeslot: {custom_fields.get('chosen_timeslot')}")
