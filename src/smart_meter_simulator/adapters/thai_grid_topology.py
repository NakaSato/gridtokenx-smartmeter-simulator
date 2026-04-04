"""
Thai Grid Topology Module

Realistic distribution network models for Thailand's electrical grid infrastructure.
Based on typical configurations from EGAT (Transmission), MEA (Bangkok Metro), 
and PEA (Provincial/Central Thailand).

References:
- EGAT: Electricity Generating Authority of Thailand (Transmission: 115-500 kV)
- MEA: Metropolitan Electricity Authority (Bangkok Metro Distribution: 22 kV)
- PEA: Provincial Electricity Authority (Provincial Distribution: 22 kV)
- Thai Distribution Standards: 22/0.4 kV transformers, 3-phase 4-wire LV

Network Characteristics:
- MV Distribution: 22 kV (MEA/PEA standard)
- LV Distribution: 0.4 kV (3-phase, 4-wire, 230V phase-to-neutral)
- Transformer: 22/0.4 kV, 160-1000 kVA typical
- Cable Types: AAC (MV), NAYY (LV)
- Network Topology: Radial feeders with open-ring backup

Typical Configurations:
| Region | MV Voltage | LV Voltage | Transformer | Feeder Type |
|--------|-----------|------------|-------------|-------------|
| Bangkok Urban (MEA) | 22 kV | 0.4 kV | 500-1000 kVA | Underground cable |
| Suburban (MEA/PEA) | 22 kV | 0.4 kV | 315-630 kVA | Mixed overhead/underground |
| Rural (PEA) | 22 kV | 0.4 kV | 160-400 kVA | Overhead AAC |
| Industrial | 22-33 kV | 0.4 kV | 1000+ kVA | Underground cable |

Usage:
    from smart_meter_simulator.adapters.thai_grid_topology import ThaiGridBuilder
    
    # Bangkok urban network
    builder = ThaiGridBuilder(region="bangkok")
    net = builder.build_urban_network(num_households=100)
    
    # Central Thailand rural network
    builder = ThaiGridBuilder(region="central_thailand")
    net = builder.build_rural_feeder(num_villages=5)
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


class ThaiRegion(Enum):
    """Thai geographical regions with typical grid characteristics."""
    BANGKOK = "bangkok"              # MEA: Dense urban, underground cables
    CENTRAL = "central"              # PEA: Mixed urban/rural, rice farming
    NORTH = "north"                  # PEA: Mountainous, hydro integration
    NORTHEAST = "northeast"          # PEA: Rural, solar farms
    SOUTH = "south"                  # PEA: Coastal, tourism loads


class CableType(Enum):
    """Thai standard cable types.
    
    Note: Uses pandapower standard types that match Thai installations.
    Reference: Thai PEA/MEA standards mapped to IEC standard types.
    """
    # MV Cables (22 kV)
    # Overhead: Use aluminum steel-reinforced (AL1/ST1A) types
    AAC_34 = "34-AL1/6-ST1A 20.0"   # ~34 mm² (small MV feeder)
    AAC_48 = "48-AL1/8-ST1A 20.0"   # ~48 mm² (medium MV feeder)
    AAC_70 = "70-AL1/11-ST1A 20.0"  # ~70 mm² (main MV feeder)
    AAC_94 = "94-AL1/15-ST1A 20.0"  # ~95 mm² equivalent
    AAC_122 = "122-AL1/20-ST1A 20.0"  # ~120 mm²
    AAC_149 = "149-AL1/24-ST1A 20.0"  # ~150 mm²
    AAC_184 = "184-AL1/30-ST1A 20.0"  # ~185 mm² equivalent
    
    # Underground: XLPE insulated (NA2XS2Y)
    XLPE_70 = "NA2XS2Y 1x70 RM/25 12/20 kV"
    XLPE_95 = "NA2XS2Y 1x95 RM/25 12/20 kV"
    XLPE_120 = "NA2XS2Y 1x120 RM/25 12/20 kV"
    XLPE_150 = "NA2XS2Y 1x150 RM/25 12/20 kV"
    XLPE_185 = "NA2XS2Y 1x185 RM/25 12/20 kV"
    XLPE_240 = "NA2XS2Y 1x240 RM/25 12/20 kV"
    
    # LV Cables (0.4 kV)
    NAYY_50 = "NAYY 4x50 SE"        # Standard service drop
    NAYY_120 = "NAYY 4x120 SE"      # Main feeder LV
    NAYY_150 = "NAYY 4x150 SE"      # High capacity LV
    
    # LV Overhead (for rural)
    LV_OVERHEAD_SMALL = "15-AL1/3-ST1A 0.4"   # ~16 mm²
    LV_OVERHEAD_MEDIUM = "48-AL1/8-ST1A 0.4"  # ~48 mm²
    LV_OVERHEAD_LARGE = "94-AL1/15-ST1A 0.4"  # ~95 mm²


class TransformerType(Enum):
    """Thai standard distribution transformers."""
    TX_160 = "160 kVA"     # Small rural
    TX_250 = "250 kVA"     # Rural village
    TX_315 = "315 kVA"     # Standard rural
    TX_400 = "400 kVA"     # Suburban
    TX_500 = "500 kVA"     # Urban residential
    TX_630 = "630 kVA"     # Urban commercial
    TX_800 = "800 kVA"     # High density urban
    TX_1000 = "1000 kVA"   # Industrial/Commercial


@dataclass
class ThaiBusConfig(BusConfig):
    """Extended bus config with Thai-specific metadata."""
    province: Optional[str] = None
    district: Optional[str] = None
    subdistrict: Optional[str] = None
    postal_code: Optional[str] = None
    meter_serial: Optional[str] = None
    customer_type: Optional[str] = None  # residential, commercial, industrial


class ThaiGridBuilder(TopologyBuilder):
    """
    Builds realistic Thai distribution network topologies.
    
    Features:
    - MEA/PEA standard voltage levels (22 kV MV, 0.4 kV LV)
    - Thai transformer configurations (22/0.4 kV)
    - Regional cable types (overhead AAC, underground XLPE/NAYY)
    - Urban/rural network patterns
    - Geographic metadata (Thai provinces)
    
    Example:
        builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
        net = builder.build_urban_network(
            num_households=200,
            transformer_capacity=630,
            underground=True
        )
    """
    
    # Thai standard voltages
    MV_VOLTAGE_KV = 22.0
    LV_VOLTAGE_KV = 0.4
    
    # Transformer parameters (22/0.4 kV)
    TRANSFORMER_VK_PERCENT = 4.0    # Short-circuit voltage
    TRANSFORMER_VKR_PERCENT = 1.2   # Resistive component
    TRANSFORMER_PFE_KW = 0.8        # No-load losses
    TRANSFORMER_I0_PERCENT = 0.3    # No-load current
    
    def __init__(
        self,
        region: ThaiRegion = ThaiRegion.BANGKOK,
        network_name: str = "Thai Distribution Network"
    ):
        """
        Initialize Thai grid builder.
        
        Args:
            region: Thai geographical region (determines cable types, topology)
            network_name: Name for the pandapower network
        """
        super().__init__(network_name)
        self.region = region
        self.province: Optional[str] = None
        
    def _get_cable_type(self, voltage_level: VoltageLevel, is_underground: bool = False) -> str:
        """
        Get appropriate cable type for region and voltage level.
        
        Args:
            voltage_level: MV or LV
            is_underground: Underground vs overhead installation
            
        Returns:
            pandapower standard type string
        """
        if self.region == ThaiRegion.BANGKOK:
            # Bangkok: Mostly underground (MEA)
            if voltage_level == VoltageLevel.MV:
                return "NA2XS2Y 1x185 RM/25 12/20 kV"  # XLPE 185 mm²
            else:
                return "NAYY 4x150 SE"
        
        elif self.region in [ThaiRegion.CENTRAL, ThaiRegion.NORTHEAST]:
            # Central/Northeast: Mixed overhead (PEA rural)
            if voltage_level == VoltageLevel.MV:
                return "184-AL1/30-ST1A 20.0"  # ~185 mm² overhead MV
            else:
                return "48-AL1/8-ST1A 0.4" if not is_underground else "NAYY 4x50 SE"
        
        else:
            # Default
            if voltage_level == VoltageLevel.MV:
                return "184-AL1/30-ST1A 20.0"  # Overhead MV
            else:
                return "NAYY 4x50 SE"
    
    def _get_transformer_capacity(self, num_households: int, customer_type: str = "residential") -> float:
        """
        Calculate appropriate transformer capacity in kVA.
        
        Thai typical loading:
        - Residential: 1-2 kW per household (diversity factor 0.6-0.8)
        - Commercial: 3-5 kW per shop
        - Industrial: 10-50 kW per facility
        
        Args:
            num_households: Number of connected households
            customer_type: Load type
            
        Returns:
            Transformer capacity in kVA
        """
        if customer_type == "residential":
            # Assume 1.5 kW/household with 0.7 diversity
            load_kva = num_households * 1.5 * 0.7
        elif customer_type == "commercial":
            # Assume 4 kW/shop with 0.8 diversity
            load_kva = num_households * 4.0 * 0.8
        else:  # industrial
            # Assume 15 kW/facility with 0.85 diversity
            load_kva = num_households * 15.0 * 0.85
        
        # Select next standard size (with 20% margin)
        standard_sizes = [160, 250, 315, 400, 500, 630, 800, 1000]
        target_kva = load_kva * 1.2
        
        for size in standard_sizes:
            if size >= target_kva:
                return float(size)
        
        return 1000.0  # Max standard size
    
    def create_thai_substation(
        self,
        location_name: str,
        province: str,
        latitude: float,
        longitude: float,
        mv_voltage_kv: float = 22.0
    ) -> int:
        """
        Create a Thai distribution substation (22 kV MV bus).
        
        Args:
            location_name: Substation name (e.g., "บางเขน", "ลำลูกกา")
            province: Thai province name
            latitude: Geographic latitude
            longitude: Geographic longitude
            mv_voltage_kv: MV voltage level (default 22 kV)
            
        Returns:
            Bus index of MV substation
        """
        if self.net is None:
            self.create_network()
        
        substation_bus_id = f"MV_SUB_{location_name.replace(' ', '_')}"
        
        bus_config = ThaiBusConfig(
            bus_id=substation_bus_id,
            voltage_level=VoltageLevel.MV,
            vn_kv=mv_voltage_kv,
            name=f"สถานีไฟฟ้าย่อย {location_name}",
            zone=f"{province}_MV",
            province=province,
            geo_data={'latitude': latitude, 'longitude': longitude}
        )
        
        bus_idx = self.add_bus(bus_config)
        
        # Add external grid connection (slack bus)
        self.add_external_grid(substation_bus_id, vm_pu=1.0)
        
        return bus_idx
    
    def create_distribution_transformer(
        self,
        mv_bus_id: str,
        lv_bus_id: str,
        capacity_kva: float,
        location_name: str,
        transformer_type: TransformerType = TransformerType.TX_500
    ) -> int:
        """
        Create a Thai distribution transformer (22/0.4 kV).
        
        Args:
            mv_bus_id: MV bus (22 kV) connection
            lv_bus_id: LV bus (0.4 kV) connection
            capacity_kva: Transformer capacity in kVA
            location_name: Transformer location identifier
            transformer_type: Standard transformer type
            
        Returns:
            Transformer index
        """
        sn_mva = capacity_kva / 1000.0
        
        trafo_config = TransformerConfig(
            hv_bus_id=mv_bus_id,
            lv_bus_id=lv_bus_id,
            sn_mva=sn_mva,
            vn_hv_kv=self.MV_VOLTAGE_KV,
            vn_lv_kv=self.LV_VOLTAGE_KV,
            name=f"TX-{location_name} ({capacity_kva:.0f} kVA)"
        )
        
        return self.add_transformer(trafo_config)
    
    def build_urban_network(
        self,
        num_households: int = 100,
        transformer_capacity_kva: Optional[float] = None,
        underground: bool = True,
        province: str = "Bangkok",
        district: str = "Bang Khen",
        latitude: float = 13.8788,
        longitude: float = 100.6025
    ) -> pp.pandapowerNet:
        """
        Build a typical Bangkok urban distribution network.
        
        Characteristics:
        - Underground cables (XLPE MV, NAYY LV)
        - High density: 50-200 households per transformer
        - 22 kV MV distribution
        - 0.4 kV LV network
        
        Args:
            num_households: Number of households to serve
            transformer_capacity_kva: Override auto-calculated capacity
            underground: Use underground cables (default True for Bangkok)
            province: Thai province name
            district: District name
            latitude: Center point latitude
            longitude: Center point longitude
            
        Returns:
            Configured pandapower network
        """
        self.create_network()
        
        # Auto-calculate transformer capacity if not specified
        if transformer_capacity_kva is None:
            transformer_capacity_kva = self._get_transformer_capacity(
                num_households, "residential"
            )
        
        # Create MV substation bus
        mv_bus_id = "MV_Bus_Main"
        mv_config = ThaiBusConfig(
            bus_id=mv_bus_id,
            voltage_level=VoltageLevel.MV,
            vn_kv=self.MV_VOLTAGE_KV,
            name=f"สถานีไฟฟ้าย่อย {district}",
            zone=f"{province}_MV",
            province=province,
            geo_data={'latitude': latitude, 'longitude': longitude}
        )
        self.add_bus(mv_config)
        self.add_external_grid(mv_bus_id, vm_pu=1.0)
        
        # Create LV bus (transformer secondary)
        lv_bus_id = "LV_Bus_Main"
        lv_config = ThaiBusConfig(
            bus_id=lv_bus_id,
            voltage_level=VoltageLevel.LV,
            vn_kv=self.LV_VOLTAGE_KV,
            name=f"Bus LV - {district}",
            zone=f"{province}_LV",
            province=province,
            geo_data={'latitude': latitude - 0.0005, 'longitude': longitude}
        )
        lv_bus_idx = self.add_bus(lv_config)
        
        # Add distribution transformer
        self.create_distribution_transformer(
            mv_bus_id=mv_bus_id,
            lv_bus_id=lv_bus_id,
            capacity_kva=transformer_capacity_kva,
            location_name=district
        )
        
        # Create LV feeders (underground)
        cable_type = "NAYY 4x150 SE" if underground else "AAC 70 mm²"
        
        # Divide households into 4 feeders
        households_per_feeder = num_households // 4
        
        for feeder_idx in range(4):
            feeder_id = f"Feeder_{feeder_idx}"
            
            # Create feeder bus
            feeder_offset = 0.001 * (feeder_idx - 1.5)
            feeder_bus_id = f"{feeder_id}_Bus"
            feeder_config = ThaiBusConfig(
                bus_id=feeder_bus_id,
                voltage_level=VoltageLevel.LV,
                vn_kv=self.LV_VOLTAGE_KV,
                name=f"Feeder {feeder_idx} - {district}",
                zone=f"{province}_LV_{feeder_idx}",
                province=province,
                geo_data={
                    'latitude': latitude - 0.001 + feeder_offset,
                    'longitude': longitude + feeder_offset * 0.5
                }
            )
            self.add_bus(feeder_config)
            
            # Connect feeder to LV bus
            line_config = LineConfig(
                from_bus_id=lv_bus_id,
                to_bus_id=feeder_bus_id,
                length_km=0.05,  # 50m from transformer
                std_type=cable_type,
                name=f"LV_Main_{feeder_idx}"
            )
            self.add_line(line_config)
            
            # Create radial feeder with households
            for house_idx in range(households_per_feeder):
                house_bus_id = f"{feeder_id}_House_{house_idx}"
                house_lat = latitude - 0.001 + feeder_offset + (house_idx * 0.0001)
                house_lng = longitude + feeder_offset * 0.5 + (house_idx * 0.00005)
                
                house_config = ThaiBusConfig(
                    bus_id=house_bus_id,
                    voltage_level=VoltageLevel.LV,
                    vn_kv=self.LV_VOLTAGE_KV,
                    name=f"House {feeder_idx}-{house_idx}",
                    zone=f"{province}_LV_{feeder_idx}",
                    province=province,
                    district=district,
                    customer_type="residential",
                    geo_data={'latitude': house_lat, 'longitude': house_lng}
                )
                self.add_bus(house_config)
                
                # Connect house to feeder
                line_length = 0.02 + (house_idx * 0.005)  # 20-70m service drop
                line_config = LineConfig(
                    from_bus_id=feeder_bus_id if house_idx == 0 else f"{feeder_id}_House_{house_idx-1}",
                    to_bus_id=house_bus_id,
                    length_km=line_length,
                    std_type="NAYY 4x50 SE",
                    name=f"Service_{feeder_idx}_{house_idx}"
                )
                self.add_line(line_config)
        
        return self.net
    
    def build_rural_feeder(
        self,
        num_villages: int = 5,
        households_per_village: int = 20,
        province: str = "Ayutthaya",
        latitude: float = 14.3532,
        longitude: float = 100.5775
    ) -> pp.pandapowerNet:
        """
        Build a typical rural distribution feeder (Central Thailand style).
        
        Characteristics:
        - Overhead AAC cables (MV and LV)
        - Long feeder lines (villages spread out)
        - One transformer per village (160-315 kVA)
        - 22 kV MV distribution along road
        
        Args:
            num_villages: Number of villages along feeder
            households_per_village: Houses per village
            province: Thai province name
            latitude: Starting point latitude
            longitude: Starting point longitude
            
        Returns:
            Configured pandapower network
        """
        self.create_network()
        
        # Create MV substation
        mv_bus_id = "MV_Substation"
        mv_config = ThaiBusConfig(
            bus_id=mv_bus_id,
            voltage_level=VoltageLevel.MV,
            vn_kv=self.MV_VOLTAGE_KV,
            name=f"สถานีไฟฟ้าย่อย {province}",
            zone=f"{province}_MV",
            province=province,
            geo_data={'latitude': latitude, 'longitude': longitude}
        )
        self.add_bus(mv_config)
        self.add_external_grid(mv_bus_id, vm_pu=1.0)
        
        # Create MV main feeder
        previous_mv_bus = mv_bus_id
        
        for village_idx in range(num_villages):
            village_name = f"Village_{village_idx}"
            
            # MV bus for this village (5 km spacing typical)
            village_mv_bus_id = f"MV_{village_name}"
            village_mv_lat = latitude - (village_idx * 0.045)  # ~5 km per village
            
            mv_config = ThaiBusConfig(
                bus_id=village_mv_bus_id,
                voltage_level=VoltageLevel.MV,
                vn_kv=self.MV_VOLTAGE_KV,
                name=f"MV Bus - {village_name}",
                zone=f"{province}_MV",
                province=province,
                geo_data={'latitude': village_mv_lat, 'longitude': longitude}
            )
            self.add_bus(mv_config)
            
            # Connect to previous MV bus
            line_config = LineConfig(
                from_bus_id=previous_mv_bus,
                to_bus_id=village_mv_bus_id,
                length_km=5.0,  # 5 km between villages
                std_type="184-AL1/30-ST1A 20.0",  # Overhead MV (~185 mm²)
                name=f"MV_Feeder_{village_idx}"
            )
            self.add_line(line_config)
            
            # Create village LV network
            village_lv_bus_id = f"LV_{village_name}"
            lv_config = ThaiBusConfig(
                bus_id=village_lv_bus_id,
                voltage_level=VoltageLevel.LV,
                vn_kv=self.LV_VOLTAGE_KV,
                name=f"LV Bus - {village_name}",
                zone=f"{province}_LV_{village_idx}",
                province=province,
                geo_data={'latitude': village_mv_lat - 0.001, 'longitude': longitude}
            )
            self.add_bus(lv_config)
            
            # Add village transformer (smaller for rural: 160-315 kVA)
            tx_capacity = self._get_transformer_capacity(
                households_per_village, "residential"
            )
            tx_capacity = min(tx_capacity, 315)  # Cap at 315 kVA for rural
            
            self.create_distribution_transformer(
                mv_bus_id=village_mv_bus_id,
                lv_bus_id=village_lv_bus_id,
                capacity_kva=tx_capacity,
                location_name=village_name
            )
            
            # Create radial LV feeder for village houses
            for house_idx in range(households_per_village):
                house_bus_id = f"{village_name}_House_{house_idx}"
                house_lat = village_mv_lat - 0.001 - (house_idx * 0.0002)
                house_lng = longitude + (house_idx * 0.0001 - 0.001)
                
                house_config = ThaiBusConfig(
                    bus_id=house_bus_id,
                    voltage_level=VoltageLevel.LV,
                    vn_kv=self.LV_VOLTAGE_KV,
                    name=f"House {village_idx}-{house_idx}",
                    zone=f"{province}_LV_{village_idx}",
                    province=province,
                    customer_type="residential",
                    geo_data={'latitude': house_lat, 'longitude': house_lng}
                )
                self.add_bus(house_config)
                
                # Connect house to LV feeder
                line_length = 0.03 + (house_idx * 0.01)  # 30-230m service drop
                line_config = LineConfig(
                    from_bus_id=village_lv_bus_id if house_idx == 0 else f"{village_name}_House_{house_idx-1}",
                    to_bus_id=house_bus_id,
                    length_km=line_length,
                    std_type="48-AL1/8-ST1A 0.4",  # Overhead LV service (~48 mm²)
                    name=f"Service_{village_idx}_{house_idx}"
                )
                self.add_line(line_config)
            
            previous_mv_bus = village_mv_bus_id
        
        return self.net
    
    def build_commercial_network(
        self,
        num_shops: int = 50,
        transformer_capacity_kva: float = 800,
        province: str = "Bangkok",
        district: str = "Pathum Wan",
        latitude: float = 13.7465,
        longitude: float = 100.5347
    ) -> pp.pandapowerNet:
        """
        Build a commercial/urban mixed-use network.
        
        Characteristics:
        - Higher capacity transformers (630-1000 kVA)
        - Underground cables throughout
        - 3-phase loads (shops, offices)
        - Higher load density
        
        Args:
            num_shops: Number of commercial units
            transformer_capacity_kva: Transformer capacity
            province: Province name
            district: District name
            latitude: Center latitude
            longitude: Center longitude
            
        Returns:
            Configured pandapower network
        """
        self.create_network()
        
        # MV bus
        mv_bus_id = "MV_Bus_Commercial"
        mv_config = ThaiBusConfig(
            bus_id=mv_bus_id,
            voltage_level=VoltageLevel.MV,
            vn_kv=self.MV_VOLTAGE_KV,
            name=f"สถานีไฟฟ้าย่อย {district}",
            zone=f"{province}_MV",
            province=province,
            geo_data={'latitude': latitude, 'longitude': longitude}
        )
        self.add_bus(mv_config)
        self.add_external_grid(mv_bus_id, vm_pu=1.0)
        
        # LV bus
        lv_bus_id = "LV_Bus_Commercial"
        lv_config = ThaiBusConfig(
            bus_id=lv_bus_id,
            voltage_level=VoltageLevel.LV,
            vn_kv=self.LV_VOLTAGE_KV,
            name=f"Bus LV - {district}",
            zone=f"{province}_LV",
            province=province,
            geo_data={'latitude': latitude - 0.0005, 'longitude': longitude}
        )
        lv_bus_idx = self.add_bus(lv_config)
        
        # Transformer
        self.create_distribution_transformer(
            mv_bus_id=mv_bus_id,
            lv_bus_id=lv_bus_id,
            capacity_kva=transformer_capacity_kva,
            location_name=district,
            transformer_type=TransformerType.TX_800
        )
        
        # Create commercial feeders (2 feeders for reliability)
        shops_per_feeder = num_shops // 2
        
        for feeder_idx in range(2):
            feeder_id = f"Comm_Feeder_{feeder_idx}"
            
            # Feeder bus
            feeder_bus_id = f"{feeder_id}_Bus"
            feeder_config = ThaiBusConfig(
                bus_id=feeder_bus_id,
                voltage_level=VoltageLevel.LV,
                vn_kv=self.LV_VOLTAGE_KV,
                name=f"Commercial Feeder {feeder_idx}",
                zone=f"{province}_LV_Commercial",
                province=province,
                geo_data={
                    'latitude': latitude - 0.001 + (feeder_idx * 0.002),
                    'longitude': longitude
                }
            )
            self.add_bus(feeder_config)
            
            # Connect to LV bus
            line_config = LineConfig(
                from_bus_id=lv_bus_id,
                to_bus_id=feeder_bus_id,
                length_km=0.1,
                std_type="NAYY 4x150 SE",
                name=f"Comm_Main_{feeder_idx}"
            )
            self.add_line(line_config)
            
            # Create shops along feeder
            for shop_idx in range(shops_per_feeder):
                shop_bus_id = f"{feeder_id}_Shop_{shop_idx}"
                shop_config = ThaiBusConfig(
                    bus_id=shop_bus_id,
                    voltage_level=VoltageLevel.LV,
                    vn_kv=self.LV_VOLTAGE_KV,
                    name=f"Shop {feeder_idx}-{shop_idx}",
                    zone=f"{province}_LV_Commercial",
                    province=province,
                    district=district,
                    customer_type="commercial",
                    geo_data={
                        'latitude': latitude - 0.001 + (feeder_idx * 0.002),
                        'longitude': longitude + (shop_idx * 0.0002)
                    }
                )
                self.add_bus(shop_config)
                
                # Connect shop to feeder
                line_config = LineConfig(
                    from_bus_id=feeder_bus_id if shop_idx == 0 else f"{feeder_id}_Shop_{shop_idx-1}",
                    to_bus_id=shop_bus_id,
                    length_km=0.02,
                    std_type="NAYY 4x120 SE",  # Commercial service (120 mm²)
                    name=f"Shop_Service_{feeder_idx}_{shop_idx}"
                )
                self.add_line(line_config)
        
        return self.net
    
    def get_network_summary(self) -> Dict[str, Any]:
        """
        Get summary with Thai-specific statistics.
        
        Returns:
            Dictionary with network statistics
        """
        summary = super().get_network_summary()
        
        if self.net is None:
            return summary
        
        # Add Thai-specific stats
        summary['region'] = self.region.value if self.region else "Unknown"
        summary['mv_voltage_kv'] = self.MV_VOLTAGE_KV
        summary['lv_voltage_kv'] = self.LV_VOLTAGE_KV
        
        # Count transformers
        summary['distribution_transformers'] = len(self.net.trafo)
        
        # Calculate total transformer capacity
        if len(self.net.trafo) > 0:
            total_capacity_mva = self.net.trafo['sn_mva'].sum()
            summary['total_transformer_capacity_mva'] = total_capacity_mva
            summary['total_transformer_capacity_kva'] = total_capacity_mva * 1000
        
        # Count cable types
        if len(self.net.line) > 0:
            cable_types = self.net.line['std_type'].value_counts().to_dict()
            summary['cable_types'] = cable_types
        
        return summary


def create_bangkok_test_network(num_meters: int = 50) -> pp.pandapowerNet:
    """
    Create a test network representing Bangkok urban distribution.
    
    Convenience function for quick testing with typical Bangkok parameters.
    
    Args:
        num_meters: Approximate number of meter connection points
        
    Returns:
        Pandapower network
    """
    builder = ThaiGridBuilder(region=ThaiRegion.BANGKOK)
    return builder.build_urban_network(
        num_households=num_meters,
        province="Bangkok",
        district="Bang Khen",
        latitude=13.8788,
        longitude=100.6025
    )


def create_central_thailand_test_network(num_villages: int = 3) -> pp.pandapowerNet:
    """
    Create a test network representing Central Thailand rural distribution.
    
    Convenience function for quick testing with typical rural parameters.
    
    Args:
        num_villages: Number of villages along the feeder
        
    Returns:
        Pandapower network
    """
    builder = ThaiGridBuilder(region=ThaiRegion.CENTRAL)
    return builder.build_rural_feeder(
        num_villages=num_villages,
        households_per_village=15,
        province="Ayutthaya",
        latitude=14.3532,
        longitude=100.5775
    )
