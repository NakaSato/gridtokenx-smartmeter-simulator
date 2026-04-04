"""
Spatial Utilities for Osmose Integration

Provides spatial matching, conflation, and GIS operations inspired by Osmose backend.
Used for matching smart meters to power infrastructure and validating spatial relationships.

Based on:
- Osmose modules/OsmGis.py
- Osmose modules/PointInPolygon.py
- Osmose analysers/Analyser_Merge.py
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class ConflationConfig:
    """Configuration for spatial conflation operations"""
    
    max_distance_m: float = 10.0  # Maximum matching distance
    confidence_threshold: float = 0.5  # Minimum confidence for matches
    use_tags: bool = True  # Consider OSM tags in matching
    tag_weight: float = 0.3  # Weight for tag similarity (0-1)
    distance_weight: float = 0.7  # Weight for distance (0-1)


@dataclass
class SpatialMatch:
    """Result of a spatial match between two objects"""
    
    object1_id: Any  # ID of first object (e.g., meter)
    object2_id: Any  # ID of second object (e.g., pole)
    distance_m: float  # Distance in meters
    confidence: float  # Match confidence (0-1)
    lat1: float  # Latitude of object 1
    lon1: float  # Longitude of object 1
    lat2: float  # Latitude of object 2
    lon2: float  # Longitude of object 2
    tags_match: Optional[Dict[str, Any]] = None  # Matching tags


class SpatialMatcher:
    """
    Spatial matching engine for infrastructure conflation.
    
    Provides:
    - Distance-based matching (Haversine formula)
    - Tag similarity scoring
    - Confidence calculation
    - Batch matching operations
    """
    
    # Earth radius in kilometers
    EARTH_RADIUS_KM = 6371.0
    
    def __init__(self):
        self.matches: List[SpatialMatch] = []
    
    def haversine_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: Coordinates of point 1 (degrees)
            lat2, lon2: Coordinates of point 2 (degrees)
        
        Returns:
            Distance in meters
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance_km = self.EARTH_RADIUS_KM * c
        return distance_km * 1000  # Convert to meters
    
    def calculate_tag_similarity(self, tags1: Dict[str, Any], 
                                 tags2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two tag dictionaries.
        
        Args:
            tags1: Tags from first object
            tags2: Tags from second object
        
        Returns:
            Similarity score (0-1)
        """
        if not tags1 or not tags2:
            return 0.0
        
        # Find common tags
        common_keys = set(tags1.keys()) & set(tags2.keys())
        if not common_keys:
            return 0.0
        
        # Calculate similarity
        matching = 0
        for key in common_keys:
            if tags1[key] == tags2[key]:
                matching += 1
            elif str(tags1[key]).lower() == str(tags2[key]).lower():
                matching += 0.5  # Partial match for case-insensitive
        
        return matching / len(common_keys)
    
    def calculate_match_confidence(self, distance_m: float, 
                                   tag_similarity: float,
                                   config: ConflationConfig) -> float:
        """
        Calculate overall match confidence.
        
        Args:
            distance_m: Distance between objects
            tag_similarity: Tag similarity score (0-1)
            config: Conflation configuration
        
        Returns:
            Confidence score (0-1)
        """
        # Distance score (exponential decay)
        # At max_distance_m, score is ~0.37
        distance_score = math.exp(-distance_m / config.max_distance_m)
        
        # Combine scores
        if config.use_tags and tag_similarity > 0:
            confidence = (config.distance_weight * distance_score + 
                         config.tag_weight * tag_similarity)
        else:
            confidence = distance_score
        
        return min(1.0, max(0.0, confidence))
    
    def match_meters_to_poles(self, meters: List[Dict[str, Any]], 
                              poles: List[Dict[str, Any]],
                              config: Optional[ConflationConfig] = None) -> List[Dict[str, Any]]:
        """
        Match smart meters to nearest power poles.
        
        Args:
            meters: List of meter dicts with 'id', 'lat', 'lon', 'tags'
            poles: List of pole dicts with 'id', 'lat', 'lon', 'tags'
            config: Conflation configuration
        
        Returns:
            List of match dictionaries with:
            - meter_id: Meter identifier
            - pole_id: Pole identifier
            - distance: Distance in meters
            - confidence: Match confidence
            - meter_lat, meter_lon: Meter coordinates
            - pole_lat, pole_lon: Pole coordinates
        """
        config = config or ConflationConfig()
        matches = []
        
        for meter in meters:
            meter_id = meter.get('id')
            meter_lat = meter.get('lat')
            meter_lon = meter.get('lon')
            meter_tags = meter.get('tags', {})
            
            if not all([meter_id, meter_lat, meter_lon]):
                logger.warning(f"Skipping invalid meter: {meter}")
                continue
            
            best_match = None
            best_confidence = 0.0
            
            # Find best matching pole
            for pole in poles:
                pole_id = pole.get('id')
                pole_lat = pole.get('lat')
                pole_lon = pole.get('lon')
                pole_tags = pole.get('tags', {})
                
                if not all([pole_id, pole_lat, pole_lon]):
                    continue
                
                # Calculate distance
                distance = self.haversine_distance(
                    meter_lat, meter_lon, pole_lat, pole_lon
                )
                
                # Skip if too far
                if distance > config.max_distance_m:
                    continue
                
                # Calculate tag similarity
                tag_similarity = self.calculate_tag_similarity(
                    meter_tags, pole_tags
                ) if config.use_tags else 0.0
                
                # Calculate confidence
                confidence = self.calculate_match_confidence(
                    distance, tag_similarity, config
                )
                
                # Update best match
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = {
                        'meter_id': meter_id,
                        'pole_id': pole_id,
                        'distance': distance,
                        'confidence': confidence,
                        'meter_lat': meter_lat,
                        'meter_lon': meter_lon,
                        'pole_lat': pole_lat,
                        'pole_lon': pole_lon,
                        'tags_match': self._find_matching_tags(meter_tags, pole_tags)
                    }
            
            if best_match and best_confidence >= config.confidence_threshold:
                matches.append(best_match)
                self.matches.append(SpatialMatch(
                    object1_id=meter_id,
                    object2_id=best_match['pole_id'],
                    distance_m=best_match['distance'],
                    confidence=best_match['confidence'],
                    lat1=meter_lat,
                    lon1=meter_lon,
                    lat2=best_match['pole_lat'],
                    lon2=best_match['pole_lon'],
                    tags_match=best_match['tags_match']
                ))
        
        logger.info(f"Matched {len(matches)} meters to poles")
        return matches
    
    def _find_matching_tags(self, tags1: Dict[str, Any], 
                           tags2: Dict[str, Any]) -> Dict[str, Any]:
        """Find tags that match between two objects"""
        if not tags1 or not tags2:
            return {}
        
        matching = {}
        for key in set(tags1.keys()) & set(tags2.keys()):
            if tags1[key] == tags2[key]:
                matching[key] = tags1[key]
        
        return matching
    
    def find_nearest(self, lat: float, lon: float, 
                     objects: List[Dict[str, Any]], 
                     max_distance_m: float = 100.0) -> Optional[Dict[str, Any]]:
        """
        Find nearest object to a location.
        
        Args:
            lat, lon: Search location
            objects: List of objects with 'id', 'lat', 'lon'
            max_distance_m: Maximum search radius
        
        Returns:
            Nearest object dict with added 'distance' field, or None
        """
        nearest = None
        min_distance = float('inf')
        
        for obj in objects:
            obj_lat = obj.get('lat')
            obj_lon = obj.get('lon')
            
            if not obj_lat or not obj_lon:
                continue
            
            distance = self.haversine_distance(lat, lon, obj_lat, obj_lon)
            
            if distance < min_distance and distance <= max_distance_m:
                min_distance = distance
                nearest = obj.copy()
                nearest['distance'] = distance
        
        return nearest
    
    def batch_distance_matrix(self, points1: List[Tuple[float, float]], 
                              points2: List[Tuple[float, float]]) -> List[List[float]]:
        """
        Calculate distance matrix between two sets of points.
        
        Args:
            points1: List of (lat, lon) tuples
            points2: List of (lat, lon) tuples
        
        Returns:
            2D list where result[i][j] is distance from points1[i] to points2[j]
        """
        matrix = []
        
        for lat1, lon1 in points1:
            row = []
            for lat2, lon2 in points2:
                distance = self.haversine_distance(lat1, lon1, lat2, lon2)
                row.append(distance)
            matrix.append(row)
        
        return matrix


