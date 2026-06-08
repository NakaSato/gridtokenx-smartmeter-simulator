"""One-time meter onboarding: bind each meter_serial to a user account.

For every simulated meter this:
  1. Registers a user (one per meter) and claims the meter in IAM via
     ``POST /api/v1/meters`` (UNIQUE serial → one-time claim, + on-chain PDA).
  2. Seeds the Aggregator Bridge Redis owner map ``gridtokenx:meters:{serial}:user_id``
     so telemetry is attributed to that user and settlement runs.
  3. Registers the meter's Ed25519 public key for telemetry signature verification.

Run this ONCE before streaming telemetry (scripts/send_to_aggregator_bridge.py).
Re-runs are idempotent: existing users/claims are reused.

Usage:
    uv run python scripts/onboard_meters.py --meters 5
    uv run python scripts/onboard_meters.py --meters 5 --skip-iam   # Redis-only
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_meter_simulator.config import get_config  # noqa: E402
from smart_meter_simulator.devices.ami import SmartMeter  # noqa: E402
from smart_meter_simulator.meter_generator import MeterGenerator  # noqa: E402
from smart_meter_simulator.transport.iam_onboarding import (
    IamOnboardingClient,
)  # noqa: E402
from smart_meter_simulator.transport.aggregator_bridge import (  # noqa: E402
    MeterKey,
    register_meter_owners_redis,
    register_pubkeys_redis,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("onboard_meters")


async def run(num_meters: int, iam_url: str, skip_iam: bool) -> None:
    config = get_config()
    meters = [SmartMeter(cfg) for cfg in MeterGenerator(num_meters).generate_meters()]
    keys = {m.meter_id: MeterKey(m.meter_id) for m in meters}
    logger.info("Onboarding %d meters", len(meters))

    ownership: dict[str, str] = {}

    if not skip_iam:
        async with IamOnboardingClient(base_url=iam_url) as iam:
            for m in meters:
                res = await iam.onboard_meter(
                    m.meter_id,
                    meter_type=m.config.get("meter_type"),
                    location=m.config.get("location"),
                )
                if res.user_id:
                    ownership[m.meter_id] = res.user_id
                flag = (
                    "✓on-chain"
                    if res.on_chain
                    else ("✓db" if res.claimed_in_iam else "✗")
                )
                logger.info(
                    "  %s -> user=%s [%s] %s", m.meter_id, res.user_id, flag, res.detail
                )
    else:
        # Redis-only: synthesize a stable user_id per meter (no IAM source of truth).
        import uuid

        for m in meters:
            ownership[m.meter_id] = str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"sim-owner:{m.meter_id}")
            )
        logger.info("Skipping IAM; synthesized %d owner ids", len(ownership))

    # Seed Aggregator Bridge attribution + telemetry signature keys.
    owners = register_meter_owners_redis(config.redis_url, ownership)
    pubkeys = register_pubkeys_redis(config.redis_url, keys.values())

    logger.info(
        "Done. IAM-bound=%d, Redis owners seeded=%d, pubkeys seeded=%d",
        len(ownership) if not skip_iam else 0,
        owners,
        pubkeys,
    )
    if owners == 0:
        logger.warning(
            "Redis owner map not seeded (Redis down?). Aggregator Bridge will resolve "
            "Uuid::nil and skip settlement until %s is reachable.",
            config.redis_url,
        )


def main() -> None:
    config = get_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meters", type=int, default=5)
    parser.add_argument(
        "--iam-url",
        default=os.getenv("IAM_GATEWAY_URL", "http://localhost:4001"),
        help="APISIX gateway base URL fronting the IAM service",
    )
    parser.add_argument(
        "--skip-iam",
        action="store_true",
        help="seed Redis owner map only, do not call IAM (no DB row / on-chain claim)",
    )
    args = parser.parse_args()
    _ = config
    asyncio.run(run(args.meters, args.iam_url, args.skip_iam))


if __name__ == "__main__":
    main()
