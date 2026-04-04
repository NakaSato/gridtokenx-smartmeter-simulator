"""
Power Infrastructure Validation Module

Based on OSMOSE QA Power Validation Rules:
https://github.com/osmose-qa/osmose-backend/tree/master/plugins
https://github.com/osmose-qa/osmose-backend/tree/master/analysers

Implements validation for:
- Power transformers (node vs way/relation)
- Voltage tagging (voltage:primary, voltage:secondary)
- Power line topology
- Tower/pole positioning
- Line management tagging
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ValidationLevel(str, Enum):
    """OSMOSE validation severity levels"""
    HIGH = 1      # Critical errors
    NORMAL = 2    # Common mistakes
    LOW = 3       # Suggestions


class IssueCategory(str, Enum):
    """Issue classification categories"""
    GEOMETRY = "geom"
    TAG = "tag"
    TOPOLOGY = "topology"
    SEMANTIC = "semantic"


class PowerIssue(BaseModel):
    """Represents a power infrastructure validation issue"""
    id: int = Field(..., description="Unique issue identifier")
    item: int = Field(..., description="Category code (9xxx for infrastructure)")
    level: ValidationLevel = Field(..., description="Severity level")
    tags: List[str] = Field(..., description="Issue tags")
    title: str = Field(..., description="Issue title")
    detail: Optional[str] = Field(None, description="Detailed explanation")
    fix: Optional[str] = Field(None, description="Fix suggestion")
    trap: Optional[str] = Field(None, description="Common mistakes to avoid")
    example: Optional[str] = Field(None, description="Example of the issue")
    
    # OSM object reference
    osm_type: Optional[str] = Field(None, description="OSM object type (node/way/relation)")
    osm_id: Optional[int] = Field(None, description="OSM object ID")
    
    # Location
    lat: Optional[float] = Field(None, description="Latitude")
    lon: Optional[float] = Field(None, description="Longitude")
    
    # Issue specifics
    subclass: Optional[int] = Field(None, description="Sub-classifier")
    text: Optional[str] = Field(None, description="Subtitle with specific values")
    
    # Fix suggestions
    fix_suggestions: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Structured fix suggestions"
    )


class PowerValidationResult(BaseModel):
    """Result of power infrastructure validation"""
    total_objects: int = Field(..., description="Total objects validated")
    total_issues: int = Field(..., description="Total issues found")
    issues_by_level: Dict[str, int] = Field(..., description="Issues grouped by severity")
    issues_by_category: Dict[str, int] = Field(..., description="Issues grouped by category")
    issues: List[PowerIssue] = Field(..., description="List of all issues")
    
    # Statistics
    transformers_validated: int = 0
    power_lines_validated: int = 0
    towers_validated: int = 0
    poles_validated: int = 0
    substations_validated: int = 0


class PowerValidator:
    """
    Power Infrastructure Validator
    
    Implements OSMOSE-style validation rules for power infrastructure:
    - Power transformers must be nodes
    - Use voltage:primary/voltage:secondary instead of voltage on transformers
    - Power line voltage consistency
    - Tower/pole positioning
    - Line management tagging
    """
    
    # Issue class definitions (matching OSMOSE item/class system)
    ISSUE_CLASSES = {
        # Transformers
        91001: {
            "item": 9100,
            "level": ValidationLevel.NORMAL,
            "tags": ["power", "fix:chair", "geom"],
            "title": "Power Transformers should always be on a node",
            "detail": "Power transformers must be mapped as nodes, not as ways or relations.",
            "fix": "Convert the transformer way/relation to a node at the transformer location.",
        },
        91002: {
            "item": 9100,
            "level": ValidationLevel.NORMAL,
            "tags": ["power", "fix:chair", "tag"],
            "title": "On Power Transformers use voltage:primary=* and voltage:secondary=* in place of voltage",
            "detail": "Transformers have multiple voltage levels. Use separate tags for primary and secondary voltages.",
            "fix": "Replace voltage=* with voltage:primary=* and voltage:secondary=* tags.",
            "example": "voltage:primary=115000; voltage:secondary=22000",
        },
        
        # Power Lines
        91101: {
            "item": 9110,
            "level": ValidationLevel.LOW,
            "tags": ["power", "voltage"],
            "title": "Power line missing voltage tag",
            "detail": "Power lines should have a voltage tag to indicate their operating voltage.",
            "fix": "Add voltage=* tag with the line's operating voltage in volts.",
        },
        91102: {
            "item": 9110,
            "level": ValidationLevel.NORMAL,
            "tags": ["power", "voltage", "tag"],
            "title": "Power line voltage format should be numeric",
            "detail": "Voltage should be specified in volts as a number (e.g., 115000 not 115kV).",
            "fix": "Convert voltage value to volts (multiply kV by 1000).",
            "example": "Use 115000 instead of 115kV",
        },
        91103: {
            "item": 9110,
            "level": ValidationLevel.LOW,
            "tags": ["power", "cables"],
            "title": "Power line missing cables tag",
            "detail": "Power lines should specify the number of conductors with cables=*.",
            "fix": "Add cables=* tag (typically multiples of 3: 3, 6, 9, 12).",
        },
        
        # Towers and Poles
        91201: {
            "item": 9120,
            "level": ValidationLevel.LOW,
            "tags": ["power", "tower:type"],
            "title": "Tower missing type",
            "detail": "Power towers should have a tower:type=* tag describing their structure.",
            "fix": "Add tower:type=* (e.g., lattice, tubular, pole).",
        },
        91202: {
            "item": 9120,
            "level": ValidationLevel.LOW,
            "tags": ["power", "line_management"],
            "title": "Support structure missing line_management tag",
            "detail": "Power line supports should have line_management=* to describe their topology function.",
            "fix": "Add line_management=* (straight, branch, split, termination, etc.).",
            "example": "line_management=termination for end anchors",
        },
        
        # Substations
        91301: {
            "item": 9130,
            "level": ValidationLevel.LOW,
            "tags": ["power", "substation"],
            "title": "Substation missing voltage",
            "detail": "Substations should have a voltage=* tag.",
            "fix": "Add voltage=* with the highest voltage level in the substation.",
        },
        91302: {
            "item": 9130,
            "level": ValidationLevel.LOW,
            "tags": ["power", "substation"],
            "title": "Substation missing type",
            "detail": "Substations should have substation=* tag (transmission, distribution, etc.).",
            "fix": "Add substation=* (transmission, distribution, minor_distribution).",
        },
        
        # Line Management
        91401: {
            "item": 9140,
            "level": ValidationLevel.LOW,
            "tags": ["power", "line_management"],
            "title": "Unknown line_management value",
            "detail": "The line_management value is not in the standard set.",
            "fix": "Use standard values: straight, branch, split, transpose, termination, transition, cross.",
        },
        91402: {
            "item": 9140,
            "level": ValidationLevel.LOW,
            "tags": ["power", "line_arrangement"],
            "title": "Unknown line_arrangement value",
            "detail": "The line_arrangement value is not in the standard set.",
            "fix": "Use standard values: horizontal, vertical, semi_vertical, triangle.",
        },
    }
    
    def __init__(self):
        self.issues: List[PowerIssue] = []
        self.stats = {
            "transformers_validated": 0,
            "power_lines_validated": 0,
            "towers_validated": 0,
            "poles_validated": 0,
            "substations_validated": 0,
        }
    
    def validate(self, osm_data: Dict[str, Any]) -> PowerValidationResult:
        """
        Validate power infrastructure from OSM data
        
        Args:
            osm_data: OSM data in dict format with nodes, ways, relations
            
        Returns:
            PowerValidationResult with all validation issues
        """
        self.issues = []
        self.stats = {
            "transformers_validated": 0,
            "power_lines_validated": 0,
            "towers_validated": 0,
            "poles_validated": 0,
            "substations_validated": 0,
        }
        
        # Validate nodes
        for node in osm_data.get("nodes", []):
            self._validate_node(node)
        
        # Validate ways
        for way in osm_data.get("ways", []):
            self._validate_way(way)
        
        # Validate relations
        for relation in osm_data.get("relations", []):
            self._validate_relation(relation)
        
        # Compile results
        return self._compile_results()
    
    def _validate_node(self, node: Dict[str, Any]):
        """Validate a power node"""
        tags = node.get("tags", {})
        
        if tags.get("power") == "transformer":
            self.stats["transformers_validated"] += 1
            self._check_transformer_voltage(node)
        
        elif tags.get("power") == "tower":
            self.stats["towers_validated"] += 1
            self._check_tower_tags(node)
        
        elif tags.get("power") == "pole":
            self.stats["poles_validated"] += 1
            self._check_pole_tags(node)
        
        elif tags.get("power") == "substation":
            self.stats["substations_validated"] += 1
            self._check_substation_tags(node)
    
    def _validate_way(self, way: Dict[str, Any]):
        """Validate a power way"""
        tags = way.get("tags", {})
        
        if tags.get("power") == "transformer":
            # Transformers should not be ways
            self._add_issue(
                91001,
                osm_type="way",
                osm_id=way.get("id"),
                text=f"Transformer way {way.get('id')}"
            )
        
        elif tags.get("power") in ["line", "minor_line"]:
            self.stats["power_lines_validated"] += 1
            self._check_power_line_tags(way)
    
    def _validate_relation(self, relation: Dict[str, Any]):
        """Validate a power relation"""
        tags = relation.get("tags", {})
        
        if tags.get("power") == "transformer":
            # Transformers should not be relations
            self._add_issue(
                91001,
                osm_type="relation",
                osm_id=relation.get("id"),
                text=f"Transformer relation {relation.get('id')}"
            )
        
        elif tags.get("power") == "line":
            self.stats["power_lines_validated"] += 1
            self._check_power_line_tags(relation)
    
    def _check_transformer_voltage(self, node: Dict[str, Any]):
        """Check transformer voltage tagging"""
        tags = node.get("tags", {})
        
        if "voltage" in tags:
            # Should use voltage:primary and voltage:secondary instead
            self._add_issue(
                91002,
                osm_type="node",
                osm_id=node.get("id"),
                text=f"voltage={tags.get('voltage')}",
                fix_suggestions=[
                    {
                        "-": ["voltage"],
                        "+": {
                            "voltage:primary": tags.get("voltage", "115000"),
                            "voltage:secondary": "22000"
                        }
                    }
                ]
            )
    
    def _check_power_line_tags(self, way: Dict[str, Any]):
        """Check power line tagging"""
        tags = way.get("tags", {})
        
        # Check for missing voltage
        if "voltage" not in tags:
            self._add_issue(
                91101,
                osm_type=way.get("type", "way"),
                osm_id=way.get("id"),
                text="Missing voltage tag"
            )
        else:
            # Check voltage format
            voltage = tags.get("voltage", "")
            if not voltage.replace(";", "").isdigit():
                self._add_issue(
                    91102,
                    osm_type=way.get("type", "way"),
                    osm_id=way.get("id"),
                    text=f"voltage={voltage}"
                )
        
        # Check for missing cables
        if "cables" not in tags:
            self._add_issue(
                91103,
                osm_type=way.get("type", "way"),
                osm_id=way.get("id"),
                text="Missing cables tag"
            )
    
    def _check_tower_tags(self, node: Dict[str, Any]):
        """Check tower tagging"""
        tags = node.get("tags", {})
        
        if "tower:type" not in tags:
            self._add_issue(
                91201,
                osm_type="node",
                osm_id=node.get("id"),
                text="Missing tower:type"
            )
        
        if "line_management" not in tags:
            self._add_issue(
                91202,
                osm_type="node",
                osm_id=node.get("id"),
                text="Missing line_management"
            )
    
    def _check_pole_tags(self, node: Dict[str, Any]):
        """Check pole tagging"""
        tags = node.get("tags", {})
        
        if "line_management" not in tags:
            self._add_issue(
                91202,
                osm_type="node",
                osm_id=node.get("id"),
                text="Missing line_management"
            )
    
    def _check_substation_tags(self, node: Dict[str, Any]):
        """Check substation tagging"""
        tags = node.get("tags", {})
        
        if "voltage" not in tags:
            self._add_issue(
                91301,
                osm_type="node",
                osm_id=node.get("id"),
                text="Missing voltage"
            )
        
        if "substation" not in tags:
            self._add_issue(
                91302,
                osm_type="node",
                osm_id=node.get("id"),
                text="Missing substation type"
            )
    
    def _add_issue(
        self,
        issue_id: int,
        osm_type: Optional[str] = None,
        osm_id: Optional[int] = None,
        text: Optional[str] = None,
        fix_suggestions: Optional[List[Dict[str, Any]]] = None
    ):
        """Add a validation issue"""
        issue_class = self.ISSUE_CLASSES.get(issue_id, {})
        
        issue = PowerIssue(
            id=issue_id,
            item=issue_class.get("item", 9000),
            level=issue_class.get("level", ValidationLevel.LOW),
            tags=issue_class.get("tags", ["power"]),
            title=issue_class.get("title", "Unknown issue"),
            detail=issue_class.get("detail"),
            fix=issue_class.get("fix"),
            trap=issue_class.get("trap"),
            example=issue_class.get("example"),
            osm_type=osm_type,
            osm_id=osm_id,
            text=text,
            subclass=issue_id % 1000,
            fix_suggestions=fix_suggestions
        )
        
        self.issues.append(issue)
    
    def _compile_results(self) -> PowerValidationResult:
        """Compile validation results"""
        issues_by_level = {"1": 0, "2": 0, "3": 0}
        issues_by_category: Dict[str, int] = {}
        
        for issue in self.issues:
            issues_by_level[str(issue.level.value)] += 1
            for tag in issue.tags:
                issues_by_category[tag] = issues_by_category.get(tag, 0) + 1
        
        total_objects = sum(self.stats.values())
        
        return PowerValidationResult(
            total_objects=total_objects,
            total_issues=len(self.issues),
            issues_by_level=issues_by_level,
            issues_by_category=issues_by_category,
            issues=self.issues,
            **self.stats
        )


# Export for API
__all__ = ["PowerValidator", "PowerIssue", "PowerValidationResult", "ValidationLevel"]
