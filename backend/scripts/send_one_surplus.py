"""Send ONE signed surplus DLMS/COSEM reading for a specific meter serial.

Used for the meter-service mint e2e: drives a single mintable reading (net_kwh > 0)
for an exact, pre-claimed serial so it forwards to meter-service and mints to the
owner's wallet. The per-meter Ed25519 key is derived deterministically from the
serial (MeterKey), so no fleet generation is involved.

Env:
  SERIAL      meter serial to send for (also the device_id / canonical sign id)
  GEN_KWH     energy_generated this interval (default 5.0)
  CONS_KWH    energy_consumed this interval (default 1.0)  -> net = GEN-CONS
  REDIS_URL   default redis://redis:6379
  BRIDGE_URL  default http://aggregator-bridge:4010
  API_KEY     default e2e-test-key

Usage (inside the simulator container):
  SERIAL=3eb13b90-... uv run python scripts/send_one_surplus.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_meter_simulator.models.reading import EnergyReading  # noqa: E402
from smart_meter_simulator.transport.aggregator_bridge import (  # noqa: E402
    AggregatorBridgeClient,
    MeterKey,
    register_pubkeys_redis,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("send_one_surplus")


async def main() -> None:
    serial = os.environ["SERIAL"]
    gen = float(os.getenv("GEN_KWH", "5.0"))
    cons = float(os.getenv("CONS_KWH", "1.0"))
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    bridge_url = os.getenv("BRIDGE_URL", "http://aggregator-bridge:4010")
    api_key = os.getenv("API_KEY", "e2e-test-key")

    net = round(gen - cons, 6)
    if net <= 0:
        raise SystemExit(f"net_kwh must be > 0 to be mintable (gen={gen} cons={cons})")

    key = MeterKey(serial)
    n = register_pubkeys_redis(redis_url, [key])
    log.info("registered %d pubkey(s) for serial=%s pub=%s", n, serial, key.public_key_hex())

    reading = EnergyReading(
        meter_id=serial,
        timestamp=datetime.now(timezone.utc),
        sequence_number=1,
        energy_generated=gen,
        energy_consumed=cons,
        surplus_energy=net,
        deficit_energy=0.0,
        interval_seconds=900,
        voltage=230.0,
        current=10.0,
        power_factor=0.99,
        frequency=50.0,
        location="e2e-test",
        meter_type="solar",
        user_type="prosumer",
    )

    client = AggregatorBridgeClient(base_url=bridge_url, api_key=api_key)
    try:
        resp = await client.send_reading(reading, key)
        log.info("bridge accepted: %s %s", resp.status_code, resp.text[:200])
    finally:
        await client.close()

    log.info("SENT serial=%s net_kwh=%s gen=%s cons=%s", serial, net, gen, cons)


if __name__ == "__main__":
    asyncio.run(main())
