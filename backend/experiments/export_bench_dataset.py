"""Export a seeded, full-physics telemetry dataset for the on-chain community

benchmark (gridtokenx-anchor/scripts/bench-community-month.ts).

Runs the ``SimulationEngine`` offline at max speed with the full GLM grid model
(load + solar device models, power flow, losses, tap control, frequency droop)
over a whole-month-in-the-past window, and writes the exact four-file schema the
bench replayer consumes:

    meters.json   [{idx, chain_id, meter_type, solar}]
    readings.jsonl one line/reading {m, t, g, c}   (g/c = INTEGER Wh)
    daily.json    [day][meterIdx] = {g, c, s}       (kWh floats)
    meta.json     run metadata + energy totals + grid-physics per-day aggregates

The fleet is forced to an EXACT prosumer count P (the generator's ratio path is
stochastic): N-P all-consumer meters + P solar prosumers chosen by a seeded RNG.

Run:
    uv run python experiments/export_bench_dataset.py \
        --meters 80 --prosumers 12 --days 30 --seed 42 --interval 900 --out DIR
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

TOPOLOGY = "glm:src/smart_meter_simulator/data/grids/grid_bus_network.glm"


def _bootstrap_env(interval: int, seed: int) -> None:
    """Force the config singleton into a deterministic, sink-free export mode.

    Must run BEFORE any ``smart_meter_simulator`` engine import so the settings
    singleton is built from these values (mirrors run_large_scale._fresh_config).
    """
    from smart_meter_simulator.config import settings

    env = {
        "GRID_TOPOLOGY": TOPOLOGY,
        "SIMULATION_INTERVAL": str(interval),
        "PV_MODEL_ENABLED": "true",
        # ratio-weighted random PV path (not one-meter-per-bus) frees the fleet
        # size from the topology bus count — we assign PV explicitly afterward.
        "PV_ON_EVERY_BUS": "false",
        "RANDOM_SEED": str(seed),
        "METER_REGISTRY": "",
        # All-consumer ratios: we override meter types by hand, so keep the
        # generator's stochastic type draw out of the picture.
        "SOLAR_PROSUMER_RATIO": "0.0",
        "HYBRID_PROSUMER_RATIO": "0.0",
        "GRID_CONSUMER_RATIO": "1.0",
        # Kill every egress / persistence sink so the offline loop is pure CPU.
        "TELEMETRY_SOURCE": "synthetic",
        "AGGREGATOR_DLMS_ENABLED": "false",
        "OPERATIONAL_TELEMETRY_ENABLED": "false",
        "POSTGIS_ENABLED": "false",
        "INFLUX_ENABLED": "false",  # default is True — must be forced off
    }
    for k, v in env.items():
        os.environ[k] = v
    settings._config_instance = None


def _build_configs(topology: Any, num_meters: int, prosumers: int, seed: int):
    """Build ``num_meters`` fleet configs with EXACTLY ``prosumers`` solar prosumers.

    Mirrors core/engine.py's generate_ieee_meters call, then rewrites meter
    type/solar so a deterministic P-subset are Solar_Prosumers and the rest are
    Grid_Consumers. Returns (configs, chain_ids, prosumer_idx).
    """
    from smart_meter_simulator.config import MeterType
    from smart_meter_simulator.meter_generator import MeterGenerator

    # Seed the global RNG that generate_ieee_meters / _create_meter_config draw
    # from (UUIDs, base load/gen, solar efficiency) so the fleet is reproducible.
    random.seed(seed)

    generator = MeterGenerator(num_meters)
    pv_capacity_by_node = {pv.bus: pv.capacity_kw for pv in topology.pvs}
    zone_by_node = {b.name: b.zone for b in topology.buses if b.zone}
    zone_code_by_node = {b.name: b.zone_code for b in topology.buses if b.zone_code}
    configs = generator.generate_ieee_meters(
        num_nodes=len(topology.buses),
        target_meters=num_meters,
        pv_on_every_bus=False,
        node_ids=[b.name for b in topology.buses],
        pv_capacity_kw_by_node=pv_capacity_by_node,
        zone_by_node=zone_by_node,
        zone_code_by_node=zone_code_by_node,
    )
    assert len(configs) == num_meters, f"generator returned {len(configs)} != {num_meters}"

    # Deterministic exact prosumer subset + deterministic solar sizing.
    prosumer_idx = sorted(random.Random(seed ^ 0x50F7).sample(range(num_meters), prosumers))
    cap_rng = random.Random(seed ^ 0x50A2)
    prosumer_set = set(prosumer_idx)
    for i, c in enumerate(configs):
        if i in prosumer_set:
            c["meter_type"] = MeterType.SOLAR_PROSUMER.value  # "Solar_Prosumer"
            c["user_type"] = "Prosumer"
            c["has_solar"] = True
            c["solar_capacity"] = cap_rng.uniform(5.0, 15.0)
            c["panel_efficiency"] = c.get("solar_efficiency", 0.18)
        else:
            c["meter_type"] = MeterType.GRID_CONSUMER.value  # "Grid_Consumer"
            c["user_type"] = "Consumer"
            c["has_solar"] = False
            c["solar_capacity"] = 0.0
            c["panel_efficiency"] = 0.0

    # Parallel chain-id list (oracle PDA seed, <=32 bytes).
    chain_ids = [f"SIM{seed}-{i:04d}" for i in range(num_meters)]
    for cid in chain_ids:
        assert len(cid.encode("utf-8")) <= 32, f"chain_id too long: {cid}"
    return configs, chain_ids, prosumer_idx


def _pick_day_weather(days: int, seed: int, fixed: str | None = None) -> List[str]:
    """One weather condition per day.

    ``fixed`` (--weather) pins EVERY day to a single condition, disabling the
    stochastic per-day draw — isolates the load/PV signal from weather variance
    for a controlled test case. When ``None`` days are drawn from the configured
    weather weights (seeded, reproducible).
    """
    from smart_meter_simulator.config import get_config

    weights = get_config().weather_weights  # {WeatherCondition: weight}
    valid = {w.value for w in weights.keys()}
    if fixed is not None:
        if fixed not in valid:
            raise SystemExit(f"--weather {fixed!r} invalid; choose from {sorted(valid)}")
        return [fixed] * days
    population = [w.value for w in weights.keys()]
    w = list(weights.values())
    wrng = random.Random(seed ^ 0x7EA)
    return [wrng.choices(population, weights=w, k=1)[0] for _ in range(days)]


async def run_export(args: argparse.Namespace) -> None:
    _bootstrap_env(args.interval, args.seed)

    # Imports AFTER env bootstrap so the config singleton reflects our settings.
    from smart_meter_simulator.core.engine import SimulationEngine
    from smart_meter_simulator.core.topology_factory import load_topology_spec
    from smart_meter_simulator.devices.ami import SmartMeter

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    interval = args.interval
    ticks_per_day = 86400 // interval
    if ticks_per_day * interval != 86400:
        raise SystemExit(f"interval {interval}s must evenly divide a day (86400s)")
    total_ticks = args.days * ticks_per_day
    N = args.meters

    print(f"loading topology {TOPOLOGY} ...")
    topology = load_topology_spec(TOPOLOGY)
    print(f"  {len(topology.buses)} buses, {len(topology.pvs)} PV nodes")

    configs, chain_ids, prosumer_idx = _build_configs(topology, N, args.prosumers, args.seed)
    prosumer_set = set(prosumer_idx)
    day_weather = _pick_day_weather(args.days, args.seed, args.weather)
    print(f"fleet: {N} meters, {args.prosumers} prosumers (idx {prosumer_idx[:8]}{'...' if len(prosumer_idx) > 8 else ''})")

    # ── Fleet sharding (worker handles a contiguous GLOBAL index range) ─────────
    # Configs for the WHOLE fleet are always built (prosumer subset + solar sizing
    # + chain_ids are seeded on the full N and must not shift when sharding), but
    # only this shard's meters are instantiated + ticked. Written readings carry
    # the GLOBAL index. Valid only at stride0 (independent meters) — enforced.
    shard_start = int(args.shard_start)
    shard_count = N - shard_start if args.shard_count < 0 else int(args.shard_count)
    if shard_start < 0 or shard_start >= N or shard_count <= 0 or shard_start + shard_count > N:
        raise SystemExit(f"bad shard range: start={shard_start} count={shard_count} N={N}")
    is_shard = shard_count != N
    if is_shard and int(args.grid_solve_stride) != 0:
        raise SystemExit("sharding (--shard-count < N) requires --grid-solve-stride 0")
    shard_meters = range(shard_start, shard_start + shard_count)
    if is_shard:
        print(f"  SHARD: global meters [{shard_start}, {shard_start + shard_count}) of {N}")

    meters = [SmartMeter(configs[gi]) for gi in shard_meters]
    eng = SimulationEngine(meters=meters, topology=topology)
    eng.grid.initialize_network(eng.meters)
    # Throttle the per-tick pandapower solve (the dominant cost). Meter g/c are
    # device+weather driven; voltage is a small correction → stride speeds gen
    # near-linearly with little effect on readings.jsonl. 0=never, 1=every tick.
    eng.grid_solve_stride = int(args.grid_solve_stride)
    if eng.grid_solve_stride != 1:
        print(f"  grid-solve-stride: {eng.grid_solve_stride} "
              f"({'never solve (nominal 1.0 pu)' if eng.grid_solve_stride == 0 else f'solve every {eng.grid_solve_stride} ticks'})")

    # Window start. For a REPRODUCIBLE research dataset the start is an explicit
    # fixed UTC midnight (--start-date) so calendar-dependent downstream logic
    # (weekday/weekend + peak-hour TOU classification keyed on reading `t`) is
    # byte-identical across run dates — not tied to when the export happens to run.
    # When --start-date is omitted we fall back to the legacy floating window
    # (midnight UTC (days+1) days ago). Either way the past-guard below still fires
    # (the oracle rejects future timestamps).
    now = datetime.now(timezone.utc)
    now_ts = int(now.timestamp())
    if args.start_date:
        try:
            start = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise SystemExit(f"--start-date must be YYYY-MM-DD: {e}")
    else:
        midnight_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = midnight_today - timedelta(days=args.days + 1)
    start_ts = int(start.timestamp())
    eng.current_sim_time = start

    # ── Accumulators ──────────────────────────────────────────────────────────
    # daily[day][meter] = [g_kwh, c_kwh, s_kwh]
    daily = [[[0.0, 0.0, 0.0] for _ in range(N)] for _ in range(args.days)]
    energy = {"generated": 0.0, "consumed": 0.0, "surplus": 0.0}
    any_gen = [False] * N  # did meter ever report g > 0?
    readings_written = 0
    # Regulatory per-prosumer daily grid-export cap (kWh). Excess generation is
    # curtailed (g reduced before any accumulation → conservation holds). Only
    # applied to prosumers; consumers never export. 0.0 = disabled.
    export_cap = float(args.max_daily_export)
    day_export = [0.0] * N          # kWh already fed to grid this sim-day, per meter
    export_curtailed_total = 0.0    # kWh generation dropped by the cap (all meters, all days)
    # Per-day grid-physics accumulators (from eng.last_tick_summary + bus_voltages).
    gp = [
        {
            "losses_kwh": 0.0,
            "curtailed_kwh": 0.0,
            "transformer_peak_loading_pct": 0.0,
            "tap_min": None,
            "tap_max": None,
            "freq_min": None,
            "freq_max": None,
            "v_min": None,
            "v_max": None,
            "_v_mean_sum": 0.0,
            "_v_mean_n": 0,
        }
        for _ in range(args.days)
    ]

    def _upd(cur, val, fn):
        return val if cur is None else fn(cur, val)

    readings_path = out / "readings.jsonl"
    t0 = time.perf_counter()
    with readings_path.open("w") as rf:
        for k in range(total_ticks):
            day = k // ticks_per_day
            if k % ticks_per_day == 0:
                eng.weather_mode = day_weather[day]
                if export_cap > 0.0:
                    day_export = [0.0] * N  # reset per-meter daily export budget

            t_sec = start_ts + k * interval
            readings = await eng.tick()

            # Verify tick() preserves meter-list order (bench indexes by position).
            if k == 0:
                for i, r in enumerate(readings):
                    if r.meter_id != meters[i].meter_id:
                        raise AssertionError(
                            f"reading order mismatch at {i}: {r.meter_id} != {meters[i].meter_id}"
                        )

            for i, r in enumerate(readings):
                gi = shard_start + i  # GLOBAL meter index (i is shard-local position)
                g_kwh = float(r.energy_generated)
                c_kwh = float(r.energy_consumed)

                # Daily grid-export cap: curtail generation so this meter's
                # cumulative feed-in (Σ max(0, g-c)) never exceeds `export_cap`
                # kWh/day. Curtail g BEFORE accumulation so g/surplus/energy all
                # reflect the curtailed value → daily-Σ conservation self-check holds.
                if export_cap > 0.0 and gi in prosumer_set:
                    export_now = g_kwh - c_kwh
                    if export_now > 0.0:
                        remaining = export_cap - day_export[gi]
                        allowed = max(0.0, min(export_now, remaining))
                        curtail = export_now - allowed
                        if curtail > 0.0:
                            g_kwh -= curtail  # generation not produced
                            export_curtailed_total += curtail
                        day_export[gi] += allowed

                g_wh = round(g_kwh * 1000)
                c_wh = round(c_kwh * 1000)
                rf.write(json.dumps({"m": gi, "t": t_sec, "g": g_wh, "c": c_wh}) + "\n")
                readings_written += 1
                d = daily[day][gi]
                d[0] += g_kwh
                d[1] += c_kwh
                d[2] += max(0.0, g_kwh - c_kwh)
                energy["generated"] += g_kwh
                energy["consumed"] += c_kwh
                energy["surplus"] += max(0.0, g_kwh - c_kwh)
                if g_wh > 0:
                    any_gen[gi] = True

            # Grid-physics per-day roll-up from this tick's summary.
            s = eng.last_tick_summary
            g = gp[day]
            g["losses_kwh"] += float(s.get("total_losses_kw", 0.0)) * interval / 3600.0
            g["curtailed_kwh"] += float(s.get("total_curtailed_kw", 0.0)) * interval / 3600.0
            g["transformer_peak_loading_pct"] = max(
                g["transformer_peak_loading_pct"], float(s.get("transformer_loading_pct", 0.0))
            )
            tap = int(s.get("transformer_tap_pos", 0))
            g["tap_min"] = _upd(g["tap_min"], tap, min)
            g["tap_max"] = _upd(g["tap_max"], tap, max)
            freq = float(s.get("frequency_hz", eng.config.freq_nominal_hz))
            g["freq_min"] = _upd(g["freq_min"], freq, min)
            g["freq_max"] = _upd(g["freq_max"], freq, max)
            volts = list(eng.grid.bus_voltages.values())
            if volts:
                vmin, vmax = min(volts), max(volts)
                g["v_min"] = _upd(g["v_min"], vmin, min)
                g["v_max"] = _upd(g["v_max"], vmax, max)
                g["_v_mean_sum"] += sum(volts) / len(volts)
                g["_v_mean_n"] += 1

            if (k + 1) % max(1, ticks_per_day) == 0:
                el = time.perf_counter() - t0
                print(
                    f"  day {day + 1}/{args.days} done  weather={day_weather[day]}  "
                    f"tick {k + 1}/{total_ticks}  {el:.1f}s  ({(k + 1) / el:.0f} ticks/s)"
                )

    elapsed = time.perf_counter() - t0
    end_ts = start_ts + (total_ticks - 1) * interval
    ticks_per_sec = total_ticks / elapsed if elapsed > 0 else 0.0

    # ── Finalize grid-physics per-day (compute mean voltage, drop scratch) ─────
    grid_physics_days = []
    for g in gp:
        vmean = (g["_v_mean_sum"] / g["_v_mean_n"]) if g["_v_mean_n"] else None
        grid_physics_days.append(
            {
                "losses_kwh": round(g["losses_kwh"], 4),
                "curtailed_kwh": round(g["curtailed_kwh"], 4),
                "transformer_peak_loading_pct": round(g["transformer_peak_loading_pct"], 3),
                "tap_min": g["tap_min"],
                "tap_max": g["tap_max"],
                "freq_min": round(g["freq_min"], 4) if g["freq_min"] is not None else None,
                "freq_max": round(g["freq_max"], 4) if g["freq_max"] is not None else None,
                "voltage_min_pu": round(g["v_min"], 5) if g["v_min"] is not None else None,
                "voltage_mean_pu": round(vmean, 5) if vmean is not None else None,
                "voltage_max_pu": round(g["v_max"], 5) if g["v_max"] is not None else None,
            }
        )

    # prosumer-days with daily surplus > 10 kWh
    prosumer_days_gt10 = sum(
        1 for d in range(args.days) for i in prosumer_idx if daily[d][i][2] > 10.0
    )

    # ── Write meters.json ──────────────────────────────────────────────────────
    meters_out = [
        {
            "idx": i,
            "chain_id": chain_ids[i],
            "meter_type": configs[i]["meter_type"],
            "solar": bool(configs[i]["has_solar"]),
        }
        for i in range(N)
    ]
    (out / "meters.json").write_text(json.dumps(meters_out, indent=2))

    # ── Write daily.json ({g,c,s} kWh floats) ──────────────────────────────────
    daily_out = [
        [
            {"g": round(daily[d][i][0], 6), "c": round(daily[d][i][1], 6), "s": round(daily[d][i][2], 6)}
            for i in range(N)
        ]
        for d in range(args.days)
    ]
    (out / "daily.json").write_text(json.dumps(daily_out))

    # ── Write meta.json ────────────────────────────────────────────────────────
    # Integrity hash of the canonical reading stream so a paper can assert the
    # dataset was reproduced byte-for-byte from (seed, start_date, args).
    readings_sha256 = hashlib.sha256(readings_path.read_bytes()).hexdigest()
    meta = {
        "meters": N,
        "prosumers": args.prosumers,
        "days": args.days,
        "readings": readings_written,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "step_sec": interval,
        "interval": interval,
        "energy_kwh": {
            "generated": round(energy["generated"], 6),
            "consumed": round(energy["consumed"], 6),
            "surplus": round(energy["surplus"], 6),
        },
        "day_weather": day_weather,
        "random_seed": args.seed,
        "start_date": args.start_date or None,
        "weather_fixed": args.weather,
        "prosumer_idx": prosumer_idx,
        "prosumer_days_surplus_gt_10kwh": prosumer_days_gt10,
        "export_cap_kwh": export_cap if export_cap > 0.0 else None,
        "export_curtailed_kwh": round(export_curtailed_total, 6),
        "grid_solve_stride": int(args.grid_solve_stride),
        "shard_start": shard_start,
        "shard_count": shard_count,
        "is_shard": is_shard,
        "grid_physics": {"days": grid_physics_days},
        "topology": topology.source_path or TOPOLOGY,
        "readings_sha256": readings_sha256,
        "argv": sys.argv[1:],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2))

    # ── Self-checks (fail hard) ────────────────────────────────────────────────
    def _check(cond: bool, msg: str) -> None:
        if not cond:
            raise SystemExit(f"SELF-CHECK FAILED: {msg}")

    expected = shard_count * total_ticks
    _check(readings_written == expected, f"readings {readings_written} != expected {expected}")

    daily_g = sum(daily[d][i][0] for d in range(args.days) for i in range(N))
    daily_c = sum(daily[d][i][1] for d in range(args.days) for i in range(N))
    tol = 0.001
    _check(
        abs(daily_g - energy["generated"]) <= tol * max(1e-9, energy["generated"]),
        f"daily Σg {daily_g} vs meta {energy['generated']} > 0.1%",
    )
    _check(
        abs(daily_c - energy["consumed"]) <= tol * max(1e-9, energy["consumed"]),
        f"daily Σc {daily_c} vs meta {energy['consumed']} > 0.1%",
    )
    for i in shard_meters:  # only meters this worker actually ran
        if i in prosumer_set:
            _check(any_gen[i], f"prosumer {i} never generated")
        else:
            _check(not any_gen[i], f"consumer {i} has non-zero generation")
    if export_cap > 0.0:
        cap_tol = export_cap + 1e-6
        for d in range(args.days):
            for i in prosumer_idx:
                _check(
                    daily[d][i][2] <= cap_tol,
                    f"prosumer {i} day {d} surplus {daily[d][i][2]:.6f} > cap {export_cap}",
                )
    _check(end_ts < now_ts, f"end_ts {end_ts} not in the past (now {now_ts})")
    _check(len(prosumer_idx) == args.prosumers, f"prosumer_idx len {len(prosumer_idx)} != {args.prosumers}")
    _check(all(len(c.encode("utf-8")) <= 32 for c in chain_ids), "a chain_id exceeds 32 bytes")

    # ── Summary ────────────────────────────────────────────────────────────────
    from collections import Counter

    wcount = Counter(day_weather)
    print("\n=== export complete ===")
    print(f"  out dir       : {out}")
    print(f"  meters        : {N} ({args.prosumers} prosumers, {N - args.prosumers} consumers)")
    print(f"  days x ticks  : {args.days} x {ticks_per_day} = {total_ticks} ticks")
    print(f"  readings      : {readings_written}")
    print(f"  window        : {start.isoformat()} .. ts {end_ts} (all in the past)")
    print(f"  energy kWh    : gen={energy['generated']:.2f}  cons={energy['consumed']:.2f}  surplus={energy['surplus']:.2f}")
    print(f"  prosumer-days surplus>10kWh : {prosumer_days_gt10}")
    if export_cap > 0.0:
        print(f"  export cap    : {export_cap:.2f} kWh/prosumer/day  "
              f"(curtailed {export_curtailed_total:.2f} kWh total)")
    print(f"  weather mix   : {dict(wcount)}")
    print(f"  elapsed       : {elapsed:.1f}s  ({ticks_per_sec:.1f} ticks/s, {readings_written / elapsed:.0f} readings/s)")
    print("  self-checks   : ALL PASSED")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export a seeded full-physics bench dataset.")
    p.add_argument("--meters", type=int, required=True, help="fleet size N")
    p.add_argument("--prosumers", type=int, required=True, help="exact solar-prosumer count P")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--interval", type=int, default=900, help="tick interval seconds")
    p.add_argument("--grid-solve-stride", type=int, default=1,
                   help="pandapower power-flow solve cadence: 1=every tick (full "
                        "grid physics), N=every Nth tick, 0=never (nominal 1.0 pu, "
                        "fastest). Meter g/c barely change; daily grid_physics "
                        "coarsens. Use to hit tight gen-time budgets at 15-min interval.")
    p.add_argument("--shard-start", type=int, default=0,
                   help="first GLOBAL meter index this worker handles (fleet sharding).")
    p.add_argument("--shard-count", type=int, default=-1,
                   help="number of meters this worker handles from --shard-start "
                        "(-1 = the whole remaining fleet = no sharding). ONLY valid "
                        "with --grid-solve-stride 0: at stride0 meters are independent "
                        "(no grid coupling), so a shard's readings equal the full run's "
                        "for those meters. Shard outputs are merged by scripts/merge_shards.py.")
    # Fixed UTC-midnight window start → byte-identical dataset across run dates.
    # Default 2025-01-06 is a Monday, so weekday/weekend + TOU boundaries are
    # stable. Pass "" for the legacy floating (days+1)-ago window.
    p.add_argument("--start-date", type=str, default="2025-01-06",
                   help='fixed UTC window start YYYY-MM-DD (default reproducible); "" = floating')
    p.add_argument("--weather", type=str, default=None,
                   choices=["Sunny", "Partly_Cloudy", "Cloudy", "Overcast", "Rainy"],
                   help="pin every day to ONE condition (disable per-day weather variation)")
    p.add_argument("--out", type=str, required=True, help="output directory")
    p.add_argument("--max-daily-export", type=float, default=0.0,
                   help="per-prosumer daily grid feed-in cap in kWh (regulatory export "
                        "limit). Generation beyond the cap is curtailed (g reduced, never "
                        "produced). 0 = unlimited (legacy behavior).")
    args = p.parse_args()
    if args.prosumers > args.meters:
        raise SystemExit("--prosumers cannot exceed --meters")
    if args.prosumers < 0:
        raise SystemExit("--prosumers must be >= 0")
    return args


if __name__ == "__main__":
    asyncio.run(run_export(parse_args()))
