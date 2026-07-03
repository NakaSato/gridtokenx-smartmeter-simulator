"""Live loopback interop check for Iec104OutstationTransport.

Runs the sim's real IEC 60870-5-104 outstation (lib60870 via ``c104``) on
127.0.0.1:2404, feeds it points produced by the real ``summary_to_points()``
mapping, then connects a c104 master, runs a general interrogation, and asserts
the delivered values arrive with the expected IOAs and types. This exercises
exactly the layer the unit tests fake — it is what caught the ``M_ME_NC`` vs
``M_ME_NC_1`` type-name bug and the ``c104.Int16`` scaled-counter requirement
(fixed in 9645987).

``c104`` ships manylinux wheels for CPython 3.11-3.13 only (no macOS, no 3.14),
so on a dev Mac run this in a container:

    docker run --rm -e PYTHONUNBUFFERED=1 \
      -v "$PWD":/backend:ro python:3.11-slim bash -c \
      "pip install -q c104 httpx && python /backend/scripts/iec104_interop_check.py"

Exits 0 and prints IEC104_INTEROP_PASS on success; exits 1 with the failure
list otherwise. Not collected by pytest — it needs a wheel-compatible
interpreter and opens a real TCP listener.
"""

import asyncio
import importlib.util
import pathlib
import sys
import time
import types

import c104

# Load operational_telemetry.py directly from file, stubbing only the metrics
# counter import, so the heavy package __init__ chain (engine -> networkx ->
# pandapower) stays out of this transport-layer check and the only hard
# dependency beyond c104 is httpx (imported at the top of the module).
_metrics = types.ModuleType("smart_meter_simulator.core.metrics")


class _Counter:
    def inc(self, *a, **k):
        pass

    def labels(self, *a, **k):
        return self


_metrics.OPERATIONAL_EMIT_FAILED = _Counter()
sys.modules["smart_meter_simulator.core.metrics"] = _metrics

_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "src"
    / "smart_meter_simulator"
    / "transport"
    / "operational_telemetry.py"
)
_spec = importlib.util.spec_from_file_location("operational_telemetry", _MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Iec104OutstationTransport = _mod.Iec104OutstationTransport
summary_to_points = _mod.summary_to_points

# A representative tick summary: system analogs, counters, and one islanded
# zone so the per-zone frequency/status points are exercised. The zone key is
# `zone_code` (what engine._zone_summaries emits), not `code`.
FAKE_SUMMARY = {
    "frequency_hz": 49.87,
    "total_losses_kw": 5.8,
    "transformer_loading_pct": 35.2,
    "transformer_loss_kw": 1.9,
    "transformer_tap_pos": 2,
    "total_curtailed_kw": 0.0,
    "total_reactive_support_kvar": 3.3,
    "total_dr_shed_kw": 0.0,
    "fault_count": 1,
    "islanded_bus_count": 4,
    "active_dr_events": 0,
    "zones": [
        {
            "zone_code": 1,
            "frequency_hz": 49.5,
            "islanded": True,
            "commanded_island": True,
            "islandable": True,
        }
    ],
}


async def main() -> int:
    points = summary_to_points(FAKE_SUMMARY)
    print(f"point map: {len(points)} points")

    # --- outstation (the sim's real transport) -------------------------------
    outstation = Iec104OutstationTransport(port=2404, common_address=1)
    await outstation.astart()
    await outstation.deliver("2026-07-02T00:00:00Z", points)

    # IOA assignment is by-name on first sight, sequential from ioa_base=1.
    expected_ioa = {}
    next_ioa = 1
    for p in points:
        if p["value"] is None:
            continue
        if p["name"] not in expected_ioa:
            expected_ioa[p["name"]] = next_ioa
            next_ioa += 1

    # --- master ----------------------------------------------------------------
    received = {}

    # c104 validates callback signatures against these exact annotations.
    def on_new_point(
        client: c104.Client,
        station: c104.Station,
        io_address: int,
        point_type: c104.Type,
    ) -> None:
        point = station.add_point(io_address=io_address, type=point_type)

        def on_receive(
            point: c104.Point,
            previous_info: c104.Information,
            message: c104.IncomingMessage,
        ) -> c104.ResponseState:
            received[point.io_address] = point.value
            return c104.ResponseState.SUCCESS

        point.on_receive(callable=on_receive)

    client = c104.Client()
    client.on_new_point(callable=on_new_point)
    connection = client.add_connection(
        ip="127.0.0.1", port=2404, init=c104.Init.INTERROGATION
    )
    connection.add_station(common_address=1)
    client.start()

    deadline = time.time() + 15
    while time.time() < deadline and len(received) < len(expected_ioa):
        await asyncio.sleep(0.25)

    client.stop()
    await outstation.aclose()

    # --- assertions --------------------------------------------------------------
    failures = []
    checks = {
        "grid_frequency_hz": 49.87,
        "total_losses_kw": 5.8,
        "transformer_loading_pct": 35.2,
        "fault_count": 1.0,
        "islanded_bus_count": 4.0,
    }
    for name, expected_value in checks.items():
        ioa = expected_ioa.get(name)
        if ioa is None:
            failures.append(f"{name}: not in point map")
            continue
        got = received.get(ioa)
        if got is None:
            failures.append(f"{name}: IOA {ioa} never received")
        elif abs(float(got) - expected_value) > 0.01:
            failures.append(f"{name}: IOA {ioa} value {got} != {expected_value}")
        else:
            print(f"ok {name}: IOA {ioa} = {got}")

    # Zone island status bit (BI -> M_SP_NA_1, delivered as bool).
    zname = "zone_1_islanded"
    ioa = expected_ioa.get(zname)
    if ioa is None:
        failures.append(f"{zname}: not in point map")
    elif received.get(ioa) is not True:
        failures.append(f"{zname}: expected True, got {received.get(ioa)!r}")
    else:
        print(f"ok {zname}: IOA {ioa} = True")

    print(f"received {len(received)}/{len(expected_ioa)} points")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(" -", f)
        return 1
    print("IEC104_INTEROP_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
