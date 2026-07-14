"""Feed real simulator telemetry for meters registered via the IAM/meter-service API.

Unlike ``send_to_aggregator_bridge.py`` (which *generates* a random fleet), this
reader takes the credential TSV produced by
``scripts/register_users_meters.sh`` and streams a signed DLMS/COSEM reading per
row, pinning ``device_id`` to that row's ``serial_number``.

Because the register script already wired, per serial:
  - gridtokenx:devices:<serial>:pubkey   (Ed25519, seed = sha256("gridtokenx-sim:<serial>"))
  - gridtokenx:meters:<serial>:user_id   (owner attribution)
  - gridtokenx:meters:<serial>:wallet    (mint recipient)
the bridge already trusts + attributes these frames. This feeder derives the SAME
key via ``MeterKey(serial)`` (identical seed formula) so signatures verify, and it
does NOT touch the owner map (that would clobber the real IAM owner with a synthetic
uuid). Pass --seed-pubkeys only if you want to re-assert the (idempotent) pubkey.

Serials default to SOLAR_PROSUMER so readings carry surplus and can trigger the
15-min settlement -> surplus-mint path.

Usage:
    uv run python scripts/feed_registered_meters.py --file ../../scripts/registered_users_meters.txt --interval 15
    uv run python scripts/feed_registered_meters.py --file <tsv> --once          # one tick, then exit
    uv run python scripts/feed_registered_meters.py --file <tsv> --dry-run       # print one frame, no network
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_meter_simulator.config import MeterType, get_config  # noqa: E402
from smart_meter_simulator.devices.ami import SmartMeter  # noqa: E402
from smart_meter_simulator.meter_generator import MeterGenerator  # noqa: E402
from smart_meter_simulator.transport.aggregator_bridge import (  # noqa: E402
    MeterKey,
    AggregatorBridgeClient,
    _build_obis_payload,
    register_enckeys_redis,
    register_pubkeys_redis,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("feed_registered_meters")


def _load_serials(path: str) -> list[str]:
    """Read serial_number column from the register-script TSV (header required)."""
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    serials = [r["serial_number"].strip() for r in rows if r.get("serial_number", "").strip()]
    if not serials:
        raise SystemExit(f"no serial_number rows in {path}")
    return serials


def _build_meters(serials: list[str]) -> tuple[list[SmartMeter], dict[str, MeterKey]]:
    """One SmartMeter per serial, forcing meter_id == serial (== telemetry device_id)."""
    gen = MeterGenerator(len(serials))
    meters: list[SmartMeter] = []
    for i, serial in enumerate(serials):
        loc = {
            "meter_id": serial,       # pin device_id to the API-registered serial
            "serial_number": serial,
            "name": f"Meter_{serial}",
            "latitude": 13.75,
            "longitude": 100.5,
            "zone_code": (i % 10) + 1,
        }
        cfg = gen.create_meter_config(i + 1, MeterType.SOLAR_PROSUMER, loc)
        meters.append(SmartMeter(cfg))
    keys = {m.meter_id: MeterKey(m.meter_id) for m in meters}
    return meters, keys


async def run(
    path: str, interval: int, once: bool, dry_run: bool, seed_pubkeys: bool, encrypt: bool
) -> None:
    config = get_config()
    serials = _load_serials(path)
    meters, keys = _build_meters(serials)
    logger.info("Loaded %d meters from %s", len(meters), path)

    if dry_run:
        ts = datetime.now(timezone.utc)
        sample = meters[0].generate_reading(ts, interval_seconds=interval or 900)
        body = {
            "protocol": "dlms",
            "device_id": sample.meter_id,
            "payload": _build_obis_payload(sample, keys[sample.meter_id], None),
        }
        logger.info("DRY-RUN sample DLMS/COSEM frame:\n%s", json.dumps(body, indent=2))
        return

    if seed_pubkeys:
        # Idempotent re-assert of the Ed25519 pubkeys (same value the register
        # script wrote). Owner map is intentionally left untouched.
        n = register_pubkeys_redis(config.redis_url, keys.values())
        logger.info("Re-asserted %d/%d pubkeys in Redis", n, len(meters))

    if encrypt:
        # The secure bridge answers plaintext `dlms` frames with 426 Upgrade
        # Required; it accepts only AES-256-GCM `dlms-enc`. The register script
        # wired pubkey/owner/wallet but NOT the per-meter GUEK, so seed it here
        # (static Phase-2 key = HKDF(meter seed); same value the bridge derives).
        n = register_enckeys_redis(config.redis_url, keys.values())
        logger.info("Seeded %d/%d meter AES keys in Redis", n, len(meters))
    # Monotonic per-meter invocation counter (replay protection). Time-seeded in
    # ms so re-runs never reuse a counter the bridge has already accepted.
    base = int(time.time() * 1000)
    counters = {m.meter_id: base for m in meters}

    client_cert = (
        (config.aggregator_tls_client_cert, config.aggregator_tls_client_key)
        if config.aggregator_tls_client_cert and config.aggregator_tls_client_key
        else None
    )
    client = AggregatorBridgeClient(
        base_url=config.aggregator_bridge_url,
        api_key=config.aggregator_api_key,
        verify=config.aggregator_tls_ca or True,
        client_cert=client_cert,
    )
    reading_interval = interval if interval > 0 else 900
    tick = 0
    try:
        while True:
            tick += 1
            ts = datetime.now(timezone.utc)
            sent = failed = 0
            for m in meters:
                reading = m.generate_reading(ts, interval_seconds=reading_interval)
                counters[m.meter_id] += 1
                try:
                    await client.send_reading(
                        reading,
                        keys[m.meter_id],
                        encrypt=encrypt,
                        counter=counters[m.meter_id] if encrypt else None,
                    )
                    sent += 1
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    if failed <= 3:
                        logger.error("Send failed for %s: %s", m.meter_id, exc)
            logger.info("Tick %d: sent=%d failed=%d", tick, sent, failed)
            if once:
                break
            await asyncio.sleep(interval)
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, help="credential TSV from register_users_meters.sh")
    parser.add_argument("--interval", type=int, default=15, help="inter-tick sleep (s); reading window")
    parser.add_argument("--once", action="store_true", help="send a single tick then exit")
    parser.add_argument("--dry-run", action="store_true", help="print one frame, no network")
    parser.add_argument("--seed-pubkeys", action="store_true", help="idempotently re-assert Ed25519 pubkeys")
    parser.add_argument(
        "--no-encrypt",
        dest="encrypt",
        action="store_false",
        help="send plaintext dlms (secure bridge answers 426; default is encrypted dlms-enc)",
    )
    parser.set_defaults(encrypt=True)
    args = parser.parse_args()
    asyncio.run(
        run(args.file, args.interval, args.once, args.dry_run, args.seed_pubkeys, args.encrypt)
    )


if __name__ == "__main__":
    main()
