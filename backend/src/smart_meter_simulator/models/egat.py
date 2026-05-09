from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class EGATSubstation:
    sub_id: str
    name: str
    name_en: str
    voltage_kv: float
    sub_type: str
    latitude: float
    longitude: float
    province: str
    region: str
    capacity_mva: float
    connected_generators: List[str] = field(default_factory=list)
    notes: str = ""

@dataclass
class EGATLine:
    line_id: str
    from_substation: str
    to_substation: str
    voltage_kv: float
    length_km: float
    circuit: int
    conductor: str
    line_type: str
    status: str
    notes: str = ""

@dataclass
class EGATPowerPlant:
    plant_id: str
    name: str
    plant_type: str
    capacity_mw: float
    status: str
    latitude: float
    longitude: float
    source: str = ""
