"""Demand-response (DR) load-curtailment events for the GLM grid simulator.

A DR event is a sim-clock window over which participating meters shed a fraction
of their flexible load — modelling a utility peak-shave / load-shed signal (the
controllable portion of a household: HVAC, water heater, deferrable appliances).
Curtailment relieves the feeder: lower aggregate load means less line/transformer
loading and a firmer voltage profile, observable in the same power-flow solve.

DR is a **runtime control surface** like fault injection (``GridManager`` faults),
not part of the seeded deterministic replay — events are user-triggered over the
API and identified by a monotonic counter (``dr-1``, ``dr-2``, …), so scheduling
is reproducible without any RNG draw. Events are evaluated against the sim clock
(the engine's ``current_sim_time``), so a bounded deterministic run shes the same
load on replay given the same schedule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class DemandResponseEvent:
    """One scheduled load-shed window.

    ``reduction_fraction`` is the share of a participating meter's load curtailed
    while the event is active (0.30 → 30% shed). ``target_meter_types`` restricts
    participation to those meter-type strings (``MeterType`` values); ``None`` =
    every meter. The window is half-open ``[start, end)`` to match the engine's
    bounded-run convention.
    """

    event_id: str
    start: datetime
    end: datetime
    reduction_fraction: float
    target_meter_types: Optional[frozenset[str]]
    label: str

    def is_active(self, now: datetime) -> bool:
        """True while ``now`` falls in the half-open ``[start, end)`` window."""
        return self.start <= now < self.end

    def applies_to(self, meter_type: str) -> bool:
        """True if this event curtails the given meter type (None target = all)."""
        return self.target_meter_types is None or meter_type in self.target_meter_types

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "reduction_fraction": self.reduction_fraction,
            "target_meter_types": (
                sorted(self.target_meter_types)
                if self.target_meter_types is not None
                else None
            ),
            "label": self.label,
        }


class DemandResponseController:
    """Holds DR events and resolves the per-meter load factor for a given instant.

    Overlapping events that both target a meter compose by the **most aggressive**
    reduction (a 30% and a 50% event yield a 50% shed, not 65%) — a single utility
    can only shed a given load once. The returned factor multiplies consumption:
    ``1.0`` = no curtailment, ``0.5`` = half the load shed.
    """

    def __init__(self) -> None:
        self._events: List[DemandResponseEvent] = []
        self._counter = 0

    def schedule(
        self,
        *,
        start: datetime,
        end: datetime,
        reduction_fraction: float,
        target_meter_types: Optional[Iterable[str]] = None,
        label: str = "",
    ) -> DemandResponseEvent:
        """Add a DR event. Raises ``ValueError`` on a bad window or fraction."""
        if not 0.0 < reduction_fraction <= 1.0:
            raise ValueError("reduction_fraction must be in (0, 1]")
        if end <= start:
            raise ValueError("end must be after start")
        targets = frozenset(target_meter_types) if target_meter_types else None
        if targets is not None and not targets:
            targets = None
        self._counter += 1
        event = DemandResponseEvent(
            event_id=f"dr-{self._counter}",
            start=start,
            end=end,
            reduction_fraction=reduction_fraction,
            target_meter_types=targets,
            label=label,
        )
        self._events.append(event)
        return event

    def cancel(self, event_id: str) -> bool:
        """Remove a scheduled event by id. False if no such event."""
        before = len(self._events)
        self._events = [e for e in self._events if e.event_id != event_id]
        return len(self._events) != before

    def clear(self) -> int:
        """Remove every event; returns how many were cleared."""
        count = len(self._events)
        self._events = []
        return count

    def load_factor(self, now: datetime, meter_type: str) -> float:
        """Consumption multiplier for ``meter_type`` at ``now`` (1.0 = no shed)."""
        reductions = [
            e.reduction_fraction
            for e in self._events
            if e.is_active(now) and e.applies_to(meter_type)
        ]
        if not reductions:
            return 1.0
        return max(0.0, 1.0 - max(reductions))

    def has_active(self, now: datetime) -> bool:
        """True if any event is curtailing load at ``now`` (fast-path guard)."""
        return any(e.is_active(now) for e in self._events)

    def active_events(self, now: datetime) -> List[DemandResponseEvent]:
        return [e for e in self._events if e.is_active(now)]

    def scheduled_events(self, now: datetime) -> List[DemandResponseEvent]:
        """Future events not yet started."""
        return [e for e in self._events if e.start > now]

    def status(self, now: datetime) -> dict:
        """Snapshot of active + scheduled events at the current sim instant."""
        active = self.active_events(now)
        scheduled = self.scheduled_events(now)
        return {
            "now": now.isoformat(),
            "active_count": len(active),
            "scheduled_count": len(scheduled),
            "active": [e.to_dict() for e in active],
            "scheduled": [e.to_dict() for e in scheduled],
        }
