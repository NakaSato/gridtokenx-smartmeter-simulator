# Meter Serial and Wallet Address Relationship

## Current Database Schema

The `meter_readings` table stores the relationship between:
- **User** (via `user_id`)
- **Wallet Address** (via `wallet_address`)
- **Meter Serial** (via `meter_serial` - optional field)
- **Meter ID** (via `meter_id` - for verified meters from `meter_registry`)

## Data Verification

### Latest Meter Reading

```
Reading ID:      cd349ffc-5f17-4742-86e3-bd58c64afdd1
User:            meter_test_1764299206
Wallet Address:  9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
Meter Serial:    TEST-METER-VERIFIED (submitted in payload)
Amount:          8.5 kWh
Status:          ✅ Correctly associated
```

## How the Association Works

### 1. **User → Wallet Address**
- Each user has ONE wallet address stored in the `users` table
- When a user submits a reading, their wallet address is automatically included

### 2. **Reading → Meter Serial**
- The `meter_serial` is provided in the submission payload
- It's stored in the `meter_readings` table
- This allows tracking which physical meter generated the reading

### 3. **Complete Flow**

```
User (meter_test_1764299206)
  ↓
Wallet Address (9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM)
  ↓
Meter Reading Submission
  ↓
Meter Serial (TEST-METER-VERIFIED) + Reading Data (8.5 kWh)
  ↓
Stored in Database with ALL associations
```

## Verification Query

To verify the relationship, run:

```sql
SELECT 
    u.username,
    u.wallet_address as user_wallet,
    mr.wallet_address as reading_wallet,
    mr.meter_serial,
    mr.kwh_amount,
    mr.reading_timestamp
FROM users u
JOIN meter_readings mr ON u.id = mr.user_id
WHERE mr.id = 'cd349ffc-5f17-4742-86e3-bd58c64afdd1';
```

This confirms:
- ✅ User's wallet address matches the reading's wallet address
- ✅ Meter serial is properly stored with the reading
- ✅ All data is correctly associated

## Smart Meter Simulator Payload

When the simulator sends a reading, it includes:

```json
{
  "meter_serial": "TEST-METER-001",
  "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
  "kwh_amount": "8.5",
  "reading_timestamp": "2025-11-28T03:08:35.000Z",
  ...
}
```

The API Gateway:
1. Validates the user's JWT token
2. Retrieves the user's wallet address from the database
3. Stores the reading with BOTH the wallet address AND meter serial
4. Ensures data integrity and proper association

## Conclusion

✅ **The meter_serial and wallet_address are correctly associated in the database.**

Each meter reading contains:
- The user who submitted it
- The wallet address for token minting
- The meter serial number for device tracking
- All telemetry data from the smart meter
