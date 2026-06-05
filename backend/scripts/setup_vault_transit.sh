#!/usr/bin/env bash
# Enable the HashiCorp Vault Transit engine + create the user-wallet key.
#
# The dev Vault container (docker-compose `vault`) ships with KV v2 at secret/ but
# NOT the Transit engine. IAM's verify-email -> create_wallet path calls
# transit/encrypt/<key> and 404s ("no handler for route transit/...") until this is
# run, which surfaces as HTTP 500 "Failed to create user wallet" on /auth/verify.
#
# Idempotent: re-running is safe (already-enabled / already-exists are ignored).
#
# Usage:
#   scripts/setup_vault_transit.sh
#   VAULT_ADDR=http://localhost:13001 VAULT_TOKEN=root \
#     VAULT_TRANSIT_KEY_NAME=gridtokenx-user-wallets scripts/setup_vault_transit.sh
set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://localhost:13001}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"
KEY_NAME="${VAULT_TRANSIT_KEY_NAME:-gridtokenx-user-wallets}"

echo "Vault: ${VAULT_ADDR}  transit key: ${KEY_NAME}"

# Enable transit (204 on success, 400 "path is already in use" if already enabled).
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "X-Vault-Token: ${VAULT_TOKEN}" -H "Content-Type: application/json" \
  -d '{"type":"transit"}' "${VAULT_ADDR}/v1/sys/mounts/transit" || true)
echo "enable transit engine: HTTP ${code}"

# Create the AES-256-GCM key (200 on success, 200/400 if it already exists).
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "X-Vault-Token: ${VAULT_TOKEN}" -H "Content-Type: application/json" \
  -d '{"type":"aes256-gcm96"}' "${VAULT_ADDR}/v1/transit/keys/${KEY_NAME}" || true)
echo "create transit key:    HTTP ${code}"

# Verify.
code=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Vault-Token: ${VAULT_TOKEN}" "${VAULT_ADDR}/v1/transit/keys/${KEY_NAME}")
if [ "${code}" = "200" ]; then
  echo "✅ Transit key ${KEY_NAME} ready"
else
  echo "❌ Transit key not reachable (HTTP ${code})"; exit 1
fi
