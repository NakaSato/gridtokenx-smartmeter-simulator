"""Validation experiment harness for the smart meter simulator research paper.

Drives ``SimulationEngine.tick()`` directly (bypassing the real-time loop) over a
synthetic day, sweeping configuration per run, and writes per-tick CSV results
plus matplotlib figures under ``experiments/results/``.

Experiments
-----------
E1  Diurnal baseline          — one 24 h day, all controls on. Time series of
                                gen/load, losses, voltage envelope, frequency.
E2  PV-penetration sweep       — peak overvoltage, curtailed energy, and losses
                                vs rooftop PV capacity per bus.
E3  IEEE-1547 control ablation — {none, volt-VAR, volt-watt, both, +OLTC} at high
                                penetration: max voltage and curtailed energy.
E4  Scalability                — per-tick wall-clock and solver outcome vs fleet
                                size.

Run:  uv run python experiments/run_experiments.py
"""

from __future__ import annotations

import asyncio
import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

TOPOLOGY = "glm:src/smart_meter_simulator/data/grids/grid_bus_network.glm"
TICKS_PER_DAY = 96          # 15-min interval
INTERVAL_S = 15 * 60


def _fresh_config(env: Dict[str, str]) -> None:
    """Apply env overrides and reset the cached config singleton."""
    from smart_meter_simulator.config import settings

    base = {
        "GRID_TOPOLOGY": TOPOLOGY,
        "SIMULATION_INTERVAL": str(INTERVAL_S),
        "PV_MODEL_ENABLED": "true",
        "PV_ON_EVERY_BUS": "true",
    }
    base.update(env)
    for k, v in base.items():
        os.environ[k] = v
    settings._config_instance = None


def build_engine(num_meters: int, env: Dict[str, str]):
    _fresh_config(env)
    from smart_meter_simulator.core.engine import SimulationEngine

    eng = SimulationEngine(grid_topology=TOPOLOGY, num_meters=num_meters)
    # Initialize the feeder network (maps meters to buses, builds the pandapower
    # net). start() does this in the live loop; we drive tick() directly so we
    # must do it ourselves.
    eng.grid.initialize_network(eng.meters)
    # Sim clock is a *naive wall-clock local* time-of-day: the PV model localizes
    # it to the grid timezone (Asia/Bangkok). A tz-aware UTC clock would place
    # local noon at night and zero all PV. Start the day at midnight.
    eng.current_sim_time = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    eng.weather_mode = "Sunny"
    for m in eng.meters:
        m.update_weather("Sunny")
    return eng


async def run_day(eng, ticks: int = TICKS_PER_DAY) -> List[Dict[str, Any]]:
    """Run ``ticks`` ticks, returning the per-tick summary augmented with the
    bus-voltage envelope (min/max pu over energized buses)."""
    rows: List[Dict[str, Any]] = []
    for k in range(ticks):
        t0 = time.perf_counter()
        await eng.tick()
        dt_ms = (time.perf_counter() - t0) * 1000.0
        s = dict(eng.last_tick_summary)
        volts = [v for v in eng.grid.bus_voltages.values() if v > 0.01]
        s["v_max_pu"] = max(volts) if volts else 0.0
        s["v_min_pu"] = min(volts) if volts else 0.0
        s["tick_ms"] = dt_ms
        s["hour"] = k * INTERVAL_S / 3600.0
        rows.append(s)
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


