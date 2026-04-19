"""
Grid Telemetry Service

Handles spatial mapping of solar panels, pseudo-measurement injection, 
and cleaning of sensor data for state estimation.
"""

import logging
import math
from typing import List, Dict, Any, Set, Optional
import pandas as pd
from smart_meter_simulator.config import MeterType

logger = logging.getLogger(__name__)

class GridTelemetryService:
    """
    Service for managing grid sensor data and measurement injection.
    """

    @staticmethod
    def map_solar_to_grid(net, solar_inventory: List[Dict[str, Any]]) -> Dict[int, float]:
        """
        Spatial matching of detected solar panels to the nearest grid bus.
        Returns a mapping of bus_index -> total_kwp.
        """
        if not net or not solar_inventory:
            return {}

        if 'bus_geocoord' not in net or net.bus_geocoord is None:
            logger.warning("Geo-SAM: Cannot perform spatial matching - net.bus_geocoord is missing")
            return {}

        from scipy.spatial import KDTree
        
        # Prepare bus coordinates [lng, lat]
        bus_coords = net.bus_geocoord[['x', 'y']].values
        bus_indices = net.bus_geocoord.index.tolist()
        tree = KDTree(bus_coords)
        
        bus_solar_capacity = {}
        for panel in solar_inventory:
            geom = panel.get('geometry', {})
            if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) == 2:
                    dist, idx_in_bus_coords = tree.query(coords)
                    
                    # Heuristic threshold: 100 meters
                    if dist < 0.001:
                        bus_idx = bus_indices[idx_in_bus_coords]
                        kwp = panel.get('kwp_potential')
                        if kwp is None:
                            area = panel.get('area_sqm', 0)
                            kwp = area * 0.15
                        
                        bus_solar_capacity[bus_idx] = bus_solar_capacity.get(bus_idx, 0.0) + kwp
        
        return bus_solar_capacity

    @staticmethod
    def inject_pseudo_measurements(net, force_all: bool = False):
        """
        Inject pseudo-measurements for buses that don't have real meter readings.
        """
        if not net:
            return

        try:
            observed_elements = set(net.measurement.element[net.measurement.element_type == 'bus'])
        except (AttributeError, KeyError):
            observed_elements = set()

        import pandapower as pp
        
        # Add virtual measurements for unobserved buses
        for bus_idx in net.bus.index:
            if bus_idx not in observed_elements or force_all:
                # P=0, Q=0 for transit nodes
                pp.create_measurement(net, 'p', 'bus', 0.0, 0.01, bus_idx)
                pp.create_measurement(net, 'q', 'bus', 0.0, 0.01, bus_idx)
