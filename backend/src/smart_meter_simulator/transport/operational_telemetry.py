"""Operational-telemetry egress — operator-facing grid/microgrid state.

DLMS/COSEM (``aggregator_bridge.py``) ships **meter** registers; this ships the
**operator** points a SCADA master expects but OBIS has no codes for: per-zone
frequency, island/breaker status, bus-fault counters, DER curtailment, transformer
loading/tap, tie-switch state. It consumes the engine **tick summary** (not
per-meter readings) and maps it to a flat list of typed DNP3/IEC-104-shaped
points.

The mapping (:func:`summary_to_points`) is the reusable, standards-aligned part —
each point carries a DNP3 group (``AI`` analog input / ``BI`` binary input) and an
IEC 60870-5-104 ASDU type id, so it serves either wire. Two transports are
provided: a dependency-free JSON-collector POST (default) and a real IEC
60870-5-104 outstation backed by the optional ``c104`` extra
(``OPERATIONAL_TRANSPORT=iec104``). Select via :func:`build_operational_transport`.

Lifecycle mirrors the DLMS emitter and the persistence stores: optional,
config-gated, fire-and-forget per tick, **drops a tick if the prior batch is still
in flight**, and never propagates a failure into the tick (increments
``operational_emit_failed_total`` instead). Default off.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Mapping, Optional

import httpx

from smart_meter_simulator.core.metrics import OPERATIONAL_EMIT_FAILED

logger = logging.getLogger(__name__)


# DNP3 point group (monitor direction) and the matching IEC 60870-5-104 ASDU
# type id, kept together so one mapping serves either outstation.
#   AI  -> analog input   ; IEC-104 M_ME_NC (13) short-float measured value
#   BI  -> binary input   ; IEC-104 M_SP_NA (1)  single-point status
#   CTR -> counter        ; IEC-104 M_ME_NB (11) scaled measured value
DNP3_AI = "AI"
DNP3_BI = "BI"
DNP3_CTR = "CTR"

IEC104_M_ME_NC = 13  # measured value, short floating point
IEC104_M_SP_NA = 1  # single-point information (status bit)
IEC104_M_ME_NB = 11  # measured value, scaled integer (counters)


def _pt(index: int, name: str, group: str, asdu: int, value: Any) -> dict:
    """One typed telemetry point in the flat outstation point list."""
    return {
        "index": index,
        "name": name,
        "dnp3_group": group,
        "iec104_asdu": asdu,
        "value": value,
    }


def summary_to_points(summary: Mapping[str, Any]) -> List[dict]:
    """Map an engine tick summary to a flat list of SCADA points.

    Pure function (no I/O, no state) so it is trivially testable and reusable by
    any transport. Point indices are stable within a category: system points are
    fixed, per-zone/per-switch points are offset by a deterministic base so a
    master can address ``zone <code>`` or ``switch <name>`` consistently.
    """
    points: List[dict] = []

    # --- System analog inputs (feeder-wide state) ---------------------------
    points.append(
        _pt(
            0, "grid_frequency_hz", DNP3_AI, IEC104_M_ME_NC, summary.get("frequency_hz")
        )
    )
    points.append(
        _pt(
            1,
            "total_losses_kw",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("total_losses_kw"),
        )
    )
    points.append(
        _pt(
            2,
            "total_curtailed_kw",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("total_curtailed_kw"),
        )
    )
    points.append(
        _pt(
            3,
            "total_reactive_support_kvar",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("total_reactive_support_kvar"),
        )
    )
    points.append(
        _pt(
            4,
            "transformer_loading_pct",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("transformer_loading_pct"),
        )
    )
    points.append(
        _pt(
            5,
            "transformer_tap_pos",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("transformer_tap_pos"),
        )
    )
    points.append(
        _pt(
            6,
            "total_dr_shed_kw",
            DNP3_AI,
            IEC104_M_ME_NC,
            summary.get("total_dr_shed_kw"),
        )
    )

    # --- System counters (contingency state) --------------------------------
    points.append(
        _pt(0, "fault_count", DNP3_CTR, IEC104_M_ME_NB, summary.get("fault_count"))
    )
    points.append(
        _pt(
            1,
            "islanded_bus_count",
            DNP3_CTR,
            IEC104_M_ME_NB,
            summary.get("islanded_bus_count"),
        )
    )
    points.append(
        _pt(
            2,
            "active_dr_events",
            DNP3_CTR,
            IEC104_M_ME_NB,
            summary.get("active_dr_events"),
        )
    )

    # --- Per-zone points: AI frequency, BI island/breaker status ------------
    # index = base offset + zone_code, so zone N's points are addressable.
    Z_FREQ_BASE = 100
    Z_ISL_BASE = 0
    Z_CMD_BASE = 1000
    for z in summary.get("zones", []) or []:
        code = int(z.get("zone_code", 0))
        points.append(
            _pt(
                Z_FREQ_BASE + code,
                f"zone_{code}_frequency_hz",
                DNP3_AI,
                IEC104_M_ME_NC,
                z.get("frequency_hz"),
            )
        )
        # Electrical island (zone de-energized / off the slack).
        points.append(
            _pt(
                Z_ISL_BASE + code,
                f"zone_{code}_islanded",
                DNP3_BI,
                IEC104_M_SP_NA,
                bool(z.get("islanded")),
            )
        )
        # Commanded island = PCC breaker open (operator action).
        points.append(
            _pt(
                Z_CMD_BASE + code,
                f"zone_{code}_breaker_open",
                DNP3_BI,
                IEC104_M_SP_NA,
                bool(z.get("commanded_island")),
            )
        )

    # --- Per-switch binary status (tie/sectionalizer closed?) ---------------
    # Optional: only present when the engine threads switch status into the
    # summary (see OperationalTelemetryEmitter.emit). Indexed by enumeration order.
    S_BASE = 2000
    for i, sw in enumerate(summary.get("switches", []) or []):
        points.append(
            _pt(
                S_BASE + i,
                f"switch_{sw.get('name')}_closed",
                DNP3_BI,
                IEC104_M_SP_NA,
                bool(sw.get("closed")),
            )
        )

    return points


# --- transports --------------------------------------------------------------
#
# A transport is duck-typed with three async methods the emitter drives:
#   astart()                    -> bring the transport up (server / no-op)
#   deliver(timestamp, points)  -> publish one tick's point batch
#   aclose()                    -> tear it down
# The point *mapping* (summary_to_points) is transport-agnostic; only the wire
# differs. Two are provided: a JSON collector POST (default, dependency-free) and
# a real IEC 60870-5-104 outstation (optional `c104` extra).


class OperationalTelemetryClient:
    """JSON-collector transport: POST one point batch per tick.

    Dependency-free stand-in for a real outstation — a single JSON POST of the
    point list to ``{base_url}/operational/telemetry``. Default transport.
    """

    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.ingest_url = f"{self.base_url}/operational/telemetry"
        self.target = self.ingest_url
        self._client = httpx.AsyncClient(timeout=timeout)

    async def astart(self) -> None:
        """No connection to establish — the POST is per-tick."""

    async def send_points(self, timestamp: str, points: List[dict]) -> httpx.Response:
        resp = await self._client.post(
            self.ingest_url, json={"timestamp": timestamp, "points": points}
        )
        resp.raise_for_status()
        return resp

    async def deliver(self, timestamp: str, points: List[dict]) -> None:
        await self.send_points(timestamp, points)

    async def aclose(self) -> None:
        await self._client.aclose()


# IEC 60870-5-104 ASDU type id -> c104 point type name. Resolved lazily so the
# module imports without the optional `c104` dependency installed.
_IEC104_TYPE_NAMES = {
    IEC104_M_ME_NC: "M_ME_NC",  # short float measured value
    IEC104_M_SP_NA: "M_SP_NA",  # single-point status
    IEC104_M_ME_NB: "M_ME_NB",  # scaled measured value
}


class Iec104OutstationTransport:
    """Real IEC 60870-5-104 outstation (monitor direction) backed by ``c104``.

    Runs a lib60870 server a SCADA master connects to; each tick's points update
    the outstation's information objects (the server reports changes to connected
    masters). Requires the optional ``iec104`` extra (``uv sync --extra iec104``);
    importing ``c104`` is deferred to :meth:`astart` so the module loads without it.

    IEC-104 information object addresses (IOA) must be unique per station, but the
    point map reuses small per-category indices (system AI 0 vs counter 0 vs zone
    bit 0). So IOAs are assigned here by **point name** on first sight (sequential
    from ``ioa_base``) and cached, decoupling the wire address from the JSON index.

    NOTE: not exercised in CI — there is no master/loopback in the test sandbox and
    no c104 wheel for every interpreter. Construction + IOA assignment are unit
    tested with the dependency mocked; live interop is manual.
    """

    def __init__(
        self,
        *,
        port: int = 2404,
        ip: str = "0.0.0.0",
        common_address: int = 1,
        ioa_base: int = 1,
    ) -> None:
        self._port = port
        self._ip = ip
        self._common_address = common_address
        self._ioa_base = ioa_base
        self.target = f"iec104://{ip}:{port}/ca{common_address}"
        self._c104 = None
        self._server = None
        self._station = None
        self._points: dict = {}  # name -> c104 point handle
        self._next_ioa = ioa_base

    async def astart(self) -> None:
        import c104  # optional dependency (extra: iec104)

        self._c104 = c104
        self._server = c104.Server(ip=self._ip, port=self._port)
        self._station = self._server.add_station(common_address=self._common_address)
        self._server.start()
        logger.info("IEC-104 outstation listening on %s", self.target)

    def _point_type(self, asdu: int):
        return getattr(self._c104.Type, _IEC104_TYPE_NAMES[asdu])

    def _ensure_point(self, name: str, asdu: int):
        """Get (creating on first sight) the c104 point for ``name``."""
        handle = self._points.get(name)
        if handle is None:
            handle = self._station.add_point(
                io_address=self._next_ioa, type=self._point_type(asdu)
            )
            self._points[name] = handle
            self._next_ioa += 1
        return handle

    async def deliver(self, timestamp: str, points: List[dict]) -> None:
        if self._station is None:
            return  # not started
        for p in points:
            value = p["value"]
            if value is None:
                continue
            handle = self._ensure_point(p["name"], p["iec104_asdu"])
            # Single-point status takes a bool; measured values take a float.
            handle.value = bool(value) if p["dnp3_group"] == DNP3_BI else float(value)

    async def aclose(self) -> None:
        if self._server is not None:
            self._server.stop()
            self._server = None
            self._station = None


def build_operational_transport(
    transport: str,
    *,
    base_url: str,
    iec104_port: int = 2404,
    iec104_common_address: int = 1,
    timeout: float = 10.0,
):
    """Construct the configured operational transport.

    ``transport`` is ``"json"`` (default collector POST) or ``"iec104"`` (real
    outstation). Construction is cheap and dependency-free for both — the ``c104``
    import happens later in :meth:`Iec104OutstationTransport.astart`, so a missing
    extra surfaces at start, not import.
    """
    if transport == "iec104":
        return Iec104OutstationTransport(
            port=iec104_port, common_address=iec104_common_address
        )
    return OperationalTelemetryClient(base_url, timeout=timeout)


class OperationalTelemetryEmitter:
    """Ship per-tick operational points over a transport, non-blocking.

    Consumes the tick **summary**; call :meth:`emit` once per tick after the
    engine has built it. Drops a tick if a prior batch is still in flight, so a
    slow sink throttles cadence instead of backing up the sim loop. Transport is
    pluggable (JSON collector or IEC-104 outstation); pass one in, or a base_url
    to default to the JSON collector.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        transport: Optional[Any] = None,
        emit_every: int = 1,
        timeout: float = 10.0,
    ):
        if transport is None:
            transport = OperationalTelemetryClient(base_url or "", timeout=timeout)
        self._transport = transport
        self._emit_every = max(1, emit_every)
        self._inflight: Optional[asyncio.Task] = None
        self._tick_count = 0
        self._started = False

    def start(self) -> None:
        """Mark active and bring the transport up. Call once at engine start."""
        self._started = True
        logger.info(
            "Operational telemetry emitter active -> %s",
            getattr(self._transport, "target", "?"),
        )
        try:
            asyncio.get_running_loop().create_task(self._astart())
        except RuntimeError:
            pass  # no running loop (e.g. unit test) — transport.astart() skipped

    async def _astart(self) -> None:
        try:
            await self._transport.astart()
        except Exception:
            OPERATIONAL_EMIT_FAILED.inc()
            logger.warning("Operational telemetry transport failed to start")

    def emit(self, summary: Mapping[str, Any]) -> None:
        """Schedule a background point-batch send for this tick's summary.

        Synchronous and non-blocking. Drops the tick if the emitter is not
        started, there is no summary, the cadence gate skips it, or a prior
        batch is still running.
        """
        if not self._started or not summary:
            return
        self._tick_count += 1
        if self._tick_count % self._emit_every != 0:
            return
        if self._inflight is not None and not self._inflight.done():
            logger.debug("Operational emit skipped: previous batch still in flight")
            return
        points = summary_to_points(summary)
        timestamp = str(summary.get("timestamp", ""))
        self._inflight = asyncio.create_task(self._send(timestamp, points))

    async def _send(self, timestamp: str, points: List[dict]) -> None:
        try:
            await self._transport.deliver(timestamp, points)
        except Exception:
            OPERATIONAL_EMIT_FAILED.inc()
            logger.warning(
                "Operational telemetry batch failed (%d points)", len(points)
            )

    async def close(self) -> None:
        """Cancel any in-flight batch and close the transport."""
        if self._inflight is not None and not self._inflight.done():
            self._inflight.cancel()
        await self._transport.aclose()
