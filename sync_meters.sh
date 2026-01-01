echo "Attemping to register sync_admin..."
TOKEN=$(curl -s -X POST http://localhost:4000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username":"sync_admin","email":"sync_admin@gridtokenx.com","password":"SuperSecureP@ssw0rd!2025","first_name":"Sync","last_name":"Admin"}' \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "Registration returned no token, trying login..."
  TOKEN=$(curl -s -X POST http://localhost:4000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"sync_admin","password":"SuperSecureP@ssw0rd!2025"}' \
    | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
fi

if [ -z "$TOKEN" ]; then
  echo "Failed to get token."
  exit 1
fi

echo "Got Token (len=${#TOKEN})"
export API_KEY="$TOKEN"
export API_GATEWAY_URL="http://localhost:4000"

echo "Running sync script..."
./.venv/bin/python scripts/sync_meters_to_gateway.py
