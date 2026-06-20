"""Operational-telemetry egress tests (SCADA/DNP3/IEC-104-shaped point map).

The mapping (``summary_to_points``) turns an engine tick summary into a flat list
of typed points carrying both a DNP3 group and an IEC 60870-5-104 ASDU id — the
grid/microgrid state DLMS/OBIS cannot carry. The emitter ships them non-blocking,
drops a tick if a prior batch is in flight, and never raises into the tick.
"""

from __future__ import annotations

import asyncio

from smart_meter_simulator.transport.operational_telemetry import (
    DNP3_AI,
    DNP3_BI,
    OperationalTelemetryEmitter,
    summary_to_points,
)


def _summary() -> dict:
    return {
        "timestamp": "2026-06-19T10:00:00+00:00",
        "frequency_hz": 49.78,
        "total_losses_kw": 2.34,
        "total_curtailed_kw": 1.2,
        "total_reactive_support_kvar": 0.3,
        "transformer_loading_pct": 16.9,
        "transformer_tap_pos": 0,
        "total_dr_shed_kw": 0.0,
        "fault_count": 1,
        "islanded_bus_count": 2,
        "active_dr_events": 0,
        "zones": [
            {
                "zone_code": 1,
                "frequency_hz": 50.41,
                "islanded": False,
                "commanded_island": True,
            },
            {
                "zone_code": 2,
                "frequency_hz": 49.50,
                "islanded": True,
                "commanded_island": True,
            },
        ],
        "switches": [{"name": "tie_1_2", "closed": False}],
    }


def _by_name(points):
    return {p["name"]: p for p in points}


def test_system_points_present_and_typed():
    pts = _by_name(summary_to_points(_summary()))
    # System analog inputs carry the grid-wide state OBIS has no code for.
    assert pts["grid_frequency_hz"]["value"] == 49.78
    assert pts["grid_frequency_hz"]["dnp3_group"] == DNP3_AI
    assert pts["grid_frequency_hz"]["iec104_asdu"] == 13  # M_ME_NC short-float
    assert pts["total_curtailed_kw"]["value"] == 1.2
    assert pts["transformer_tap_pos"]["value"] == 0
    # Counters carry contingency state.
    assert pts["fault_count"]["value"] == 1
    assert pts["islanded_bus_count"]["value"] == 2
    assert pts["fault_count"]["iec104_asdu"] == 11  # M_ME_NB scaled int


def test_per_zone_points_addressable_by_code():
    pts = _by_name(summary_to_points(_summary()))
    # Per-zone frequency is an AI; island/breaker are BI status bits.
    assert pts["zone_1_frequency_hz"]["value"] == 50.41
    assert pts["zone_1_frequency_hz"]["dnp3_group"] == DNP3_AI
    assert pts["zone_1_breaker_open"]["value"] is True
    assert pts["zone_1_breaker_open"]["dnp3_group"] == DNP3_BI
    assert pts["zone_1_islanded"]["value"] is False
    # Zone 2 is electrically dark (islanded) AND commanded.
    assert pts["zone_2_islanded"]["value"] is True
    assert pts["zone_2_breaker_open"]["value"] is True
    # Indices are offset by zone code so a master can address them.
    assert pts["zone_1_frequency_hz"]["index"] == 101
    assert pts["zone_2_frequency_hz"]["index"] == 102


def test_switch_points_when_threaded_in():
    pts = _by_name(summary_to_points(_summary()))
    assert pts["switch_tie_1_2_closed"]["value"] is False
    assert pts["switch_tie_1_2_closed"]["dnp3_group"] == DNP3_BI


def test_no_zones_yields_only_system_points():
    s = _summary()
    s["zones"] = []
    s["switches"] = []
    names = {p["name"] for p in summary_to_points(s)}
    assert "grid_frequency_hz" in names
    assert not any(n.startswith("zone_") for n in names)


# --- emitter behaviour -------------------------------------------------------


class _FakeClient:
    def __init__(self):
        self.sent = []
        self.ingest_url = "http://collector/operational/telemetry"

    async def send_points(self, timestamp, points):
        self.sent.append((timestamp, points))

    async def close(self):
        pass


def _emitter_with_fake():
    em = OperationalTelemetryEmitter("http://collector")
    fake = _FakeClient()
    em._client = fake
    return em, fake


def test_emit_before_start_is_noop():
    em, fake = _emitter_with_fake()
    em.emit(_summary())  # not started
    assert fake.sent == []


def test_emit_sends_points_after_start():
    async def run():
        em, fake = _emitter_with_fake()
        em.start()
        em.emit(_summary())
        await em._inflight  # let the background send complete
        assert len(fake.sent) == 1
        ts, points = fake.sent[0]
        assert ts == "2026-06-19T10:00:00+00:00"
        assert any(p["name"] == "zone_1_frequency_hz" for p in points)

    asyncio.run(run())


def test_emit_drops_tick_when_batch_in_flight():
    async def run():
        em, fake = _emitter_with_fake()

        # A client whose send blocks until released, to hold a batch in flight.
        release = asyncio.Event()

        async def blocking_send(timestamp, points):
            await release.wait()
            fake.sent.append((timestamp, points))

        fake.send_points = blocking_send
        em.start()

        em.emit(_summary())  # batch 1 -> in flight (blocked)
        em.emit(_summary())  # batch 2 -> dropped (prior still running)
        release.set()
        await em._inflight
        assert len(fake.sent) == 1  # second tick was dropped, not queued

    asyncio.run(run())


def test_send_failure_never_raises():
    async def run():
        em, fake = _emitter_with_fake()

        async def boom(timestamp, points):
            raise RuntimeError("collector down")

        fake.send_points = boom
        em.start()
        em.emit(_summary())
        await em._inflight  # must not raise — failure is swallowed + counted
        assert em._inflight.done()

    asyncio.run(run())
