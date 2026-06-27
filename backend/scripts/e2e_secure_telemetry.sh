#!/usr/bin/env bash
# End-to-end assertions for the SECURE smart-meter telemetry profile against a
# running stack (`just secure-up`): mTLS, ingest lockdown, per-meter AES-256-GCM
# payload encryption, Vault-KEK key rotation, and at-rest stream encryption.
#
# Run against the live compose stack:
#   bash scripts/e2e_secure_telemetry.sh
#
# Exits non-zero if any check fails. Read-only except for the key-rotation check
# (which calls the sim's rotate endpoint — additive, safe).
set -uo pipefail

# --- config (host-side) ------------------------------------------------------
BRIDGE_URL="${BRIDGE_URL:-https://localhost:4030}"
SIM_URL="${SIM_URL:-http://localhost:12010}"
REDIS_CTR="${REDIS_CTR:-gridtokenx-redis}"
SIM_CTR="${SIM_CTR:-gridtokenx-smartmeter-simulator}"
API_KEY="${API_KEY:-engineering-department-api-key-2025}"
# Repo-root cert dir (script lives in <repo>/backend/scripts).
CERTS="${CERTS:-$(cd "$(dirname "$0")/../../../infra/certs" && pwd)}"
CA="$CERTS/ca.crt"
CLIENT_CRT="$CERTS/clients/smartmeter-simulator.crt"
CLIENT_KEY="$CERTS/clients/smartmeter-simulator.key"
INGEST="$BRIDGE_URL/v1/private-network/ingest"

pass=0 fail=0
ok()   { echo "  ✅ PASS: $1"; pass=$((pass + 1)); }
no()   { echo "  ❌ FAIL: $1"; fail=$((fail + 1)); }
hr()   { echo; echo "── $1"; }

mtls() { curl -sk --cert "$CLIENT_CRT" --key "$CLIENT_KEY" --max-time 8 "$@"; }

# --- 1. mTLS: client cert required -------------------------------------------
hr "1. mTLS — bridge requires a client cert"
code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 8 -X POST "$INGEST" \
        -H "X-API-KEY: $API_KEY" -d '{}' 2>/dev/null)
# No client cert ⇒ TLS handshake fails ⇒ curl can't get an HTTP code (000 / exit 56).
[ "$code" = "000" ] && ok "no-client-cert request rejected at TLS ($code)" \
                     || no "no-client-cert request not rejected (got HTTP $code)"

# --- 2. Ingest lockdown: secure mode rejects non-encrypted -------------------
hr "2. Ingest lockdown — secure mode (REQUIRE_SECURE)"
code=$(mtls -o /dev/null -w '%{http_code}' -X POST "$INGEST" -H "X-API-KEY: $API_KEY" \
        -H 'Content-Type: application/json' \
        -d '{"protocol":"dlms","device_id":"E2E","payload":{"kwh":1,"timestamp":"2026-06-27T00:00:00+00:00","signature":"x"}}')
[ "$code" = "426" ] && ok "plaintext dlms rejected (426)" || no "plaintext dlms not 426 (got $code)"
code=$(mtls -o /dev/null -w '%{http_code}' -X POST "$INGEST" -H "X-API-KEY: $API_KEY" \
        -H 'Content-Type: application/json' \
        -d '{"protocol":"simulator","device_id":"E2E","payload":{}}')
[ "$code" = "426" ] && ok "unsigned simulator bypass refused (426)" || no "simulator not 426 (got $code)"

# --- 3. Encrypted ingest flowing (live sim → bridge, 202) --------------------
hr "3. Encrypted ingest — live sim → bridge"
codes=$(docker logs "$SIM_CTR" --since 30s 2>&1 | grep -oE 'private-network/ingest "HTTP/1.1 [0-9]+' | grep -oE '[0-9]+$' | sort | uniq -c)
echo "  ingest status (last 30s): ${codes:-<none>}"
echo "$codes" | grep -q ' 202' && ok "sim ingest returning 202 over mTLS" \
                                || no "no 202 ingest in last 30s (sim emitting?)"

# --- 4. At-rest: zone stream payload is encrypted, no plaintext registers ----
hr "4. At-rest — zone Redis stream payloads encrypted"
entry=$(docker exec "$REDIS_CTR" redis-cli XREVRANGE gridtokenx:events:zone_1 + - COUNT 1 2>/dev/null)
if echo "$entry" | grep -q '"enc"' && echo "$entry" | grep -q 'ciphertext'; then
  ok "zone entry is a sealed {event_type, enc:{...}} envelope"
else
  no "zone entry not encrypted (no enc/ciphertext)"
fi
if echo "$entry" | grep -qiE 'voltage|consumed_kwh|generated_kwh|"kwh"|1\.1\.1\.8|sum_active_power'; then
  no "plaintext register leaked in zone stream at rest"
else
  ok "no plaintext registers in the zone stream at rest"
fi
sek=$(docker exec "$REDIS_CTR" redis-cli GET gridtokenx:stream:sek 2>/dev/null)
[[ "$sek" == vault:* ]] && ok "stream SEK is Vault-wrapped at rest (${sek:0:9}…)" \
                        || no "stream SEK not Vault-wrapped (got ${sek:0:12})"

# --- 5. Key rotation: versioned + rotatable ----------------------------------
hr "5. Key rotation — Vault-KEK versioned GUEK"
status=$(curl -s --max-time 8 "$SIM_URL/api/v1/simulation/keys/status" 2>/dev/null)
echo "$status" | grep -q '"enabled":true' && ok "key rotation enabled" || no "key rotation not enabled"
# A pre-rotation kid for one meter, then rotate the fleet, then re-read.
mid=$(echo "$status" | grep -oE '"[0-9a-f-]{36}":[0-9]+' | head -1 | cut -d'"' -f2)
before=$(echo "$status" | grep -oE "\"$mid\":[0-9]+" | grep -oE '[0-9]+$')
rotated=$(curl -s --max-time 8 -X POST "$SIM_URL/api/v1/simulation/keys/rotate" 2>/dev/null)
after=$(curl -s --max-time 8 "$SIM_URL/api/v1/simulation/keys/status" 2>/dev/null | grep -oE "\"$mid\":[0-9]+" | grep -oE '[0-9]+$')
if [ -n "$before" ] && [ -n "$after" ] && [ "$after" -gt "$before" ]; then
  ok "rotate advanced meter $mid kid: $before → $after"
else
  no "rotate did not advance kid (before=$before after=$after)"
fi
# Rotation-specific guarantee: a new key version must not break decryption. After
# rotating, the bridge must log NO GCM/decrypt/unwrap failures over the next ~20s
# (general ingest health — 202 rate, owner/api-key auth — is check 3's job and is
# orthogonal to whether rotation works). Wait out a couple of emit cycles first.
sleep 18
decrypterr=$(docker logs gridtokenx-aggregator-bridge --since 20s 2>&1 \
  | grep -ic 'GCM auth/decrypt failed\|no AES key v[0-9]\|failed to unwrap GUEK\|stream GCM auth')
[ "$decrypterr" = 0 ] && ok "no decrypt failures after rotation (new kid decodes)" \
                       || no "rotation broke decryption ($decrypterr GCM/unwrap errors)"

# --- summary -----------------------------------------------------------------
echo
echo "════════════════════════════════════════════"
echo "  secure-telemetry E2E: $pass passed, $fail failed"
echo "════════════════════════════════════════════"
[ "$fail" -eq 0 ]
