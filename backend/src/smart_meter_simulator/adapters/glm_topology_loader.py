"""
GLM topology loader for the simulator core.

This module turns ``.glm`` topology objects into the shared ``GridTopology``
model. It intentionally handles topology and static load extraction only; no
external solver is executed by the core loader.
"""

from __future__ import annotations

import logging
import re
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from smart_meter_simulator.core.topology import (
    GridBattery,
    GridBus,
    GridEVStation,
    GridLine,
    GridLoad,
    GridPV,
    GridTopology,
    GridTransformer,
    ZoneSpec,
)

from .glm_converter import GLMParser, GLMToken

logger = logging.getLogger(__name__)

_BUS_OBJECTS = {"node", "meter", "substation"}
_LINE_OBJECTS = {"overhead_line", "underground_line", "triplex_line"}
# Controllable tie/sectionalizing switches — modeled as (near-ideal) line edges
# that can be opened/closed at runtime. `status OPEN` => normally open.
_SWITCH_OBJECTS = {"switch", "recloser", "sectionalizer"}
_LINE_CONFIGURATION_OBJECTS = {
    "line_configuration",
    "overhead_line_configuration",
    "underground_line_configuration",
    "triplex_line_configuration",
}
_LOAD_OBJECTS = {"load"}
_INVERTER_OBJECTS = {"inverter", "inverter_dyn"}
_PV_OBJECTS = {"solar"}
_BATTERY_OBJECTS = {"battery"}
# GridLAB-D EV charger objects (residential/commercial charging).
_EVCHARGER_OBJECTS = {"evcharger", "evcharger_det"}
_TRANSFORMER_OBJECTS = {"transformer"}
_TRANSFORMER_CONFIGURATION_OBJECTS = {"transformer_configuration"}
_RESISTANCE_PER_KM_KEYS = ("resistance_ohm_per_km", "r_ohm_per_km")
_REACTANCE_PER_KM_KEYS = ("reactance_ohm_per_km", "x_ohm_per_km")
_RESISTANCE_PER_MILE_KEYS = ("resistance_ohm_per_mile", "r_ohm_per_mile")
_REACTANCE_PER_MILE_KEYS = ("reactance_ohm_per_mile", "x_ohm_per_mile")
_GENERIC_RESISTANCE_KEYS = ("r1", "resistance")
_GENERIC_REACTANCE_KEYS = ("x1", "reactance")
_IMPEDANCE_KEYS = (
    "z11",
    "z22",
    "z33",
    "z1",
    "positive_sequence_impedance",
    "impedance",
)


def _derive_zone_codes(labels: Iterable[str]) -> Dict[str, int]:
    """Map distinct zone labels to stable numeric codes, in load order.

    Labels are the zones' **PCC transformer names** (see ``_build_zones``); a
    bus's GLM ``groupid``/``zone`` no longer participates in zone identity.

    Cascade per label: a pure-integer label is its own code; else its trailing
    digit run (``pcc_3`` -> 3); else the smallest positive integer not already
    taken (a load-order counter). Codes match the parent bridge's
    ``zone_<code>`` partitions.

    Note: two digit-suffixed labels sharing a number (``pcc_1`` and
    ``tx_1``) collapse to one code — keep numeric suffixes unique per
    transformer.
    """
    codes: Dict[str, int] = {}
    used: set[int] = set()
    deferred: List[str] = []
    for label in labels:
        if not label or label in codes:
            continue
        text = str(label).strip()
        if text.isdigit():
            code: Optional[int] = int(text)
        else:
            match = re.search(r"(\d+)$", text)
            code = int(match.group(1)) if match else None
        if code is None:
            deferred.append(label)
        else:
            codes[label] = code
            used.add(code)
    counter = 1
    for label in deferred:
        while counter in used:
            counter += 1
        codes[label] = counter
        used.add(counter)
        counter += 1
    return codes


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text.strip('"').strip("'")


def _parse_float(value: Any, default: float = 0.0) -> float:
    text = _clean(value)
    for suffix in (
        "MVA",
        "kVA",
        "VA",
        "kV",
        "V",
        "A",
        "ohm",
        "km",
        "sf",
        "sqft",
        "m",
        "ft",
        "in",
    ):
        text = text.replace(suffix, "")
    try:
        return float(text.strip())
    except ValueError:
        return default


