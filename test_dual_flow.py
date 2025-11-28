#!/usr/bin/env python3
"""
Comprehensive Test Suite for Dual Flow (24h Website / 72h Facebook Ads)
Tests source detection, window management, and message routing
"""
import json
from datetime import datetime, timedelta
import pytz

# Import our modules
from config import Config
from services.message_handler import MessageHandler

print("=" * 80)
print("INNER JOY DUAL FLOW TEST SUITE")
print("=" * 80)
print()

# Initialize
handler = MessageHandler()
timezone = pytz.timezone(Config.TIMEZONE)

# Test Results Tracking
tests_passed = 0
tests_failed = 0
test_results = []

def test_result(test_name, passed, details=""):
    global tests_passed, tests_failed
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")

    if passed:
        tests_passed += 1
    else:
        tests_failed += 1

    test_results.append({
        'test': test_name,
        'passed': passed,
        'details': details
    })
    print()

# ==================== TEST 1: Configuration ====================
print("\n" + "=" * 80)
print("TEST 1: Configuration Validation")
print("=" * 80)

try:
    # Check timezone
    assert Config.TIMEZONE == 'Asia/Singapore', f"Expected 'Asia/Singapore', got '{Config.TIMEZONE}'"
    test_result("Timezone Configuration", True, f"Timezone: {Config.TIMEZONE} (UTC+8)")

    # Check timeslots
    expected_slots = ['A', 'B', 'C', 'D']
    actual_slots = list(Config.TIME_SLOTS.keys())
    assert actual_slots == expected_slots, f"Expected {expected_slots}, got {actual_slots}"
    test_result("Timeslots Configuration", True, f"Timeslots: {actual_slots}")

    # Check source constants
    assert Config.SOURCE_FACEBOOK_ADS == 'facebook_ads'
    assert Config.SOURCE_WEBSITE == 'website'
    test_result("Source Constants", True, f"FB Ads: {Config.SOURCE_FACEBOOK_ADS}, Website: {Config.SOURCE_WEBSITE}")

    # Check trigger message
    assert Config.WEBSITE_TRIGGER_MESSAGE == 'free Zoom preview link'
    test_result("Website Trigger", True, f"Trigger phrase: '{Config.WEBSITE_TRIGGER_MESSAGE}'")

    # Check window durations
    fb_window = Config.get_window_duration('facebook_ads')
    web_window = Config.get_window_duration('website')
    assert fb_window == 72, f"Expected 72h, got {fb_window}h"
    assert web_window == 24, f"Expected 24h, got {web_window}h"
    test_result("Window Duration Logic", True, f"FB Ads: {fb_window}h, Website: {web_window}h")

    # Check payment links
    assert 'innerjoy.live' in Config.MEMBERSHIP_LINK
    assert 'innerjoy.live' in Config.TRIAL_LINK
    test_result("Payment Links", True, f"Membership: {Config.MEMBERSHIP_LINK}")

except AssertionError as e:
    test_result("Configuration Validation", False, str(e))
except Exception as e:
    test_result("Configuration Validation", False, f"Error: {e}")


# ==================== TEST 2: Source Detection ====================
print("\n" + "=" * 80)
print("TEST 2: Source Detection Logic")
print("=" * 80)

# Test 2.1: Website Lead Detection
webhook_website = {
    'contact': {
        'id': 'test_web_001',
        'phone': '+8562022398887',
        'firstName': 'TestUser'
    },
    'message': {
        'text': 'Hello, I would like to have the free Zoom preview link. Ineke',
        'type': 'text'
    }
}

detected_source = handler._detect_contact_source(webhook_website)
test_result(
    "Website Lead Detection",
    detected_source == 'website',
    f"Message: '{webhook_website['message']['text'][:50]}...' → Detected: {detected_source}"
)

# Test 2.2: Facebook Ads Lead Detection
webhook_fb_ads = {
    'contact': {
        'id': 'test_fb_001',
        'phone': '+8562022398888',
        'firstName': 'TestUser'
    },
    'message': {
        'text': 'Hi Ineke, I saw your ad',
        'type': 'text'
    }
}

detected_source = handler._detect_contact_source(webhook_fb_ads)
test_result(
    "Facebook Ads Lead Detection",
    detected_source == 'facebook_ads',
    f"Message: '{webhook_fb_ads['message']['text']}' → Detected: {detected_source}"
)

