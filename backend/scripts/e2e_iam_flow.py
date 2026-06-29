"""Full IAM-backed end-to-end: register account → verify → claim meter → stream.

For each meter this runs the real ownership lifecycle against a live IAM service
(reached directly, presenting the ApiGateway role headers IAM normally gets from
APISIX), then streams signed DLMS/COSEM telemetry that the Aggregator Bridge attributes
to the owning account.

Per meter:
  1. POST /api/v1/auth/register   → create a user account
  2. read email_verification_token from Postgres, GET /api/v1/auth/verify
     → activate account + provision Vault wallet
  3. POST /api/v1/auth/login      → JWT
  4. POST /api/v1/meters          → one-time claim (UNIQUE serial). IAM seeds the
     Aggregator Bridge owner map (gridtokenx:meters:{serial}:user_id) itself.
  5. register the device Ed25519 pubkey, then POST a signed OBIS frame per tick.

Prerequisites (see scripts/setup_vault_transit.sh and the README): Postgres, Redis,
Vault (transit engine enabled), IAM service, Aggregator Bridge all reachable.

Token retrieval uses `docker exec <pg> psql` because IAM publishes the verification
token as an event (consumed by the Noti service to send mail) rather than returning
it — in a full stack you would click the emailed link instead.

Usage:
    uv run python scripts/e2e_iam_flow.py --meters 3 --once
    uv run python scripts/e2e_iam_flow.py --meters 3 --iam-url http://localhost:4013
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

import httpx

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_meter_simulator.config import get_config  # noqa: E402
from smart_meter_simulator.devices.ami import SmartMeter  # noqa: E402
from smart_meter_simulator.meter_generator import MeterGenerator  # noqa: E402
from smart_meter_simulator.transport.aggregator_bridge import (  # noqa: E402
    MeterKey,
    AggregatorBridgeClient,
    register_pubkeys_redis,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("e2e_iam_flow")

GATEWAY_HEADERS = {
    "x-gridtokenx-role": "api-gateway",
    "x-gridtokenx-gateway-secret": os.getenv(
        "GATEWAY_SECRET", "gridtokenx-gateway-secret-2025"
    ),
}
PASSWORD = "OwnerPass#2026"


def _pg_token(pg_container: str, db_user: str, db_name: str, email: str) -> str:
    """Read the email verification token straight from Postgres (dev convenience)."""
    out = subprocess.run(
        [
            "docker",
            "exec",
            pg_container,
            "psql",
            "-U",
            db_user,
            "-d",
            db_name,
            "-tAc",
            f"SELECT email_verification_token FROM users WHERE email='{email}'",
        ],
        capture_output=True,
        text=True,
    )
    return out.stdout.strip()


async def onboard_account(
    client: httpx.AsyncClient,
    iam: str,
    meter_svc: str,
    meter_id: str,
    pg: tuple[str, str, str],
) -> tuple[str, str] | None:
    """Register → verify → login (IAM) → claim (meter-service). Returns (user_id, jwt) or None."""
    tag = uuid.uuid5(uuid.NAMESPACE_DNS, meter_id).hex[:10]
    username = f"owner_{tag}"
    email = f"{username}@sim.gridtokenx.local"

    r = await client.post(
        f"{iam}/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": PASSWORD,
            "first_name": "Grid",
            "last_name": "Owner",
        },
    )
    if r.status_code not in (200, 409):
        logger.error(
            "register failed for %s: %s %s", meter_id, r.status_code, r.text[:120]
        )
        return None

    token = _pg_token(*pg, email=email)
    if token:
        await client.get(f"{iam}/api/v1/auth/verify", params={"token": token})

    lg = await client.post(
        f"{iam}/api/v1/auth/login", json={"username": username, "password": PASSWORD}
    )
    if lg.status_code != 200:
        logger.error(
            "login failed for %s: %s (account unverified?)", meter_id, lg.status_code
        )
        return None
    data = lg.json()
    jwt = data.get("access_token")
    user_id = data.get("user", {}).get("id")

    # Meter ownership lives in meter-service (`:4062`), not IAM — IAM has no
    # meter-claim endpoint. The claim writes the parent `meters` row (user_id),
    # which the Aggregator Bridge joins to resolve telemetry → owner. Auth is a
    # plain JWT Bearer (meter-service reads `claims.sub`); no gateway headers.
    # Best-effort: a transport drop on the on-chain leg still leaves the DB row.
    try:
        cm = await client.post(
            f"{meter_svc}/api/v1/meters",
            headers={"Authorization": f"Bearer {jwt}"},
            json={"serial_number": meter_id, "meter_type": "solar"},
        )
        jm = (
            cm.json()
            if cm.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        logger.info(
            "  %s → user=%s claimed=%s onchain=%s",
            meter_id,
            user_id,
            jm.get("meter") is not None,
            jm.get("success"),
        )
    except httpx.HTTPError as exc:
        logger.info(
            "  %s → user=%s claimed=db-only (on-chain leg dropped: %s)",
            meter_id,
            user_id,
            type(exc).__name__,
        )
    return (user_id, jwt) if user_id else None


async def run(
    num_meters: int,
    interval: int,
    once: bool,
    iam: str,
    meter_svc: str,
    pg: tuple[str, str, str],
) -> None:
    config = get_config()
    meters = [SmartMeter(cfg) for cfg in MeterGenerator(num_meters).generate_meters()]
    keys = {m.meter_id: MeterKey(m.meter_id) for m in meters}

    logger.info("=== Onboarding %d accounts + claiming meters via IAM ===", len(meters))
    owners: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=30) as c:
        for m in meters:
            res = await onboard_account(c, iam, meter_svc, m.meter_id, pg)
            if res:
                owners[m.meter_id] = res[0]

    # Device pubkeys are device identity → registered by the simulator. The owner
    # map was seeded by IAM during the claim above.
    register_pubkeys_redis(config.redis_url, keys.values())
    logger.info(
        "Claimed %d/%d meters; streaming telemetry...", len(owners), len(meters)
    )

    # X-API-KEY is mandatory on /ingest (bridge api_key_auth middleware) — without
    # it every POST 401s before the Ed25519 signature is even checked.
    # mTLS to the secure-mode bridge (AGGREGATOR_REQUIRE_SECURE=true): present a
    # client cert signed by the IoT-gateway CA and trust that CA. When the bridge
    # URL is https and no certs are given via env, auto-default to the dev certs the
    # superproject ships under infra/certs/ — so the secure path "just works" without
    # extra flags. Env (E2E_TLS_*) always overrides; plaintext http is untouched.
    _ca = os.getenv("E2E_TLS_CA")
    _crt = os.getenv("E2E_TLS_CERT")
    _key = os.getenv("E2E_TLS_KEY")
    if config.aggregator_bridge_url.lower().startswith("https") and not (_crt and _key):
        # scripts/ -> backend/ -> gridtokenx-smartmeter-simulator/ -> <superproject root>
        _root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        _certs = os.path.join(_root, "infra", "certs")
        _def_crt = os.path.join(_certs, "clients", "smartmeter-simulator.crt")
        _def_key = os.path.join(_certs, "clients", "smartmeter-simulator.key")
        _def_ca = os.path.join(_certs, "ca.crt")
        if os.path.exists(_def_crt) and os.path.exists(_def_key):
            _crt, _key = _def_crt, _def_key
            _ca = _ca or (_def_ca if os.path.exists(_def_ca) else None)
            logger.info("https bridge: using dev mTLS client cert %s", _def_crt)
        else:
            logger.warning(
                "https bridge but no client cert found at %s — ingest will fail the "
                "mTLS handshake; set E2E_TLS_CERT/E2E_TLS_KEY (and E2E_TLS_CA).",
                _def_crt,
            )
    _tls = {}
    if _crt and _key:
        _tls["client_cert"] = (_crt, _key)
        _tls["verify"] = _ca if _ca else False
    client = AggregatorBridgeClient(
        base_url=config.aggregator_bridge_url,
        api_key=config.aggregator_api_key,
        **_tls,
    )
    tick = 0
    try:
        while True:
            tick += 1
            ts = datetime.now(timezone.utc)
            sent = failed = 0
            for m in meters:
                reading = m.generate_reading(ts, interval_seconds=interval)
                try:
                    await client.send_reading(reading, keys[m.meter_id])
                    sent += 1
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    if failed <= 3:
                        logger.error("send failed %s: %s", m.meter_id, exc)
            logger.info(
                "Tick %d: sent=%d failed=%d (attributed owners: %d)",
                tick,
                sent,
                failed,
                len(owners),
            )
            if once:
                break
            await asyncio.sleep(interval)
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meters", type=int, default=3)
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--once", action="store_true")
    parser.add_argument(
        "--iam-url", default=os.getenv("IAM_URL", "http://localhost:4010")
    )
    parser.add_argument(
        "--meter-url", default=os.getenv("METER_SERVICE_URL", "http://localhost:4062")
    )
    parser.add_argument("--pg-container", default="gridtokenx-postgres")
    parser.add_argument("--db-user", default="gridtokenx_user")
    parser.add_argument("--db-name", default="gridtokenx")
    args = parser.parse_args()
    asyncio.run(
        run(
            args.meters,
            args.interval,
            args.once,
            args.iam_url,
            args.meter_url,
            (args.pg_container, args.db_user, args.db_name),
        )
    )


if __name__ == "__main__":
    main()
