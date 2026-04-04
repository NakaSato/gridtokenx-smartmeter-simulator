"""
Power Line Connectivity Validator

Validates OSM power=line and power=cable elements:
- Dangling line ends (not connected to substation/transformer)
- Self-intersecting lines
- Missing voltage tags
- Invalid conductor material tags
"""

from typing import Dict, Any, List, Optional, Set
import logging
import time

from ..core.analyser import Analyser
from ..core.issue import OsmoseIssue, OsmoseValidationResult, IssueLevel, IssueCategory

logger = logging.getLogger(__name__)


class PowerLineConnectivity(Analyser):
    """
    Validates OSM power=line and power=cable connectivity.

    Checks:
    1. Dangling line ends (not connected to substation/transformer/other line)
    2. Missing voltage tag on power lines
    3. Self-intersecting power lines
    4. Invalid conductor material
    5. Lines crossing without junction
    """

    ITEM_DANGLING_END = 9201
    ITEM_MISSING_VOLTAGE = 9202
    ITEM_SELF_INTERSECTING = 9203
    ITEM_INVALID_CONDUCTOR = 9204
    ITEM_UNJUNCTIONED_CROSSING = 9205

    VALID_MATERIALS = {
        "aluminum", "copper", "aluminium", "acsr", "aac", "aaac",
        "steel", "optical", "opgw", "adss",
    }

    def __init__(self, country: str = "TH"):
        super().__init__("power_line_connectivity", country)

        self.errors[1] = self.def_class(
            item=self.ITEM_DANGLING_END,
            level=IssueLevel.HIGH,
            tags=[IssueCategory.TOPOLOGY, IssueCategory.POWER],
            title="Power line not connected at one end",
            detail="This power line has an endpoint that is not connected to a substation, "
                   "transformer, or another power line.",
            fix="Extend the line to connect to the nearest facility, or add a junction node.",
        )

        self.errors[2] = self.def_class(
            item=self.ITEM_MISSING_VOLTAGE,
            level=IssueLevel.NORMAL,
            tags=[IssueCategory.TAG, IssueCategory.POWER],
            title="Power line missing voltage tag",
            detail="Power lines should have a `voltage=*` tag specifying the voltage level.",
            fix="Add the `voltage=*` tag with the correct voltage in volts.",
        )

        self.errors[3] = self.def_class(
            item=self.ITEM_SELF_INTERSECTING,
            level=IssueLevel.NORMAL,
            tags=[IssueCategory.GEOM, IssueCategory.POWER],
            title="Self-intersecting power line",
            detail="This power line intersects itself. This may be a mapping error.",
            fix="Review the line geometry and fix any incorrect node ordering.",
        )

        self.errors[4] = self.def_class(
            item=self.ITEM_INVALID_CONDUCTOR,
            level=IssueLevel.LOW,
            tags=[IssueCategory.TAG, IssueCategory.POWER],
            title="Power line with invalid conductor material",
            detail="The `material=*` or `conductor=*` tag has an unrecognized value.",
            fix="Use a standard material: aluminum, copper, acsr, aac, steel.",
        )

        self.errors[5] = self.def_class(
            item=self.ITEM_UNJUNCTIONED_CROSSING,
            level=IssueLevel.LOW,
            tags=[IssueCategory.TOPOLOGY, IssueCategory.POWER],
            title="Power line crosses another line without junction",
            detail="Two power lines cross but there is no shared node at the intersection.",
            fix="Add a junction node at the crossing point if lines are connected.",
        )

    def run(self, osm_data: Dict[str, Any]) -> OsmoseValidationResult:
        """
        Validate power line connectivity.

        Args:
            osm_data: Dict with 'nodes', 'ways', 'relations' keys

        Returns:
            OsmoseValidationResult with all issues found
        """
        self._start_timer()
        issues = []

        nodes = osm_data.get("nodes", [])
        ways = osm_data.get("ways", [])

        # Build node lookup
        node_map: Dict[int, Dict] = {}
        for node in nodes:
            node_id = node.get("id")
            if node_id is not None:
                node_map[node_id] = node

        # Extract power lines
        power_lines = self._extract_power_lines(ways, node_map)
        logger.info(f"Found {len(power_lines)} power lines to validate")

        # Check 1: Missing voltage
        for line in power_lines:
            if "voltage" not in line["tags"]:
                issues.append(self._create_issue(
                    class_id=2,
                    osm_type="way",
                    osm_id=line["id"],
                    text="Missing voltage=* tag on power line",
                ))

        # Check 2: Invalid conductor material
        for line in power_lines:
            material = line["tags"].get("material") or line["tags"].get("conductor")
            if material and material.lower() not in self.VALID_MATERIALS:
                issues.append(self._create_issue(
                    class_id=4,
                    osm_type="way",
                    osm_id=line["id"],
                    text=f"Invalid conductor material: {material}",
                ))

        # Check 3: Dangling ends
        issues.extend(self._check_dangling_ends(power_lines, node_map))

        # Check 4: Self-intersecting
        issues.extend(self._check_self_intersecting(power_lines))

        # Check 5: Unjunctioned crossings
        issues.extend(self._check_crossings(power_lines))

        return self._compile_result(issues, len(nodes) + len(ways))

    def _extract_power_lines(self, ways: List[Dict], node_map: Dict) -> List[Dict[str, Any]]:
        """Extract power=line and power=cable ways."""
        power_lines = []
        for way in ways:
            tags = way.get("tags", {})
            if tags.get("power") in ("line", "cable", "minor_line"):
                node_refs = way.get("nodes", [])
                coords = []
                for ref in node_refs:
                    if ref in node_map:
                        n = node_map[ref]
                        coords.append((n.get("lat"), n.get("lon")))
                power_lines.append({
                    "id": way.get("id"),
                    "tags": tags,
                    "node_refs": node_refs,
                    "coords": coords,
                })
        return power_lines

    def _check_dangling_ends(self, power_lines: List[Dict], node_map: Dict) -> List[OsmoseIssue]:
        """Check for line ends not connected to any facility."""
        issues = []

        # Build set of all endpoints
        all_endpoints: Dict[int, List[int]] = {}  # node_ref -> list of line_ids
        facility_nodes: Set[int] = set()  # nodes that are substations/transformers

        for node_id, node_data in node_map.items():
            tags = node_data.get("tags", {})
            if tags.get("power") in ("substation", "transformer", "pole", "tower"):
                facility_nodes.add(node_id)

        for line in power_lines:
            refs = line["node_refs"]
            if not refs:
                continue
            all_endpoints.setdefault(refs[0], []).append(line["id"])
            if len(refs) > 1:
                all_endpoints.setdefault(refs[-1], []).append(line["id"])

        # Find dangling ends: endpoint appears in only 1 line AND is not a facility
        for node_ref, line_ids in all_endpoints.items():
            if len(line_ids) == 1 and node_ref not in facility_nodes:
                node_data = node_map.get(node_ref, {})
                issues.append(self._create_issue(
                    class_id=1,
                    osm_type="way",
                    osm_id=line_ids[0],
                    lat=node_data.get("lat"),
                    lon=node_data.get("lon"),
                    text=f"Dangling end at node {node_ref}",
                ))

        return issues

    def _check_self_intersecting(self, power_lines: List[Dict]) -> List[OsmoseIssue]:
        """Check for self-intersecting power lines."""
        issues = []

        for line in power_lines:
            coords = line["coords"]
            if len(coords) < 4:
                continue  # Need at least 4 points for self-intersection

            # Check if any segment intersects with any other segment
            for i in range(len(coords) - 1):
                for j in range(i + 2, len(coords) - 1):
                    if i == 0 and j == len(coords) - 2:
                        continue  # Skip adjacent segments
                    if self._segments_intersect(coords[i], coords[i + 1], coords[j], coords[j + 1]):
                        issues.append(self._create_issue(
                            class_id=3,
                            osm_type="way",
                            osm_id=line["id"],
                            lat=coords[i][0],
                            lon=coords[i][1],
                            text="Self-intersecting power line",
                        ))
                        break
                else:
                    continue
                break

        return issues

    def _check_crossings(self, power_lines: List[Dict]) -> List[OsmoseIssue]:
        """Check for unjunctioned crossings between power lines."""
        issues = []
        # Build shared node set
        line_node_sets = []
        for line in power_lines:
            line_node_sets.append(set(line["node_refs"]))

        for i in range(len(power_lines)):
            for j in range(i + 1, len(power_lines)):
                # Check if lines share any nodes
                shared = line_node_sets[i] & line_node_sets[j]
                if shared:
                    continue  # Connected, not a crossing

                # Check segment intersections
                coords_a = power_lines[i]["coords"]
                coords_b = power_lines[j]["coords"]
                if self._polylines_intersect(coords_a, coords_b):
                    issues.append(self._create_issue(
                        class_id=5,
                        osm_type="way",
                        osm_id=power_lines[i]["id"],
                        text=f"Crosses power line {power_lines[j]['id']} without junction",
                    ))

        return issues

    @staticmethod
    def _segments_intersect(a1: tuple, a2: tuple, b1: tuple, b2: tuple) -> bool:
        """Check if segment a1-a2 intersects segment b1-b2."""
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        return ccw(a1, b1, b2) != ccw(a2, b1, b2) and ccw(a1, a2, b1) != ccw(a1, a2, b2)

    @staticmethod
    def _polylines_intersect(coords_a: List[tuple], coords_b: List[tuple]) -> bool:
        """Check if any segment in polyline A intersects any segment in polyline B."""
        for i in range(len(coords_a) - 1):
            for j in range(len(coords_b) - 1):
                if PowerLineConnectivity._segments_intersect(
                    coords_a[i], coords_a[i + 1], coords_b[j], coords_b[j + 1]
                ):
                    return True
        return False

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
