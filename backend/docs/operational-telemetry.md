# Operational telemetry — SCADA grid/microgrid state egress

This document describes the **operational-telemetry** egress: a second, independent
output path that ships the **operator/SCADA-facing grid and microgrid state** the
metering egress cannot carry — per-zone frequency, island/breaker status, fault
counters, DER curtailment, transformer loading/tap, tie-switch state.

> Related: metering egress (the *other* path) is the DLMS/COSEM OBIS frame in
> [`realtime-telemetry.md`](realtime-telemetry.md) and the aggregator section of
> [`../CLAUDE.md`](../CLAUDE.md); the grid/microgrid state itself is produced by
> the engine documented in [`multi-zone-microgrid.md`](multi-zone-microgrid.md).
> Doc index: [`README.md`](README.md).

> Conventions: claims are cited to `file:line` into
> `backend/src/smart_meter_simulator/`. Line numbers drift — re-verify before publishing.

---

## 1. Why a second egress

**DLMS/COSEM (IEC 62056)** is a *revenue-metering* standard. Its OBIS register
space covers energy, power, demand, power factor, and tariff — what a physical
meter measures. It has **no codes** for grid-edge / microgrid concepts:

| Signal | In OBIS? |
|---|---|
| energy import/export, power, PF, demand, TOU tariff | yes |
| meter-local frequency, voltage | yes |
| microgrid **zone** | no (sent as a custom `zone_code` string, a routing hint only) |
| **island / breaker** status | no |
| **per-zone** frequency | no |
| DER **curtailment** (volt-watt) / reactive support (volt-VAR) | no |
| transformer **tap / loading** | no |
| **tie-switch** state, fault/islanded-bus counters | no |

A real meter does not know it sits in an islanded microgrid zone — that is
**operator state**, not meter state. So rather than fake it as bogus meter
registers, the simulator emits it over the protocol family built for it:
**DNP3 (IEEE 1815)** / **IEC 60870-5-104** SCADA telemetry.

See [`multi-zone-microgrid.md`](multi-zone-microgrid.md) §6 for the matching
discussion of what DLMS *does* carry, and the standards map below for where each
domain belongs.

### Standards map (which protocol owns what)

| Domain | Standard | Manages |
|---|---|---|
| Revenue metering | **DLMS/COSEM (IEC 62056)** | energy/power/PF/demand/tariff (the OBIS frame) |
| Operational telemetry | **DNP3 (IEEE 1815) / IEC 60870-5-104** | bus V, frequency, breaker/switch status, fault flags ← *this doc* |
| DER control | **IEEE 2030.5 / SunSpec Modbus** | curtailment, volt-VAR/volt-watt commands, anti-islanding |
| Substation/feeder automation | **IEC 61850 (GOOSE/MMS) + CIM** | switchgear, tie-switch ops, protection, network model |
| Demand response | **OpenADR 2.0b/3.0** | DR event signaling (maps to the zone load-shed) |

This module implements the **operational-telemetry** row (monitor direction).

---

## 2. The point model (`transport/operational_telemetry.py`)

The core is a **pure mapping**, `summary_to_points(summary)`, from an engine tick
summary to a flat list of typed points. Each point carries **both** a DNP3 group
and the matching IEC 60870-5-104 ASDU type id, so one mapping serves either
outstation:

| DNP3 group | IEC-104 ASDU | Used for |
|---|---|---|
| `AI` (analog input) | `M_ME_NC` (13) short-float | measured analogs (frequency, kW, %) |
| `BI` (binary input) | `M_SP_NA` (1) single-point | status bits (island, breaker, switch) |
| `CTR` (counter) | `M_ME_NB` (11) scaled int | contingency counters |

Each point: `{index, name, dnp3_group, iec104_asdu, value}`.

### Points emitted per tick

**System analog inputs** (feeder-wide, indices 0–6):
`grid_frequency_hz`, `total_losses_kw`, `total_curtailed_kw`,
`total_reactive_support_kvar`, `transformer_loading_pct`,
`transformer_tap_pos`, `total_dr_shed_kw`.

**System counters** (contingency, indices 0–2):
`fault_count`, `islanded_bus_count`, `active_dr_events`.

**Per-zone** (one set per zone, addressable by zone code):
| name | type | index | source |
|---|---|---|---|
| `zone_<n>_frequency_hz` | AI | `100 + n` | decoupled per-zone frequency |
| `zone_<n>_islanded` | BI | `0 + n` | electrical island (zone dark) |
| `zone_<n>_breaker_open` | BI | `1000 + n` | commanded island (PCC open) |

**Per-switch** (tie/sectionalizer, index `2000 + i`):
`switch_<name>_closed` (BI).

Indices are offset by a deterministic base per category so a master can address
`zone <code>` / `switch <name>` consistently across ticks.

---

## 3. Transport and lifecycle

`OperationalTelemetryEmitter` mirrors the DLMS emitter and the persistence stores:

