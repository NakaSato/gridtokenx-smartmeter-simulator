"""
Microgrid Core

Electrical and geospatial boundary management for microgrid simulation:
- Geographic boundary polygon (auto-computed from meter coordinates)
- Point of Common Coupling (PCC) status tracking
- Feeder network topology (spanning tree from real meter coordinates)
- Grid-tied / islanded mode management with power flow simulation
"""

import math
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class GridMode(str, Enum):
    GRID_TIED = "grid-tied"
    ISLANDED = "islanded"
    TRANSITIONING = "transitioning"


@dataclass
class PCCStatus:
    """Point of Common Coupling status"""
    mode: GridMode = GridMode.GRID_TIED
    power_kw: float = 0.0          # positive = importing, negative = exporting
    voltage_pu: float = 1.0        # per-unit voltage at PCC
    frequency_hz: float = 50.0
    last_sync: float = 0.0         # timestamp

    def __post_init__(self):
        if not self.last_sync:
            self.last_sync = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value if isinstance(self.mode, GridMode) else self.mode,
            "power_kw": round(self.power_kw, 3),
            "voltage_pu": round(self.voltage_pu, 4),
            "frequency_hz": round(self.frequency_hz, 3),
            "last_sync": self.last_sync,
        }


@dataclass
class MicrogridBoundary:
    """Geographic boundary definition"""
    type: str = "Polygon"
    coordinates: List[List[List[float]]] = field(default_factory=list)


@dataclass
class FeederLink:
    """Single feeder connection"""
    from_id: str
    to_id: str
    from_lon: float
    from_lat: float
    to_lon: float
    to_lat: float
    is_cross_link: bool = False


