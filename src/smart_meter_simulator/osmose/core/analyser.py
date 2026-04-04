"""
OSMOSE Analyser Base Classes

Abstract base classes for different analyser types:
- Analyser: Base class
- AnalyserOsmosis: SQL-based analysers using PostgreSQL/PostGIS
- AnalyserMerge: OpenData conflation analysers
- AnalyserSax: PBF parser with plugin validation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import time

from .issue import OsmoseIssue, OsmoseValidationResult, IssueLevel

logger = logging.getLogger(__name__)


class Analyser(ABC):
    """
    Abstract base class for all OSMOSE analysers.
    
    Analysers validate OSM data and produce lists of issues.
    This is the main interface that all analyser types implement.
    """
    
    def __init__(self, analyser_id: str, country: str):
        self.analyser_id = analyser_id
        self.country = country
        self.start_time = 0
        self.errors: Dict[int, Dict[str, Any]] = {}
        
    def def_class(self, item: int, level: IssueLevel, tags: List[str], 
                  title: str, detail: Optional[str] = None,
                  fix: Optional[str] = None, trap: Optional[str] = None,
                  example: Optional[str] = None, source: Optional[str] = None,
                  resource: Optional[str] = None) -> Dict[str, Any]:
        """
        Define an issue class (used in plugins and analysers)
        
        This matches OSMOSE's def_class pattern for defining issue types.
        """
        return {
            "item": item,
            "level": level,
            "tags": tags,
            "title": title,
            "detail": detail,
            "fix": fix,
            "trap": trap,
            "example": example,
            "source": source or f"analyser/{self.analyser_id}.py",
            "resource": resource,
        }
    
    @abstractmethod
    def run(self, osm_data: Dict[str, Any]) -> OsmoseValidationResult:
        """
        Run the analyser on OSM data.
        
        Args:
            osm_data: OSM data in dict format
            
        Returns:
            OsmoseValidationResult with all issues found
        """
        pass
    
    def _start_timer(self):
        """Start processing timer"""
        self.start_time = time.time()
    
    def _stop_timer(self) -> int:
        """Stop timer and return milliseconds"""
        return int((time.time() - self.start_time) * 1000)
    
    def _create_issue(self, class_id: int, osm_type: Optional[str] = None,
                      osm_id: Optional[int] = None, lat: Optional[float] = None,
                      lon: Optional[float] = None, text: Optional[str] = None,
                      subclass: Optional[int] = None,
                      fix_suggestions: Optional[List[Dict[str, Any]]] = None) -> OsmoseIssue:
        """
        Create an issue from a defined class.
        
        This matches OSMOSE's issue creation pattern.
        """
        issue_class = self.errors.get(class_id, {})
        
        return OsmoseIssue(
            id=class_id,
            item=issue_class.get("item", 9000),
            level=issue_class.get("level", IssueLevel.LOW),
            tags=issue_class.get("tags", []),
            title=issue_class.get("title", "Unknown issue"),
            detail=issue_class.get("detail"),
            fix=issue_class.get("fix"),
            trap=issue_class.get("trap"),
            example=issue_class.get("example"),
            source=issue_class.get("source"),
            resource=issue_class.get("resource"),
            osm_type=osm_type,
            osm_id=osm_id,
            lat=lat,
            lon=lon,
            text=text,
            subclass=subclass or (class_id % 1000),
            fix_suggestions=fix_suggestions,
            analyser=self.analyser_id,
        )


class AnalyserOsmosis(Analyser):
    """
    SQL-based analyser using PostgreSQL/PostGIS (Osmosis schema).
    
    This type runs SQL queries on an Osmosis-imported OSM database
    to find complex validation issues involving geometry and topology.
    """
    
    def __init__(self, analyser_id: str, country: str, 
                 db_connection_string: Optional[str] = None):
        super().__init__(analyser_id, country)
        self.db_connection = db_connection_string
        self.schema = "public"  # Osmosis schema
    
    @abstractmethod
    def get_sql_queries(self) -> List[str]:
        """
        Return list of SQL queries to execute.
        
        Each query should return columns matching OSMOSE issue format:
        - id (issue class ID)
        - osm_type, osm_id (object reference)
        - lat, lon (location)
        - text (subtitle)
        - fix (structured fix suggestions)
        """
        pass
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        
        In production, this would connect to PostgreSQL and execute.
        """
        logger.debug(f"Executing SQL: {query}")
        # Placeholder - actual implementation would use asyncpg or similar
        return []
    
    def run(self, osm_data: Dict[str, Any] = None) -> OsmoseValidationResult:
        """Run SQL-based validation"""
        self._start_timer()
        issues = []
        
        for query in self.get_sql_queries():
            results = self.execute_query(query)
            for row in results:
                issue = self._create_issue(
                    class_id=row.get("id"),
                    osm_type=row.get("osm_type"),
                    osm_id=row.get("osm_id"),
                    lat=row.get("lat"),
                    lon=row.get("lon"),
                    text=row.get("text"),
                    fix_suggestions=row.get("fix"),
                )
                issues.append(issue)
        
        return self._compile_result(issues)
    
    def _compile_result(self, issues: List[OsmoseIssue]) -> OsmoseValidationResult:
        """Compile validation result"""
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
            total_objects=0,  # Would count from database
            total_issues=len(issues),
            issues_by_level=issues_by_level,
            issues_by_item=issues_by_item,
            issues_by_tag=issues_by_tag,
            issues=issues,
            processing_time_ms=self._stop_timer(),
        )


