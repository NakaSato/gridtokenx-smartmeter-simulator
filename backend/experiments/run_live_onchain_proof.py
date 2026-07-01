"""Live on-chain proof: small fleet, full pipeline (NOT a solver benchmark).

Unlike run_experiments.py / run_large_scale.py (which call eng.tick() directly,
bypassing eng.start() for solver-throughput-only runs), this script calls
eng.start() so the real per-tick path runs end to end:

  IAM onboarding (register/verify/login per meter owner, on-chain registration)
  -> Ed25519 device-key registration in the bridge's Redis registry
  -> per-tick DLMS/COSEM ingest (mTLS + AES-256-GCM encrypted, signed OBIS frames)
  -> bridge signature verification + zone dissemination + settlement-bin aggregation
  -> real Solana mint transaction via Chain Bridge once a settlement window closes

Deliberately small (default 100 meters) -- IAM onboarding is one HTTP round-trip
per owner and mint is a real signed Solana tx per settlement window, so this does
NOT scale to the 10k/50k/100k offline solver benchmark (see run_large_scale.py).

Requires: aggregator-bridge, redis, iam-service, chain-bridge, vault all up and
healthy, and a live solana-test-validator (chain-bridge wired to it). Reads the
mTLS/encryption/IAM-onboarding config from backend/.env -- see that file's
AGGREGATOR_* keys.

Run:  uv run python experiments/run_live_onchain_proof.py [--meters N] [--ticks N]
"""

from __future__ import annotations

import argparse
import asyncio
import faulthandler
import os
import sys
import time
from datetime import datetime
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

TOPOLOGY = "glm:src/smart_meter_simulator/data/grids/grid_bus_network.glm"
INTERVAL_S = 15 * 60


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--meters", type=int, default=100)
    p.add_argument("--ticks", type=int, default=5)
    return p.parse_args()


async def main() -> None:
    args = parse_args()

    # A prior 10k-meter run stalled silently (100% CPU, zero progress, zero DB
    # activity for 9+ min) with no diagnosis possible. Dump every thread's
    # traceback every 60s so a repeat shows exactly where it's stuck instead of
    # an unexplained spin.
    faulthandler.dump_traceback_later(60, repeat=True, file=sys.stderr)

    os.environ.setdefault("GRID_TOPOLOGY", TOPOLOGY)
    os.environ.setdefault("SIMULATION_INTERVAL", str(INTERVAL_S))
    os.environ.setdefault("PV_MODEL_ENABLED", "true")
    os.environ.setdefault("PV_ON_EVERY_BUS", "false")
    os.environ.setdefault("SOLAR_PROSUMER_RATIO", "0.10")
    os.environ.setdefault("HYBRID_PROSUMER_RATIO", "0.0")
    os.environ.setdefault("GRID_CONSUMER_RATIO", "0.90")

    from smart_meter_simulator.config import settings

    settings._config_instance = None
    from smart_meter_simulator.core.engine import SimulationEngine

    print(f"=== Live on-chain proof: {args.meters} meters, {args.ticks} ticks ===")
    t0 = time.perf_counter()
    eng = SimulationEngine(grid_topology=os.environ["GRID_TOPOLOGY"], num_meters=args.meters)

    # eng.start() -- NOT eng.tick() bypass -- wires the aggregator emitter,
    # IAM-onboards every meter owner (register/verify/login + on-chain
    # registration), and registers each meter's Ed25519 key in the bridge.
    await eng.start()
    start_ms = (time.perf_counter() - t0) * 1000.0
    print(f"start() (incl. IAM onboarding) took {start_ms:.0f} ms")

    n_pv = sum(1 for m in eng.meters if m.solar is not None)
    print(f"{n_pv}/{args.meters} meters have PV ({n_pv / args.meters:.1%})")

    eng.current_sim_time = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    eng.weather_mode = "Sunny"
    for m in eng.meters:
        m.update_weather("Sunny")

    for i in range(args.ticks):
        t0 = time.perf_counter()
        await eng.tick()
        dt_ms = (time.perf_counter() - t0) * 1000.0
        print(f"  tick {i + 1}/{args.ticks}  {dt_ms:.0f} ms")
        await asyncio.sleep(1.0)  # let the in-flight ingest gather settle

    await asyncio.sleep(3.0)
    await eng.stop()
    print("Done. Check aggregator-bridge / chain-bridge logs for ingest + mint confirmations.")


if __name__ == "__main__":
    asyncio.run(main())
