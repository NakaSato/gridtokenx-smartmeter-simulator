"""
Microgrid Zoning Service using K-Means Clustering.

This module groups smart meters into zones (representing transformer service areas)
based on their GPS coordinates. This enables:
1. Local P2P Trading - prioritize trades within the same zone
2. Wheeling Charge Calculation - lower fees for same-zone, higher for cross-zone
3. Grid Topology Awareness - physical constraints in trading simulation
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

# Try to import sklearn, but provide fallback if not available
try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available. K-Means zoning will use geographic grid fallback.")


# =============================================================================
# Wheeling Charge Constants (THB/kWh)
# =============================================================================
# These represent the "toll fees" for using the distribution grid.
# Lower fees encourage local P2P trading, reducing physical energy losses.
INTRA_ZONE_WHEELING = 0.50      # Same zone - local LV transformer loop
ADJACENT_ZONE_WHEELING = 1.00   # Adjacent zones (<2 km via MV)
CROSS_ZONE_WHEELING = 1.50      # Cross zones (2-5 km via MV)
REMOTE_ZONE_WHEELING = 2.00     # Remote zones (>5 km, multiple transformers)

# =============================================================================
# Technical Loss Factors (percentage)
# =============================================================================
# Physical energy dissipation based on electrical distance.
# Longer paths = more resistance = more I²R losses.
INTRA_ZONE_LOSS = 0.01          # 1% - minimal local distribution loss
ADJACENT_ZONE_LOSS = 0.02       # 2% - short MV transfer
CROSS_ZONE_LOSS = 0.04          # 4% - medium distance MV transfer
REMOTE_ZONE_LOSS = 0.06         # 6% - long MV with transformer stepping


@dataclass
class ZoneInfo:
    """Information about a microgrid zone."""
    zone_id: int
    centroid_lat: float
    centroid_lon: float
    meter_count: int
    transformer_name: str


class MicrogridZoningService:
    """
    Service for clustering meters into microgrid zones using K-Means.
    
    In the real world, houses near each other connect to the same distribution
    transformer. This service simulates that topology for P2P trading optimization.
    """
    
    def __init__(self, num_zones: int = 5, random_state: int = 42):
        """
        Initialize the zoning service.
        
        Args:
            num_zones: Number of microgrid zones (= number of transformers)
            random_state: Seed for reproducibility
        """
        self.num_zones = num_zones
        self.random_state = random_state
        self.kmeans = None
        self.transformer_locations: List[Tuple[float, float]] = []
        self.zones: Dict[int, ZoneInfo] = {}
        self._fitted = False
        
    def fit(self, coordinates: List[Tuple[float, float]]) -> List[int]:
        """
        Cluster coordinates into zones using K-Means.
        
        Args:
            coordinates: List of (latitude, longitude) tuples
            
        Returns:
            List of zone IDs (0 to num_zones-1) for each coordinate
        """
        if len(coordinates) < self.num_zones:
            logger.warning(f"Too few meters ({len(coordinates)}) for {self.num_zones} zones. Using simple assignment.")
            return [i % self.num_zones for i in range(len(coordinates))]
        
        coords_array = np.array(coordinates)
        
        if SKLEARN_AVAILABLE:
            self.kmeans = KMeans(
                n_clusters=self.num_zones,
                random_state=self.random_state,
                n_init=10
            )
            zone_ids = self.kmeans.fit_predict(coords_array)
            self.transformer_locations = [
                (center[0], center[1]) 
                for center in self.kmeans.cluster_centers_
            ]
        else:
            # Fallback: Simple geographic grid division
            zone_ids = self._simple_grid_assignment(coords_array)
            self._calculate_centroids(coords_array, zone_ids)
        
        # Build zone info
        self._build_zone_info(coords_array, zone_ids)
        self._fitted = True
        
        logger.info(f"Clustered {len(coordinates)} meters into {self.num_zones} zones")
        return zone_ids.tolist()
    
    def _simple_grid_assignment(self, coords: np.ndarray) -> np.ndarray:
        """Fallback: Assign zones based on simple geographic grid."""
        lat_min, lat_max = coords[:, 0].min(), coords[:, 0].max()
        lon_min, lon_max = coords[:, 1].min(), coords[:, 1].max()
        
        # Divide lat/lon into grid cells
        grid_size = int(np.ceil(np.sqrt(self.num_zones)))
        lat_bins = np.linspace(lat_min, lat_max + 0.0001, grid_size + 1)
        lon_bins = np.linspace(lon_min, lon_max + 0.0001, grid_size + 1)
        
        lat_idx = np.digitize(coords[:, 0], lat_bins) - 1
        lon_idx = np.digitize(coords[:, 1], lon_bins) - 1
        
        zone_ids = (lat_idx * grid_size + lon_idx) % self.num_zones
        return zone_ids
    
    def _calculate_centroids(self, coords: np.ndarray, zone_ids: np.ndarray):
        """Calculate zone centroids for fallback method."""
        self.transformer_locations = []
        for zone_id in range(self.num_zones):
            mask = zone_ids == zone_id
            if mask.any():
                centroid = coords[mask].mean(axis=0)
                self.transformer_locations.append((centroid[0], centroid[1]))
            else:
                # Empty zone - use grid center
                self.transformer_locations.append((0.0, 0.0))
    
    def _build_zone_info(self, coords: np.ndarray, zone_ids: np.ndarray):
        """Build ZoneInfo objects for each zone."""
        self.zones = {}
        for zone_id in range(self.num_zones):
            mask = zone_ids == zone_id
            count = mask.sum()
            
            if zone_id < len(self.transformer_locations):
                lat, lon = self.transformer_locations[zone_id]
            else:
                lat, lon = 0.0, 0.0
            
            self.zones[zone_id] = ZoneInfo(
                zone_id=zone_id,
                centroid_lat=lat,
                centroid_lon=lon,
                meter_count=count,
                transformer_name=f"TX_{zone_id:02d}"
            )
    
    def predict_zone(self, lat: float, lon: float) -> int:
        """
        Predict zone for a new meter based on its coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Zone ID (0 to num_zones-1)
        """
        if not self._fitted:
            logger.warning("Zoning not fitted. Returning zone 0.")
            return 0
        
        if SKLEARN_AVAILABLE and self.kmeans is not None:
            return int(self.kmeans.predict([[lat, lon]])[0])
        else:
            # Fallback: Find nearest centroid
            return self._find_nearest_zone(lat, lon)
    
    def _find_nearest_zone(self, lat: float, lon: float) -> int:
        """Find the nearest zone by Euclidean distance to centroids."""
        min_dist = float('inf')
        nearest_zone = 0
        
        for zone_id, (clat, clon) in enumerate(self.transformer_locations):
            dist = np.sqrt((lat - clat)**2 + (lon - clon)**2)
            if dist < min_dist:
                min_dist = dist
                nearest_zone = zone_id
        
        return nearest_zone
    
    def calculate_zone_distance(self, from_zone: int, to_zone: int) -> float:
        """
        Calculate approximate distance between two zone centroids in kilometers.
        
        Args:
            from_zone: Source zone ID
            to_zone: Destination zone ID
            
        Returns:
            Distance in kilometers (approximate, using Haversine simplification)
        """
        if from_zone == to_zone:
            return 0.0
        
        if not self.transformer_locations:
            return 0.0
        
        if from_zone >= len(self.transformer_locations) or to_zone >= len(self.transformer_locations):
            return 0.0
        
        from_lat, from_lon = self.transformer_locations[from_zone]
        to_lat, to_lon = self.transformer_locations[to_zone]
        
        # Approximate distance in km using simplified Haversine
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(latitude)
        lat_diff_km = (to_lat - from_lat) * 111
        lon_diff_km = (to_lon - from_lon) * 111 * np.cos(np.radians(from_lat))
        
        dist_km = np.sqrt(lat_diff_km ** 2 + lon_diff_km ** 2)
        return float(dist_km)
    
    def calculate_loss_factor(self, from_zone: int, to_zone: int) -> float:
        """
        Calculate technical loss factor based on zone distance.
        
        Physical losses (I²R) increase with electrical distance due to:
        - Line resistance accumulation
        - Transformer losses at step-up/step-down points
        - Reactive power compensation requirements
        
        Args:
            from_zone: Seller's zone ID
            to_zone: Buyer's zone ID
            
        Returns:
            Loss factor as decimal (e.g., 0.02 = 2% loss)
        """
        if from_zone == to_zone:
            return INTRA_ZONE_LOSS
        
        dist_km = self.calculate_zone_distance(from_zone, to_zone)
        
        # Tiered loss based on distance
        if dist_km < 2.0:
            return ADJACENT_ZONE_LOSS
        elif dist_km < 5.0:
            return CROSS_ZONE_LOSS
        else:
            return REMOTE_ZONE_LOSS
    
    def calculate_wheeling_charge(
        self,
        from_zone: int,
        to_zone: int,
        energy_amount: float = 1.0  # kWh
    ) -> float:
        """
        Calculate wheeling charge in THB based on zone distance.
        
        The wheeling charge represents the "toll fee" for using the distribution
        grid infrastructure. It incentivizes local P2P trading by making cross-zone
        transfers more expensive.
        
        Pricing Tiers:
        - Intra-zone (same transformer): 0.50 THB/kWh
        - Adjacent zones (<2 km): 1.00 THB/kWh
        - Cross zones (2-5 km): 1.50 THB/kWh
        - Remote zones (>5 km): 2.00 THB/kWh
        
        Args:
            from_zone: Seller's zone ID
            to_zone: Buyer's zone ID
            energy_amount: Energy being transferred in kWh (default 1.0 for rate)
            
        Returns:
            Wheeling charge in THB
        """
        if from_zone == to_zone:
            # Same zone: minimal charge (local LV transformer loop)
            rate = INTRA_ZONE_WHEELING
        else:
            dist_km = self.calculate_zone_distance(from_zone, to_zone)
            
            if dist_km < 2.0:
                rate = ADJACENT_ZONE_WHEELING
            elif dist_km < 5.0:
                rate = CROSS_ZONE_WHEELING
            else:
                rate = REMOTE_ZONE_WHEELING
        
        logger.debug(f"Wheeling Rate: {from_zone}->{to_zone} = {rate} THB/kWh (Amt: {energy_amount})")
        return rate * energy_amount
    
    def get_zone_summary(self) -> Dict[int, ZoneInfo]:
        """Returns summary of all zones."""
        return self.zones.copy()
    
    def get_wheeling_charge_matrix(self) -> Dict[str, float]:
        """
        Returns the wheeling charge rate matrix for all zone pairs.
        Useful for display and UI purposes.
        
        Returns:
            Dictionary mapping zone pair descriptions to rates in THB/kWh
        """
        return {
            "Intra-Zone (Same)": INTRA_ZONE_WHEELING,
            "Adjacent (<2km)": ADJACENT_ZONE_WHEELING,
            "Cross-Zone (2-5km)": CROSS_ZONE_WHEELING,
            "Remote (>5km)": REMOTE_ZONE_WHEELING,
        }
    
    def get_loss_factor_matrix(self) -> Dict[str, float]:
        """
        Returns the loss factor matrix for all zone distance tiers.
        Useful for display and UI purposes.
        
        Returns:
            Dictionary mapping distance tier to loss percentage
        """
        return {
            "Intra-Zone (Same)": INTRA_ZONE_LOSS,
            "Adjacent (<2km)": ADJACENT_ZONE_LOSS,
            "Cross-Zone (2-5km)": CROSS_ZONE_LOSS,
            "Remote (>5km)": REMOTE_ZONE_LOSS,
        }