# --------------------------------------------------------------------------- E1
async def exp1_diurnal(num_meters: int = 60) -> List[Dict[str, Any]]:
    print("E1 diurnal baseline ...")
    eng = build_engine(num_meters, {"BUS_PV_CAPACITY_MIN_KW": "10",
                                     "BUS_PV_CAPACITY_MAX_KW": "10"})
    rows = await run_day(eng)
    write_csv("e1_diurnal", rows)

    hrs = [r["hour"] for r in rows]
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].plot(hrs, [r["total_generation_kwh"] for r in rows], label="PV gen")
    ax[0, 0].plot(hrs, [r["total_consumption_kwh"] for r in rows], label="load")
    ax[0, 0].set(title="Fleet energy per interval", xlabel="hour", ylabel="kWh")
    ax[0, 0].legend()
    ax[0, 1].plot(hrs, [r["v_max_pu"] for r in rows], label="max")
    ax[0, 1].plot(hrs, [r["v_min_pu"] for r in rows], label="min")
    ax[0, 1].axhline(1.05, ls="--", c="r", lw=0.8)
    ax[0, 1].set(title="Bus voltage envelope", xlabel="hour", ylabel="pu")
    ax[0, 1].legend()
    ax[1, 0].plot(hrs, [r["total_losses_kw"] for r in rows], c="purple")
    ax[1, 0].set(title="Feeder losses", xlabel="hour", ylabel="kW")
    ax[1, 1].plot(hrs, [r["frequency_hz"] for r in rows], c="green")
    ax[1, 1].set(title="System frequency", xlabel="hour", ylabel="Hz")
    fig.tight_layout()
    fig.savefig(RESULTS / "e1_diurnal.png", dpi=110)
    plt.close(fig)
    print(f"  wrote results/e1_diurnal.png")
    return rows


# --------------------------------------------------------------------------- E2
async def exp2_penetration(num_meters: int = 60) -> List[Dict[str, Any]]:
    print("E2 PV-penetration sweep ...")
    caps = [10, 25, 50, 75, 100, 125, 150, 200]
    out: List[Dict[str, Any]] = []
    for cap in caps:
        eng = build_engine(num_meters, {"BUS_PV_CAPACITY_MIN_KW": str(cap),
                                        "BUS_PV_CAPACITY_MAX_KW": str(cap)})
        rows = await run_day(eng)
        # Aggregate over the day; peak at solar noon drives overvoltage.
        v_peak = max(r["v_max_pu"] for r in rows)
        curtail_kwh = sum(r["total_curtailed_kw"] for r in rows) * (INTERVAL_S / 3600.0)
        loss_kwh = sum(r["total_losses_kw"] for r in rows) * (INTERVAL_S / 3600.0)
        gen_kwh = sum(r["total_generation_kwh"] for r in rows)
        out.append({
            "pv_kw_per_bus": cap,
            "v_peak_pu": v_peak,
            "curtailed_kwh": curtail_kwh,
            "curtailed_pct": 100.0 * curtail_kwh / gen_kwh if gen_kwh else 0.0,
            "loss_kwh": loss_kwh,
            "gen_kwh": gen_kwh,
        })
        print(f"  cap={cap:>2} kW  v_peak={v_peak:.3f}  curtail={curtail_kwh:.1f} kWh")
    write_csv("e2_penetration", out)

    caps_x = [r["pv_kw_per_bus"] for r in out]
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    ax[0].plot(caps_x, [r["v_peak_pu"] for r in out], "o-")
    ax[0].axhline(1.05, ls="--", c="r", lw=0.8)
    ax[0].set(title="Peak overvoltage", xlabel="PV kW/bus", ylabel="max V (pu)")
    ax[1].plot(caps_x, [r["curtailed_pct"] for r in out], "o-", c="orange")
    ax[1].set(title="Curtailed energy", xlabel="PV kW/bus", ylabel="% of PV gen")
    ax[2].plot(caps_x, [r["loss_kwh"] for r in out], "o-", c="purple")
    ax[2].set(title="Daily feeder losses", xlabel="PV kW/bus", ylabel="kWh")
    fig.tight_layout()
    fig.savefig(RESULTS / "e2_penetration.png", dpi=110)
    plt.close(fig)
    print(f"  wrote results/e2_penetration.png")
    return out


