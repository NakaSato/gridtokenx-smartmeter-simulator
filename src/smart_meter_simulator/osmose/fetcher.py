"""
OSMOSE Data Fetcher

Fetches OSM data from multiple sources:
- Overpass API
- OSM PBF files
- OSMOSE backend database
- Local OSM extracts
"""

import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class OSMOSEDataFetcher:
    """
    Fetch OSM data for validation.
    
    Supports multiple data sources:
    - Overpass API (live queries)
    - PBF files (local extracts)
    - OSMOSE database (pre-processed)
    """
    
    # Overpass API endpoints
    OVERPASS_ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter",
    ]
    
    def __init__(self, endpoint_index: int = 0, timeout: int = 120):
        self.endpoint_index = endpoint_index
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_endpoint(self) -> str:
        """Get current Overpass endpoint"""
        return self.OVERPASS_ENDPOINTS[self.endpoint_index % len(self.OVERPASS_ENDPOINTS)]
    
    def _rotate_endpoint(self):
        """Rotate to next endpoint on failure"""
        self.endpoint_index += 1
        logger.warning(f"Rotated to Overpass endpoint: {self._get_endpoint()}")
    
    async def fetch_overpass(self, query: str, bbox: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Fetch data from Overpass API.
        
        Args:
            query: Overpass QL or XML query
            bbox: Optional bounding box {north, south, east, west}
            
        Returns:
            Overpass API response as dict
        """
        if bbox:
            # Replace {{bbox}} in query
            bbox_str = f"{bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']}"
            query = query.replace("{{bbox}}", bbox_str)
        
        endpoint = self._get_endpoint()
        logger.info(f"Fetching from Overpass: {endpoint}")
        
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            async with self.session.post(
                endpoint,
                data={"data": query},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Overpass error {response.status}: {error_text}")
        
        except Exception as e:
            logger.error(f"Overpass fetch failed: {e}")
            self._rotate_endpoint()
            raise
    
    async def fetch_power_infrastructure(self, bbox: Dict[str, float]) -> Dict[str, Any]:
        """
        Fetch power infrastructure from Overpass.
        
        Args:
            bbox: Bounding box {north, south, east, west}
            
        Returns:
            OSM data with power infrastructure
        """
        query = """
        [out:json][timeout:{{timeout}}];
        (
          // Power lines
          way["power"~"line|minor_line|cable"]({{bbox}});
          
          // Power supports
          node["power"~"tower|pole|portal|terminal"]({{bbox}});
          
          // Substations
          node["power"="substation"]({{bbox}});
          way["power"="substation"]({{bbox}});
          
          // Transformers
          node["power"="transformer"]({{bbox}});
          
          // Generators and plants
          node["power"="generator"]({{bbox}});
          way["power"="plant"]({{bbox}});
          
          // Switches
          node["power"="switch"]({{bbox}});
        );
        out body;
        >;
        out skel qt;
        """.replace("{{timeout}}", str(self.timeout))
        
        return await self.fetch_overpass(query, bbox)
    
    async def fetch_osmose_issues(self, country: str, analyser: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch existing OSMOSE issues from backend.
        
        Args:
            country: Country code
            analyser: Optional analyser filter
            
        Returns:
            OSMOSE issues data
        """
        # This would connect to OSMOSE backend database
        # For now, return placeholder
        logger.info(f"Fetching OSMOSE issues for {country}")
        
        return {
            "country": country,
            "analyser": analyser,
            "issues": [],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    
    async def fetch_pbf(self, pbf_path: str) -> Dict[str, Any]:
        """
        Parse OSM PBF file.
        
        Args:
            pbf_path: Path to .osm.pbf file
            
        Returns:
            Parsed OSM data
        """
        logger.info(f"Parsing PBF file: {pbf_path}")
        
        # Placeholder - would use osmium or pyosmium
        # Actual implementation:
        # import osmium
        # handler = OSMHandler()
        # osmium.apply_file(pbf_path, handler)
        
        return {
            "nodes": [],
            "ways": [],
            "relations": [],
            "source": pbf_path,
        }
    
    async def fetch_bbox(self, bbox: Dict[str, float], 
                         tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Fetch all OSM data in bounding box.
        
        Args:
            bbox: Bounding box {north, south, east, west}
            tags: Optional list of tags to filter
            
        Returns:
            OSM data
        """
        tag_filter = ""
        if tags:
            tag_join = '"|"'.join(tags)
            tag_filter = f'["{tag_join}"]'
        
        query = f"""
        [out:json][timeout:{{timeout}}];
        (
          node{tag_filter}({{bbox}});
          way{tag_filter}({{bbox}});
          relation{tag_filter}({{bbox}});
        );
        out body;
        >;
        out skel qt;
        """
        
        return await self.fetch_overpass(query, bbox)
    
    async def test_connection(self) -> bool:
        """Test Overpass API connection"""
        try:
            query = "[out:json];node(48.8566,2.3522,48.8566,2.3522);out;"
            await self.fetch_overpass(query)
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


class OSMOSEDataCache:
    """
    Cache for OSMOSE data to avoid repeated API calls.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, datetime] = {}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if not expired"""
        if key in self.cache:
            age = (datetime.utcnow() - self.timestamps[key]).total_seconds()
            if age < self.ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, data: Dict[str, Any]):
        """Cache data"""
        self.cache[key] = data
        self.timestamps[key] = datetime.utcnow()
        logger.debug(f"Cached data for key: {key}")
    
    def clear(self):
        """Clear all cached data"""
        self.cache.clear()
        self.timestamps.clear()
        logger.info("Cache cleared")
