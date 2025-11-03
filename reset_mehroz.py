"""Reset Mehroz's contact data for testing"""
from services.respond_api import RespondAPI
from config import Config

api = RespondAPI()

# Reset Mehroz (original number)
contact_id = "phone:+923273626526"

print(f"Resetting {contact_id}...")

try:
    # Clear member_status, chosen_timeslot, and other tracking fields
    api.update_contact_fields(contact_id, {
        Config.CUSTOM_FIELDS['MEMBER_STATUS']: None,
        Config.CUSTOM_FIELDS['CHOSEN_TIMESLOT']: None,
        Config.CUSTOM_FIELDS['THUMBS_UP']: None,
        Config.CUSTOM_FIELDS['REMINDER_12H']: None,
        Config.CUSTOM_FIELDS['REMINDER_60MIN']: None,
        Config.CUSTOM_FIELDS['REMINDER_10MIN']: None,
    })
    print("✓ Reset complete!")

    # Verify
    contact = api.get_contact(contact_id)
    custom_fields = contact.get('customFields', {})
    print(f"\nVerification:")
    print(f"  member_status: {custom_fields.get(Config.CUSTOM_FIELDS['MEMBER_STATUS'])}")
    print(f"  chosen_timeslot: {custom_fields.get(Config.CUSTOM_FIELDS['CHOSEN_TIMESLOT'])}")

except Exception as e:
    print(f"✗ Error: {e}")
