"""
Thai Grid Topology Module - Refactored
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

from .topology_builder import (
    TopologyBuilder,
    BusConfig,
    LineConfig,
    TransformerConfig,
    VoltageLevel,
)

from .grid_configs.thai_standards import ThaiRegion, CableType, TransformerType, THAI_MV_KV, THAI_LV_KV
from .thai_builders.urban import UrbanNetworkBuilder
from .thai_builders.rural import RuralNetworkBuilder
from .thai_builders.commercial import CommercialNetworkBuilder

# Import EGAT transmission and PyPSA-TH integration modules
try:
    from .egat_transmission import EGATTransmissionBuilder, EGATSubstation, EGATLine
    EGAT_AVAILABLE = True
except ImportError:
    EGAT_AVAILABLE = False
    EGATTransmissionBuilder = None

@dataclass
class ThaiBusConfig(BusConfig):
    """Extended bus config with Thai-specific metadata."""
    province: Optional[str] = None
    district: Optional[str] = None
    subdistrict: Optional[str] = None
    customer_type: Optional[str] = None

class ThaiGridBuilder(TopologyBuilder):
    """
    Builds realistic Thai distribution network topologies.
    Delegates complex builds to specialized sub-builders.
    """
    
    MV_VOLTAGE_KV = THAI_MV_KV
    LV_VOLTAGE_KV = THAI_LV_KV
    
    def __init__(self, region: ThaiRegion = ThaiRegion.BANGKOK, network_name: str = "Thai Distribution Network"):
        super().__init__(network_name)
        self.region = region
        self.province: Optional[str] = None
        
    def build_urban_network(self, num_households: int = 100, **kwargs) -> pp.pandapowerNet:
        """Builds a typical Bangkok urban network (MEA style)."""
        return UrbanNetworkBuilder.build(
            self, num_households, 
            kwargs.get('province', "Bangkok"), 
            kwargs.get('district', "Bang Khen"),
            kwargs.get('latitude', 13.8788), 
            kwargs.get('longitude', 100.6025)
        )
    
    def build_rural_feeder(self, num_villages: int = 5, **kwargs) -> pp.pandapowerNet:
        """Builds a typical rural distribution feeder (PEA style)."""
        return RuralNetworkBuilder.build(
            self, num_villages, 
            kwargs.get('households_per_village', 20),
            kwargs.get('province', "Ayutthaya"),
            kwargs.get('latitude', 14.3532), 
            kwargs.get('longitude', 100.5775)
        )
    
    def build_commercial_network(self, num_shops: int = 50, **kwargs) -> pp.pandapowerNet:
        """Builds a commercial/urban mixed-use network."""
        return CommercialNetworkBuilder.build(
            self, num_shops, 
            kwargs.get('transformer_capacity_kva', 800),
            kwargs.get('province', "Bangkok"),
            kwargs.get('district', "Pathum Wan"),
            kwargs.get('latitude', 13.7465), 
            kwargs.get('longitude', 100.5347)
        )

    def get_network_summary(self) -> Dict[str, Any]:
        summary = super().get_network_summary()
        if self.net is not None:
            summary.update({
                'region': self.region.value,
                'mv_voltage_kv': self.MV_VOLTAGE_KV,
                'lv_voltage_kv': self.LV_VOLTAGE_KV,
                'distribution_transformers': len(self.net.trafo)
            })
        return summary

    def build_combined_transmission_distribution(
        self,
        region: str = "Central",
        num_households_per_substation: int = 50,
    ) -> pp.pandapowerNet:
        """
        Build combined EGAT transmission + MEA/PEA distribution network.
        """
        if not EGAT_AVAILABLE:
            raise ImportError("EGAT transmission module not available.")

        self.create_network()

        # Build EGAT transmission network for region
        egat_builder = EGATTransmissionBuilder(network_name=f"EGAT_{region}_Transmission")
        egat_net = egat_builder.build_regional_network(region=region)

        # Copy EGAT components to our network
        for bus_idx, bus_row in egat_net.bus.iterrows():
            pp.create_bus(self.net, vn_kv=bus_row['vn_kv'], name=f"EGAT_{bus_row['name']}",
                         zone=f"EGAT_{region}", geodata=egat_net.bus_geodata.get(bus_idx, (0, 0)))

        for line_idx, line_row in egat_net.line.iterrows():
            pp.create_line(self.net, from_bus=line_row['from_bus'], to_bus=line_row['to_bus'],
                          length_km=line_row['length_km'], std_type=line_row['std_type'], name=f"EGAT_{line_row['name']}")

        for trafo_idx, trafo_row in egat_net.trafo.iterrows():
            pp.create_transformer_from_parameters(self.net, hv_bus=trafo_row['hv_bus'], lv_bus=trafo_row['lv_bus'],
                                                sn_mva=trafo_row['sn_mva'], vn_hv_kv=trafo_row['vn_hv_kv'],
                                                vn_lv_kv=trafo_row['vn_lv_kv'], name=f"EGAT_{trafo_row['name']}")

        # Add distribution networks at 115 kV interface points
        egat_115kv_buses = [idx for idx, row in egat_net.bus.iterrows() if row['vn_kv'] == 115.0]

        for mv_bus_idx in egat_115kv_buses[:5]:
            mv_dist_bus = pp.create_bus(self.net, vn_kv=22.0, name=f"MV_Dist_{mv_bus_idx}", zone=f"{region}_MV")
            pp.create_transformer_from_parameters(self.net, hv_bus=mv_bus_idx, lv_bus=mv_dist_bus,
                                                sn_mva=50.0, vn_hv_kv=115.0, vn_lv_kv=22.0, name=f"TX_115_22_{mv_bus_idx}")

            lv_dist_bus = pp.create_bus(self.net, vn_kv=0.4, name=f"LV_Dist_{mv_bus_idx}", zone=f"{region}_LV")
            pp.create_transformer_from_parameters(self.net, hv_bus=mv_dist_bus, lv_bus=lv_dist_bus,
                                                sn_mva=0.5, vn_hv_kv=22.0, vn_lv_kv=0.4, name=f"TX_22_04_{mv_bus_idx}")

            for h_idx in range(num_households_per_substation):
                house_bus = pp.create_bus(self.net, vn_kv=0.4, name=f"House_{mv_bus_idx}_{h_idx}", zone=f"{region}_LV")
                pp.create_line(self.net, from_bus=lv_dist_bus, to_bus=house_bus, length_km=0.02 + (h_idx * 0.005),
                              std_type="NAYY 4x50 SE", name=f"Service_{mv_bus_idx}_{h_idx}")

        return self.net

    def export_thai_grid_geojson(self, include_transmission: bool = True, include_distribution: bool = True) -> Dict[str, Any]:
        """Export combined Thai grid as GeoJSON."""
        features = []
        # Simplified GeoJSON export logic...
        return {"type": "FeatureCollection", "features": features}

# Convenience functions
def create_bangkok_test_network(num_meters: int = 50) -> pp.pandapowerNet:
    return ThaiGridBuilder(region=ThaiRegion.BANGKOK).build_urban_network(num_households=num_meters)

def create_central_thailand_test_network(num_villages: int = 3) -> pp.pandapowerNet:
    return ThaiGridBuilder(region=ThaiRegion.CENTRAL).build_rural_feeder(num_villages=num_villages)
