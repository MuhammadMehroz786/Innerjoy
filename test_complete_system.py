"""
Comprehensive Test Suite for Inner Joy WhatsApp Automation
Tests all major flows including new two-step timeslot selection
"""
import sys
import os
from datetime import datetime, timedelta
import pytz

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from services.message_handler import MessageHandler
from services.google_sheets import GoogleSheetsService

print("=" * 80)
print("INNER JOY AUTOMATION - COMPREHENSIVE TEST SUITE")
print("=" * 80)
print()

# Test counters
total_tests = 0
passed_tests = 0
failed_tests = 0

def test_result(test_name, passed, details=""):
    """Track and display test results"""
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    if passed:
        passed_tests += 1
        print(f"✅ PASS: {test_name}")
    else:
        failed_tests += 1
        print(f"❌ FAIL: {test_name}")
    if details:
        print(f"   Details: {details}")
    print()

# ============================================================================
# TEST 1: Configuration Tests
# ============================================================================
print("\n" + "=" * 80)
print("TEST CATEGORY 1: CONFIGURATION")
print("=" * 80 + "\n")

# Test 1.1: Timezone Configuration
try:
    assert Config.TIMEZONE == 'Asia/Bangkok', f"Expected Asia/Bangkok, got {Config.TIMEZONE}"
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    offset = now.strftime('%z')
    test_result("1.1 Timezone is UTC+7", offset == '+0700', f"Timezone offset: {offset}")
except Exception as e:
    test_result("1.1 Timezone is UTC+7", False, str(e))

# Test 1.2: New Timeslot Structure
try:
    expected_slots = ['SA', 'SB', 'SC', 'SD', 'SE', 'UA', 'UB', 'UC', 'UD', 'UE']
    actual_slots = list(Config.TIME_SLOTS.keys())
    assert actual_slots == expected_slots, f"Expected {expected_slots}, got {actual_slots}"
    test_result("1.2 All 10 timeslots exist (SA-SE, UA-UE)", True, f"Slots: {', '.join(actual_slots)}")
except Exception as e:
    test_result("1.2 All 10 timeslots exist", False, str(e))

# Test 1.3: Day Selection Mapping
try:
    assert 'S' in Config.DAY_SELECTION, "Day 'S' not in DAY_SELECTION"
    assert 'U' in Config.DAY_SELECTION, "Day 'U' not in DAY_SELECTION"
    assert Config.DAY_SELECTION['S'] == 'Saturday', "S should map to Saturday"
    assert Config.DAY_SELECTION['U'] == 'Sunday', "U should map to Sunday"
    test_result("1.3 Day selection mapping (S/U)", True, "S=Saturday, U=Sunday")
except Exception as e:
    test_result("1.3 Day selection mapping (S/U)", False, str(e))

# Test 1.4: Time Selection Mapping
try:
    from datetime import time
    assert len(Config.TIME_SELECTION) == 5, f"Expected 5 times, got {len(Config.TIME_SELECTION)}"
    assert Config.TIME_SELECTION['A'] == time(15, 30), "A should be 15:30"
    assert Config.TIME_SELECTION['B'] == time(19, 30), "B should be 19:30"
    assert Config.TIME_SELECTION['C'] == time(20, 0), "C should be 20:00"
    assert Config.TIME_SELECTION['D'] == time(20, 30), "D should be 20:30"
    assert Config.TIME_SELECTION['E'] == time(21, 0), "E should be 21:00"
    test_result("1.4 Time selection mapping (A-E)", True, "All 5 times correctly mapped")
except Exception as e:
    test_result("1.4 Time selection mapping (A-E)", False, str(e))

# Test 1.5: 24-Hour Window for All Contacts
try:
    fb_window = Config.get_window_duration('facebook_ads')
    web_window = Config.get_window_duration('website')
    unknown_window = Config.get_window_duration('unknown')

    assert fb_window == 24, f"Facebook Ads should be 24h, got {fb_window}h"
    assert web_window == 24, f"Website should be 24h, got {web_window}h"
    assert unknown_window == 24, f"Unknown should be 24h, got {unknown_window}h"
    test_result("1.5 All contacts use 24-hour window", True, "FB Ads, Website, Unknown all = 24h")
except Exception as e:
    test_result("1.5 All contacts use 24-hour window", False, str(e))