- **Consumes the tick summary** (not per-meter readings). The engine threads
  tie-switch status into the summary before emitting (`core/engine.py`, tick
  egress) since switches are not part of the canonical summary.
- **Non-blocking**, fire-and-forget per tick; **drops a tick if the prior batch is
  still in flight** (a slow collector throttles cadence, never backs up the loop).
- **Never raises into the tick** — a send failure increments
  `operational_emit_failed_total` and is swallowed.
- **Optional / config-gated**, default off.

Two transports are provided; select with `OPERATIONAL_TRANSPORT`
(`build_operational_transport`):

**`json`** (default) — `OperationalTelemetryClient`, a thin **JSON-collector POST**
(`POST {url}/operational/telemetry` with `{timestamp, points}`). Dependency-free.

**`iec104`** — `Iec104OutstationTransport`, a **real IEC 60870-5-104 outstation**
backed by the optional `c104` extra (lib60870). It runs a server a SCADA master
connects to; each tick updates the outstation's information objects. The `c104`
import is deferred to `astart()`, so the module loads (and `json` works) without
the extra. IEC-104 information object addresses (IOA) must be unique per station,
but the point map reuses small per-category indices — so IOAs are assigned here by
**point name** on first sight (sequential, cached), decoupling the wire address
from the JSON index. ASDU type → `c104.Type` (`M_ME_NC`/`M_SP_NA`/`M_ME_NB`); BI
points set a bool, AI/CTR a float.

> **Status — `iec104` is unverified live.** Install the extra with
> `uv sync --extra iec104`. `c104` ships wheels for **CPython 3.11–3.13**; there is
> no 3.14 wheel yet and the sdist did not build in this environment, so the
> outstation could not be exercised here. The code follows the `c104` 2.x API and
> its construction / IOA assignment / value typing are unit tested with `c104`
> faked; **live master interop is manual and unconfirmed.** The default `json`
> transport is fully tested.

Either way, the **mapping** (`summary_to_points`) is the reusable, standards-aligned
part — a different outstation (e.g. `pydnp3` for DNP3) slots in behind it unchanged.

### Engine wiring (`core/engine.py`)
Four touch points, parallel to the DLMS emitter: construct in `__init__` (gated on
`operational_telemetry_enabled`), `start()` in the engine start, `emit(summary)` in
the per-tick egress (after the summary is built, with switch status merged in),
`close()` on stop.

---

## 4. Configuration

```bash
OPERATIONAL_TELEMETRY_ENABLED=false        # default off
OPERATIONAL_TRANSPORT=json                 # json | iec104
OPERATIONAL_OUTSTATION_URL=http://localhost:4040   # json collector endpoint
OPERATIONAL_EMIT_EVERY=1                    # tick cadence thinning (>=1)
OPERATIONAL_IEC104_PORT=2404                # iec104 outstation listen port
OPERATIONAL_IEC104_COMMON_ADDRESS=1         # iec104 station common address
```

`config/settings.py` (`operational_telemetry_enabled` / `operational_transport` /
`operational_outstation_url` / `operational_emit_every` / `operational_iec104_port`
/ `operational_iec104_common_address`). The `iec104` extra:
`uv sync --extra iec104` (Python 3.11–3.13).

---

## 5. Example — a 2-zone islanded tick

Islanding zone 1 (DER, self-supporting) and zone 2 (no DER, dark), one tie open,
`summary_to_points` yields (selected):

```
grid_frequency_hz       = 49.5      (AI)
fault_count             = 2         (CTR)
islanded_bus_count      = 2         (CTR)
zone_1_frequency_hz     = 50.44     (AI)   # decoupled island frequency
zone_1_breaker_open     = True      (BI)   # PCC open (commanded)
zone_1_islanded         = False     (BI)   # held up by local DER
zone_2_frequency_hz     = 49.5      (AI)
zone_2_breaker_open     = True      (BI)
zone_2_islanded         = True      (BI)   # no DER -> dark
switch_tie_1_2_closed   = False     (BI)
```

A SCADA master reading these sees exactly what an operator needs: which zones are
commanded open, which are actually de-energized, their individual frequencies, and
the switch positions available to restore them.

---

## 6. What this is not

- **DNP3 not implemented** — a real **IEC-104** outstation exists (`c104` extra,
  unverified live, see §3); a DNP3 outstation (`pydnp3`) would slot in behind the
  same `summary_to_points` mapping but is not written.
- **Not control direction** — monitor (telemetry out) only. Remote SCADA *control*
  (master → sim, e.g. command a zone to island via `C_SC_NA`) would map back onto
  `ZoneController.island()`; that symmetric path is not implemented here.
- **No parent consumer yet** — the Aggregator Bridge ingests DLMS, not operational
  telemetry. This needs a SCADA-side sink (or a new bridge ingest path) to land.

---

## 7. Tests

`tests/test_operational_telemetry.py` — point-map typing (DNP3 group + ASDU id),
per-zone index addressing, switch points, no-zone (system-only) case, and emitter
behaviour (no-op before start, send after start, drop-tick when a batch is in
flight, failure never raises).
