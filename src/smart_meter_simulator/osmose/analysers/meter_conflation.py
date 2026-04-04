"""
Meter Conflation Validator

Matches simulator smart meters to OSM power infrastructure:
- Matches meters to nearest power pole
- Matches meters to nearest substation (for large consumers)
- Flags meters with no nearby infrastructure
- Validates meter GPS accuracy against OSM infrastructure
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
import time
import math
from dataclasses import dataclass, field

from ..core.analyser import Analyser
from ..core.issue import OsmoseIssue, OsmoseValidationResult, IssueLevel, IssueCategory

logger = logging.getLogger(__name__)


@dataclass
class MeterMatch:
    """Result of meter-to-infrastructure matching."""
    meter_id: str
    meter_lat: float
    meter_lon: float
    matched_type: Optional[str] = None  # 'pole', 'substation', 'transformer'
    matched_id: Optional[int] = None
    matched_lat: Optional[float] = None
    matched_lon: Optional[float] = None
    distance_m: float = float("inf")
    confidence: float = 0.0
    status: str = "unmatched"  # 'matched', 'unmatched', 'suspicious'


@dataclass
class ConflationConfig:
    """Configuration for meter conflation."""
    max_pole_distance_m: float = 50.0
    max_substation_distance_m: float = 100.0
    max_transformer_distance_m: float = 30.0
    suspicious_distance_m: float = 200.0  # Flag if > this but < unmatched threshold


class MeterConflation(Analyser):
    """
    Matches simulator smart meters to OSM power infrastructure.

    Checks:
    1. Meters matched to nearest power pole (within 50m)
    2. Meters assigned to nearest substation (within 100m)
    3. Unmatched meters (no infrastructure within 500m)
    4. Suspicious distances (>200m from nearest infrastructure)
    """

    ITEM_UNMATCHED_METER = 9401
    ITEM_SUSPICIOUS_DISTANCE = 9402
    ITEM_MULTI_MATCH = 9403
    ITEM_METER_OUTSIDE_GRID = 9404

    def __init__(
        self,
        country: str = "TH",
        config: Optional[ConflationConfig] = None,
    ):
        super().__init__("meter_conflation", country)

        self.config = config or ConflationConfig()

        # Infrastructure lookup index
        self._poles: List[Dict[str, Any]] = []
        self._substations: List[Dict[str, Any]] = []
        self._transformers: List[Dict[str, Any]] = []

        self.errors[1] = self.def_class(
            item=self.ITEM_UNMATCHED_METER,
            level=IssueLevel.NORMAL,
            tags=[IssueCategory.SEMANTIC, IssueCategory.POWER],
            title="Smart meter not matched to any power infrastructure",
            detail=f"This meter has no power pole, substation, or transformer "
                   f"within {self.config.max_pole_distance_m}m. "
                   "The meter may be misplaced or infrastructure may be missing from OSM.",
            fix="Check the meter location and add nearby power infrastructure to OSM if missing.",
        )

        self.errors[2] = self.def_class(
            item=self.ITEM_SUSPICIOUS_DISTANCE,
            level=IssueLevel.LOW,
            tags=[IssueCategory.GEOM, IssueCategory.POWER],
            title="Smart meter far from power infrastructure",
            detail=f"This meter is more than {self.config.suspicious_distance_m}m from the "
                   "nearest power infrastructure. The GPS accuracy may be poor.",
            fix="Verify the meter GPS coordinates and adjust if necessary.",
        )

        self.errors[3] = self.def_class(
            item=self.ITEM_MULTI_MATCH,
            level=IssueLevel.LOW,
            tags=[IssueCategory.GEOM, IssueCategory.POWER],
            title="Smart meter equidistant to multiple infrastructure elements",
            detail="This meter is approximately equidistant to multiple poles/transformers. "
                   "The assignment is ambiguous.",
            fix="Verify the meter location and assign to the correct infrastructure element.",
        )

        self.errors[4] = self.def_class(
            item=self.ITEM_METER_OUTSIDE_GRID,
            level=IssueLevel.HIGH,
            tags=[IssueCategory.GEOM, IssueCategory.POWER],
            title="Smart meter outside grid coverage area",
            detail="This meter is located outside any known grid coverage area. "
                   "It may be incorrectly located or the grid boundary needs updating.",
            fix="Verify the meter is actually connected to the grid and update the location if needed.",
        )

    def load_infrastructure(self, osm_data: Dict[str, Any]):
        """
        Pre-load infrastructure from OSM data for matching.

        Call this before run() to populate the infrastructure index.

        Args:
            osm_data: Dict with 'nodes', 'ways', 'relations' keys
        """
        nodes = osm_data.get("nodes", [])
        for node in nodes:
            tags = node.get("tags", {})
            power = tags.get("power")
            lat, lon = node.get("lat"), node.get("lon")
            if lat is None or lon is None:
                continue

            elem = {
                "type": "node",
                "id": node.get("id"),
                "lat": lat,
                "lon": lon,
                "tags": tags,
            }

            if power == "pole":
                self._poles.append(elem)
            elif power == "transformer":
                self._transformers.append(elem)
            elif power == "substation":
                self._substations.append(elem)

        logger.info(
            f"Loaded infrastructure index: {len(self._poles)} poles, "
            f"{len(self._transformers)} transformers, {len(self._substations)} substations"
        )

    def run(self, meter_data: List[Dict[str, Any]],
            osm_data: Optional[Dict[str, Any]] = None) -> OsmoseValidationResult:
        """
        Match meters to infrastructure and validate.

        Args:
            meter_data: List of meter dicts with 'meter_id', 'lat', 'lon' keys
            osm_data: Optional OSM data (if load_infrastructure not called separately)

        Returns:
            OsmoseValidationResult with all matching issues
        """
        self._start_timer()

        # Load infrastructure if not already loaded
        if osm_data and not self._poles and not self._substations:
            self.load_infrastructure(osm_data)

        issues = []
        matches: List[MeterMatch] = []
        total_objects = len(meter_data)

        for meter in meter_data:
            match = self._match_meter(meter)
            matches.append(match)

            if match.status == "unmatched":
                issues.append(self._create_issue(
                    class_id=1,
                    osm_type="meter",
                    osm_id=hash(match.meter_id),
                    lat=match.meter_lat,
                    lon=match.meter_lon,
                    text=f"No infrastructure within {self.config.max_pole_distance_m}m",
                ))
            elif match.status == "suspicious":
                issues.append(self._create_issue(
                    class_id=2,
                    osm_type="meter",
                    osm_id=hash(match.meter_id),
                    lat=match.meter_lat,
                    lon=match.meter_lon,
                    text=f"Distance to nearest {match.matched_type}: {match.distance_m:.0f}m",
                ))

        return self._compile_result(issues, total_objects, matches)

    def _match_meter(self, meter: Dict[str, Any]) -> MeterMatch:
        """Match a single meter to nearest infrastructure."""
        meter_id = meter.get("meter_id", str(meter.get("id", "unknown")))
        lat = meter.get("lat") or meter.get("latitude")
        lon = meter.get("lon") or meter.get("longitude")

        if lat is None or lon is None:
            return MeterMatch(
                meter_id=meter_id,
                meter_lat=0,
                meter_lon=0,
                status="unmatched",
            )

        match = MeterMatch(
            meter_id=meter_id,
            meter_lat=lat,
            meter_lon=lon,
        )

        # Find nearest pole
        nearest_pole, pole_dist = self._find_nearest(lat, lon, self._poles)
        # Find nearest transformer
        nearest_xfm, xfm_dist = self._find_nearest(lat, lon, self._transformers)
        # Find nearest substation
        nearest_sub, sub_dist = self._find_nearest(lat, lon, self._substations)

        # Pick best match based on thresholds
        candidates = [
            ("pole", nearest_pole, pole_dist, self.config.max_pole_distance_m),
            ("transformer", nearest_xfm, xfm_dist, self.config.max_transformer_distance_m),
            ("substation", nearest_sub, sub_dist, self.config.max_substation_distance_m),
        ]

        best_match = None
        best_dist = float("inf")
        ambiguous = False

        for inf_type, inf_elem, dist, threshold in candidates:
            if dist < threshold and dist < best_dist:
                if best_dist - dist < 5:  # Within 5m = ambiguous
                    ambiguous = True
                best_match = (inf_type, inf_elem, dist)
                best_dist = dist

        if best_match:
            inf_type, inf_elem, dist = best_match
            match.matched_type = inf_type
            match.matched_id = inf_elem["id"]
            match.matched_lat = inf_elem["lat"]
            match.matched_lon = inf_elem["lon"]
            match.distance_m = dist
            match.confidence = max(0, 1.0 - (dist / self.config.suspicious_distance_m))

            if dist > self.config.suspicious_distance_m:
                match.status = "suspicious"
            else:
                match.status = "matched"

            if ambiguous:
                # Log ambiguous match
                logger.debug(f"Ambiguous match for {meter_id}: multiple infrastructure nearby")

        else:
            # Check if truly unmatched or just far
            min_dist = min(pole_dist, xfm_dist, sub_dist)
            if min_dist < self.config.suspicious_distance_m:
                match.status = "suspicious"
                match.distance_m = min_dist
            else:
                match.status = "unmatched"
                match.distance_m = min_dist

        return match

    def _find_nearest(
        self,
        lat: float,
        lon: float,
        elements: List[Dict[str, Any]],
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """Find nearest element to given coordinates."""
        best = None
        best_dist = float("inf")

        for elem in elements:
            elat = elem.get("lat")
            elon = elem.get("lon")
            if elat is None or elon is None:
                continue

            dist = self._haversine(lat, lon, elat, elon)
            if dist < best_dist:
                best_dist = dist
                best = elem

        return best, best_dist

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance in meters."""
        R = 6371000
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def get_match_summary(self, matches: List[MeterMatch]) -> Dict[str, Any]:
        """Generate summary of matching results."""
        matched = sum(1 for m in matches if m.status == "matched")
        suspicious = sum(1 for m in matches if m.status == "suspicious")
        unmatched = sum(1 for m in matches if m.status == "unmatched")
        total = len(matches)

        avg_dist = (
            sum(m.distance_m for m in matches if m.distance_m < float("inf"))
            / max(1, matched + suspicious)
        )

        return {
            "total_meters": total,
            "matched": matched,
            "suspicious": suspicious,
            "unmatched": unmatched,
            "match_rate": f"{matched / max(1, total) * 100:.1f}%",
            "avg_distance_m": round(avg_dist, 1),
        }

    def _compile_result(
        self,
        issues: List[OsmoseIssue],
        total_objects: int,
        matches: List[MeterMatch],
    ) -> OsmoseValidationResult:
        """Compile validation result."""
        issues_by_level = {"1": 0, "2": 0, "3": 0}
        issues_by_item: Dict[str, int] = {}
        issues_by_tag: Dict[str, int] = {}

        for issue in issues:
            issues_by_level[str(issue.level)] += 1
            item_key = str(issue.item)
            issues_by_item[item_key] = issues_by_item.get(item_key, 0) + 1
            for tag in issue.tags:
                issues_by_tag[tag] = issues_by_tag.get(tag, 0) + 1

        return OsmoseValidationResult(
            analyser=self.analyser_id,
            country=self.country,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            total_objects=total_objects,
            total_issues=len(issues),
            issues_by_level=issues_by_level,
            issues_by_item=issues_by_item,
            issues_by_tag=issues_by_tag,
            issues=issues,
            processing_time_ms=self._stop_timer(),
        )