def _parse_area_square_meters(value: Any) -> float:
    text = _clean(value).lower()
    area = _parse_float(text)
    if any(unit in text for unit in ("sf", "sqft", "ft^2", "ft2")):
        return area * 0.09290304
    return area


def _per_distance_to_per_km(value: float, unit: str) -> float:
    normalized = unit.lower()
    if normalized in {"km", "kilometer", "kilometers"}:
        return value
    if normalized in {"mi", "mile", "miles"}:
        return value / 1.609344
    if normalized in {"m", "meter", "meters"}:
        return value * 1000.0
    if normalized in {"ft", "feet", "foot"}:
        return value / 0.0003048
    return value


def _first_float(properties: Dict[str, Any], keys: tuple[str, ...]) -> float:
    for key in keys:
        if key in properties:
            value = _parse_float(properties[key])
            if value:
                return value
    return 0.0


def _parse_length_unit(value: Any) -> str:
    text = _clean(value).lower()
    for unit in ("km", "mi", "mile", "miles", "ft", "feet", "m"):
        if unit in text:
            return unit
    return ""


def _parse_complex(value: Any) -> complex:
    text = _clean(value)
    text = re.sub(r"\s*(ohm|ohms)(/|\s+per\s+)?[a-zA-Z]*\s*$", "", text)
    text = text.replace("i", "j")
    text = text.replace(" ", "")
    if not text:
        return 0j
    try:
        return complex(text)
    except ValueError:
        return 0j


def _clean_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    return {key: _clean(value) for key, value in properties.items()}


def _named_objects(tokens: Iterable[GLMToken]) -> Dict[str, Dict[str, Any]]:
    objects: Dict[str, Dict[str, Any]] = {}
    for token in tokens:
        props = _clean_properties(token.properties)
        name = _clean(token.name) or props.get("name", "")
        if name:
            objects[name] = {
                "obj_type": token.obj_type,
                "parent": _clean(token.parent),
                "properties": props,
            }
    return objects


def _all_tokens(tokens: Iterable[GLMToken]) -> List[GLMToken]:
    result: List[GLMToken] = []
    for token in tokens:
        result.append(token)
        result.extend(_all_tokens(token.children))
    return result


