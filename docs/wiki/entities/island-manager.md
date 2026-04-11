---
title: "Island Manager"
category: entities
created: 2026-04-10
updated: 2026-04-10
sources: ["src/smart_meter_simulator/core/island.py"]
tags: [island, microgrid, black-start, slack]
related: [[Frequency Regulator]], [[VPP Orchestrator]], [[Pandapower Adapter]]
---

# Island Manager

The `IslandManager` handles microgrid islanding — the intentional disconnection from the main grid and autonomous operation of a local network segment — plus reconnection and black start recovery.

## Summary

When the main grid fails or is intentionally isolated, the IslandManager finds the best battery asset to become a grid-forming source, swaps the pandapower slack bus to maintain power flow solvability, and sequences the restoration of critical loads during black start.

## Islanding Process

### Disconnect

```python
def disconnect(self, net, meters, meter_to_bus):
    # 1. Find best grid-forming candidate
    #    Battery with highest SoC
    candidate = max(
        [m for m in meters if m.has_battery],
        key=lambda m: m.battery_soc
    )

    # 2. Disable external grid (main_grid_bus_id = 0)
    net.ext_grid.in_service = False

    # 3. Create virtual slack generator at battery bus
    net.sgen.loc[-1, :] = {
        "bus": meter_to_bus[candidate.meter_id],
        "p_mw": 0.0,
        "q_mvar": 0.0,
        "in_service": True,
        "name": "VPP_Anchor_Slack"
    }
```

### Reconnect

```python
def reconnect(self, net):
    # 1. Re-enable external grid
    net.ext_grid.in_service = True

    # 2. Remove temporary slack generator
    # 3. Reset island state
```

## Black Start Sequence

After total grid collapse:

1. **Stage 1:** Restore critical loads (priority 1) — hospitals, substations
2. **Stage 2:** Energize feeders incrementally
3. **Stage 3:** Reconnect remaining loads
4. **Stage 4:** Synchronize with main grid (if available)

```python
def black_start_sequence(self, vpp):
    # Restore priority 1 resources first
    critical = [r for r in vpp.resources if r.priority == 1]
    for resource in critical:
        vpp.energize(resource)

    # Then expand to remaining
    remaining = [r for r in vpp.resources if r.priority > 1]
    for resource in remaining:
        vpp.energize(resource)
```

## State

```python
@dataclass
class IslandState:
    is_islanded: bool = False
    slack_bus_id: Optional[int] = None
    grid_forming_meter_id: Optional[str] = None
```

## Grid-Forming Selection Criteria

| Criteria | Weight | Description |
|----------|--------|-------------|
| Battery SoC | Primary | Higher SoC = longer island survival |
| Capacity | Secondary | Larger battery = more power headroom |
| Location | Tertiary | Central bus = better voltage support |

## Key Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `main_grid_bus_id` | 0 | External grid connection bus in pandapower |
| `slack_sgen_name` | "VPP_Anchor_Slack" | Temporary slack generator name |

## Islanding Triggers

| Trigger | Type | Description |
|---------|------|-------------|
| Frequency collapse | Automatic | Freq < 47 Hz or > 53 Hz |
| Voltage collapse | Automatic | Voltage < 0.8 pu or > 1.2 pu |
| Manual command | Operator | Intentional islanding for maintenance |
| Protection trip | Automatic | Fault detection on feeder |

## Pandapower Slack Bus Swap

In islanded mode, the external grid (ext_grid) is disabled. Without a slack bus, pandapower cannot solve power flow. The IslandManager creates a virtual `sgen` element at the battery's bus to serve as the new reference.

This is a simplification — real grid-forming inverters also provide voltage and frequency references, not just power balance.

## Relationships

- **Manager:** `core/island.py`
- **Frequency reference:** [[Frequency Regulator]]
- **Grid-forming source:** [[VPP Orchestrator]] (battery cluster)
- **Power flow:** [[Pandapower Adapter]]
- **Topology:** [[Thai Grid Topology]] (islanding nodes)

## Known Issues

- Only supports single island — no partitioned islanding
- Black start sequence assumes VPP resources are available
- Slack bus swap is a power flow hack — not true grid-forming inverter model
- No synchronization check before reconnection (phase angle matching)
- Island stability not modeled — assumes infinite bus at battery
