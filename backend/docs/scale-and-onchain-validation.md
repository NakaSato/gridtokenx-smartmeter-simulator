# Scale and On-Chain Mint Validation

Two test cases that exercise the simulator beyond unit/E2E coverage: a fleet-size
solver-throughput benchmark, and a live proof that simulated surplus actually
mints on-chain through the full GridTokenX stack. Both live under
`backend/experiments/`, alongside the existing research-paper harness
(`run_experiments.py`, E1–E4 — see
[`backend-core-features-academic-report.md`](backend-core-features-academic-report.md)).
This page documents a fifth and sixth case, E5 and E6.

## E5 — Fleet-size scale benchmark (`run_large_scale.py`)

**What it measures.** Per-tick wall-clock cost of reading generation + the
fixed-topology power-flow solve as fleet size grows, independent of any
network egress. Drives `SimulationEngine.tick()` directly — it does **not**
call `start()`, so no aggregator emitter, IAM onboarding, or chain interaction
happens. This is a pure solver/throughput benchmark, the same pattern as
`run_experiments.py`'s E1–E4 (`run_large_scale.py` docstring; mirrors
`backend/experiments/run_experiments.py:60-78`).

**Setup.** `FLEET_SIZES = [10_000, 50_000, 100_000]`, PV assigned **randomly per
meter** (not "every Nth bus") via `SOLAR_PROSUMER_RATIO=0.10` ,
`HYBRID_PROSUMER_RATIO=0.0`, `GRID_CONSUMER_RATIO=0.90`, 4 ticks/case, fixed
80-bus reference topology (`grid_bus_network.glm`).

This required a fix: `MeterGenerator.generate_ieee_meters`
(`src/smart_meter_simulator/meter_generator.py:127-141`) previously hardcoded
the prosumer/consumer/hybrid split to `weights=[0.7, 0.2, 0.1]` for any
topology-driven fleet (i.e. every `glm:` run, which is all of them), silently
ignoring `SOLAR_PROSUMER_RATIO`/`GRID_CONSUMER_RATIO`/`HYBRID_PROSUMER_RATIO`.
Fixed to read those three config values as the `random.choices` weights, so
"N% random PV" is now actually configurable for topology-backed fleets.

**Results** (`backend/experiments/results/e5_scale_summary.csv`):

| Meters | PV meters | PV % | `start()`-free build | Median tick | p95 tick |
| --- | --- | --- | --- | --- | --- |
| 10,000 | 990 | 9.90% | 4.0 s | 16.5 s | 17.7 s |
| 50,000 | 4,906 | 9.81% | 3.3 s | 97.6 s | 107.8 s |
| 100,000 | 9,970 | 9.97% | 5.2 s | 230.4 s | 397.5 s |

PV percentage converges to the configured 10% target as fleet size grows (law
of large numbers over the per-meter `random.choices` draw), confirming the
ratio fix is wired correctly. Tick time scales mildly super-linearly with
fleet size (100k is ~14× the 10k tick time for 10× the meters) — reading
generation (`ReadingManager.generate_all`, dispatched via `asyncio.to_thread`,
still single-threaded CPU work) is the bottleneck, not the power-flow solve
(fixed at 80 buses regardless of meter count).

**Run it:**

```bash
cd backend
uv run python experiments/run_large_scale.py
```

## E6 — Live on-chain mint proof (`run_live_onchain_proof.py`)

**What it measures.** Whether simulated surplus energy actually reaches an
on-chain mint, end to end through the real GridTokenX stack — not just that
the simulator computes correct net-surplus numbers. Unlike E5, this script
calls `eng.start()` (`src/smart_meter_simulator/core/engine.py:352`), which
wires the live path:

```
eng.start()
  -> IAM onboarding per meter owner (register -> verify -> login, on-chain PDA)
  -> Ed25519 device-key registration in the bridge's Redis registry
eng.tick()  (per tick, AggregatorBridgeEmitter, engine.py:200)
  -> mTLS + AES-256-GCM encrypted, signed OBIS/DLMS POST per meter
  -> bridge: signature verify -> zone Redis stream -> settlement-bin aggregate
  -> on settlement-window close: real Ed25519-signed Solana mint tx via Chain Bridge
```

This is deliberately small (default 100 meters, 5 ticks) — IAM onboarding is
one HTTP round-trip per owner and a real signed Solana transaction per
settlement window, so it does not scale to E5's 10k/50k/100k (an honest
100k-meter live run would need ~28h of onboarding alone at 1/sec against a
single shared dev validator — see the E5/E6 scope discussion in chat history,
not reproduced here).

**Prerequisites.** `aggregator-bridge`, `redis`, `iam-service`, `chain-bridge`,
`vault` healthy, plus a live `solana-test-validator` with Chain Bridge pointed
at it. mTLS/encryption/IAM-onboarding config comes from `backend/.env`
(`AGGREGATOR_TLS_CA`/`_CLIENT_CERT`/`_CLIENT_KEY`, `AGGREGATOR_ENCRYPT_ENABLED`,
`AGGREGATOR_KEY_ROTATION_ENABLED`, `AGGREGATOR_IAM_ONBOARD_ENABLED`) — the
bridge runs `AGGREGATOR_REQUIRE_SECURE=true` in this environment, so
plaintext/unencrypted ingest is refused with 426.

**Run it:**

```bash
cd backend
uv run python experiments/run_live_onchain_proof.py --meters 100 --ticks 5
```

**Result.** 100 meters onboarded in ~11 s; 5 ticks completed (~400 ms–1.7 s
each). Bridge logs confirmed real signature verification and zone
dissemination for every ingested reading, and — the actual proof point —
**140 real on-chain mint transactions across 20 unique meters**, each with a
genuine Solana transaction signature and slot number, e.g.:

```
⚡ minted 0.08568 kWh surplus for meter c07a30f2-edd4-453b-90f0-fd0a750cab75
   (sig=3NbmxvqEKRLfM2yEYJLNy7axVcibwBXTzVbDAPAhdbNaN643ZPdVJa3mAvnxuqK6Y2dZ64BRdKK29bM1ttyjV7kw, slot=1424)
```

This confirms the simulator's net-surplus computation, the DLMS/COSEM signed
egress, the bridge's settlement aggregation, and Chain Bridge's mint signing
all agree end to end against a live validator — the gap E5 deliberately does
not test (E5 never calls `start()`, so it never touches the bridge or chain at
all).

## Related fix surfaced during this validation

Driving live E2E traffic against the IAM service during E6 setup (account
registration/onboarding for 100 throwaway dev users) surfaced a brute-force
lockout bug in `gridtokenx-iam-service`: `CacheService::increment_with_ttl`'s
Redis `MULTI`/`EXEC` pipeline returned 2 non-ignored replies but was
destructured into a 1-tuple, so every call failed to deserialize and silently
fell back to attempt-count 0 — the lockout threshold (5 failed logins) was
never reachable. Fixed in `gridtokenx-iam-service` commit `cca8d6b`
(`crates/iam-persistence/src/cache.rs:121-134`); not part of this repo, noted
here because it was found via this validation work. See that repo's commit
message for the full root-cause writeup.
