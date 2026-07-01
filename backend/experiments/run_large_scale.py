"""Large-fleet scalability test: 10k / 50k / 100k meters, ~10% random PV.

Drives ``SimulationEngine.tick()`` directly (no real-time loop, no API server)
over a short window, sweeping fleet size. PV is assigned randomly per meter
(not "every Nth bus") via ``SOLAR_PROSUMER_RATIO`` — same mechanism as
``run_experiments.py`` E4, but uses ``generate_ieee_meters``'s ratio-weighted
random.choices path (fixed in meter_generator.py to honor the configured
ratios instead of a hardcoded 70/20/10 split).

Run:  uv run python experiments/run_large_scale.py
"""

from __future__ import annotations

import asyncio
import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

TOPOLOGY = "glm:src/smart_meter_simulator/data/grids/grid_bus_network.glm"
INTERVAL_S = 15 * 60
TICKS = 4  # short window; this is a throughput/scale test, not a full day

FLEET_SIZES = [10_000, 50_000, 100_000]
PV_RATIO = 0.10  # fraction of meters with rooftop PV, assigned at random


def _fresh_config(env: Dict[str, str]) -> None:
    from smart_meter_simulator.config import settings

    base = {
        "GRID_TOPOLOGY": TOPOLOGY,
        "SIMULATION_INTERVAL": str(INTERVAL_S),
        "PV_MODEL_ENABLED": "true",
        "PV_ON_EVERY_BUS": "false",  # use ratio-weighted random PV, not every-bus
        "SOLAR_PROSUMER_RATIO": str(PV_RATIO),
        "HYBRID_PROSUMER_RATIO": "0.0",
        "GRID_CONSUMER_RATIO": str(1.0 - PV_RATIO),
    }
    base.update(env)
    for k, v in base.items():
        os.environ[k] = v
    settings._config_instance = None


def build_engine(num_meters: int, env: Dict[str, str]):
    _fresh_config(env)
    from smart_meter_simulator.core.engine import SimulationEngine

    eng = SimulationEngine(grid_topology=TOPOLOGY, num_meters=num_meters)
    eng.grid.initialize_network(eng.meters)
    eng.current_sim_time = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    eng.weather_mode = "Sunny"
    for m in eng.meters:
        m.update_weather("Sunny")
    return eng


async def run_ticks(eng, ticks: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for k in range(ticks):
        t0 = time.perf_counter()
        await eng.tick()
        dt_ms = (time.perf_counter() - t0) * 1000.0
        s = dict(eng.last_tick_summary)
        s["tick_ms"] = dt_ms
        s["hour"] = k * INTERVAL_S / 3600.0
        rows.append(s)
        print(f"    tick {k+1}/{ticks}  {dt_ms:.0f} ms")
    return rows


def write_csv(name: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    path = RESULTS / f"{name}.csv"
    keys = list(rows[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path.relative_to(RESULTS.parent)}")


async def run_case(num_meters: int) -> Dict[str, Any]:
    print(f"\n=== {num_meters:,} meters, {PV_RATIO:.0%} random PV ===")
    t0 = time.perf_counter()
    eng = build_engine(num_meters, {})
    build_ms = (time.perf_counter() - t0) * 1000.0

    n_pv = sum(1 for m in eng.meters if m.solar is not None)
    print(f"  built in {build_ms:.0f} ms; {n_pv:,}/{num_meters:,} meters have PV "
          f"({n_pv / num_meters:.1%})")

    rows = await run_ticks(eng, TICKS)
    write_csv(f"e5_scale_{num_meters}", rows)

    ms = sorted(r["tick_ms"] for r in rows)
    summary = {
        "num_meters": num_meters,
        "pv_meters": n_pv,
        "pv_pct": round(100.0 * n_pv / num_meters, 2),
        "build_ms": round(build_ms, 1),
        "median_tick_ms": ms[len(ms) // 2],
        "p95_tick_ms": ms[int(len(ms) * 0.95)],
        "max_tick_ms": ms[-1],
    }
    print(f"  median={summary['median_tick_ms']:.0f} ms  "
          f"p95={summary['p95_tick_ms']:.0f} ms  max={summary['max_tick_ms']:.0f} ms")
    return summary


async def main() -> None:
    out = []
    for n in FLEET_SIZES:
        out.append(await run_case(n))
    write_csv("e5_scale_summary", out)
    print("\nDone. Results in experiments/results/")


if __name__ == "__main__":
    asyncio.run(main())
