"""
OSMOSE Core Data Models

Defines the core data structures for OSMOSE validation issues.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import hashlib


class IssueLevel(int, Enum):
    """OSMOSE issue severity levels"""
    HIGH = 1      # Critical errors - break data integrity
    NORMAL = 2    # Common mistakes - reduce data quality
    LOW = 3       # Suggestions - improvements


class IssueCategory(str, Enum):
    """OSMOSE issue classification tags"""
    GEOM = "geom"              # Geometry issues
    TAG = "tag"                # Tagging errors
    TOPOLOGY = "topology"      # Topological errors
    SEMANTIC = "semantic"      # Semantic inconsistencies
    SOURCE = "source"          # Source data issues
    FIX_CHAIR = "fix:chair"    # Can be fixed in editor
    FIX_IMAGERY = "fix:imagery" # Needs imagery check
    POWER = "power"            # Power infrastructure
    TRANSPORT = "transport"    # Transport infrastructure
    BUILDING = "building"      # Building errors
    ADDRESS = "addr"           # Address issues
    NATURAL = "natural"        # Natural features
    BOUNDARY = "boundary"      # Boundary problems


class OsmoseIssue(BaseModel):
    """
    OSMOSE Validation Issue
    
    Represents a single validation issue found by an analyser.
    Matches OSMOSE backend issue format.
    """
    # Issue identification
    id: int = Field(..., description="Unique issue identifier (analyser-specific)")
    item: int = Field(..., description="Category code (e.g., 9100 for power)")
    level: IssueLevel = Field(..., description="Severity level (1-3)")
    tags: List[str] = Field(default_factory=list, description="Issue classification tags")
    
    # Human-readable descriptions
    title: str = Field(..., description="Short issue title")
    detail: Optional[str] = Field(None, description="Detailed explanation (markdown)")
    fix: Optional[str] = Field(None, description="Fix instructions (markdown)")
    trap: Optional[str] = Field(None, description="Common mistakes to avoid")
    example: Optional[str] = Field(None, description="Example of the issue")
    source: Optional[str] = Field(None, description="Source code reference")
    resource: Optional[str] = Field(None, description="External resource URL")
    
    # OSM object reference
    osm_type: Optional[str] = Field(None, description="OSM object type (node/way/relation)")
    osm_id: Optional[int] = Field(None, description="OSM object ID")
    
    # Location (WGS84)
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    
    # Issue specifics
    subclass: Optional[int] = Field(None, description="Sub-classifier for unique identification")
    text: Optional[str] = Field(None, description="Subtitle with specific values")
    
    # Fix suggestions (structured)
    fix_suggestions: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Structured fix suggestions (add/delete/modify tags)"
    )
    
    # Metadata
    analyser: Optional[str] = Field(None, description="Analyser that found this issue")
    timestamp: Optional[str] = Field(None, description="When the issue was found")
    
    class Config:
        use_enum_values = True
    
    def to_geojson(self) -> Dict[str, Any]:
        """Convert issue to GeoJSON Feature"""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.lon, self.lat] if self.lon and self.lat else [0, 0]
            },
            "properties": {
                "id": self.id,
                "item": self.item,
                "level": self.level,
                "tags": self.tags,
                "title": self.title,
                "detail": self.detail,
                "fix": self.fix,
                "osm_type": self.osm_type,
                "osm_id": self.osm_id,
                "subclass": self.subclass,
                "text": self.text,
                "analyser": self.analyser,
            }
        }
    
    def to_mvt_properties(self) -> Dict[str, Any]:
        """Convert to Mapbox Vector Tile properties"""
        return {
            "id": self.id,
            "item": self.item,
            "level": self.level,
            "tags": ",".join(self.tags),
            "title": self.title,
            "severity": "error" if self.level == 1 else "warning" if self.level == 2 else "info",
            "osm_type": self.osm_type,
            "osm_id": self.osm_id,
            "resource": self.resource,
        }
    
    def get_unique_id(self) -> str:
        """Generate unique hash for this issue"""
        key = f"{self.osm_type}:{self.osm_id}:{self.item}:{self.subclass}"
        return hashlib.md5(key.encode()).hexdigest()


class OsmoseValidationResult(BaseModel):
    """
    Complete validation result from an OSMOSE analyser run.
    """
    # Metadata
    analyser: str = Field(..., description="Analyser name")
    country: str = Field(..., description="Country code")
    timestamp: str = Field(..., description="Validation timestamp")
    
    # Statistics
    total_objects: int = Field(..., description="Total OSM objects validated")
    total_issues: int = Field(..., description="Total issues found")
    issues_by_level: Dict[str, int] = Field(..., description="Issues grouped by severity")
    issues_by_item: Dict[str, int] = Field(..., description="Issues grouped by category")
    issues_by_tag: Dict[str, int] = Field(..., description="Issues grouped by tags")
    
    # Issues list
    issues: List[OsmoseIssue] = Field(default_factory=list, description="All validation issues")
    
    # Processing info
    processing_time_ms: int = Field(0, description="Processing time in milliseconds")
    memory_usage_mb: float = Field(0, description="Memory usage in MB")
    
    def to_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        return {
            "analyser": self.analyser,
            "country": self.country,
            "timestamp": self.timestamp,
            "total_objects": self.total_objects,
            "total_issues": self.total_issues,
            "issues_by_level": self.issues_by_level,
            "top_items": dict(sorted(
                self.issues_by_item.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]),
            "processing_time_ms": self.processing_time_ms,
        }
    
    def filter_by_level(self, min_level: int, max_level: int) -> "OsmoseValidationResult":
        """Filter issues by severity level"""
        filtered = [
            issue for issue in self.issues 
            if min_level <= issue.level <= max_level
        ]
        
        return OsmoseValidationResult(
            analyser=self.analyser,
            country=self.country,
            timestamp=self.timestamp,
            total_objects=self.total_objects,
            total_issues=len(filtered),
            issues_by_level=self.issues_by_level,
            issues_by_item=self.issues_by_item,
            issues_by_tag=self.issues_by_tag,
            issues=filtered,
            processing_time_ms=self.processing_time_ms,
            memory_usage_mb=self.memory_usage_mb,
        )
    
    def filter_by_bbox(self, min_lat: float, max_lat: float, 
                       min_lon: float, max_lon: float) -> "OsmoseValidationResult":
        """Filter issues by bounding box"""
        filtered = [
            issue for issue in self.issues 
            if issue.lat and issue.lon and
               min_lat <= issue.lat <= max_lat and
               min_lon <= issue.lon <= max_lon
        ]
        
        return OsmoseValidationResult(
            analyser=self.analyser,
            country=self.country,
            timestamp=self.timestamp,
            total_objects=self.total_objects,
            total_issues=len(filtered),
            issues=filtered,
            processing_time_ms=self.processing_time_ms,
            memory_usage_mb=self.memory_usage_mb,
        )


class OsmoseAnalyserStatus(BaseModel):
    """Status of an OSMOSE analyser"""
    id: str = Field(..., description="Analyser identifier")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Analyser description")
    enabled: bool = Field(True, description="Whether analyser is active")
    last_run: Optional[str] = Field(None, description="Last successful run timestamp")
    next_run: Optional[str] = Field(None, description="Next scheduled run")
    status: str = Field("idle", description="Current status (idle/running/error)")
    error_message: Optional[str] = Field(None, description="Last error message")
    issues_found: int = Field(0, description="Total issues found in last run")
    objects_validated: int = Field(0, description="Objects validated in last run")