# Test 1.6: Window constant exists
try:
    assert hasattr(Config, 'WINDOW_24H_SECONDS'), "WINDOW_24H_SECONDS constant missing"
    assert Config.WINDOW_24H_SECONDS == 86400, f"Expected 86400 seconds, got {Config.WINDOW_24H_SECONDS}"
    test_result("1.6 WINDOW_24H_SECONDS constant", True, "86400 seconds (24 hours)")
except Exception as e:
    test_result("1.6 WINDOW_24H_SECONDS constant", False, str(e))

# ============================================================================
# TEST 2: Message Template Tests
# ============================================================================
print("\n" + "=" * 80)
print("TEST CATEGORY 2: MESSAGE TEMPLATES")
print("=" * 80 + "\n")

templates = Config.get_message_templates()

# Test 2.1: B1_Z1 exists and is unified
try:
    assert 'B1_Z1' in templates, "B1_Z1 template missing"
    assert 'B1_Z1_24H' not in templates or templates.get('B1_Z1_24H') is None, "B1_Z1_24H should not exist (unified to B1_Z1)"
    b1_z1 = templates['B1_Z1']
    assert 'Ineke' in b1_z1, "Should mention Ineke"
    assert 'name' in b1_z1.lower(), "Should ask for name"
    test_result("2.1 B1_Z1 template (unified for all contacts)", True, "Single template for all contacts")
except Exception as e:
    test_result("2.1 B1_Z1 template", False, str(e))

# Test 2.2: B1_Z2 asks for day (S/U)
try:
    assert 'B1_Z2' in templates, "B1_Z2 template missing"
    b1_z2 = templates['B1_Z2']
    assert 'S = Saturday' in b1_z2, "Should have S = Saturday"
    assert 'U = Sunday' in b1_z2, "Should have U = Sunday"
    assert 'Reply S or U' in b1_z2, "Should ask to reply S or U"
    assert 'UTC+7' in b1_z2, "Should mention UTC+7"
    test_result("2.2 B1_Z2 asks for day (S/U)", True, "Day selection present")
except Exception as e:
    test_result("2.2 B1_Z2 asks for day", False, str(e))

# Test 2.3: B1_Z2A asks for time (A-E) - NEW template
try:
    assert 'B1_Z2A' in templates, "B1_Z2A template missing"
    b1_z2a = templates['B1_Z2A']
    assert 'A = 15:30' in b1_z2a, "Should have A = 15:30"
    assert 'B = 19:30' in b1_z2a, "Should have B = 19:30"
    assert 'C = 20:00' in b1_z2a, "Should have C = 20:00"
    assert 'D = 20:30' in b1_z2a, "Should have D = 20:30"
    assert 'E = 21:00' in b1_z2a, "Should have E = 21:00"
    assert 'UTC+7' in b1_z2a, "Should mention UTC+7"
    test_result("2.3 B1_Z2A asks for time (A-E)", True, "All 5 time options present")
except Exception as e:
    test_result("2.3 B1_Z2A asks for time", False, str(e))

# Test 2.4: Reminder messages simplified (no thumbs-up)
try:
    r1 = templates['B1_R1']
    r2 = templates['B1_R2']

    assert '👍' not in r1, "R1 should not ask for thumbs up"
    assert 'thumbs' not in r1.lower(), "R1 should not mention thumbs up"
    assert '🕒' in r1, "R1 should have clock emoji"

    assert '👍' not in r2, "R2 should not ask for thumbs up"
    assert 'thumbs' not in r2.lower(), "R2 should not mention thumbs up"

    test_result("2.4 Reminders simplified (no thumbs-up requests)", True, "R1 and R2 don't ask for thumbs up")
except Exception as e:
    test_result("2.4 Reminders simplified", False, str(e))

# Test 2.5: Confirmation message includes UTC+7
try:
    b1_z2a1 = templates['B1_Z2A1']
    assert 'UTC+7' in b1_z2a1, "Confirmation should mention UTC+7"
    test_result("2.5 B1_Z2A1 confirmation includes UTC+7", True)
except Exception as e:
    test_result("2.5 B1_Z2A1 confirmation", False, str(e))

# Test 2.6: Member welcome messages show UTC+7
try:
    m1 = templates['B1_M1']
    assert '20:00 / 20:30 (UTC+7)' in m1, "Member welcome should show UTC+7"
    test_result("2.6 Member welcome shows UTC+7 times", True)
except Exception as e:
    test_result("2.6 Member welcome UTC+7", False, str(e))