# --------------------------------------------------------------------------- E3
async def exp3_ablation(num_meters: int = 60) -> List[Dict[str, Any]]:
    print("E3 IEEE-1547 control ablation ...")
    high_pv = {"BUS_PV_CAPACITY_MIN_KW": "150", "BUS_PV_CAPACITY_MAX_KW": "150"}
    scenarios = {
        "none":      {"PV_VOLTVAR_ENABLED": "false", "PV_VOLTWATT_ENABLED": "false",
                      "TRANSFORMER_OLTC_ENABLED": "false"},
        "volt-VAR":  {"PV_VOLTVAR_ENABLED": "true",  "PV_VOLTWATT_ENABLED": "false",
                      "TRANSFORMER_OLTC_ENABLED": "false"},
        "volt-watt": {"PV_VOLTVAR_ENABLED": "false", "PV_VOLTWATT_ENABLED": "true",
                      "TRANSFORMER_OLTC_ENABLED": "false"},
        "both":      {"PV_VOLTVAR_ENABLED": "true",  "PV_VOLTWATT_ENABLED": "true",
                      "TRANSFORMER_OLTC_ENABLED": "false"},
        "both+OLTC": {"PV_VOLTVAR_ENABLED": "true",  "PV_VOLTWATT_ENABLED": "true",
                      "TRANSFORMER_OLTC_ENABLED": "true"},
    }
    out: List[Dict[str, Any]] = []
    for label, flags in scenarios.items():
        env = dict(high_pv)
        env.update(flags)
        eng = build_engine(num_meters, env)
        rows = await run_day(eng)
        v_peak = max(r["v_max_pu"] for r in rows)
        curtail_kwh = sum(r["total_curtailed_kw"] for r in rows) * (INTERVAL_S / 3600.0)
        reactive = max(r["total_reactive_support_kvar"] for r in rows)
        out.append({
            "scenario": label,
            "v_peak_pu": v_peak,
            "curtailed_kwh": curtail_kwh,
            "max_reactive_kvar": reactive,
        })
        print(f"  {label:>10}  v_peak={v_peak:.3f}  curtail={curtail_kwh:.1f} kWh")
    write_csv("e3_ablation", out)

    labels = [r["scenario"] for r in out]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].bar(labels, [r["v_peak_pu"] for r in out], color="steelblue")
    ax[0].axhline(1.05, ls="--", c="r", lw=0.8)
    ax[0].set(title="Peak voltage by control", ylabel="max V (pu)")
    ax[0].set_ylim(1.0, max(1.06, max(r["v_peak_pu"] for r in out) + 0.01))
    ax[0].tick_params(axis="x", rotation=20)
    ax[1].bar(labels, [r["curtailed_kwh"] for r in out], color="orange")
    ax[1].set(title="Curtailed energy by control", ylabel="kWh/day")
    ax[1].tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(RESULTS / "e3_ablation.png", dpi=110)
    plt.close(fig)
    print(f"  wrote results/e3_ablation.png")
    return out


# --------------------------------------------------------------------------- E4
async def exp4_scalability() -> List[Dict[str, Any]]:
    print("E4 scalability ...")
    sizes = [10, 20, 40, 60, 100, 150, 200]
    out: List[Dict[str, Any]] = []
    for n in sizes:
        eng = build_engine(n, {"BUS_PV_CAPACITY_MIN_KW": "10",
                               "BUS_PV_CAPACITY_MAX_KW": "10"})
        rows = await run_day(eng, ticks=24)  # shorter run; timing only
        ms = sorted(r["tick_ms"] for r in rows)
        median = ms[len(ms) // 2]
        out.append({
            "num_meters": n,
            "median_tick_ms": median,
            "p95_tick_ms": ms[int(len(ms) * 0.95)],
        })
        print(f"  n={n:>3}  median={median:.1f} ms")
    write_csv("e4_scalability", out)

    xs = [r["num_meters"] for r in out]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(xs, [r["median_tick_ms"] for r in out], "o-", label="median")
    ax.plot(xs, [r["p95_tick_ms"] for r in out], "s--", label="p95", alpha=0.6)
    ax.set(title="Per-tick solve time vs fleet size",
           xlabel="meters", ylabel="ms / tick")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "e4_scalability.png", dpi=110)
    plt.close(fig)
    print(f"  wrote results/e4_scalability.png")
    return out


async def main() -> None:
    await exp1_diurnal()
    await exp2_penetration()
    await exp3_ablation()
    await exp4_scalability()
    print("\nDone. Results in experiments/results/")


if __name__ == "__main__":
    asyncio.run(main())
