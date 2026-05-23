"""
Thailand Power Plant Registry
Real-world power plant data for grid simulation.
Sources: EGAT, Department of Alternative Energy, IEA Thailand Grid Assessment.

Provides:
- Plant inventory with location, capacity, fuel type, carbon intensity
- Grid integration: map plants to pandapower external grids
- API data: list, filter, group, stats
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class FuelType(str, Enum):
    NATURAL_GAS = "natural_gas"
    COAL = "coal"
    LIGNITE = "lignite"
    HYDRO = "hydro"
    SOLAR = "solar"
    WIND = "wind"
    BIOMASS = "biomass"
    BIOGAS = "biogas"
    DIESEL = "diesel"
    BATTERY = "battery_storage"
    WASTE = "waste_to_energy"
    NUCLEAR = "nuclear"  # Planned


class PlantRegion(str, Enum):
    BANGKOK = "bangkok"
    CENTRAL = "central"
    NORTH = "north"
    NORTHEAST = "northeast"
    SOUTH = "south"
    EAST = "east"


# Carbon intensity factors (g CO2/kWh) — Thai grid averages
CARBON_INTENSITY = {
    FuelType.NATURAL_GAS: 490,
    FuelType.COAL: 820,
    FuelType.LIGNITE: 1100,
    FuelType.HYDRO: 24,
    FuelType.SOLAR: 48,
    FuelType.WIND: 11,
    FuelType.BIOMASS: 230,
    FuelType.BIOGAS: 380,
    FuelType.DIESEL: 740,
    FuelType.BATTERY: 0,
    FuelType.WASTE: 550,
    FuelType.NUCLEAR: 12,
}


# ============================================================================
# Plant Data Model
# ============================================================================


@dataclass
class PowerPlant:
    """Single power plant record."""

    id: str
    name: str
    name_th: str
    fuel: FuelType
    region: PlantRegion
    province: str
    capacity_mw: float
    units: int = 1
    commission_year: int = 0
    operator: str = "EGAT"
    lat: float = 0.0
    lon: float = 0.0
    status: str = "operational"  # operational, planned, decommissioned
    notes: str = ""

    @property
    def carbon_intensity(self) -> float:
        return CARBON_INTENSITY.get(self.fuel, 500)

    @property
    def is_renewable(self) -> bool:
        return self.fuel in (
            FuelType.HYDRO,
            FuelType.SOLAR,
            FuelType.WIND,
            FuelType.BIOMASS,
            FuelType.BIOGAS,
        )

    @property
    def is_dispatchable(self) -> bool:
        """Can the plant ramp output on demand?"""
        return self.fuel in (
            FuelType.NATURAL_GAS,
            FuelType.COAL,
            FuelType.HYDRO,
            FuelType.DIESEL,
            FuelType.BATTERY,
            FuelType.WASTE,
        )


# ============================================================================
# Thai Power Plant Database
# Based on EGAT installed capacity data (2024–2026).
# Reference: https://www.egat.co.th/home/statistics/
# ============================================================================

PLANTS: List[PowerPlant] = [
    # ── Natural Gas (Combined Cycle) — backbone of Thai grid (~60%) ──
    PowerPlant(
        "bangpakong",
        "Bang Pakong",
        "บางปะกง",
        FuelType.NATURAL_GAS,
        PlantRegion.EAST,
        "Chachoengsao",
        capacity_mw=3500,
        units=7,
        commission_year=1989,
        lat=13.60,
        lon=100.90,
        operator="EGAT",
    ),
    PowerPlant(
        "chana",
        "Chana",
        "จะนะ",
        FuelType.NATURAL_GAS,
        PlantRegion.SOUTH,
        "Songkhla",
        capacity_mw=1432,
        units=2,
        commission_year=2001,
        lat=6.95,
        lon=100.83,
        operator="EGAT",
    ),
    PowerPlant(
        "krabi",
        "Krabi",
        "กระบี่",
        FuelType.NATURAL_GAS,
        PlantRegion.SOUTH,
        "Krabi",
        capacity_mw=800,
        units=2,
        commission_year=1996,
        lat=8.09,
        lon=98.91,
        operator="EGAT",
        status="decommissioned",
    ),
    PowerPlant(
        "nongchok",
        "Nong Chok",
        "หนองจอก",
        FuelType.NATURAL_GAS,
        PlantRegion.BANGKOK,
        "Bangkok",
        capacity_mw=2400,
        units=4,
        commission_year=1993,
        lat=13.87,
        lon=100.85,
        operator="EGAT",
    ),
    PowerPlant(
        "ratburi",
        "Ratchaburi",
        "ราชบุรี",
        FuelType.NATURAL_GAS,
        PlantRegion.CENTRAL,
        "Ratchaburi",
        capacity_mw=4400,
        units=6,
        commission_year=1998,
        lat=13.53,
        lon=99.81,
        operator="Ratchaburi Electricity",
    ),
    PowerPlant(
        "wangnoi",
        "Wang Noi",
        "วังน้อย",
        FuelType.NATURAL_GAS,
        PlantRegion.CENTRAL,
        "Ayutthaya",
        capacity_mw=2300,
        units=4,
        commission_year=1994,
        lat=14.20,
        lon=100.69,
        operator="EGAT",
    ),
    PowerPlant(
        "southbangkok",
        "South Bangkok",
        "บางกอกน้อย",
        FuelType.NATURAL_GAS,
        PlantRegion.BANGKOK,
        "Bangkok",
        capacity_mw=1200,
        units=2,
        commission_year=1987,
        lat=13.74,
        lon=100.48,
        operator="EGAT",
    ),
    PowerPlant(
        "phraeksa",
        "Phraeksa",
        "แพรกษา",
        FuelType.NATURAL_GAS,
        PlantRegion.CENTRAL,
        "Samut Prakan",
        capacity_mw=1650,
        units=3,
        commission_year=2001,
        lat=13.57,
        lon=100.60,
        operator="EGAT",
    ),
    # ── Coal / Lignite ──
    PowerPlant(
        "maemoh",
        "Mae Moh",
        "แม่เมาะ",
        FuelType.LIGNITE,
        PlantRegion.NORTH,
        "Lampang",
        capacity_mw=2450,
        units=9,
        commission_year=1955,
        lat=18.44,
        lon=99.65,
        operator="EGAT",
    ),
    PowerPlant(
        "banpaew",
        "Ban Pae",
        "บ้านแพ้ว",
        FuelType.COAL,
        PlantRegion.CENTRAL,
        "Samut Sakhon",
        capacity_mw=890,
        units=1,
        commission_year=2018,
        lat=13.68,
        lon=100.27,
        operator="GLOW",
    ),
    # ── Hydro (Thailand limited, plus Mekong imports) ──
    PowerPlant(
        "bhumibol",
        "Bhumibol Dam",
        "เขื่อนภูมิพล",
        FuelType.HYDRO,
        PlantRegion.NORTH,
        "Tak",
        capacity_mw=768,
        units=8,
        commission_year=1964,
        lat=17.18,
        lon=99.06,
        operator="EGAT",
    ),
    PowerPlant(
        "sirikit",
        "Sirikit Dam",
        "เขื่อนสิริกิติ์",
        FuelType.HYDRO,
        PlantRegion.NORTH,
        "Uttaradit",
        capacity_mw=500,
        units=4,
        commission_year=1972,
        lat=17.65,
        lon=100.60,
        operator="EGAT",
    ),
    PowerPlant(
        "rajjaprabha",
        "Ratchaprapha",
        "เขื่อนรัชชประภา",
        FuelType.HYDRO,
        PlantRegion.SOUTH,
        "Surat Thani",
        capacity_mw=240,
        units=3,
        commission_year=1987,
        lat=8.68,
        lon=98.81,
        operator="EGAT",
    ),
    PowerPlant(
        "sirindhorn",
        "Sirindhorn Dam",
        "เขื่อนสิรินธร",
        FuelType.HYDRO,
        PlantRegion.NORTHEAST,
        "Ubon Ratchathani",
        capacity_mw=36,
        units=3,
        commission_year=1971,
        lat=15.17,
        lon=105.33,
        operator="EGAT",
    ),
    # ── Solar (rooftop + farm, major capacity in NE) ──
    PowerPlant(
        "loei_solar",
        "Loei Solar Farm",
        "ฟาร์มโซลาร์เซลล์เลย",
        FuelType.SOLAR,
        PlantRegion.NORTHEAST,
        "Loei",
        capacity_mw=120,
        units=1,
        commission_year=2019,
        lat=17.49,
        lon=101.73,
        operator="EGAT",
    ),
    PowerPlant(
        "nakornratchasima_solar",
        "Nakhon Ratchasima Solar",
        "โซลาร์โคราช",
        FuelType.SOLAR,
        PlantRegion.NORTHEAST,
        "Nakhon Ratchasima",
        capacity_mw=90,
        units=1,
        commission_year=2020,
        lat=14.97,
        lon=102.10,
        operator="GPP",
    ),
    PowerPlant(
        "lopburi_solar",
        "Lopburi Solar",
        "โซลาร์ลพบุรี",
        FuelType.SOLAR,
        PlantRegion.CENTRAL,
        "Lopburi",
        capacity_mw=85,
        units=1,
        commission_year=2018,
        lat=14.80,
        lon=100.62,
        operator="SPCG",
    ),
    # ── Wind ──
    PowerPlant(
        "phetchabun_wind",
        "Phetchabun Wind",
        "ฟาร์มลมเพชรบูรณ์",
        FuelType.WIND,
        PlantRegion.NORTH,
        "Phetchabun",
        capacity_mw=90,
        units=1,
        commission_year=2020,
        lat=16.42,
        lon=101.16,
        operator="B.Grimm",
    ),
    PowerPlant(
        "nakornsithammarat_wind",
        "Nakhon Si Wind",
        "ลมนครศรี",
        FuelType.WIND,
        PlantRegion.SOUTH,
        "Nakhon Si Thammarat",
        capacity_mw=55,
        units=1,
        commission_year=2021,
        lat=8.43,
        lon=99.96,
        operator="Wind Energy Holding",
    ),
    # ── Biomass ──
    PowerPlant(
        "buriram_biomass",
        "Buriram Biomass",
        "ชีวมวลบุรีรัมย์",
        FuelType.BIOMASS,
        PlantRegion.NORTHEAST,
        "Buriram",
        capacity_mw=30,
        units=1,
        commission_year=2017,
        lat=14.99,
        lon=103.10,
        operator="Local",
    ),
    PowerPlant(
        "kanchanaburi_biomass",
        "Kanchanaburi Biomass",
        "ชีวมวลกาญจนบุรี",
        FuelType.BIOMASS,
        PlantRegion.CENTRAL,
        "Kanchanaburi",
        capacity_mw=25,
        units=1,
        commission_year=2016,
        lat=14.02,
        lon=99.54,
        operator="Local",
    ),
    # ── Biogas (from agricultural waste) ──
    PowerPlant(
        "saraburi_biogas",
        "Saraburi Biogas",
        "ไบโอแก๊สระบุรี",
        FuelType.BIOGAS,
        PlantRegion.CENTRAL,
        "Saraburi",
        capacity_mw=12,
        units=1,
        commission_year=2015,
        lat=14.53,
        lon=100.91,
        operator="Local",
    ),
    # ── Battery Storage (EGAT pilot) ──
    PowerPlant(
        "phuket_battery",
        "Phuket BESS",
        "แบตเตอรี่ภูเก็ต",
        FuelType.BATTERY,
        PlantRegion.SOUTH,
        "Phuket",
        capacity_mw=21,
        units=1,
        commission_year=2022,
        lat=7.88,
        lon=98.39,
        operator="EGAT",
    ),
    # ── Diesel (Island backup) ──
    PowerPlant(
        "kohsamui_diesel",
        "Ko Samui Diesel",
        "ดีเซลเกาะสมุย",
        FuelType.DIESEL,
        PlantRegion.SOUTH,
        "Surat Thani",
        capacity_mw=15,
        units=2,
        commission_year=2005,
        lat=9.51,
        lon=100.01,
        operator="PEA",
        notes="Backup generators for island grid",
    ),
]


# ============================================================================
# Registry API
# ============================================================================


class PowerPlantRegistry:
    """
    In-memory registry of Thai power plants with query, filter, and stats.
    Used by both the simulator grid model and REST API.
    """

    def __init__(self, plants: Optional[List[PowerPlant]] = None):
        self.plants: List[PowerPlant] = plants if plants is not None else list(PLANTS)
        self._by_id: Dict[str, PowerPlant] = {p.id: p for p in self.plants}

    # ── Queries ──

    def get_by_id(self, plant_id: str) -> Optional[PowerPlant]:
        return self._by_id.get(plant_id)

    def list_all(
        self,
        fuel: Optional[FuelType] = None,
        region: Optional[PlantRegion] = None,
        status: Optional[str] = "operational",
        limit: int = 100,
    ) -> List[PowerPlant]:
        results = self.plants
        if fuel:
            results = [p for p in results if p.fuel == fuel]
        if region:
            results = [p for p in results if p.region == region]
        if status:
            results = [p for p in results if p.status == status]
        return results[:limit]

    def search(self, query: str) -> List[PowerPlant]:
        """Search by name (EN or TH)."""
        q = query.lower()
        return [p for p in self.plants if q in p.name.lower() or q in p.name_th.lower()]

    def nearby(
        self, lat: float, lon: float, radius_km: float = 50.0
    ) -> List[PowerPlant]:
        """Find plants within radius of coordinates."""
        results = []
        for p in self.plants:
            if p.lat == 0.0 and p.lon == 0.0:
                continue
            # Haversine approximation
            dlat = abs(p.lat - lat)
            dlon = abs(p.lon - lon)
            dist = ((dlat * 111.0) ** 2 + (dlon * 111.0 * 0.9) ** 2) ** 0.5
            if dist <= radius_km:
                results.append((dist, p))
        results.sort(key=lambda x: x[0])
        return [p for _, p in results]

    # ── Aggregation ──

    def stats(self) -> Dict:
        total = sum(p.capacity_mw for p in self.plants if p.status == "operational")
        operational = [p for p in self.plants if p.status == "operational"]

        by_fuel: Dict[str, float] = {}
        by_region: Dict[str, float] = {}
        renewable_mw = 0.0
        thermal_mw = 0.0

        for p in operational:
            by_fuel.setdefault(p.fuel.value, 0.0)
            by_fuel[p.fuel.value] += p.capacity_mw

            by_region.setdefault(p.region.value, 0.0)
            by_region[p.region.value] += p.capacity_mw

            if p.is_renewable:
                renewable_mw += p.capacity_mw
            else:
                thermal_mw += p.capacity_mw

        avg_carbon = (
            sum(p.carbon_intensity * p.capacity_mw for p in operational) / total
            if total > 0
            else 0
        )

        return {
            "total_plants": len(operational),
            "total_capacity_mw": round(total, 1),
            "renewable_mw": round(renewable_mw, 1),
            "thermal_mw": round(thermal_mw, 1),
            "renewable_pct": round(renewable_mw / total * 100, 1) if total else 0,
            "avg_carbon_intensity_gco2_kwh": round(avg_carbon, 0),
            "by_fuel": {k: round(v, 1) for k, v in by_fuel.items()},
            "by_region": {k: round(v, 1) for k, v in by_region.items()},
        }

    def group_by(self, field: str) -> Dict[str, List[Dict]]:
        """Group plants by a field name, return as nested dict of records."""
        grouped: Dict[str, List[Dict]] = {}
        for p in self.plants:
            key = getattr(p, field, "unknown")
            if isinstance(key, Enum):
                key = key.value
            rec = self._to_dict(p)
            grouped.setdefault(str(key), []).append(rec)
        return grouped

    def _to_dict(self, p: PowerPlant) -> Dict:
        return {
            "id": p.id,
            "name": p.name,
            "name_th": p.name_th,
            "fuel": p.fuel.value,
            "region": p.region.value,
            "province": p.province,
            "capacity_mw": p.capacity_mw,
            "units": p.units,
            "commission_year": p.commission_year,
            "operator": p.operator,
            "lat": p.lat,
            "lon": p.lon,
            "status": p.status,
            "carbon_intensity_gco2_kwh": p.carbon_intensity,
            "is_renewable": p.is_renewable,
            "is_dispatchable": p.is_dispatchable,
        }


# Singleton
_registry: Optional[PowerPlantRegistry] = None


def get_registry() -> PowerPlantRegistry:
    global _registry
    if _registry is None:
        _registry = PowerPlantRegistry()
    return _registry


def reset_registry(plants: Optional[List[PowerPlant]] = None) -> None:
    """Reset with custom plant list (for testing)."""
    global _registry
    _registry = PowerPlantRegistry(plants)
