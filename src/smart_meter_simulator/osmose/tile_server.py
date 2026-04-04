"""
OSMOSE Vector Tile Server

Generate Mapbox Vector Tiles (MVT) from OSMOSE validation issues.
Compatible with MapLibre GL JS and other MVT clients.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import mapbox_vector_tile
    HAS_MVT = True
except ImportError:
    HAS_MVT = False
    logger = logging.getLogger(__name__)
    logger.warning("mapbox_vector_tile not installed. MVT generation disabled.")

from .database import OSMOSEDatabase
from .core.issue import OsmoseIssue

logger = logging.getLogger(__name__)


class OSMOSEVectorTileServer:
    """
    Generate vector tiles from OSMOSE issues.
    
    Produces MVT tiles compatible with:
    - MapLibre GL JS
    - Mapbox GL JS
    - OpenLayers
    - Leaflet (with vector grid plugin)
    """
    
    # Tile configuration
    MIN_ZOOM = 10
    MAX_ZOOM = 18
    EXTENT = 4096  # MVT extent
    
    def __init__(self, database: OSMOSEDatabase):
        self.db = database
        if not HAS_MVT:
            logger.error("MVT generation requires mapbox-vector-tile package")
    
    async def get_tile(self, z: int, x: int, y: int,
                       level_min: int = 1, level_max: int = 3,
                       tags: Optional[str] = None) -> Optional[bytes]:
        """
        Generate vector tile for given Z/X/Y.
        
        Args:
            z: Zoom level
            x: Tile X coordinate
            y: Tile Y coordinate
            level_min: Minimum issue severity
            level_max: Maximum issue severity
            tags: Comma-separated tags filter (e.g., "power,building")
            
        Returns:
            MVT binary data or None
        """
        if not HAS_MVT:
            return None
        
        # Check zoom range
        if z < self.MIN_ZOOM or z > self.MAX_ZOOM:
            return None
        
        # Calculate tile bounding box
        bbox = self._tile_to_bbox(z, x, y)
        
        # Fetch issues in tile bounds
        issues = await self.db.get_issues(
            bbox=bbox,
            level_min=level_min,
            level_max=level_max,
            limit=1000  # Limit features per tile
        )
        
        # Filter by tags if specified
        if tags:
            tag_list = tags.split(",")
            issues = [
                issue for issue in issues
                if any(tag in issue.tags for tag in tag_list)
            ]
        
        if not issues:
            return None
        
        # Convert to GeoJSON
        features = [issue.to_geojson() for issue in issues]
        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }
        
        # Generate MVT
        try:
            mvt_data = mapbox_vector_tile.encode({
                "issues": geojson
            }, extents=self.EXTENT)
            return mvt_data
        except Exception as e:
            logger.error(f"MVT encoding failed: {e}")
            return None
    
    async def get_tile_stats(self, z: int, x: int, y: int) -> Dict[str, Any]:
        """Get statistics for a tile without generating it"""
        bbox = self._tile_to_bbox(z, x, y)
        
        issues = await self.db.get_issues(bbox=bbox, limit=10000)
        
        stats = {
            "total": len(issues),
            "by_level": {"1": 0, "2": 0, "3": 0},
            "by_item": {},
            "zoom": z,
            "x": x,
            "y": y,
        }
        
        for issue in issues:
            stats["by_level"][str(issue.level)] += 1
            item_key = str(issue.item)
            stats["by_item"][item_key] = stats["by_item"].get(item_key, 0) + 1
        
        return stats
    
    def _tile_to_bbox(self, z: int, x: int, y: int) -> Dict[str, float]:
        """
        Convert tile coordinates to bounding box.
        
        Uses Web Mercator projection (EPSG:3857).
        """
        import math
        
        # Tile to degrees
        lon_min = (x / (2 ** z)) * 360 - 180
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / (2 ** z))))
        lat_min = lat_rad * 180 / math.pi
        
        lon_max = ((x + 1) / (2 ** z)) * 360 - 180
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / (2 ** z))))
        lat_max = lat_rad * 180 / math.pi
        
        return {
            "north": lat_max,
            "south": lat_min,
            "east": lon_max,
            "west": lon_min,
        }
    
    async def get_clustered_tile(self, z: int, x: int, y: int,
                                 cluster_radius: int = 10) -> Optional[bytes]:
        """
        Generate clustered vector tile for better performance at low zoom.
        
        At low zoom levels, cluster nearby issues to reduce feature count.
        """
        if not HAS_MVT:
            return None
        
        # At high zoom, don't cluster
        if z >= 15:
            return await self.get_tile(z, x, y)
        
        bbox = self._tile_to_bbox(z, x, y)
        issues = await self.db.get_issues(bbox=bbox, limit=5000)
        
        if not issues:
            return None
        
        # Simple clustering (grid-based)
        clusters = self._cluster_issues(issues, cluster_radius)
        
        # Convert clusters to features
        features = []
        for cluster in clusters:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": cluster["center"]
                },
                "properties": {
                    "cluster": True,
                    "count": cluster["count"],
                    "level": min(i.level for i in cluster["issues"]),
                    "item": cluster["issues"][0].item,
                    "title": f"{cluster['count']} issues",
                }
            })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }
        
        try:
            return mapbox_vector_tile.encode({"issues": geojson}, extents=self.EXTENT)
        except Exception as e:
            logger.error(f"MVT encoding failed: {e}")
            return None
    
    def _cluster_issues(self, issues: List[OsmoseIssue], 
                        radius: int) -> List[Dict[str, Any]]:
        """
        Cluster issues by proximity.
        
        Simple grid-based clustering.
        """
        if not issues:
            return []
        
        # Group by grid cell
        grid: Dict[str, List[OsmoseIssue]] = {}
        for issue in issues:
            if not issue.lat or not issue.lon:
                continue
            
            # Calculate grid cell
            cell_x = int(issue.lon * 100) // radius
            cell_y = int(issue.lat * 100) // radius
            cell_key = f"{cell_x},{cell_y}"
            
            if cell_key not in grid:
                grid[cell_key] = []
            grid[cell_key].append(issue)
        
        # Create clusters
        clusters = []
        for cell_issues in grid.values():
            if not cell_issues:
                continue
            
            # Calculate center
            center_lon = sum(i.lon for i in cell_issues if i.lon) / len(cell_issues)
            center_lat = sum(i.lat for i in cell_issues if i.lat) / len(cell_issues)
            
            clusters.append({
                "center": [center_lon, center_lat],
                "count": len(cell_issues),
                "issues": cell_issues,
            })
        
        return clusters


class OSMOSEVectorTileRouter:
    """
    FastAPI router for vector tile endpoints.
    """
    
    def __init__(self, tile_server: OSMOSEVectorTileServer):
        self.tile_server = tile_server
    
    def register_routes(self, app):
        """Register tile endpoints with FastAPI app"""
        from fastapi import APIRouter, Response, Query
        from fastapi.responses import Response
        
        router = APIRouter(prefix="/api/0.3", tags=["OSMOSE Tiles"])
        
        @router.get("/issues/{z}/{x}/{y}.mvt")
        async def get_tile(
            z: int, x: int, y: int,
            level_min: int = Query(1, ge=1, le=3),
            level_max: int = Query(3, ge=1, le=3),
            tags: Optional[str] = Query(None),
        ):
            """Get vector tile with issues"""
            mvt_data = await self.tile_server.get_tile(
                z, x, y, level_min, level_max, tags
            )
            
            if not mvt_data:
                return Response(status_code=204)  # No content
            
            return Response(
                content=mvt_data,
                media_type="application/x-protobuf",
                headers={
                    "Content-Encoding": "gzip",
                    "Cache-Control": "public, max-age=3600",
                }
            )
        
        @router.get("/issues/{z}/{x}/{y}.stats")
        async def get_tile_stats(z: int, x: int, y: int):
            """Get tile statistics"""
            stats = await self.tile_server.get_tile_stats(z, x, y)
            return stats
        
        app.include_router(router)
