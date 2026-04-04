"""
Duplicate Detection Validator

Detects duplicate electrical infrastructure elements in OSM data:
- Duplicate power poles at same location
- Duplicate transformers
- Duplicate substations
- Near-duplicate elements (within configurable distance)
"""

from typing import Dict, Any, List, Optional
import logging
import time
import math

from ..core.analyser import Analyser
from ..core.issue import OsmoseIssue, OsmoseValidationResult, IssueLevel, IssueCategory

logger = logging.getLogger(__name__)


class DuplicateDetection(Analyser):
    """
    Detects duplicate electrical infrastructure elements in OSM data.

    Checks:
    1. Duplicate power poles at same location (within 5m)
    2. Duplicate transformers at same location (within 5m)
    3. Duplicate substations at same location (within 10m)
    4. Near-duplicate elements (configurable distance threshold)
    """

    ITEM_DUPLICATE_POLE = 9301
    ITEM_DUPLICATE_TRANSFORMER = 9302
    ITEM_DUPLICATE_SUBSTATION = 9303
    ITEM_NEAR_DUPLICATE = 9304

    # Default distance thresholds (meters)
    DEFAULT_POLE_DIST_M = 5.0
    DEFAULT_TRANSFORMER_DIST_M = 5.0
    DEFAULT_SUBSTATION_DIST_M = 10.0
    DEFAULT_NEAR_DUPLICATE_DIST_M = 15.0

    def __init__(
        self,
        country: str = "TH",
        pole_dist_m: Optional[float] = None,
        transformer_dist_m: Optional[float] = None,
        substation_dist_m: Optional[float] = None,
        near_duplicate_dist_m: Optional[float] = None,
    ):
        super().__init__("duplicate_detection", country)

        self.pole_dist = pole_dist_m or self.DEFAULT_POLE_DIST_M
        self.transformer_dist = transformer_dist_m or self.DEFAULT_TRANSFORMER_DIST_M
        self.substation_dist = substation_dist_m or self.DEFAULT_SUBSTATION_DIST_M
        self.near_dup_dist = near_duplicate_dist_m or self.DEFAULT_NEAR_DUPLICATE_DIST_M

        self.errors[1] = self.def_class(
            item=self.ITEM_DUPLICATE_POLE,
            level=IssueLevel.HIGH,
            tags=[IssueCategory.GEOM, IssueCategory.POWER],
            title="Duplicate power poles at same location",
            detail=f"Multiple power poles found within {self.pole_dist}m of each other. "
                   "These are likely duplicates.",
            fix="Merge duplicate poles or verify they are separate facilities.",
        )

        self.errors[2] = self.def_class(
            item=self.ITEM_DUPLICATE_TRANSFORMER,
            level=IssueLevel.HIGH,
            tags=[IssueCategory.GEOM, IssueCategory.POWER],
            title="Duplicate transformers at same location",
            detail=f"Multiple transformers found within {self.transformer_dist}m. "
                   "These may be duplicates.",
            fix="Merge duplicate transformers or verify they are separate units.",
        )

        self.errors[3] = self.def_class(
            item=self.ITEM_DUPLICATE_SUBSTATION,
            level=IssueLevel.HIGH,
            tags=[IssueCategory.GEOM, IssueCategory.POWER],
            title="Duplicate substations at same location",
            detail=f"Multiple substations found within {self.substation_dist}m. "
                   "These may be duplicates or separate facilities.",
            fix="Merge duplicate substations or verify they are separate facilities.",
        )

        self.errors[4] = self.def_class(
            item=self.ITEM_NEAR_DUPLICATE,
            level=IssueLevel.NORMAL,
            tags=[IssueCategory.GEOM, IssueCategory.POWER],
            title="Near-duplicate power infrastructure elements",
            detail=f"Similar power infrastructure elements found within {self.near_dup_dist}m. "
                   "May indicate mapping error or actual close facilities.",
            fix="Review and merge if duplicates, or add distinguishing tags.",
        )

    def run(self, osm_data: Dict[str, Any]) -> OsmoseValidationResult:
        """
        Detect duplicate elements in OSM data.

        Args:
            osm_data: Dict with 'nodes', 'ways', 'relations' keys

        Returns:
            OsmoseValidationResult with all duplicate issues found
        """
        self._start_timer()
        issues = []

        nodes = osm_data.get("nodes", [])
        ways = osm_data.get("ways", [])

        # Categorize elements
        poles = []
        transformers = []
        substations = []
        all_power_elements = []

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
            all_power_elements.append(elem)

            if power == "pole":
                poles.append(elem)
            elif power == "transformer":
                transformers.append(elem)

        for way in ways:
            tags = way.get("tags", {})
            power = tags.get("power")
            if power in ("pole", "transformer", "substation"):
                # For ways, use first node as approximate location
                node_refs = way.get("nodes", [])
                if node_refs:
                    all_power_elements.append({
                        "type": "way",
                        "id": way.get("id"),
                        "lat": None,
                        "lon": None,
                        "tags": tags,
                    })

            if power == "substation":
                substations.append({
                    "type": "way",
                    "id": way.get("id"),
                    "lat": None,
                    "lon": None,
                    "tags": tags,
                })

        logger.info(
            f"Found {len(poles)} poles, {len(transformers)} transformers, "
            f"{len(substations)} substations"
        )

        # Check duplicates
        issues.extend(self._find_duplicates(poles, self.pole_dist, 1))
        issues.extend(self._find_duplicates(transformers, self.transformer_dist, 2))
        issues.extend(self._find_duplicates(substations, self.substation_dist, 3))

        # Check near-duplicates across different types
        issues.extend(self._find_near_duplicates(all_power_elements, self.near_dup_dist, 4))

        return self._compile_result(issues, len(nodes) + len(ways))

    def _find_duplicates(
        self,
        elements: List[Dict[str, Any]],
        threshold_m: float,
        class_id: int,
    ) -> List[OsmoseIssue]:
        """Find duplicate elements within threshold distance."""
        issues = []
        processed = set()

        for i, elem_a in enumerate(elements):
            if i in processed:
                continue
            if elem_a.get("lat") is None:
                continue

            duplicates = []
            for j, elem_b in enumerate(elements):
                if i >= j or j in processed:
                    continue
                if elem_b.get("lat") is None:
                    continue

                dist = self._haversine(
                    elem_a["lat"], elem_a["lon"],
                    elem_b["lat"], elem_b["lon"],
                )
                if dist < threshold_m:
                    processed.add(j)
                    duplicates.append((elem_b, dist))

            if duplicates:
                processed.add(i)
                dup_ids = ", ".join(
                    f"{d['type']} {d['id']}" for d, _ in duplicates
                )
                min_dist = min(d for _, d in duplicates)
                issues.append(self._create_issue(
                    class_id=class_id,
                    osm_type=elem_a["type"],
                    osm_id=elem_a["id"],
                    lat=elem_a["lat"],
                    lon=elem_a["lon"],
                    text=f"{len(duplicates)} duplicate(s) within {threshold_m}m: {dup_ids} (closest: {min_dist:.1f}m)",
                ))

        return issues

    def _find_near_duplicates(
        self,
        elements: List[Dict[str, Any]],
        threshold_m: float,
        class_id: int,
    ) -> List[OsmoseIssue]:
        """Find near-duplicate elements of different types."""
        issues = []
        processed_pairs = set()

        for i, elem_a in enumerate(elements):
            if elem_a.get("lat") is None:
                continue
            for j, elem_b in enumerate(elements):
                if i >= j:
                    continue
                if elem_b.get("lat") is None:
                    continue
                if elem_a["tags"].get("power") == elem_b["tags"].get("power"):
                    continue  # Same type - handled by _find_duplicates

                pair_key = (i, j)
                if pair_key in processed_pairs:
                    continue

                dist = self._haversine(
                    elem_a["lat"], elem_a["lon"],
                    elem_b["lat"], elem_b["lon"],
                )
                if dist < threshold_m:
                    processed_pairs.add(pair_key)
                    issues.append(self._create_issue(
                        class_id=class_id,
                        osm_type=elem_a["type"],
                        osm_id=elem_a["id"],
                        lat=elem_a["lat"],
                        lon=elem_a["lon"],
                        text=f"Near {elem_b['tags'].get('power')} {elem_b['type']} {elem_b['id']} at {dist:.1f}m",
                    ))

        return issues

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

    def _compile_result(self, issues: List[OsmoseIssue], total_objects: int) -> OsmoseValidationResult:
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