# Test 2.7: Tree 2 messages use new format
try:
    b2_ra = templates['B2_RA']
    b2_rb = templates['B2_RB']

    # Check B2_RA
    assert 'S = Saturday' in b2_ra, "B2_RA should have day selection"
    assert 'U = Sunday' in b2_ra, "B2_RA should have day selection"
    assert 'A = 15:30' in b2_ra, "B2_RA should have time selection"
    assert 'E = 21:00' in b2_ra, "B2_RA should have all times"
    assert 'UTC+7' in b2_ra, "B2_RA should mention UTC+7"
    assert 'Reply S and then A–E' in b2_ra, "B2_RA should have instruction"

    # Check B2_RB
    assert 'S = Saturday' in b2_rb, "B2_RB should have day selection"
    assert 'UTC+7' in b2_rb, "B2_RB should mention UTC+7"

    test_result("2.7 Tree 2 messages use new two-step format", True, "B2_RA and B2_RB updated")
except Exception as e:
    test_result("2.7 Tree 2 messages", False, str(e))

# Test 2.8: NoSales/NoShow messages use new format
try:
    nosales = templates['B1_NOSALES']
    noshow = templates['B1_NOSHOW']

    for template, name in [(nosales, 'NoSales'), (noshow, 'NoShow')]:
        assert 'S = Saturday' in template, f"{name} should have day selection"
        assert 'U = Sunday' in template, f"{name} should have day selection"
        assert 'A = 15:30' in template, f"{name} should have time selection"
        assert 'E = 21:00' in template, f"{name} should have all times"
        assert 'UTC+7' in template, f"{name} should mention UTC+7"
        assert 'Reply S and then A–E' in template, f"{name} should have instruction"

    test_result("2.8 NoSales/NoShow messages use new format", True, "Both updated")
except Exception as e:
    test_result("2.8 NoSales/NoShow messages", False, str(e))

# ============================================================================
# TEST 3: Timeslot Display Tests
# ============================================================================
print("\n" + "=" * 80)
print("TEST CATEGORY 3: TIMESLOT DISPLAY")
print("=" * 80 + "\n")

# Test 3.1: Saturday timeslot displays
try:
    sa_display = Config.get_timeslot_display('SA')
    sb_display = Config.get_timeslot_display('SB')
    sc_display = Config.get_timeslot_display('SC')
    sd_display = Config.get_timeslot_display('SD')
    se_display = Config.get_timeslot_display('SE')

    assert sa_display == "Saturday 15:30 (UTC+7)", f"SA should be 'Saturday 15:30 (UTC+7)', got '{sa_display}'"
    assert sb_display == "Saturday 19:30 (UTC+7)", f"SB should be 'Saturday 19:30 (UTC+7)', got '{sb_display}'"
    assert sc_display == "Saturday 20:00 (UTC+7)", f"SC should be 'Saturday 20:00 (UTC+7)', got '{sc_display}'"
    assert sd_display == "Saturday 20:30 (UTC+7)", f"SD should be 'Saturday 20:30 (UTC+7)', got '{sd_display}'"
    assert se_display == "Saturday 21:00 (UTC+7)", f"SE should be 'Saturday 21:00 (UTC+7)', got '{se_display}'"

    test_result("3.1 Saturday timeslot displays (SA-SE)", True, "All 5 Saturday slots correct")
except Exception as e:
    test_result("3.1 Saturday timeslot displays", False, str(e))

# Test 3.2: Sunday timeslot displays
try:
    ua_display = Config.get_timeslot_display('UA')
    ub_display = Config.get_timeslot_display('UB')
    uc_display = Config.get_timeslot_display('UC')
    ud_display = Config.get_timeslot_display('UD')
    ue_display = Config.get_timeslot_display('UE')

    assert ua_display == "Sunday 15:30 (UTC+7)", f"UA should be 'Sunday 15:30 (UTC+7)', got '{ua_display}'"
    assert ub_display == "Sunday 19:30 (UTC+7)", f"UB should be 'Sunday 19:30 (UTC+7)', got '{ub_display}'"
    assert uc_display == "Sunday 20:00 (UTC+7)", f"UC should be 'Sunday 20:00 (UTC+7)', got '{uc_display}'"
    assert ud_display == "Sunday 20:30 (UTC+7)", f"UD should be 'Sunday 20:30 (UTC+7)', got '{ud_display}'"
    assert ue_display == "Sunday 21:00 (UTC+7)", f"UE should be 'Sunday 21:00 (UTC+7)', got '{ue_display}'"

    test_result("3.2 Sunday timeslot displays (UA-UE)", True, "All 5 Sunday slots correct")
