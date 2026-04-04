"""
OSMOSE Plugin System

Plugins are lightweight validators that check individual OSM objects.
They can be written in Python or generated from MapCSS rules.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """
    Base class for OSMOSE plugins.
    
    Plugins validate individual OSM objects (nodes, ways, relations).
    They are fast and run during PBF parsing.
    """
    
    def __init__(self):
        self.errors: Dict[int, Dict[str, Any]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def init(self, logger):
        """Initialize plugin with logger"""
        pass
    
    def def_class(self, item: int, level: int, tags: List[str], 
                  title: str, detail: Optional[str] = None,
                  fix: Optional[str] = None) -> Dict[str, Any]:
        """Define an issue class"""
        return {
            "item": item,
            "level": level,
            "tags": tags,
            "title": title,
            "detail": detail,
            "fix": fix,
        }
    
    @abstractmethod
    def node(self, node: Dict[str, Any], tags: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Validate a node.
        
        Args:
            node: Node data with id, lat, lon, tags
            tags: Node tags dictionary
            
        Returns:
            List of issue dictionaries
        """
        return []
    
    @abstractmethod
    def way(self, way: Dict[str, Any], tags: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Validate a way.
        
        Args:
            way: Way data with id, nodes, tags
            tags: Way tags dictionary
            
        Returns:
            List of issue dictionaries
        """
        return []
    
    @abstractmethod
    def relation(self, relation: Dict[str, Any], tags: Dict[str, str], 
                 members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate a relation.
        
        Args:
            relation: Relation data with id, members, tags
            tags: Relation tags dictionary
            members: Relation members list
            
        Returns:
            List of issue dictionaries
        """
        return []


class PluginMapCSS(Plugin):
    """
    MapCSS-based plugin.
    
    These plugins are generated from MapCSS rules using mapcss2osmose.py
    The MapCSS language is the same as used in JOSM validator.
    """
    
    def __init__(self):
        super().__init__()
        self.mapcss_rules = []
    
    def init(self, logger):
        """Initialize MapCSS plugin"""
        super().init(logger)
        logger.info(f"Initialized MapCSS plugin: {self.__class__.__name__}")
    
    def node(self, node: Dict[str, Any], tags: Dict[str, str]) -> List[Dict[str, Any]]:
        """Validate node using MapCSS rules"""
        errors = []
        # MapCSS rules would be evaluated here
        # This is a placeholder - actual implementation would have compiled rules
        return errors
    
    def way(self, way: Dict[str, Any], tags: Dict[str, str]) -> List[Dict[str, Any]]:
        """Validate way using MapCSS rules"""
        errors = []
        return errors
    
    def relation(self, relation: Dict[str, Any], tags: Dict[str, str], 
                 members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate relation using MapCSS rules"""
        errors = []
        return errors


# Example: Power Plugin (generated from Power.validator.mapcss)
class PowerPlugin(PluginMapCSS):
    """
    Power infrastructure validation plugin.
    
    Generated from: plugins/Power.validator.mapcss
    Based on OSMOSE QA power validation rules.
    """
    
    def init(self, logger):
        super().init(logger)
        
        # Define issue classes (from MapCSS)
        self.errors[91001] = self.def_class(
            item=9100, 
            level=2, 
            tags=["power", "fix:chair", "geom"],
            title="Power Transformers should always be on a node"
        )
        
        self.errors[91002] = self.def_class(
            item=9100, 
            level=2, 
            tags=["power", "fix:chair", "tag"],
            title="On Power Transformers use voltage:primary=* and voltage:secondary=* in place of voltage"
        )
    
    def node(self, node: Dict[str, Any], tags: Dict[str, str]) -> List[Dict[str, Any]]:
        """Validate power nodes"""
        errors = []
        
        # Rule: node[power=transformer][voltage]
        if tags.get("power") == "transformer" and "voltage" in tags:
            errors.append({
                "class": 91002,
                "item": 9100,
                "level": 2,
                "tags": ["power", "fix:chair", "tag"],
                "text": f"voltage={tags.get('voltage')}",
                "detail": "Transformers have multiple voltage levels. Use separate tags for primary and secondary voltages.",
                "fix": "Replace voltage=* with voltage:primary=* and voltage:secondary=* tags.",
                "example": "voltage:primary=115000; voltage:secondary=22000",
                "fix_suggestions": [{
                    "-": ["voltage"],
                    "+": {
                        "voltage:primary": tags.get("voltage", "115000"),
                        "voltage:secondary": "22000"
                    }
                }]
            })
        
        return errors
    
    def way(self, way: Dict[str, Any], tags: Dict[str, str]) -> List[Dict[str, Any]]:
        """Validate power ways"""
        errors = []
        
        # Rule: way[power=transformer]
        if tags.get("power") == "transformer":
            errors.append({
                "class": 91001,
                "item": 9100,
                "level": 2,
                "tags": ["power", "fix:chair", "geom"],
                "text": f"Transformer way {way.get('id')}",
                "detail": "Power transformers must be mapped as nodes, not as ways.",
                "fix": "Convert the transformer way to a node at the transformer location.",
            })
        
        return errors
    
    def relation(self, relation: Dict[str, Any], tags: Dict[str, str], 
                 members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate power relations"""
        errors = []
        
        # Rule: relation[power=transformer]
        if tags.get("power") == "transformer":
            errors.append({
                "class": 91001,
                "item": 9100,
                "level": 2,
                "tags": ["power", "fix:chair", "geom"],
                "text": f"Transformer relation {relation.get('id')}",
                "detail": "Power transformers must be mapped as nodes, not as relations.",
                "fix": "Convert the transformer relation to a node.",
            })
        
        return errors


# Plugin registry
PLUGIN_REGISTRY = {
    "Power": PowerPlugin,
}


def get_plugin(plugin_name: str) -> Optional[Plugin]:
    """Get plugin instance by name"""
    plugin_class = PLUGIN_REGISTRY.get(plugin_name)
    if plugin_class:
        return plugin_class()
    return None


def list_plugins() -> List[str]:
    """List available plugins"""
    return list(PLUGIN_REGISTRY.keys())