class BoundingBoxFilter:
    """
    Spatial filter for bounding box queries.
    
    Inspired by Osmose modules/PointInPolygon.py
    """
    
    def __init__(self, south: float, north: float, west: float, east: float):
        """
        Initialize bounding box.
        
        Args:
            south: Southern latitude
            north: Northern latitude
            west: Western longitude
            east: Eastern longitude
        """
        self.south = south
        self.north = north
        self.west = west
        self.east = east
    
    def contains(self, lat: float, lon: float) -> bool:
        """Check if point is within bounding box"""
        return (self.south <= lat <= self.north and 
                self.west <= lon <= self.east)
    
    def filter_objects(self, objects: List[Dict[str, Any]], 
                      lat_key: str = 'lat', lon_key: str = 'lon') -> List[Dict[str, Any]]:
        """
        Filter objects to those within bounding box.
        
        Args:
            objects: List of objects with lat/lon
            lat_key: Key for latitude
            lon_key: Key for longitude
        
        Returns:
            Filtered list of objects
        """
        return [
            obj for obj in objects
            if self.contains(obj.get(lat_key, 0), obj.get(lon_key, 0))
        ]
    
    def intersection(self, other: 'BoundingBoxFilter') -> Optional['BoundingBoxFilter']:
        """
        Calculate intersection with another bounding box.
        
        Args:
            other: Another bounding box
        
        Returns:
            Intersection bounding box, or None if no overlap
        """
        south = max(self.south, other.south)
        north = min(self.north, other.north)
        west = max(self.west, other.west)
        east = min(self.east, other.east)
        
        if south > north or west > east:
            return None
        
        return BoundingBoxFilter(south, north, west, east)


def create_thailand_bbox() -> BoundingBoxFilter:
    """Create bounding box for Thailand"""
    # Approximate Thailand bounds
    return BoundingBoxFilter(
        south=5.6,    # Southernmost
        north=20.5,   # Northernmost
        west=97.4,    # Westernmost
        east=105.6    # Easternmost
    )


def create_bangkok_bbox() -> BoundingBoxFilter:
    """Create bounding box for Bangkok metropolitan area"""
    return BoundingBoxFilter(
        south=13.4,
        north=14.2,
        west=100.3,
        east=101.0
    )