except Exception as e:
    test_result("3.2 Sunday timeslot displays", False, str(e))

# Test 3.3: Invalid timeslot returns empty string
try:
    invalid = Config.get_timeslot_display('XYZ')
    assert invalid == '', f"Invalid timeslot should return empty string, got '{invalid}'"
    test_result("3.3 Invalid timeslot handling", True, "Returns empty string")
except Exception as e:
    test_result("3.3 Invalid timeslot handling", False, str(e))

# ============================================================================
# TEST 4: Message Handler Logic Tests
# ============================================================================
print("\n" + "=" * 80)
print("TEST CATEGORY 4: MESSAGE HANDLER LOGIC")
print("=" * 80 + "\n")

# Test 4.1: MessageHandler can be instantiated
try:
    handler = MessageHandler()
    assert handler is not None, "MessageHandler should instantiate"
    assert hasattr(handler, '_handle_day_selection'), "Should have _handle_day_selection method"
    assert hasattr(handler, '_handle_time_selection'), "Should have _handle_time_selection method"
    test_result("4.1 MessageHandler instantiation", True, "Handler created with new methods")
except Exception as e:
    test_result("4.1 MessageHandler instantiation", False, str(e))

# Test 4.2: Template formatting works
try:
    handler = MessageHandler()
    templates = handler.templates

    # Test B1_Z2 formatting
    b1_z2_formatted = templates['B1_Z2'].format(
        name="TestUser",
        zoom_link="https://zoom.us/test",
        zoom_download_link="https://zoom.us/download"
    )
    assert "TestUser" in b1_z2_formatted, "Name should be in formatted message"
    assert "https://zoom.us/test" in b1_z2_formatted, "Zoom link should be in formatted message"

    # Test B1_Z2A (no formatting needed)
    b1_z2a_formatted = templates['B1_Z2A']
    assert "A = 15:30" in b1_z2a_formatted, "Time options should be present"

    # Test B1_Z2A1 formatting
    b1_z2a1_formatted = templates['B1_Z2A1'].format(
        name="TestUser",
        timeslot="Saturday 15:30 (UTC+7)"
    )
    assert "TestUser" in b1_z2a1_formatted, "Name should be in confirmation"
    assert "Saturday 15:30 (UTC+7)" in b1_z2a1_formatted, "Timeslot should be in confirmation"

    test_result("4.2 Template formatting", True, "All templates format correctly")
except Exception as e:
    test_result("4.2 Template formatting", False, str(e))

# Test 4.3: First name extraction
try:
    handler = MessageHandler()

    # Test various name formats
    name1 = handler._extract_first_name("John")
    assert name1 == "John", f"Expected 'John', got '{name1}'"

    name2 = handler._extract_first_name("sarah smith")
    assert name2 == "Sarah", f"Expected 'Sarah', got '{name2}'"

    name3 = handler._extract_first_name("MIKE JONES")
    assert name3 == "Mike", f"Expected 'Mike', got '{name3}'"

    name4 = handler._extract_first_name("👍")  # Emoji only
    assert name4 == "there", f"Emoji should default to 'there', got '{name4}'"

    test_result("4.3 First name extraction", True, "Correctly extracts and capitalizes names")
except Exception as e:
    test_result("4.3 First name extraction", False, str(e))

# ============================================================================
# TEST 5: Session DateTime Calculation
# ============================================================================
print("\n" + "=" * 80)
print("TEST CATEGORY 5: SESSION DATETIME CALCULATION")
print("=" * 80 + "\n")

# Test 5.1: Calculate next Saturday session
try:
    handler = MessageHandler()
    tz = pytz.timezone(Config.TIMEZONE)

    # Calculate for Saturday 15:30
    session_sa = handler._calculate_next_session('SA')
    assert session_sa.weekday() == 5, f"SA should be Saturday (5), got {session_sa.weekday()}"
    assert session_sa.hour == 15 and session_sa.minute == 30, f"SA should be 15:30, got {session_sa.hour}:{session_sa.minute}"

    # Calculate for Saturday 21:00
    session_se = handler._calculate_next_session('SE')
    assert session_se.weekday() == 5, f"SE should be Saturday (5), got {session_se.weekday()}"
    assert session_se.hour == 21 and session_se.minute == 0, f"SE should be 21:00, got {session_se.hour}:{session_se.minute}"

    test_result("5.1 Saturday session calculation", True, f"Next Saturday sessions calculated correctly")