def _line_configuration_properties(
    properties: Dict[str, Any], objects_by_name: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    config_name = properties.get("configuration", "")
    if not config_name:
        return {}
    config = objects_by_name.get(config_name, {})
    if config.get("obj_type") not in _LINE_CONFIGURATION_OBJECTS:
        return {}
    return dict(config.get("properties", {}))


def _transformer_config_properties(
    properties: Dict[str, Any], objects_by_name: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    config_name = properties.get("configuration", "")
    if not config_name:
        return {}
    config = objects_by_name.get(config_name, {})
    if config.get("obj_type") not in _TRANSFORMER_CONFIGURATION_OBJECTS:
        return {}
    return dict(config.get("properties", {}))


def _transformer_params(cfg_props: Dict[str, Any]) -> tuple[float, float, float]:
    """Derive ``(sn_mva, vk_percent, vkr_percent)`` from a GLM transformer config.

    GridLAB-D ``transformer_configuration`` gives ``power_rating`` in kVA and a
    per-unit ``resistance``/``reactance`` on the transformer base. The pandapower
    short-circuit voltage is the impedance magnitude (``vk% = |Z|·100``) and its
    real part is the copper component (``vkr% = R·100``). Missing values stay 0
    so the builder substitutes the configured ``TRANSFORMER_*`` defaults.
    """
    rating_kva = _first_float(
        cfg_props,
        ("power_rating", "powerA_rating", "powerB_rating", "powerC_rating"),
    )
    sn_mva = rating_kva / 1000.0 if rating_kva > 0 else 0.0
    r_pu = _first_float(cfg_props, ("resistance", "r", "r1"))
    x_pu = _first_float(cfg_props, ("reactance", "x", "x1"))
    if r_pu <= 0 and x_pu <= 0:
        return sn_mva, 0.0, 0.0
    vk_percent = ((r_pu**2 + x_pu**2) ** 0.5) * 100.0
    vkr_percent = r_pu * 100.0
    return sn_mva, vk_percent, vkr_percent


def _impedance_length_unit(properties: Dict[str, Any], default: str) -> str:
    return (
        properties.get("impedance_length_unit")
        or properties.get("impedance_unit")
        or default
    )


def _average_impedance_per_km(properties: Dict[str, Any], default_unit: str) -> complex:
    values = [
        _parse_complex(properties[key])
        for key in _IMPEDANCE_KEYS
        if key in properties and _parse_complex(properties[key]) != 0j
    ]
    if not values:
        return 0j

    impedance = sum(values, 0j) / len(values)
    unit = _impedance_length_unit(properties, default_unit)
    return complex(
        _per_distance_to_per_km(impedance.real, unit),
        _per_distance_to_per_km(impedance.imag, unit),
    )


def _line_impedance_per_km(
    line_properties: Dict[str, Any], config_properties: Dict[str, Any]
) -> tuple[float, float]:
    resistance = (
        _first_float(line_properties, _RESISTANCE_PER_KM_KEYS)
        or _first_float(config_properties, _RESISTANCE_PER_KM_KEYS)
        or _per_distance_to_per_km(
            _first_float(line_properties, _RESISTANCE_PER_MILE_KEYS), "mile"
        )
        or _per_distance_to_per_km(
            _first_float(config_properties, _RESISTANCE_PER_MILE_KEYS), "mile"
        )
        or _first_float(line_properties, _GENERIC_RESISTANCE_KEYS)
    )
    reactance = (
        _first_float(line_properties, _REACTANCE_PER_KM_KEYS)
        or _first_float(config_properties, _REACTANCE_PER_KM_KEYS)
        or _per_distance_to_per_km(
            _first_float(line_properties, _REACTANCE_PER_MILE_KEYS), "mile"
        )
        or _per_distance_to_per_km(
            _first_float(config_properties, _REACTANCE_PER_MILE_KEYS), "mile"
        )
        or _first_float(line_properties, _GENERIC_REACTANCE_KEYS)
    )

    if not resistance or not reactance:
        line_impedance = _average_impedance_per_km(line_properties, "km")
        config_impedance = _average_impedance_per_km(config_properties, "mile")
        impedance = line_impedance or config_impedance
        resistance = resistance or impedance.real
        reactance = reactance or impedance.imag

    if not resistance:
        resistance = _per_distance_to_per_km(
            _first_float(config_properties, _GENERIC_RESISTANCE_KEYS), "mile"
        )
    if not reactance:
        reactance = _per_distance_to_per_km(
            _first_float(config_properties, _GENERIC_REACTANCE_KEYS), "mile"
        )

    return resistance, reactance


def _inverter_bus_name(
    inverter_name: str, objects_by_name: Dict[str, Dict[str, Any]]
) -> str:
    inverter = objects_by_name.get(inverter_name, {})
    if inverter.get("obj_type") not in _INVERTER_OBJECTS:
        return ""
    return _clean(inverter.get("parent")) or inverter.get("properties", {}).get(
        "parent", ""
    )


def _solar_capacity_kw(
    properties: Dict[str, Any], inverter_properties: Dict[str, Any]
) -> float:
    if "rated_power" in inverter_properties:
        return _parse_float(inverter_properties["rated_power"]) / 1000.0
    if "rated_power" in properties:
        return _parse_float(properties["rated_power"]) / 1000.0
    area_m2 = _parse_area_square_meters(properties.get("area"))
    efficiency = _parse_float(properties.get("efficiency"), default=0.20)
    return area_m2 * efficiency


def _device_bus_name(parent: str, objects_by_name: Dict[str, Dict[str, Any]]) -> str:
    """Resolve the bus a battery/EV attaches to.

    A device may hang off an ``inverter`` (like PV) or sit directly on a
    ``node``/``meter`` bus. Try the inverter path first, else use the parent
    itself as the bus.
    """
    return _inverter_bus_name(parent, objects_by_name) or parent


def _battery_power_energy_kw_kwh(
    properties: Dict[str, Any], inverter_properties: Dict[str, Any]
) -> tuple[float, float]:
    """Return (power_kw, energy_kwh) for a GLM battery object.

    Power comes from the inverter ``rated_power`` (W) when present, else the
    battery's own ``rated_power``. Energy comes from the battery capacity in
    Wh (``battery_capacity``/``energy``/``capacity``).
    """
    if "rated_power" in inverter_properties:
        power_kw = _parse_float(inverter_properties["rated_power"]) / 1000.0
    else:
        power_kw = _parse_float(properties.get("rated_power")) / 1000.0
    energy_wh = _first_float(
        properties, ("battery_capacity", "energy", "capacity", "state_of_charge_wh")
    )
    return power_kw, energy_wh / 1000.0


def _ev_rating_kw(properties: Dict[str, Any]) -> float:
    """Per-port charging power (kW) from a GLM EV charger object."""
    watts = _first_float(
        properties,
        ("charge_rate", "max_charge_rate", "rated_power", "power_rating"),
    )
    return watts / 1000.0 if watts else 0.0


def _zone_partition(bus_names: List[str], lines: List[GridLine]) -> List[List[str]]:
    """Partition buses into transformer-bounded groups.

    A zone is *every bus under the same transformer*, so the partition is
    derived from the graph rather than read off a label: transformers are not
    line edges, so each connected component of the line-only graph is exactly
    one transformer's downstream set. Nested transformers fall out for free —
    an inner MV/LV unit's buses form their own component, separate from the
    outer unit's, so there is no "which transformer owns this bus" ambiguity.

    **Normally-open tie-switches are cut** as well: a tie is an inter-zone
    coupling by construction, and leaving it in the graph would merge the two
    zones it joins into one. Closed switches stay in — they are ordinary
    sectionalizing edges inside a zone.

    Components and their members both come back in bus load order, so codes and
    ``member_buses`` are stable across runs.
    """
    order = {name: idx for idx, name in enumerate(bus_names)}
    adjacency: Dict[str, List[str]] = {name: [] for name in bus_names}
    for line in lines:
        if line.is_switch and line.normally_open:
            continue
        if line.from_bus in adjacency and line.to_bus in adjacency:
            adjacency[line.from_bus].append(line.to_bus)
            adjacency[line.to_bus].append(line.from_bus)

    seen: set[str] = set()
    components: List[List[str]] = []
    for name in bus_names:
        if name in seen:
            continue
        seen.add(name)
        component = [name]
        queue = [name]
        while queue:
            current = queue.pop()
            for neighbour in adjacency[current]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    component.append(neighbour)
                    queue.append(neighbour)
        components.append(sorted(component, key=order.__getitem__))
    return components


def _build_zones(
    buses: List[GridBus],
    lines: List[GridLine],
    transformers: List[GridTransformer],
    pvs: List[GridPV],
    batteries: Optional[List[GridBattery]] = None,
) -> Tuple[Dict[str, Tuple[int, str]], Dict[int, ZoneSpec]]:
    """Derive zones from the transformer topology and bind PCC + DER buses.

    Membership comes from ``_zone_partition`` — the set of buses fed through one
    transformer — not from any authored label, so a zone cannot drift out of
    sync with the electrical topology. A component with no transformer on it is
    unzoned (code 0): that is the grid-edge/utility side, or a group left
    stranded by a missing transformer.

    The zone's point of common coupling is the transformer feeding the
    component; tripping it islands the zone. The DER bus is the member bus
    carrying the most dispatchable capacity — PV plus BESS power — so a large
    battery can serve as the island slack even in a PV-less zone; it forms the
    local slack that holds the zone's voltage when islanded (none -> dark on
    island).

    Returns ``(zone_by_bus, zones)`` where ``zone_by_bus`` maps a bus name to
    its ``(code, label)`` pair for stamping onto ``GridBus``.
    """
    der_kw_by_bus: Dict[str, float] = {}
    for pv in pvs:
        if pv.bus:
            der_kw_by_bus[pv.bus] = der_kw_by_bus.get(pv.bus, 0.0) + pv.capacity_kw
    for battery in batteries or []:
        if battery.bus:
            der_kw_by_bus[battery.bus] = (
                der_kw_by_bus.get(battery.bus, 0.0) + battery.power_kw
            )

    # (members, pcc_bus, pcc_transformer) per transformer-fed component. The PCC
    # is the first transformer *in declaration order* landing in the component;
    # more than one means the group is fed from several points, so opening the
    # PCC alone will not island it — warn rather than silently mis-model.
    zoned: List[Tuple[List[str], str, str]] = []
    for component in _zone_partition([bus.name for bus in buses], lines):
        member_set = set(component)
        feeders = [t for t in transformers if t.lv_bus in member_set]
        if not feeders:
            continue
        if len(feeders) > 1:
            logger.warning(
                "Bus group %s is fed by %d transformers (%s); using %s as its PCC "
                "— opening it alone will not island the zone.",
                component[0],
                len(feeders),
                ", ".join(t.name for t in feeders),
                feeders[0].name,
            )
        zoned.append((component, feeders[0].lv_bus, feeders[0].name))

    codes = _derive_zone_codes(transformer for _, _, transformer in zoned)

    zone_by_bus: Dict[str, Tuple[int, str]] = {}
    zones: Dict[int, ZoneSpec] = {}
    for member_buses, pcc_bus, pcc_transformer in zoned:
        code = codes[pcc_transformer]
        # Largest-DER member bus (PV + BESS power) becomes the island slack
        # reference (stable: ties break to the first member by load order). Empty
        # when the zone has no dispatchable resource.
        der_bus = ""
        best_kw = 0.0
        for name in member_buses:
            kw = der_kw_by_bus.get(name, 0.0)
            if kw > best_kw:
                best_kw = kw
                der_bus = name
        zones[code] = ZoneSpec(
            code=code,
            label=pcc_transformer,
            pcc_bus=pcc_bus,
            pcc_transformer=pcc_transformer,
            der_bus=der_bus,
            member_buses=tuple(member_buses),
            # A zone is defined by its transformer, so every zone has a PCC and
            # is islandable — unlike the old label-driven model, where a
            # `groupid` with no transformer produced a non-islandable zone.
            islandable=bool(pcc_transformer),
        )
        for name in member_buses:
            zone_by_bus[name] = (code, pcc_transformer)
    return zone_by_bus, zones


class GlmTopologyLoader:
    """Load a GLM topology file into ``GridTopology``."""

    def __init__(self) -> None:
        self.parser = GLMParser()

    def load(self, glm_path: str | Path) -> GridTopology:
        path = Path(glm_path)
        tokens = _all_tokens(self.parser.parse(path))
        objects_by_name = _named_objects(tokens)

        buses: List[GridBus] = []
        lines: List[GridLine] = []
        loads: List[GridLoad] = []
        pvs: List[GridPV] = []
        batteries: List[GridBattery] = []
        ev_stations: List[GridEVStation] = []
        transformers: List[GridTransformer] = []

        for token in tokens:
            obj_type = token.obj_type
            props = _clean_properties(token.properties)
            name = _clean(token.name) or props.get("name", "")

            if obj_type in _BUS_OBJECTS:
                # Zone is derived from the transformer topology once every bus,
                # line and transformer is parsed (see `_build_zones` below), so
                # buses start unzoned here. Any authored `groupid`/`zone` stays
                # readable in `properties` but no longer sets zone identity.
                buses.append(
                    GridBus(
                        name=name,
                        phases=props.get("phases", ""),
                        nominal_voltage=_parse_float(props.get("nominal_voltage")),
                        source_type=obj_type,
                        properties=props,
                    )
                )
                continue

            if obj_type in _LINE_OBJECTS:
                config_props = _line_configuration_properties(props, objects_by_name)
                line_properties = {**config_props, **props}
                resistance, reactance = _line_impedance_per_km(props, config_props)
                lines.append(
                    GridLine(
                        name=name,
                        from_bus=props.get("from", ""),
                        to_bus=props.get("to", ""),
                        length=_parse_float(props.get("length")),
                        length_unit=_parse_length_unit(props.get("length")),
                        resistance_ohm_per_km=resistance,
                        reactance_ohm_per_km=reactance,
                        capacity_kw=_first_float(
                            line_properties,
                            ("capacity_kw", "rating_kw", "emergency_rating_kw"),
                        ),
                        phases=props.get("phases", ""),
                        source_type=obj_type,
                        properties=line_properties,
                    )
                )
                continue

            if obj_type in _SWITCH_OBJECTS:
                # A switch is a near-ideal controllable edge. Honour an explicit
                # impedance/length if authored, else fall back to the LINE_*
                # defaults at build time (length 0 -> ~ideal short segment).
                resistance, reactance = _line_impedance_per_km(props, {})
                normally_open = _clean(props.get("status")).upper() == "OPEN"
                lines.append(
                    GridLine(
                        name=name,
                        from_bus=props.get("from", ""),
                        to_bus=props.get("to", ""),
                        length=_parse_float(props.get("length")),
                        length_unit=_parse_length_unit(props.get("length")),
                        resistance_ohm_per_km=resistance,
                        reactance_ohm_per_km=reactance,
                        capacity_kw=_first_float(
                            props, ("capacity_kw", "rating_kw", "emergency_rating_kw")
                        ),
                        phases=props.get("phases", ""),
                        source_type=obj_type,
                        is_switch=True,
                        normally_open=normally_open,
                        properties=props,
                    )
                )
                continue

            if obj_type in _LOAD_OBJECTS:
                power_values = [
                    _parse_complex(props[key])
                    for key in (
                        "constant_power_A",
                        "constant_power_B",
                        "constant_power_C",
                    )
                    if key in props
                ]
                if not power_values and "constant_power" in props:
                    power_values.append(_parse_complex(props["constant_power"]))

                loads.append(
                    GridLoad(
                        name=name,
                        parent=_clean(token.parent) or props.get("parent", ""),
                        constant_power=sum(power_values, 0j),
                        phases=props.get("phases", ""),
                        nominal_voltage=_parse_float(props.get("nominal_voltage")),
                        source_type=obj_type,
                        properties=props,
                    )
                )

            if obj_type in _TRANSFORMER_OBJECTS:
                cfg_props = _transformer_config_properties(props, objects_by_name)
                sn_mva, vk_percent, vkr_percent = _transformer_params(cfg_props)
                # GridLAB-D convention: `from` is the primary (HV) terminal,
                # `to` is the secondary (LV) terminal.
                transformers.append(
                    GridTransformer(
                        name=name,
                        hv_bus=props.get("from", ""),
                        lv_bus=props.get("to", ""),
                        sn_mva=sn_mva,
                        vk_percent=vk_percent,
                        vkr_percent=vkr_percent,
                        source_type=obj_type,
                        properties={**cfg_props, **props},
                    )
                )
                continue

            if obj_type in _PV_OBJECTS:
                parent = _clean(token.parent) or props.get("parent", "")
                inverter = objects_by_name.get(parent, {})
                inverter_props = inverter.get("properties", {})
                bus_name = _inverter_bus_name(parent, objects_by_name)
                pvs.append(
                    GridPV(
                        name=name,
                        parent=parent,
                        bus=bus_name,
                        capacity_kw=_solar_capacity_kw(props, inverter_props),
                        inverter_name=parent,
                        phases=props.get("phases", ""),
                        properties=props,
                    )
                )
                continue

            if obj_type in _BATTERY_OBJECTS:
                parent = _clean(token.parent) or props.get("parent", "")
                inverter_props = objects_by_name.get(parent, {}).get("properties", {})
                bus_name = _device_bus_name(parent, objects_by_name)
                power_kw, energy_kwh = _battery_power_energy_kw_kwh(
                    props, inverter_props
                )
                batteries.append(
                    GridBattery(
                        name=name,
                        parent=parent,
                        bus=bus_name,
                        power_kw=power_kw,
                        energy_kwh=energy_kwh,
                        inverter_name=(
                            parent
                            if _inverter_bus_name(parent, objects_by_name)
                            else ""
                        ),
                        phases=props.get("phases", ""),
                        properties=props,
                    )
                )
                continue

            if obj_type in _EVCHARGER_OBJECTS:
                parent = _clean(token.parent) or props.get("parent", "")
                bus_name = _device_bus_name(parent, objects_by_name)
                ev_stations.append(
                    GridEVStation(
                        name=name,
                        parent=parent,
                        bus=bus_name,
                        max_charger_kw=_ev_rating_kw(props),
                        num_ports=int(_first_float(props, ("num_ports", "ports")) or 1),
                        dc_fast=obj_type == "evcharger_det"
                        or _clean(props.get("charger_type")).upper() == "DC",
                        phases=props.get("phases", ""),
                        properties=props,
                    )
                )
                continue

        # Zones are derived from the transformer topology, then stamped back
        # onto their member buses (buses are frozen, so rebuild them).
        zone_by_bus, zones = _build_zones(buses, lines, transformers, pvs, batteries)
        buses = [
            (
                replace(
                    bus,
                    zone=zone_by_bus[bus.name][1],
                    zone_code=zone_by_bus[bus.name][0],
                )
                if bus.name in zone_by_bus
                else bus
            )
            for bus in buses
        ]

        return GridTopology(
            source="glm",
            source_path=str(path),
            buses=buses,
            lines=lines,
            loads=loads,
            pvs=pvs,
            batteries=batteries,
            ev_stations=ev_stations,
            transformers=transformers,
            zones=zones,
            metadata={"token_count": len(tokens)},
        )


def load_glm_topology(glm_path: str | Path) -> GridTopology:
    """Convenience wrapper for one-off GLM topology loading."""
    return GlmTopologyLoader().load(glm_path)
