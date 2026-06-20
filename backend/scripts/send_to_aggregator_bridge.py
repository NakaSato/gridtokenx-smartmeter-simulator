"""Send simulator readings to the Aggregator Bridge over DLMS/COSEM (IEC 62056).

End-to-end Path A wiring: generate a meter fleet, register each meter's Ed25519
public key in the bridge's Redis device registry, then on every tick generate a
reading per meter and POST it as a signed OBIS-coded JSON frame to the bridge's
``/v1/private-network/ingest`` endpoint (``protocol = "dlms"``).

With ``--onboard`` the SAME in-process fleet is also bound to owner accounts before
streaming (so meter ids stay consistent — generating a fleet twice yields different
ids). Owner binding seeds ``gridtokenx:meters:{serial}:user_id`` so the bridge
attributes readings; without it telemetry resolves to nil and settlement is skipped.
For the full IAM register→verify→claim path (real accounts + DB rows), use
``scripts/e2e_iam_flow.py`` instead — when a meter is claimed through IAM, IAM seeds
the owner map itself, so this script only needs to register the device pubkey.

Usage:
    uv run python scripts/send_to_aggregator_bridge.py --meters 5 --interval 15
    uv run python scripts/send_to_aggregator_bridge.py --once --onboard   # bind + 1 tick
    uv run python scripts/send_to_aggregator_bridge.py --once --dry-run   # no network
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_meter_simulator.config import get_config  # noqa: E402
from smart_meter_simulator.devices.ami import SmartMeter  # noqa: E402
from smart_meter_simulator.meter_generator import MeterGenerator  # noqa: E402
from smart_meter_simulator.transport.aggregator_bridge import (  # noqa: E402
    MeterKey,
    AggregatorBridgeClient,
    _build_obis_payload,
    register_meter_owners_redis,
    register_pubkeys_redis,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("send_to_aggregator_bridge")


async def run(
    num_meters: int,
    interval: int,
    once: bool,
    dry_run: bool,
    onboard: bool,
    duration: float = 0.0,
    report: bool = False,
) -> None:
    config = get_config()

    generator = MeterGenerator(num_meters)
    meters = [SmartMeter(cfg) for cfg in generator.generate_meters()]
    keys = {m.meter_id: MeterKey(m.meter_id) for m in meters}
    logger.info("Created %d meters", len(meters))

    if not dry_run:
        registered = register_pubkeys_redis(config.redis_url, keys.values())
        logger.info("Registered %d/%d pubkeys in Redis", registered, len(meters))

        if onboard:
            # Bind this exact fleet to owner accounts so the bridge attributes
            # readings. Synthesized stable user_ids (no IAM source of truth) — use
            # scripts/e2e_iam_flow.py for real IAM-claimed accounts.
            ownership = {
                m.meter_id: str(
                    uuid.uuid5(uuid.NAMESPACE_DNS, f"sim-owner:{m.meter_id}")
                )
                for m in meters
            }
            seeded = register_meter_owners_redis(config.redis_url, ownership)
            logger.info("Bound %d/%d meters to owner accounts", seeded, len(meters))

    if dry_run:
        ts = datetime.now(timezone.utc)
        sample = meters[0].generate_reading(ts, interval_seconds=interval)
        body = {
            "protocol": "dlms",
            "device_id": sample.meter_id,
            "payload": _build_obis_payload(sample, keys[sample.meter_id], None),
        }
        logger.info("DRY-RUN sample DLMS/COSEM frame:\n%s", json.dumps(body, indent=2))
        return

    # The bridge's api_key_auth middleware requires X-API-KEY on /ingest; pass the
    # configured key (AGGREGATOR_API_KEY) or 401s are returned before signature check.
    client = AggregatorBridgeClient(
        base_url=config.aggregator_bridge_url,
        api_key=config.aggregator_api_key,
    )
    # `interval` doubles as the inter-tick sleep; for max-offered-rate benchmarks it
    # is 0 (no sleep). But a reading must represent a positive sampling window, so
    # clamp the value handed to generate_reading to the real meter cadence (900 s).
    reading_interval = interval if interval > 0 else 900
    tick = 0
    total_sent = total_failed = 0
    start = time.monotonic()
    try:
        while True:
            tick += 1
            ts = datetime.now(timezone.utc)
            sent = failed = 0
            for m in meters:
                reading = m.generate_reading(ts, interval_seconds=reading_interval)
                try:
                    await client.send_reading(reading, keys[m.meter_id])
                    sent += 1
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    if failed <= 3:
                        logger.error("Send failed for %s: %s", m.meter_id, exc)
            total_sent += sent
            total_failed += failed
            logger.info("Tick %d: sent=%d failed=%d", tick, sent, failed)
            if once:
                break
            # Bounded run for benchmarking: stop once the wall-clock budget is spent.
            if duration > 0 and (time.monotonic() - start) >= duration:
                break
            await asyncio.sleep(interval)
    finally:
        await client.close()

    elapsed = time.monotonic() - start
    if report:
        summary = {
            "meters": num_meters,
            "interval": interval,
            "ticks": tick,
            "elapsed_s": round(elapsed, 3),
            "total_sent": total_sent,
            "total_failed": total_failed,
            "send_rate_per_s": round(total_sent / elapsed, 3) if elapsed > 0 else 0.0,
        }
        # Machine-readable line for the bench harness to parse (prefix-tagged).
        print("BENCH_JSON " + json.dumps(summary), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meters", type=int, default=5)
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--once", action="store_true", help="send a single tick")
    parser.add_argument(
        "--dry-run", action="store_true", help="build/sign a frame but do not send"
    )
    parser.add_argument(
        "--onboard",
        action="store_true",
        help="bind this fleet to owner accounts (seed owner map) before streaming",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="stop after this many wall-clock seconds (0 = loop until Ctrl-C)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="print a BENCH_JSON summary line (sent/failed/elapsed/rate) on exit",
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            args.meters,
            args.interval,
            args.once,
            args.dry_run,
            args.onboard,
            args.duration,
            args.report,
        )
    )


if __name__ == "__main__":
    main()