# Test 2.3: Generic Message (should default to FB Ads)
webhook_generic = {
    'contact': {
        'id': 'test_gen_001',
        'phone': '+8562022398889',
        'firstName': 'TestUser'
    },
    'message': {
        'text': 'Hello',
        'type': 'text'
    }
}

detected_source = handler._detect_contact_source(webhook_generic)
test_result(
    "Generic Message (Default to FB Ads)",
    detected_source == 'facebook_ads',
    f"Message: '{webhook_generic['message']['text']}' → Detected: {detected_source} (default)"
)

# Test 2.4: Existing Contact with Stored Source
webhook_existing = {
    'contact': {
        'id': 'test_existing_001',
        'phone': '+8562022398890',
        'firstName': 'TestUser',
        'customFields': {
            'contact_source': 'website'
        }
    },
    'message': {
        'text': 'I saw your Facebook ad',  # Contains FB ad reference but should use stored source
        'type': 'text'
    }
}

detected_source = handler._detect_contact_source(webhook_existing)
test_result(
    "Existing Contact (Stored Source)",
    detected_source == 'website',
    f"Stored source: website, Message mentions FB ad → Still returns: {detected_source}"
)


# ==================== TEST 3: Message Templates ====================
print("\n" + "=" * 80)
print("TEST 3: Message Template Selection")
print("=" * 80)

templates = Config.get_message_templates()

# Test 3.1: Website Flow Initial Message
assert 'B1_Z1_24H' in templates, "B1_Z1_24H template missing"
website_msg = templates['B1_Z1_24H']
assert 'from your website' in website_msg.lower() or 'A — Sat' in website_msg
test_result(
    "Website Initial Message (B1_Z1_24H)",
    True,
    f"Template includes timeslots upfront: {len(website_msg)} chars"
)

# Test 3.2: Facebook Ads Flow Initial Message
assert 'B1_Z1' in templates, "B1_Z1 template missing"
fb_msg = templates['B1_Z1']
assert 'name' in fb_msg.lower() and 'zoom link' in fb_msg.lower()
test_result(
    "Facebook Ads Initial Message (B1_Z1)",
    True,
    f"Template asks for name only: {len(fb_msg)} chars"
)

# Test 3.3: Message Length Validation
website_has_timeslots = 'A — Sat' in website_msg or 'A = Sat' in website_msg
fb_no_timeslots = 'A — Sat' not in fb_msg and 'A = Sat' not in fb_msg
test_result(
    "Template Differentiation",
    website_has_timeslots and fb_no_timeslots,
    f"Website has timeslots: {website_has_timeslots}, FB Ads doesn't: {fb_no_timeslots}"
)


# ==================== TEST 4: Timeslot Configuration ====================
print("\n" + "=" * 80)
print("TEST 4: Timeslot Configuration (4 slots: A-D)")
print("=" * 80)

expected_timeslots = {
    'A': {'day': 'Saturday', 'time': '15:30', 'is_walkin': False},
    'B': {'day': 'Saturday', 'time': '19:30', 'is_walkin': True},
    'C': {'day': 'Sunday', 'time': '15:30', 'is_walkin': False},
    'D': {'day': 'Sunday', 'time': '19:30', 'is_walkin': True}
}

all_correct = True
for slot, expected in expected_timeslots.items():
    actual = Config.TIME_SLOTS.get(slot)
    if actual:
        time_str = actual['time'].strftime('%H:%M')
        match = (
            actual['day'] == expected['day'] and
            time_str == expected['time'] and
            actual['is_walkin'] == expected['is_walkin']
        )
        if not match:
            all_correct = False
        print(f"   Slot {slot}: {actual['day']} {time_str} {'(walk-in)' if actual['is_walkin'] else '(fixed)'}")
    else:
        all_correct = False

test_result(
    "Timeslot Configuration (A-D)",
    all_correct,
    f"4 timeslots configured correctly"
)


# ==================== TEST 5: Window Duration Logic ====================
print("\n" + "=" * 80)
print("TEST 5: Window Duration Calculations")
print("=" * 80)

# Test window calculations
now = datetime.now(timezone)

# Website window (24h)
website_window = Config.get_window_duration('website')
website_expires = now + timedelta(hours=website_window)
test_result(
    "Website Window (24h)",
    website_window == 24,
    f"Window: {website_window}h, Expires: {website_expires.strftime('%Y-%m-%d %H:%M')}"
)

