#!/bin/bash

# Test Conversation Flow for Inner Joy Studio Automation
# This simulates a complete customer journey

BASE_URL="http://localhost:9000"
CONTACT_ID="test_contact_$(date +%s)"

echo "================================================"
echo "Testing Inner Joy Studio WhatsApp Automation"
echo "================================================"
echo ""
echo "Contact ID: $CONTACT_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: New contact arrives (no name yet)${NC}"
echo "Sending first message..."
curl -s -X POST $BASE_URL/webhook/respond \
  -H "Content-Type: application/json" \
  -d "{
    \"event\": \"message.received\",
    \"contact\": {\"id\": \"$CONTACT_ID\"},
    \"message\": {\"text\": \"Hi\"}
  }" | python3 -m json.tool
echo ""
sleep 2

echo -e "${BLUE}Step 2: Customer provides name${NC}"
echo "Sending name: John..."
curl -s -X POST $BASE_URL/webhook/respond \
  -H "Content-Type: application/json" \
  -d "{
    \"event\": \"message.received\",
    \"contact\": {\"id\": \"$CONTACT_ID\"},
    \"message\": {\"text\": \"John\"}
  }" | python3 -m json.tool
echo ""
sleep 2

echo -e "${BLUE}Step 3: Customer chooses timeslot${NC}"
echo "Sending timeslot choice: A..."
curl -s -X POST $BASE_URL/webhook/respond \
  -H "Content-Type: application/json" \
  -d "{
    \"event\": \"message.received\",
    \"contact\": {\"id\": \"$CONTACT_ID\"},
    \"message\": {\"text\": \"A\"}
  }" | python3 -m json.tool
echo ""
sleep 2

echo -e "${BLUE}Step 4: Customer sends thumbs up${NC}"
echo "Sending confirmation..."
curl -s -X POST $BASE_URL/webhook/respond \
  -H "Content-Type: application/json" \
  -d "{
    \"event\": \"message.received\",
    \"contact\": {\"id\": \"$CONTACT_ID\"},
    \"message\": {\"text\": \"👍\"}
  }" | python3 -m json.tool
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Test completed!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Check the logs to see the system responses:"
echo "tail -f /tmp/innerjoy.log"
echo ""
echo "Or check Respond.io to see messages sent to contact: $CONTACT_ID"