class MicrogridCore:
    """
    Manages microgrid boundary, PCC, and feeder network.

    Boundary is auto-computed from meter coordinates with configurable padding.
    Feeder network is a spanning tree rooted at PCC with mesh cross-links.
    """

    # Default PCC location (substation side)
    DEFAULT_PCC_LON = 100.6605
    DEFAULT_PCC_LAT = 13.7570
    DEFAULT_PADDING_DEG = 0.001  # ~100m

    def __init__(
        self,
        pcc_lon: Optional[float] = None,
        pcc_lat: Optional[float] = None,
        padding_deg: Optional[float] = None,
    ):
        self.pcc_lon = pcc_lon or self.DEFAULT_PCC_LON
        self.pcc_lat = pcc_lat or self.DEFAULT_PCC_LAT
        self.padding_deg = padding_deg or self.DEFAULT_PADDING_DEG
        self.pcc_status = PCCStatus()
        self._meters: Dict[str, Dict[str, float]] = {}  # id -> {lon, lat, gen, cons}

    # ── Meter Management ────────────────────────────────────────────────

    def update_meters(self, meters: List[Dict[str, Any]]) -> None:
        """Update meter positions and electrical data"""
        self._meters.clear()
        for m in meters:
            if m.get("latitude") and m.get("longitude"):
                self._meters[m["meter_id"]] = {
                    "lon": float(m["longitude"]),
                    "lat": float(m["latitude"]),
                    "gen_kwh": float(m.get("generation", 0)),
                    "cons_kwh": float(m.get("consumption", 0)),
                }

    # ── Boundary Computation ────────────────────────────────────────────

    def compute_boundary(self) -> MicrogridBoundary:
        """Compute bounding box from meter coordinates + PCC with padding"""
        lons = [self.pcc_lon]
        lats = [self.pcc_lat]
        for m in self._meters.values():
            lons.append(m["lon"])
            lats.append(m["lat"])

        pad = self.padding_deg
        min_lon, max_lon = min(lons) - pad, max(lons) + pad
        min_lat, max_lat = min(lats) - pad, max(lats) + pad

        return MicrogridBoundary(
            coordinates=[[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]]
        )

    def boundary_geojson(self) -> Dict[str, Any]:
        """Return boundary as GeoJSON FeatureCollection"""
        b = self.compute_boundary()
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": b.coordinates,
                },
                "properties": {
                    "name": "Microgrid Boundary",
                    "area_km2": self._boundary_area_km2(b),
                },
            }],
        }

    def _boundary_area_km2(self, boundary: MicrogridBoundary) -> float:
        """Approximate area of bounding box in km²"""
        coords = boundary.coordinates[0]
        min_lon = min(c[0] for c in coords)
        max_lon = max(c[0] for c in coords)
        min_lat = min(c[1] for c in coords)
        max_lat = max(c[1] for c in coords)

        # Approximate at equator: 1° ≈ 111 km
        avg_lat = (min_lat + max_lat) / 2
        lon_km = (max_lon - min_lon) * 111.32 * math.cos(math.radians(avg_lat))
        lat_km = (max_lat - min_lat) * 110.574
        return round(lon_km * lat_km, 4)

    # ── Feeder Network ──────────────────────────────────────────────────

    def compute_feeders(self) -> Dict[str, Any]:
        """Build spanning tree feeder network from PCC to all meters"""
        if not self._meters:
            return {"type": "FeatureCollection", "features": []}

        visited = set()
        feeders: List[Dict[str, Any]] = []
        unvisited = dict(self._meters)

        # Start from PCC
        current_id = "PCC"
        current_lon, current_lat = self.pcc_lon, self.pcc_lat
        visited.add("PCC")

        while unvisited:
            # Find nearest unvisited meter
            nearest_id = None
            nearest_dist = float("inf")
            nearest = None
            for mid, m in unvisited.items():
                d = (m["lon"] - current_lon) ** 2 + (m["lat"] - current_lat) ** 2
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_id = mid
                    nearest = m

            if nearest and nearest_id:
                feeders.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [current_lon, current_lat],
                            [nearest["lon"], nearest["lat"]],
                        ],
                    },
                    "properties": {
                        "from": current_id,
                        "to": nearest_id,
                        "distance_m": round(math.sqrt(nearest_dist) * 111320, 1),
                    },
                })
                visited.add(nearest_id)
                del unvisited[nearest_id]
                current_id = nearest_id
                current_lon = nearest["lon"]
                current_lat = nearest["lat"]
            else:
                break

        # Add mesh cross-links (connect last meter back to PCC area)
        if len(feeders) >= 3:
            last = feeders[-1]
            last_coords = last["geometry"]["coordinates"][1]
            feeders.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [last_coords[0], last_coords[1]],
                        [self.pcc_lon, self.pcc_lat],
                    ],
                },
                "properties": {
                    "from": last["properties"]["to"],
                    "to": "PCC",
                    "is_cross_link": True,
                    "distance_m": round(
                        self._haversine_km(
                            last_coords[0], last_coords[1],
                            self.pcc_lon, self.pcc_lat,
                        ) * 1000
                    ),
                },
            })

        return {"type": "FeatureCollection", "features": feeders}

    # ── PCC Management ──────────────────────────────────────────────────

    @property
    def pcc(self) -> Dict[str, Any]:
        """Get PCC location and status"""
        return {
            "location": {
                "latitude": self.pcc_lat,
                "longitude": self.pcc_lon,
            },
            "status": self.pcc_status.to_dict(),
        }

    def set_mode(self, mode: GridMode) -> Dict[str, Any]:
        """Switch grid mode"""
        if mode == GridMode.TRANSITIONING:
            self.pcc_status.mode = GridMode.TRANSITIONING
            self.pcc_status.frequency_hz = 50.0
            return self.pcc_status.to_dict()

        self.pcc_status.mode = mode
        self.pcc_status.last_sync = time.time()

        if mode == GridMode.ISLANDED:
            self.pcc_status.power_kw = 0.0
            self.pcc_status.voltage_pu = 0.98
            self.pcc_status.frequency_hz = 49.95
        else:
            self.pcc_status.voltage_pu = 1.0
            self.pcc_status.frequency_hz = 50.0
            self._recalc_pcc_power()

        logger.info(f"PCC mode changed to {mode.value}")
        return self.pcc_status.to_dict()

    def _recalc_pcc_power(self) -> None:
        """Recalculate PCC power flow from meter data"""
        total_gen = sum(m["gen_kwh"] for m in self._meters.values())
        total_cons = sum(m["cons_kwh"] for m in self._meters.values())
        deficit = total_cons - total_gen

        if self.pcc_status.mode == GridMode.GRID_TIED and deficit > 0:
            self.pcc_status.power_kw = deficit
        else:
            self.pcc_status.power_kw = 0.0

    # ── Electrical Status ───────────────────────────────────────────────

    def electrical_status(self) -> Dict[str, Any]:
        """Full electrical boundary status"""
        total_gen = sum(m["gen_kwh"] for m in self._meters.values())
        total_cons = sum(m["cons_kwh"] for m in self._meters.values())
        net = total_gen - total_cons

        self._recalc_pcc_power()

        return {
            "pcc": self.pcc_status.to_dict(),
            "total_generation_kwh": round(total_gen, 3),
            "total_consumption_kwh": round(total_cons, 3),
            "net_energy_kwh": round(net, 3),
            "self_sufficiency_pct": round(
                (total_gen / total_cons * 100) if total_cons > 0 else 0, 1
            ),
            "island_capable": total_gen >= total_cons * 0.8,
            "meter_count": len(self._meters),
        }

    # ── Center Point ────────────────────────────────────────────────────

    @property
    def center(self) -> Dict[str, float]:
        """Compute center of all meters"""
        if not self._meters:
            return {"lat": self.pcc_lat, "lon": self.pcc_lon}
        lats = [m["lat"] for m in self._meters.values()]
        lons = [m["lon"] for m in self._meters.values()]
        return {
            "lat": sum(lats) / len(lats),
            "lon": sum(lons) / len(lons),
        }

    # ── Utilities ───────────────────────────────────────────────────────

    @staticmethod
    def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """Haversine distance in km"""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