except Exception as e:
    test_result("5.1 Saturday session calculation", False, str(e))

# Test 5.2: Calculate next Sunday session
try:
    handler = MessageHandler()

    # Calculate for Sunday 15:30
    session_ua = handler._calculate_next_session('UA')
    assert session_ua.weekday() == 6, f"UA should be Sunday (6), got {session_ua.weekday()}"
    assert session_ua.hour == 15 and session_ua.minute == 30, f"UA should be 15:30, got {session_ua.hour}:{session_ua.minute}"

    # Calculate for Sunday 21:00
    session_ue = handler._calculate_next_session('UE')
    assert session_ue.weekday() == 6, f"UE should be Sunday (6), got {session_ue.weekday()}"
    assert session_ue.hour == 21 and session_ue.minute == 0, f"UE should be 21:00, got {session_ue.hour}:{session_ue.minute}"

    test_result("5.2 Sunday session calculation", True, f"Next Sunday sessions calculated correctly")
except Exception as e:
    test_result("5.2 Sunday session calculation", False, str(e))

# Test 5.3: Session is in the future
try:
    handler = MessageHandler()
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)

    session = handler._calculate_next_session('SA')
    assert session > now, f"Calculated session should be in the future. Now: {now}, Session: {session}"

    test_result("5.3 Calculated session is in future", True, f"Session is {(session - now).days} days ahead")
except Exception as e:
    test_result("5.3 Calculated session is in future", False, str(e))

# ============================================================================
# TEST 6: Integration Test - Simulated Flow
# ============================================================================
print("\n" + "=" * 80)
print("TEST CATEGORY 6: SIMULATED MESSAGE FLOW")
print("=" * 80 + "\n")

# Test 6.1: Simulate complete two-step selection
try:
    # Simulate the flow logic
    selected_day = 'S'  # User selects Saturday
    selected_time = 'B'  # User selects 19:30
    full_timeslot = selected_day + selected_time  # Should be 'SB'

    assert full_timeslot == 'SB', f"Combined timeslot should be 'SB', got '{full_timeslot}'"
    assert full_timeslot in Config.TIME_SLOTS, f"'{full_timeslot}' should be valid timeslot"

    display = Config.get_timeslot_display(full_timeslot)
    assert display == "Saturday 19:30 (UTC+7)", f"Display should be 'Saturday 19:30 (UTC+7)', got '{display}'"

    test_result("6.1 Two-step selection simulation", True, f"S + B = SB = {display}")
except Exception as e:
    test_result("6.1 Two-step selection simulation", False, str(e))

# Test 6.2: All day+time combinations are valid
try:
    days = ['S', 'U']
    times = ['A', 'B', 'C', 'D', 'E']

    valid_count = 0
    for day in days:
        for time_code in times:
            combo = day + time_code
            if combo in Config.TIME_SLOTS:
                valid_count += 1

    assert valid_count == 10, f"Expected 10 valid combinations, got {valid_count}"
    test_result("6.2 All day+time combinations valid", True, "10/10 combinations exist")
except Exception as e:
    test_result("6.2 All day+time combinations", False, str(e))

# Test 6.3: Invalid combinations don't exist
try:
    invalid_combos = ['AA', 'BB', 'SS', 'UU', 'XY', 'Z1']
    all_invalid = True
    for combo in invalid_combos:
        if combo in Config.TIME_SLOTS:
            all_invalid = False
            break

    assert all_invalid, "Invalid combinations should not exist in TIME_SLOTS"
    test_result("6.3 Invalid combinations rejected", True, "Invalid combos not in TIME_SLOTS")
except Exception as e:
    test_result("6.3 Invalid combinations", False, str(e))

# ============================================================================
# FINAL RESULTS
# ============================================================================
print("\n" + "=" * 80)
print("TEST RESULTS SUMMARY")
print("=" * 80 + "\n")

print(f"Total Tests:  {total_tests}")
print(f"✅ Passed:     {passed_tests}")
print(f"❌ Failed:     {failed_tests}")
print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
print()

if failed_tests == 0:
    print("🎉 ALL TESTS PASSED! System is ready for deployment.")
else:
    print(f"⚠️  {failed_tests} test(s) failed. Please review the errors above.")

print("\n" + "=" * 80)
print("END OF TEST SUITE")
print("=" * 80 + "\n")

# Exit with appropriate code
sys.exit(0 if failed_tests == 0 else 1)