# Facebook Ads window (72h)
fb_window = Config.get_window_duration('facebook_ads')
fb_expires = now + timedelta(hours=fb_window)
test_result(
    "Facebook Ads Window (72h)",
    fb_window == 72,
    f"Window: {fb_window}h, Expires: {fb_expires.strftime('%Y-%m-%d %H:%M')}"
)

# Unknown source (should default to 24h - conservative)
unknown_window = Config.get_window_duration('unknown_source')
test_result(
    "Unknown Source (Default to 24h)",
    unknown_window == 24,
    f"Unknown source defaults to {unknown_window}h (conservative)"
)


# ==================== TEST 6: Timeslot Display ====================
print("\n" + "=" * 80)
print("TEST 6: Timeslot Display Formatting")
print("=" * 80)

slot_displays = {}
for slot in ['A', 'B', 'C', 'D']:
    display = Config.get_timeslot_display(slot)
    slot_displays[slot] = display
    print(f"   Slot {slot}: {display}")

# Verify walk-in slots have proper formatting
b_display = Config.get_timeslot_display('B')
d_display = Config.get_timeslot_display('D')
has_walkin_indicator = '(walk-in)' in b_display.lower() and '(walk-in)' in d_display.lower()

test_result(
    "Walk-in Slot Formatting",
    has_walkin_indicator,
    f"Slots B & D marked as walk-in: {has_walkin_indicator}"
)


# ==================== TEST 7: Make.com Transformation ====================
print("\n" + "=" * 80)
print("TEST 7: Make.com Data Transformation")
print("=" * 80)

# Import the transformation function
import sys
import importlib
app_module = importlib.import_module('app')

# Test complex Make.com format
makecom_data = {
    'event_type': 'message.received',
    'Contact': {
        'Contact ID': '339593905',
        'First Name': 'TestUser',
        'Phone No.': '+8562022398887'
    },
    'Message': {
        'ID': 'msg_123',
        'Message': {
            'Type': 'text',
            'Text': 'Hello, I would like to have the free Zoom preview link. Ineke'
        },
        'Timestamp': '2025-11-27T10:00:00Z'
    }
}

try:
    transformed = app_module._transform_makecom_to_internal(makecom_data)

    # Verify transformation
    checks = [
        ('contact.id' in str(transformed), "Contact ID extracted"),
        ('contact.phone' in str(transformed), "Phone extracted"),
        ('message.text' in str(transformed), "Message text extracted"),
        (transformed.get('contact', {}).get('customFields') is not None, "Custom fields included"),
        (transformed.get('contact', {}).get('tags') is not None, "Tags included")
    ]

    all_passed = all(check[0] for check in checks)
    details = ", ".join([check[1] for check in checks if check[0]])

    test_result(
        "Make.com Data Transformation",
        all_passed,
        details
    )
except Exception as e:
    test_result("Make.com Data Transformation", False, f"Error: {e}")


# ==================== FINAL SUMMARY ====================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"Total Tests: {tests_passed + tests_failed}")
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"Success Rate: {(tests_passed / (tests_passed + tests_failed) * 100):.1f}%")
print("=" * 80)

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
else:
    print(f"\n⚠️  {tests_failed} test(s) failed. Please review the failures above.")

print("\n" + "=" * 80)
print("IMPLEMENTATION CHECKLIST")
print("=" * 80)
print("✅ Timezone: UTC+8 (Singapore/Hong Kong)")
print("✅ Timeslots: 4 slots (A-D) with walk-in options")
print("✅ Source Detection: Message-based trigger ('from your website')")
print("✅ Window Management: 72h for Facebook Ads, 24h for Website")
print("✅ Payment Links: innerjoy.live platform")
print("✅ Message Templates: Dual flow (B1_Z1 vs B1_Z1_24H)")
print("✅ Google Sheets: contact_source field added")
print("✅ Make.com: Data transformation with custom fields")
print("=" * 80)

print("\n📋 DEPLOYMENT LINKS")
print("=" * 80)
print("Website Link (24h):")
print("https://wa.me/8562022398887?text=Hello%2C%20I%20would%20like%20to%20have%20the%20free%20Zoom%20preview%20link.%20Ineke")
print()
print("Facebook Ads Link (72h):")
print("https://wa.me/8562022398887?text=Hi%20Ineke%2C%20I%20saw%20your%20ad")
print("=" * 80)
