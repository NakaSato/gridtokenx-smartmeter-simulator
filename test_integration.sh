#!/usr/bin/env bash
# Simple Smart Meter Data Transfer Test
# Tests the complete flow: register user -> login -> submit reading

set -e

API_URL="http://localhost:8080"
TIMESTAMP=$(date +%s)
TEST_EMAIL="meter-test-${TIMESTAMP}@example.com"
TEST_PASSWORD="SecurePass123!"
TEST_USERNAME="meter_test_${TIMESTAMP}"

echo "=========================================="
echo "Smart Meter Data Transfer Test"
echo "=========================================="
echo ""

# Step 1: Register User
echo "1. Registering test user..."
REGISTER_RESPONSE=$(curl -s -X POST "${API_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_PASSWORD}\",
    \"username\": \"${TEST_USERNAME}\",
    \"first_name\": \"Test\",
    \"last_name\": \"Prosumer\"
  }")

echo "   Response: ${REGISTER_RESPONSE}"

# Check if registration was successful
if echo "$REGISTER_RESPONSE" | grep -q "error\|Error"; then
    echo "   ❌ Registration failed"
    exit 1
fi
echo "   ✅ User registered"
echo ""

# Step 2: Login
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${TEST_USERNAME}\",
    \"password\": \"${TEST_PASSWORD}\"
  }")

echo "   Response: ${LOGIN_RESPONSE}"

# Extract token (simple grep approach)
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "   ✅ Login successful"
    # Extract token using sed/awk
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "   Token: ${TOKEN:0:20}..."
else
    echo "   ❌ Login failed"
    exit 1
fi
echo ""

# Step 3: Set Wallet Address
echo "3. Setting wallet address..."
WALLET_ADDRESS="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
WALLET_RESPONSE=$(curl -s -X PUT "${API_URL}/api/user/wallet" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"wallet_address\": \"${WALLET_ADDRESS}\"
  }")

echo "   Response: ${WALLET_RESPONSE}"
if echo "$WALLET_RESPONSE" | grep -q "error\|Error"; then
    echo "   ⚠️  Wallet update may have failed (continuing anyway)"
else
    echo "   ✅ Wallet address set"
fi
echo ""

# Step 4: Submit Meter Reading
echo "4. Submitting meter reading..."
READING_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
READING_RESPONSE=$(curl -s -X POST "${API_URL}/api/meters/submit-reading" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"kwh_amount\": \"5.5\",
    \"reading_timestamp\": \"${READING_TIMESTAMP}\",
    \"meter_signature\": \"test-sig-${TIMESTAMP}\",
    \"meter_serial\": \"TEST-METER-001\"
  }")

echo "   Response: ${READING_RESPONSE}"

if echo "$READING_RESPONSE" | grep -q "error\|Error\|Forbidden"; then
    echo "   ❌ Meter reading submission failed"
    echo "   This might be because the user role is not 'prosumer'"
    exit 1
else
    echo "   ✅ Meter reading submitted successfully!"
fi
echo ""

# Step 5: Verify Reading
echo "5. Retrieving submitted readings..."
READINGS_RESPONSE=$(curl -s -X GET "${API_URL}/api/meters/my-readings" \
  -H "Authorization: Bearer ${TOKEN}")

echo "   Response: ${READINGS_RESPONSE}"
if echo "$READINGS_RESPONSE" | grep -q "data"; then
    echo "   ✅ Readings retrieved successfully"
else
    echo "   ⚠️  Could not retrieve readings"
fi
echo ""

echo "=========================================="
echo "✅ Test Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - User registered: ${TEST_EMAIL}"
echo "  - Wallet address: ${WALLET_ADDRESS}"
echo "  - Reading submitted: 5.5 kWh"
echo "  - Timestamp: ${READING_TIMESTAMP}"
echo ""
echo "Next: Check database for the reading"
echo "  docker exec -it gridtokenx-postgres psql -U gridtokenx -d gridtokenx \\"
echo "    -c \"SELECT * FROM meter_readings ORDER BY submitted_at DESC LIMIT 1;\""
