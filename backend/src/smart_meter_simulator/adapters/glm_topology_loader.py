"""
GLM topology loader for the simulator core.

This module turns ``.glm`` topology objects into the shared ``GridTopology``
model. It intentionally handles topology and static load extraction only; no
external solver is executed by the core loader.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from smart_meter_simulator.core.topology import (
    GridBus,
    GridLine,
    GridLoad,
    GridPV,
    GridTopology,
)

from .glm_converter import GLMParser, GLMToken


_BUS_OBJECTS = {"node", "meter", "substation"}
_LINE_OBJECTS = {"overhead_line", "underground_line", "triplex_line"}
_LINE_CONFIGURATION_OBJECTS = {
    "line_configuration",
    "overhead_line_configuration",
    "underground_line_configuration",
    "triplex_line_configuration",
}
_LOAD_OBJECTS = {"load"}
_INVERTER_OBJECTS = {"inverter", "inverter_dyn"}
_PV_OBJECTS = {"solar"}
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

        for token in tokens:
            obj_type = token.obj_type
            props = _clean_properties(token.properties)
            name = _clean(token.name) or props.get("name", "")

            if obj_type in _BUS_OBJECTS:
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

        return GridTopology(
            source="glm",
            source_path=str(path),
            buses=buses,
            lines=lines,
            loads=loads,
            pvs=pvs,
            metadata={"token_count": len(tokens)},
        )


def load_glm_topology(glm_path: str | Path) -> GridTopology:
    """Convenience wrapper for one-off GLM topology loading."""
    return GlmTopologyLoader().load(glm_path)
