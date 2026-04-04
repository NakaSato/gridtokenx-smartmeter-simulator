"""
Power Substation Validator

Validates OSM power=substation elements:
- Missing voltage/substation tags
- Invalid transformer counts
- Orphaned substations (not connected to any power line)
- Substation type validation (transmission vs distribution)
"""

from typing import Dict, Any, List, Optional
import logging
import time

from ..core.analyser import Analyser
from ..core.issue import OsmoseIssue, OsmoseValidationResult, IssueLevel, IssueCategory

logger = logging.getLogger(__name__)


class PowerSubstationValidator(Analyser):
    """
    Validates OSM power=substation elements for completeness and correctness.

    Checks:
    1. Missing 'voltage' tag
    2. Missing 'substation' type (transmission/distribution)
    3. Invalid transformer count (>0 if specified)
    4. Orphaned substations (not connected to power lines)
    5. Duplicate substations at same location
    """

    # Item codes (following OSMOSE convention: 9xxx for power)
    ITEM_MISSING_VOLTAGE = 9101
    ITEM_MISSING_TYPE = 9102
    ITEM_INVALID_TRANSFORMERS = 9103
    ITEM_ORPHANED_SUBSTATION = 9104
    ITEM_DUPLICATE_SUBSTATION = 9105

    # Valid substation types
    VALID_SUBSTATION_TYPES = {"transmission", "distribution", "traction", "converter"}

    # Valid voltage levels (kV) for Thai grid
    VALID_VOLTAGES_KV = {
        # Transmission (EGAT)
        500, 230, 115,
        # Distribution (MEA/PEA)
        22, 11.5, 6.6, 0.4,
    }

    def __init__(self, country: str = "TH", power_lines: Optional[List[Dict[str, Any]]] = None):
        """
        Args:
            country: Country code
            power_lines: List of power line GeoJSON features (for orphan detection)
        """
        super().__init__("power_substation_validator", country)

        # Define issue classes
        self.errors[1] = self.def_class(
            item=self.ITEM_MISSING_VOLTAGE,
            level=IssueLevel.HIGH,
            tags=[IssueCategory.TAG, IssueCategory.POWER],
            title="Substation missing voltage tag",
            detail="Power substations should have a `voltage=*` tag specifying the voltage level(s). "
                   "Multiple values separated by `;` are accepted.",
            fix="Add the `voltage=*` tag with the correct voltage in volts (e.g., `22000` for 22 kV).",
            example="node 123456: power=substation, voltage=22000",
        )

        self.errors[2] = self.def_class(
            item=self.ITEM_MISSING_TYPE,
            level=IssueLevel.NORMAL,
            tags=[IssueCategory.TAG, IssueCategory.POWER],
            title="Substation missing type tag",
            detail="Power substations should have a `substation=*` tag indicating the type "
                   "(transmission, distribution, traction, converter).",
            fix="Add `substation=transmission` or `substation=distribution` as appropriate.",
        )

        self.errors[3] = self.def_class(
            item=self.ITEM_INVALID_TRANSFORMERS,
            level=IssueLevel.LOW,
            tags=[IssueCategory.TAG, IssueCategory.POWER],
            title="Substation with zero or negative transformer count",
            detail="If `transformers=*` is specified, it should be a positive integer.",
            fix="Remove the tag or set it to the actual number of transformers.",
        )

        self.errors[4] = self.def_class(
            item=self.ITEM_ORPHANED_SUBSTATION,
            level=IssueLevel.NORMAL,
            tags=[IssueCategory.TOPOLOGY, IssueCategory.POWER],
            title="Orphaned substation not connected to any power line",
            detail="This substation is not connected to any power line. "
                   "It may be missing `power=line` or `power=cable` connections.",
            fix="Verify the substation location and add connecting power lines if they exist.",
        )

        self.errors[5] = self.def_class(
            item=self.ITEM_DUPLICATE_SUBSTATION,
            level=IssueLevel.HIGH,
            tags=[IssueCategory.GEOM, IssueCategory.POWER],
            title="Duplicate substations at same location",
            detail="Multiple substations found within 10 meters of each other. "
                   "These may be duplicates or separate facilities.",
            fix="Merge duplicate substations or verify they are separate facilities.",
        )

        # Build spatial index for power lines
        self._line_endpoints: List[tuple] = []
        if power_lines:
            for line in power_lines:
                geom = line.get("geometry", {})
                if geom.get("type") == "LineString":
                    coords = geom.get("coordinates", [])
                    if coords:
                        self._line_endpoints.append((coords[0][1], coords[0][0]))  # lat, lon
                        self._line_endpoints.append((coords[-1][1], coords[-1][0]))

        logger.info(f"Initialized PowerSubstationValidator with {len(self._line_endpoints)} line endpoints")

    def run(self, osm_data: Dict[str, Any]) -> OsmoseValidationResult:
        """
        Validate power substations in OSM data.

        Args:
            osm_data: Dict with 'nodes', 'ways', 'relations' keys

        Returns:
            OsmoseValidationResult with all issues found
        """
        self._start_timer()
        issues = []

        nodes = osm_data.get("nodes", [])
        ways = osm_data.get("ways", [])

        # Collect all substations (nodes and way centers)
        substations = self._extract_substations(nodes, ways)
        logger.info(f"Found {len(substations)} substations to validate")

        # Check each substation
        for sub in substations:
            issues.extend(self._validate_tags(sub))

        # Check for orphaned substations
        issues.extend(self._check_orphaned(substations))

        # Check for duplicates
        issues.extend(self._check_duplicates(substations))

        return self._compile_result(issues, len(nodes) + len(ways))

    def _extract_substations(self, nodes: List[Dict], ways: List[Dict]) -> List[Dict[str, Any]]:
        """Extract all substation elements from OSM data."""
        substations = []

        # Node substations
        for node in nodes:
            tags = node.get("tags", {})
            if tags.get("power") == "substation":
                substations.append({
                    "type": "node",
                    "id": node.get("id"),
                    "lat": node.get("lat"),
                    "lon": node.get("lon"),
                    "tags": tags,
                })

        # Way substations (use centroid)
        for way in ways:
            tags = way.get("tags", {})
            if tags.get("power") == "substation":
                nodes_refs = way.get("nodes", [])
                if nodes_refs:
                    # For ways, we use the first node as approximate location
                    # In production, this would compute the actual centroid
                    substations.append({
                        "type": "way",
                        "id": way.get("id"),
                        "lat": None,  # Would need node lookup for centroid
                        "lon": None,
                        "tags": tags,
                        "node_refs": nodes_refs,
                    })

        return substations

    def _validate_tags(self, substation: Dict[str, Any]) -> List[OsmoseIssue]:
        """Validate tags on a single substation."""
        issues = []
        tags = substation["tags"]
        sub_id = substation["id"]
        sub_type = substation["type"]
        lat = substation.get("lat")
        lon = substation.get("lon")

        # Check 1: Missing voltage
        if "voltage" not in tags:
            issues.append(self._create_issue(
                class_id=1,
                osm_type=sub_type,
                osm_id=sub_id,
                lat=lat,
                lon=lon,
                text="Missing voltage=* tag",
            ))

        # Check 2: Missing substation type
        if "substation" not in tags:
            issues.append(self._create_issue(
                class_id=2,
                osm_type=sub_type,
                osm_id=sub_id,
                lat=lat,
                lon=lon,
                text="Missing substation=* tag",
            ))
        elif tags.get("substation") not in self.VALID_SUBSTATION_TYPES:
            # Invalid substation type
            issues.append(self._create_issue(
                class_id=2,
                osm_type=sub_type,
                osm_id=sub_id,
                lat=lat,
                lon=lon,
                text=f"Invalid substation type: {tags.get('substation')}",
            ))

        # Check 3: Invalid transformer count
        if "transformers" in tags:
            try:
                count = int(tags["transformers"])
                if count <= 0:
                    issues.append(self._create_issue(
                        class_id=3,
                        osm_type=sub_type,
                        osm_id=sub_id,
                        lat=lat,
                        lon=lon,
                        text=f"transformers={count} (should be > 0)",
                    ))
            except ValueError:
                issues.append(self._create_issue(
                    class_id=3,
                    osm_type=sub_type,
                    osm_id=sub_id,
                    lat=lat,
                    lon=lon,
                    text=f"transformers={tags['transformers']} (not an integer)",
                ))

        return issues

    def _check_orphaned(self, substations: List[Dict[str, Any]]) -> List[OsmoseIssue]:
        """Check for substations not connected to any power line."""
        if not self._line_endpoints:
            return []  # No line data, skip orphan check

        issues = []
        threshold_m = 50  # meters

        for sub in substations:
            lat = sub.get("lat")
            lon = sub.get("lon")
            if lat is None or lon is None:
                continue

            # Check if any line endpoint is within threshold
            connected = False
            for ep_lat, ep_lon in self._line_endpoints:
                dist = self._haversine(lat, lon, ep_lat, ep_lon)
                if dist < threshold_m:
                    connected = True
                    break

            if not connected:
                issues.append(self._create_issue(
                    class_id=4,
                    osm_type=sub["type"],
                    osm_id=sub["id"],
                    lat=lat,
                    lon=lon,
                    text="Not connected to any power line within 50m",
                ))

        return issues

    def _check_duplicates(self, substations: List[Dict[str, Any]]) -> List[OsmoseIssue]:
        """Check for duplicate substations at same location."""
        issues = []
        threshold_m = 10  # meters
        checked = set()

        for i, sub_a in enumerate(substations):
            if i in checked:
                continue
            lat_a = sub_a.get("lat")
            lon_a = sub_a.get("lon")
            if lat_a is None or lon_a is None:
                continue

            for j, sub_b in enumerate(substations):
                if i >= j or j in checked:
                    continue
                lat_b = sub_b.get("lat")
                lon_b = sub_b.get("lon")
                if lat_b is None or lon_b is None:
                    continue

                dist = self._haversine(lat_a, lon_a, lat_b, lon_b)
                if dist < threshold_m:
                    checked.add(i)
                    checked.add(j)
                    issues.append(self._create_issue(
                        class_id=5,
                        osm_type=sub_a["type"],
                        osm_id=sub_a["id"],
                        lat=lat_a,
                        lon=lon_a,
                        text=f"Duplicate at {dist:.1f}m from node {sub_b['id']}",
                    ))
                    break

        return issues

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance in meters."""
        import math
        R = 6371000  # Earth radius in meters
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
