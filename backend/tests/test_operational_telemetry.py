"""Operational-telemetry egress tests (SCADA/DNP3/IEC-104-shaped point map).

The mapping (``summary_to_points``) turns an engine tick summary into a flat list
of typed points carrying both a DNP3 group and an IEC 60870-5-104 ASDU id — the
grid/microgrid state DLMS/OBIS cannot carry. The emitter ships them non-blocking,
drops a tick if a prior batch is in flight, and never raises into the tick.
"""

from __future__ import annotations

import asyncio


def _make_self_signed(tmp_path):
    """Write a throwaway EC cert+key pair; return (cert_path, key_path)."""
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-op-client")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime(2020, 1, 1))
        .not_valid_after(datetime.datetime(2040, 1, 1))
        .sign(key, hashes.SHA256())
    )
    crt = tmp_path / "op.crt"
    k = tmp_path / "op.key"
    crt.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    k.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return str(crt), str(k)


from smart_meter_simulator.transport.operational_telemetry import (  # noqa: E402
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


class _FakeTransport:
    """Stand-in transport exposing the astart/deliver/aclose interface."""

    def __init__(self):
        self.sent = []
        self.target = "fake://collector"

    async def astart(self):
        pass

    async def deliver(self, timestamp, points):
        self.sent.append((timestamp, points))

    async def aclose(self):
        pass


def _emitter_with_fake():
    fake = _FakeTransport()
    em = OperationalTelemetryEmitter(transport=fake)
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

        # A transport whose deliver blocks until released, to hold a batch in flight.
        release = asyncio.Event()

        async def blocking_deliver(timestamp, points):
            await release.wait()
            fake.sent.append((timestamp, points))

        fake.deliver = blocking_deliver
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

        fake.deliver = boom
        em.start()
        em.emit(_summary())
        await em._inflight  # must not raise — failure is swallowed + counted
        assert em._inflight.done()

    asyncio.run(run())


# --- transport selection + IEC-104 mapping -----------------------------------


def test_build_transport_defaults_to_json_collector():
    from smart_meter_simulator.transport.operational_telemetry import (
        OperationalTelemetryClient,
        build_operational_transport,
    )

    t = build_operational_transport("json", base_url="http://c")
    assert isinstance(t, OperationalTelemetryClient)
    assert t.ingest_url == "http://c/operational/telemetry"


def test_operational_client_threads_tls_cert_and_api_key(monkeypatch, tmp_path):
    # Hardening mirrors the DLMS egress: with a client cert the verify arg becomes
    # an SSLContext (httpx 0.28 dropped cert=), and the API key rides as X-API-KEY.
    import ssl

    import smart_meter_simulator.transport.operational_telemetry as mod

    captured = {}

    class _FakeClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(mod.httpx, "AsyncClient", _FakeClient)

    crt, key = _make_self_signed(tmp_path)
    mod.OperationalTelemetryClient(
        "https://collector:4040",
        client_cert=(crt, key),
        api_key="op-secret",
    )
    assert isinstance(captured["verify"], ssl.SSLContext)
    assert captured["headers"] == {"X-API-KEY": "op-secret"}


def test_operational_client_plain_when_unconfigured(monkeypatch):
    import smart_meter_simulator.transport.operational_telemetry as mod

    captured = {}

    class _FakeClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(mod.httpx, "AsyncClient", _FakeClient)
    mod.OperationalTelemetryClient("http://collector:4040")
    assert captured["verify"] is True  # passthrough, no SSLContext
    assert captured["headers"] is None  # no API key


def test_build_transport_iec104_selects_outstation_without_importing_c104():
    # Construction must NOT import c104 (the extra may be absent) — the import is
    # deferred to astart(). So this resolves even with no c104 installed.
    from smart_meter_simulator.transport.operational_telemetry import (
        Iec104OutstationTransport,
        build_operational_transport,
    )

    t = build_operational_transport(
        "iec104", base_url="unused", iec104_port=2404, iec104_common_address=1
    )
    assert isinstance(t, Iec104OutstationTransport)
    assert t.target == "iec104://0.0.0.0:2404/ca1"


def test_iec104_maps_points_to_unique_ioas_and_typed_values():
    """IOA assigned per point name (small per-category indices would collide);
    bits set bool, measured values set float, counters set c104.Int16. c104
    server/station are faked, mirroring the real c104 2.x surface (`_1`-suffixed
    IEC ASDU type names, Int16 for scaled values) — pinned by the live loopback
    interop run 2026-07-02."""
    from smart_meter_simulator.transport.operational_telemetry import (
        DNP3_AI,
        DNP3_BI,
        DNP3_CTR,
        Iec104OutstationTransport,
    )

    class _FakePoint:
        def __init__(self, io_address, type):
            self.io_address = io_address
            self.type = type
            self.value = None

    class _FakeStation:
        def __init__(self):
            self.points = []

        def add_point(self, io_address, type):
            p = _FakePoint(io_address, type)
            self.points.append(p)
            return p

    class _FakeType:
        # Real c104 uses the full IEC 60870-5-101 identifiers (`_1` suffix);
        # bare names like M_ME_NC do not exist on c104.Type.
        M_ME_NC_1 = "M_ME_NC_1"
        M_SP_NA_1 = "M_SP_NA_1"
        M_ME_NB_1 = "M_ME_NB_1"

    class _FakeInt16(int):
        pass

    class _FakeC104:
        Type = _FakeType
        Int16 = _FakeInt16

    t = Iec104OutstationTransport(port=2404)
    t._c104 = _FakeC104()
    t._station = _FakeStation()

    points = [
        {
            "name": "grid_frequency_hz",
            "dnp3_group": DNP3_AI,
            "iec104_asdu": 13,
            "value": 49.5,
        },
        {
            "name": "zone_1_breaker_open",
            "dnp3_group": DNP3_BI,
            "iec104_asdu": 1,
            "value": True,
        },
        {
            "name": "fault_count",
            "dnp3_group": DNP3_CTR,
            "iec104_asdu": 11,
            "value": 3,
        },
        {"name": "skipme", "dnp3_group": DNP3_AI, "iec104_asdu": 13, "value": None},
    ]

    async def run():
        await t.deliver("2026-06-20T00:00:00+00:00", points)
        # None-valued point is skipped; the three real ones get distinct IOAs.
        assert len(t._station.points) == 3
        ioas = {p.io_address for p in t._station.points}
        assert ioas == {1, 2, 3}
        freq = t._points["grid_frequency_hz"]
        brk = t._points["zone_1_breaker_open"]
        ctr = t._points["fault_count"]
        assert freq.value == 49.5 and isinstance(freq.value, float)
        assert brk.value is True
        # Scaled counters must be wrapped in c104.Int16 — a plain int is
        # rejected by the real library's information-object validation.
        assert ctr.value == 3 and isinstance(ctr.value, _FakeInt16)
        # A second tick reuses the same point handles (stable IOA), no new points.
        await t.deliver("t2", points)
        assert len(t._station.points) == 3

    asyncio.run(run())