class AnalyserMerge(Analyser):
    """
    OpenData conflation analyser.
    
    Compares OSM data with external OpenData sources to find:
    - Missing objects in OSM
    - Objects in OSM not in OpenData
    - Attribute improvements from OpenData
    """
    
    def __init__(self, analyser_id: str, country: str,
                 opendata_source: str, opendata_format: str = "geojson"):
        super().__init__(analyser_id, country)
        self.opendata_source = opendata_source
        self.opendata_format = opendata_format
        self.opendata_cache: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def load_opendata(self) -> Dict[str, Any]:
        """Load external OpenData source"""
        pass
    
    @abstractmethod
    def compare(self, osm_data: Dict[str, Any], 
                opendata: Dict[str, Any]) -> List[OsmoseIssue]:
        """Compare OSM with OpenData and generate issues"""
        pass
    
    def run(self, osm_data: Dict[str, Any]) -> OsmoseValidationResult:
        """Run conflation validation"""
        self._start_timer()
        
        # Load OpenData
        opendata = self.load_opendata()
        
        # Compare and generate issues
        issues = self.compare(osm_data, opendata)
        
        return self._compile_result(issues, len(osm_data.get("nodes", [])) + 
                                    len(osm_data.get("ways", [])))
    
    def _compile_result(self, issues: List[OsmoseIssue], 
                        total_objects: int) -> OsmoseValidationResult:
        """Compile validation result"""
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


class AnalyserSax(Analyser):
    """
    SAX parser-based analyser with plugin validation.
    
    Parses OSM PBF files and runs plugin validators on each object.
    This is the fastest analyser type for simple tag validation.
    """
    
    def __init__(self, analyser_id: str, country: str):
        super().__init__(analyser_id, country)
        self.plugins: List[Any] = []  # Plugin instances
    
    def register_plugin(self, plugin: Any):
        """Register a validation plugin"""
        self.plugins.append(plugin)
        logger.debug(f"Registered plugin: {plugin.__class__.__name__}")
    
    def run(self, osm_data: Dict[str, Any]) -> OsmoseValidationResult:
        """Run plugin-based validation"""
        self._start_timer()
        issues = []
        total_objects = 0
        
        # Validate nodes
        for node in osm_data.get("nodes", []):
            total_objects += 1
            for plugin in self.plugins:
                if hasattr(plugin, "node"):
                    node_issues = plugin.node(node, node.get("tags", {}))
                    for issue_data in node_issues:
                        issues.append(self._plugin_issue_to_issue(issue_data, "node", node.get("id")))
        
        # Validate ways
        for way in osm_data.get("ways", []):
            total_objects += 1
            for plugin in self.plugins:
                if hasattr(plugin, "way"):
                    way_issues = plugin.way(way, way.get("tags", {}))
                    for issue_data in way_issues:
                        issues.append(self._plugin_issue_to_issue(issue_data, "way", way.get("id")))
        
        # Validate relations
        for relation in osm_data.get("relations", []):
            total_objects += 1
            for plugin in self.plugins:
                if hasattr(plugin, "relation"):
                    rel_issues = plugin.relation(relation, relation.get("tags", {}), relation.get("members", []))
                    for issue_data in rel_issues:
                        issues.append(self._plugin_issue_to_issue(issue_data, "relation", relation.get("id")))
        
        return self._compile_result(issues, total_objects)
    
    def _plugin_issue_to_issue(self, issue_data: Dict[str, Any], 
                                osm_type: str, osm_id: int) -> OsmoseIssue:
        """Convert plugin issue format to OsmoseIssue"""
        return OsmoseIssue(
            id=issue_data.get("class", 0),
            item=issue_data.get("item", 9000),
            level=IssueLevel(issue_data.get("level", 3)),
            tags=issue_data.get("tags", []),
            title=issue_data.get("text", "Unknown issue"),
            detail=issue_data.get("detail"),
            fix=issue_data.get("fix"),
            osm_type=osm_type,
            osm_id=osm_id,
            subclass=issue_data.get("subclass"),
            text=issue_data.get("text"),
            fix_suggestions=issue_data.get("fix_suggestions"),
            analyser=self.analyser_id,
        )
    
    def _compile_result(self, issues: List[OsmoseIssue], 
                        total_objects: int) -> OsmoseValidationResult:
        """Compile validation result"""
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
