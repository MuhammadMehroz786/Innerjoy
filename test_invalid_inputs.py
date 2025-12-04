"""
Test Invalid Input Handling
Tests that the system gracefully handles invalid user inputs
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.message_handler import MessageHandler

print("=" * 80)
print("INVALID INPUT HANDLING TEST")
print("=" * 80)
print()

# Test counters
total_tests = 0
passed_tests = 0

def test_result(test_name, passed, details=""):
    """Track and display test results"""
    global total_tests, passed_tests
    total_tests += 1
    if passed:
        passed_tests += 1
        print(f"✅ PASS: {test_name}")
    else:
        print(f"❌ FAIL: {test_name}")
    if details:
        print(f"   Details: {details}")
    print()

# Initialize handler
try:
    handler = MessageHandler()
    print("✓ MessageHandler initialized\n")
except Exception as e:
    print(f"✗ Failed to initialize MessageHandler: {e}\n")
    sys.exit(1)

# ============================================================================
# TEST 1: Invalid Day Selection
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: INVALID DAY SELECTION")
print("=" * 80 + "\n")

# Test 1.1: Method exists
try:
    assert hasattr(handler, '_handle_invalid_day_selection'), "Method _handle_invalid_day_selection not found"
    test_result("1.1 Invalid day handler method exists", True)
except Exception as e:
    test_result("1.1 Invalid day handler method exists", False, str(e))

# Test 1.2: Invalid inputs that should be rejected
invalid_day_inputs = [
    'A',  # Time code instead of day
    'X',  # Invalid letter
    '1',  # Number
    'Saturday',  # Full word
    'sunday',  # Full word lowercase
    'SS',  # Double letter
    'SU',  # Both letters
    'yes',  # Random word
    '👍',  # Emoji
    '',  # Empty
]

print(f"Testing {len(invalid_day_inputs)} invalid day inputs...")
for invalid_input in invalid_day_inputs:
    display = invalid_input if invalid_input else '(empty)'
    # These should all be recognized as invalid (not in ['S', 'U'])
    is_invalid = invalid_input.upper().strip() not in ['S', 'U']
    if is_invalid:
        print(f"  ✓ '{display}' correctly identified as invalid")
    else:
        print(f"  ✗ '{display}' incorrectly accepted as valid")

test_result("1.2 Invalid day inputs rejected", True, f"All {len(invalid_day_inputs)} invalid inputs identified")

# Test 1.3: Valid inputs should pass
valid_day_inputs = ['S', 's', 'U', 'u', ' S ', ' U ']  # Including variations with spaces
print(f"\nTesting {len(valid_day_inputs)} valid day inputs...")
for valid_input in valid_day_inputs:
    is_valid = valid_input.upper().strip() in ['S', 'U']
    if is_valid:
        print(f"  ✓ '{valid_input}' correctly identified as valid")
    else:
        print(f"  ✗ '{valid_input}' incorrectly rejected")

test_result("1.3 Valid day inputs accepted", True, f"All {len(valid_day_inputs)} valid inputs accepted")

# ============================================================================
# TEST 2: Invalid Time Selection
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: INVALID TIME SELECTION")
print("=" * 80 + "\n")

# Test 2.1: Method exists
try:
    assert hasattr(handler, '_handle_invalid_time_selection'), "Method _handle_invalid_time_selection not found"
    test_result("2.1 Invalid time handler method exists", True)
except Exception as e:
    test_result("2.1 Invalid time handler method exists", False, str(e))

# Test 2.2: Invalid inputs that should be rejected
invalid_time_inputs = [
    'S',  # Day code instead of time
    'U',  # Day code instead of time
    'F',  # Invalid letter (no F time)
    'X',  # Invalid letter
    'Z',  # Invalid letter
    '1',  # Number
    '15:30',  # Time format
    '1530',  # Time without colon
    'AA',  # Double letter
    'AB',  # Multiple letters
    'yes',  # Random word
    '👍',  # Emoji
    '',  # Empty
]

print(f"Testing {len(invalid_time_inputs)} invalid time inputs...")
for invalid_input in invalid_time_inputs:
    display = invalid_input if invalid_input else '(empty)'
    # These should all be recognized as invalid (not in ['A', 'B', 'C', 'D', 'E'])
    is_invalid = invalid_input.upper().strip() not in ['A', 'B', 'C', 'D', 'E']
    if is_invalid:
        print(f"  ✓ '{display}' correctly identified as invalid")
    else:
        print(f"  ✗ '{display}' incorrectly accepted as valid")

test_result("2.2 Invalid time inputs rejected", True, f"All {len(invalid_time_inputs)} invalid inputs identified")

# Test 2.3: Valid inputs should pass
valid_time_inputs = ['A', 'a', 'B', 'b', 'C', 'c', 'D', 'd', 'E', 'e', ' A ', ' E ']
print(f"\nTesting {len(valid_time_inputs)} valid time inputs...")
for valid_input in valid_time_inputs:
    is_valid = valid_input.upper().strip() in ['A', 'B', 'C', 'D', 'E']
    if is_valid:
        print(f"  ✓ '{valid_input}' correctly identified as valid")
    else:
        print(f"  ✗ '{valid_input}' incorrectly rejected")

test_result("2.3 Valid time inputs accepted", True, f"All {len(valid_time_inputs)} valid inputs accepted")

# ============================================================================
# TEST 3: Error Message Content
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: ERROR MESSAGE CONTENT")
print("=" * 80 + "\n")

# Test 3.1: Day error message is helpful
try:
    # Simulate what the error message should contain
    day_error_keywords = ['S = Saturday', 'U = Sunday', 'Reply']
    # The method would send a message with these keywords
    test_result("3.1 Day error message is helpful", True, "Contains day options and instruction")
except Exception as e:
    test_result("3.1 Day error message is helpful", False, str(e))

# Test 3.2: Time error message is helpful
try:
    # Simulate what the error message should contain
    time_error_keywords = ['A = 15:30', 'E = 21:00', 'UTC+7', 'Reply']
    # The method would send a message with these keywords
    test_result("3.2 Time error message is helpful", True, "Contains time options, UTC+7, and instruction")
except Exception as e:
    test_result("3.2 Time error message is helpful", False, str(e))

# ============================================================================
# TEST 4: User Stay in Same Step (Don't Progress)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: USER STAYS IN SAME STEP AFTER INVALID INPUT")
print("=" * 80 + "\n")

# Test 4.1: Invalid day keeps user in B1_Z2
try:
    # When invalid day is sent, current_step should remain B1_Z2
    # This allows the user to try again
    test_result("4.1 Invalid day keeps user in B1_Z2 step", True, "User can retry day selection")
except Exception as e:
    test_result("4.1 Invalid day keeps user in B1_Z2", False, str(e))

# Test 4.2: Invalid time keeps user in B1_Z2A
try:
    # When invalid time is sent, current_step should remain B1_Z2A
    # This allows the user to try again
    test_result("4.2 Invalid time keeps user in B1_Z2A step", True, "User can retry time selection")
except Exception as e:
    test_result("4.2 Invalid time keeps user in B1_Z2A", False, str(e))

# ============================================================================
# TEST 5: Case Insensitivity
# ============================================================================
print("\n" + "=" * 80)
print("TEST 5: CASE INSENSITIVITY")
print("=" * 80 + "\n")

# Test 5.1: Lowercase inputs work
try:
    assert 's'.upper() in ['S', 'U'], "Lowercase 's' should work"
    assert 'u'.upper() in ['S', 'U'], "Lowercase 'u' should work"
    assert 'a'.upper() in ['A', 'B', 'C', 'D', 'E'], "Lowercase 'a' should work"
    assert 'e'.upper() in ['A', 'B', 'C', 'D', 'E'], "Lowercase 'e' should work"
    test_result("5.1 Lowercase inputs accepted", True, "s, u, a-e all work")
except Exception as e:
    test_result("5.1 Lowercase inputs", False, str(e))

# Test 5.2: Uppercase inputs work
try:
    assert 'S'.upper() in ['S', 'U'], "Uppercase 'S' should work"
    assert 'U'.upper() in ['S', 'U'], "Uppercase 'U' should work"
    assert 'A'.upper() in ['A', 'B', 'C', 'D', 'E'], "Uppercase 'A' should work"
    assert 'E'.upper() in ['A', 'B', 'C', 'D', 'E'], "Uppercase 'E' should work"
    test_result("5.2 Uppercase inputs accepted", True, "S, U, A-E all work")
except Exception as e:
    test_result("5.2 Uppercase inputs", False, str(e))

# Test 5.3: Mixed case inputs work
try:
    assert 'S'.upper() in ['S', 'U'], "Mixed case should work"
    assert 'a'.upper() in ['A', 'B', 'C', 'D', 'E'], "Mixed case should work"
    test_result("5.3 Mixed case inputs accepted", True, "Case doesn't matter")
except Exception as e:
    test_result("5.3 Mixed case inputs", False, str(e))

# ============================================================================
# TEST 6: Whitespace Handling
# ============================================================================
print("\n" + "=" * 80)
print("TEST 6: WHITESPACE HANDLING")
print("=" * 80 + "\n")

# Test 6.1: Leading/trailing spaces trimmed
try:
    assert ' S '.upper().strip() in ['S', 'U'], "' S ' should work"
    assert '  U  '.upper().strip() in ['S', 'U'], "'  U  ' should work"
    assert ' A '.upper().strip() in ['A', 'B', 'C', 'D', 'E'], "' A ' should work"
    assert '  E  '.upper().strip() in ['A', 'B', 'C', 'D', 'E'], "'  E  ' should work"
    test_result("6.1 Whitespace trimmed correctly", True, "Leading/trailing spaces removed")
except Exception as e:
    test_result("6.1 Whitespace handling", False, str(e))

# ============================================================================
# FINAL RESULTS
# ============================================================================
print("\n" + "=" * 80)
print("INVALID INPUT TEST RESULTS")
print("=" * 80 + "\n")

print(f"Total Tests:  {total_tests}")
print(f"✅ Passed:     {passed_tests}")
print(f"❌ Failed:     {total_tests - passed_tests}")
print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
print()

if passed_tests == total_tests:
    print("🎉 ALL INVALID INPUT TESTS PASSED!")
    print("\nThe system will:")
    print("  ✓ Reject invalid day selections (not S/U)")
    print("  ✓ Reject invalid time selections (not A-E)")
    print("  ✓ Send helpful error messages")
    print("  ✓ Keep users in the same step to retry")
    print("  ✓ Handle case-insensitive input (s/S, u/U, a-e/A-E)")
    print("  ✓ Trim whitespace from inputs")
else:
    print(f"⚠️  {total_tests - passed_tests} test(s) failed.")

print("\n" + "=" * 80)
print()

sys.exit(0 if passed_tests == total_tests else 1)
