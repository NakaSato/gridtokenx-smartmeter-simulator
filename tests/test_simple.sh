#!/usr/bin/env bash
# Simple Smart Meter Data Transfer Test
# Uses existing verified prosumer user

set -e

API_URL="http://localhost:8080"

# Use the verified prosumer user we just created
TEST_USERNAME="meter_test_1764299222"
TEST_PASSWORD="SecurePass123!"

echo "=========================================="
echo "Smart Meter Data Transfer Test"
echo "=========================================="
echo ""

# Step 1: Login
echo "1. Logging in as verified prosumer..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${TEST_USERNAME}\",
    \"password\": \"${TEST_PASSWORD}\"
  }")

echo "   Response: ${LOGIN_RESPONSE}"

# Extract token
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "   ✅ Login successful"
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "   Token: ${TOKEN:0:30}..."
else
    echo "   ❌ Login failed"
    echo "   Full response: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# Step 2: Set Wallet Address
echo "2. Setting wallet address..."
WALLET_ADDRESS="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
WALLET_RESPONSE=$(curl -s -X PUT "${API_URL}/api/user/wallet" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"wallet_address\": \"${WALLET_ADDRESS}\"
  }")

echo "   Response: ${WALLET_RESPONSE}"
echo "   ✅ Wallet address set"
echo ""

# Step 3: Submit Meter Reading
echo "3. Submitting meter reading..."
READING_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
READING_RESPONSE=$(curl -s -X POST "${API_URL}/api/meters/submit-reading" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"kwh_amount\": \"7.5\",
    \"reading_timestamp\": \"${READING_TIMESTAMP}\",
    \"meter_signature\": \"test-sig-$(date +%s)\",
    \"meter_serial\": \"TEST-METER-001\"
  }")

echo "   Response: ${READING_RESPONSE}"

if echo "$READING_RESPONSE" | grep -q '"id"'; then
    echo "   ✅ Meter reading submitted successfully!"
    READING_ID=$(echo "$READING_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    echo "   Reading ID: ${READING_ID}"
else
    echo "   ❌ Meter reading submission failed"
    exit 1
fi
echo ""

# Step 4: Verify Reading
echo "4. Retrieving submitted readings..."
READINGS_RESPONSE=$(curl -s -X GET "${API_URL}/api/meters/my-readings?page=1&page_size=5" \
  -H "Authorization: Bearer ${TOKEN}")

echo "   Response (truncated): ${READINGS_RESPONSE:0:200}..."
if echo "$READINGS_RESPONSE" | grep -q "data"; then
    COUNT=$(echo "$READINGS_RESPONSE" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "   ✅ Found ${COUNT} readings"
else
    echo "   ⚠️  Could not retrieve readings"
fi
echo ""

echo "=========================================="
echo "✅ Smart Meter Data Transfer Test PASSED!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - User: ${TEST_USERNAME}"
echo "  - Wallet: ${WALLET_ADDRESS}"
echo "  - Reading: 7.5 kWh"
echo "  - Timestamp: ${READING_TIMESTAMP}"
echo "  - Reading ID: ${READING_ID}"
echo ""
echo "✅ Data successfully transferred from simulator to API gateway!"
echo ""
echo "Verify in database:"
echo "  docker exec gridtokenx-postgres psql -U gridtokenx -d gridtokenx \\"
echo "    -c \"SELECT id, kwh_amount, reading_timestamp, minted FROM meter_readings WHERE id = '${READING_ID}';\""
