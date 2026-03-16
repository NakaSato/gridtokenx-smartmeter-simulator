"""
Pandapower Adapter - Phase 2 PoC

Converts SmartMeter instances and EnergyReadings into pandapower net.measurement tables.

This is a Proof of Concept implementation for Phase 2. It demonstrates:
1. Mapping SmartMeter → pandapower measurement DataFrame
2. Sign convention handling (Load vs. Generator reference frames)
3. Element-based modeling (load elements, bus measurements)
4. Accuracy class to std_dev conversion (basic implementation)

References:
- meter_spec.md Sections 4.1-4.3 (Pandapower Architecture)
- meter_spec.md Section 5.3 (Measurement Accuracy)
"""

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import json
import os

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False
    print("Warning: pandapower not installed. Run: pip install -e .[dev]")

from ..config import AccuracyClass, MeterType
from ..core.meter import SmartMeter
from ..models.reading import EnergyReading
from .topology_builder import TopologyBuilder, BusConfig, VoltageLevel


class MeasurementTableBuilder:
    """
    Builds pandapower net.measurement DataFrames from SmartMeter readings.
    
    This class handles:
    - Creating measurement entries for voltage (v), active power (p), reactive power (q)
    - Calculating std_dev from accuracy class
    - Enforcing sign conventions (load consumption positive, generation negative)
    - Mapping to grid elements (bus, load, trafo)
    """
    
    def __init__(self, sigma_factor: int = 3):
        """
        Initialize measurement table builder.
        
        Args:
            sigma_factor: Conversion factor for accuracy class to std_dev.
                         3 = conservative (3σ bound at 99.7% confidence)
                         2 = standard (2σ bound at 95% confidence)
        """
        self.sigma_factor = sigma_factor
        self.measurements: List[Dict[str, Any]] = []
        
        # Accuracy class mapping by meter type
        # Using the available MeterType values from config
        self.accuracy_map = {
            MeterType.SOLAR_PROSUMER: AccuracyClass.CLASS_1_0,
            MeterType.GRID_CONSUMER: AccuracyClass.CLASS_2_0,
            MeterType.HYBRID_PROSUMER: AccuracyClass.CLASS_1_0,
            MeterType.BATTERY_STORAGE: AccuracyClass.CLASS_0_5,
            # Phase 2 additions
            MeterType.RESIDENTIAL: AccuracyClass.CLASS_2_0,
            MeterType.COMMERCIAL: AccuracyClass.CLASS_1_0,
            MeterType.FEEDER: AccuracyClass.CLASS_0_5,
            MeterType.SUBSTATION: AccuracyClass.CLASS_0_2,
        }
    
    def calculate_std_dev(self, accuracy_class: Any, nominal_value: float) -> float:
        """
        Calculate standard deviation from accuracy class.
        
        Formula (meter_spec.md Section 5.3):
            σ = (AccuracyClass / (100 * sigma_factor)) × |NominalValue|
            
        Uses a minimum absolute floor to prevent near-zero std_dev when
        measured values are small (common in distribution-level smart meters
        where loads are < 0.1 MW). Without this floor, the Chi² test
        produces astronomical residuals from tiny absolute errors.
            
        Args:
            accuracy_class: Accuracy class value (float or Enum)
            nominal_value: Nominal value of measurement
            
        Returns:
            Standard deviation with sensible minimum floor
        """
        accuracy_value = accuracy_class.value if isinstance(accuracy_class, AccuracyClass) else accuracy_class
        std_dev = (accuracy_value / (100 * self.sigma_factor)) * abs(nominal_value)
        # Minimum floor: 0.001 for power (1 kW), 0.005 for voltage (0.5% pu)
        # This prevents near-zero std_dev from dominating the Chi² statistic
        min_floor = 0.001
        return max(std_dev, min_floor)
    
    def add_voltage_measurement(
        self,
        meter_id: str,
        bus_index: int,
        voltage_pu: float,
        meter_type: MeterType,
        std_dev: Optional[float] = None
    ):
        """
        Add voltage measurement at a bus.
        
        Sign convention: Voltage is always positive (magnitude).
        Element type: 'bus' (voltage is a nodal property)
        Typical std_dev: 1% of nominal for residential, 0.2-0.5% for commercial
        
        Args:
            meter_id: Unique meter identifier
            bus_index: Index of bus in pandapower network
            voltage_pu: Voltage magnitude in per-unit
            meter_type: Type of meter (determines accuracy class)
            std_dev: Optional standard deviation (uses accuracy class if None)
        """
        if std_dev is None:
            accuracy = self.accuracy_map.get(meter_type, AccuracyClass.CLASS_1_0)
            std_dev = self.calculate_std_dev(accuracy, voltage_pu)
        
        self.measurements.append({
            'name': f'{meter_id}_V',
            'measurement_type': 'v',
            'element_type': 'bus',
            'element': bus_index,
            'value': voltage_pu,
            'std_dev': std_dev,
            'side': None,  # Not applicable for bus measurements
        })
    
    def add_active_power_measurement(
        self,
        meter_id: str,
        load_index: int,
        power_mw: float,
        meter_type: MeterType,
        is_generation: bool = False,
        element_type: str = 'load',
        std_dev: Optional[float] = None
    ):
        """
        Add active power measurement at a load element.
        
        Sign convention (meter_spec.md Section 4.3):
        - Load consumption: positive value (element_type='load')
        - Generation: negative value for bus injection, OR positive at sgen element
        
        Typical std_dev: 2% of nominal for residential, 1% for commercial
        
        Args:
            meter_id: Unique meter identifier
            load_index: Index of load/sgen in pandapower network
            power_mw: Active power in MW (positive for consumption)
            meter_type: Type of meter (determines accuracy class)
            is_generation: True if this is generator output (affects sign)
        """
        if std_dev is None:
            accuracy = self.accuracy_map.get(meter_type, AccuracyClass.CLASS_1_0)
            # Use slightly higher std_dev for power than voltage (typically 2% vs 1%)
            std_dev = self.calculate_std_dev(accuracy, power_mw) * 2.0
        
        # For generation, we model it as positive at sgen element
        # (Alternative: negative bus injection - see meter_spec.md Section 4.3)
        # element_type = 'sgen' if is_generation else 'load' # Overridden by param
        
        self.measurements.append({
            'name': f'{meter_id}_P',
            'measurement_type': 'p',
            'element_type': element_type,
            'element': load_index,
            'value': power_mw,
            'std_dev': std_dev,
            'side': None,  # Not applicable for load/sgen measurements
        })
    
    def add_reactive_power_measurement(
        self,
        meter_id: str,
        load_index: int,
        power_mvar: float,
        meter_type: MeterType,
        is_generation: bool = False,
        element_type: str = 'load',
        std_dev: Optional[float] = None
    ):
        """
        Add reactive power measurement at a load element.
        
        Sign convention: Same as active power.
        Typical std_dev: 3% of nominal (higher uncertainty than active power)
        
        Args:
            meter_id: Unique meter identifier
            load_index: Index of load/sgen in pandapower network
            power_mvar: Reactive power in MVar
            meter_type: Type of meter (determines accuracy class)
            is_generation: True if this is generator output
        """
        if std_dev is None:
            accuracy = self.accuracy_map.get(meter_type, AccuracyClass.CLASS_1_0)
            # Reactive power typically has higher uncertainty (3% vs 2% for P)
            std_dev = self.calculate_std_dev(accuracy, power_mvar) * 3.0
        
        # element_type = 'sgen' if is_generation else 'load' # Overridden by param
        
        self.measurements.append({
            'name': f'{meter_id}_Q',
            'measurement_type': 'q',
            'element_type': element_type,
            'element': load_index,
            'value': power_mvar,
            'std_dev': std_dev,
            'side': None,
        })
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert measurements to pandapower-compatible DataFrame.
        
        Returns:
            DataFrame with columns: name, meas_type, element_type, element,
                                   value, std_dev, side
        """
        if not self.measurements:
            return pd.DataFrame(columns=[
                'name', 'meas_type', 'measurement_type', 'element_type', 'element',
                'value', 'std_dev', 'side'
            ])
        
        df = pd.DataFrame(self.measurements)
        if 'measurement_type' in df.columns:
            df['meas_type'] = df['measurement_type']
        elif 'meas_type' in df.columns:
            df['measurement_type'] = df['meas_type']
        return df
    
    def clear(self):
        """Clear all measurements."""
        self.measurements = []


class PandapowerAdapter:
    """
    High-level adapter for converting SmartMeter instances to pandapower networks.
    
    This adapter integrates:
    - TopologyBuilder: Network structure creation
    - MeasurementTableBuilder: Measurement data conversion
    - Element placement: Load/sgen assignment to buses
    
    Full Phase 2 features:
    - Network topology creation (buses, lines, transformers)
    - Load/sgen element creation
    - Measurement mapping with proper indexing
    - State estimation integration (future)
    """
    
    def __init__(self, sigma_factor: int = 3, topology_builder: Optional[TopologyBuilder] = None):
        """
        Initialize pandapower adapter.
        
        Args:
            sigma_factor: Accuracy class to std_dev conversion factor
            topology_builder: Optional TopologyBuilder instance (creates new if None)
        """
        if not PANDAPOWER_AVAILABLE:
            raise ImportError(
                "pandapower is required for this adapter. "
                "Install with: pip install pandapower>=2.14.0"
            )
        
        self.sigma_factor = sigma_factor
        self.builder = MeasurementTableBuilder(sigma_factor)
        self.topology_builder = topology_builder or TopologyBuilder()
    
    def create_simple_network(self, num_buses: int = 1) -> pp.pandapowerNet:
        """
        Create a simple pandapower network for PoC/testing.
        
        Deprecated: Use TopologyBuilder directly for production networks.
        This method is kept for backward compatibility with PoC scripts.
        
        Creates:
        - External grid connection at bus 0
        - num_buses buses at 0.4 kV (LV distribution)
        - Lines connecting buses
        
        Args:
            num_buses: Number of buses to create
            
        Returns:
            pandapower network object
        """
        # Use TopologyBuilder for network creation
        return self.topology_builder.build_radial_network(
            num_buses=num_buses,
            voltage_kv=0.4,
            line_length_km=0.1,
            add_grid=True
        )
    
    def build_network_from_meters(self, meters: List[SmartMeter]) -> Tuple[pp.pandapowerNet, Dict[str, int]]:
        """
        Build a realistic grid topology based on meter coordinates using spatial constraints.
        
        Logic:
        - Creates a BusConfig for each meter with its geographic coordinates.
        - Uses Delaunay Triangulation and MST to form a sparse, radial distribution grid.
        - Returns the net and a mapping of meter_id -> bus_index.
        
        Args:
            meters: List of SmartMeter instances
            
        Returns:
            Tuple of (pandapowerNet, meter_to_bus_map)
        """
        # 1. Create BusConfigs for each meter to enable spatial optimization
        bus_configs = []
        for meter in meters:
            lat = meter.config.get('latitude')
            lng = meter.config.get('longitude')
            
            # Default coordinates if missing (centered in Bangkok)
            if lat is None or lng is None:
                lat, lng = 13.7563, 100.6610
                
            bus_configs.append(BusConfig(
                bus_id=meter.meter_id,
                voltage_level=VoltageLevel.LV,
                vn_kv=0.4,
                name=meter.config.get('location_name', meter.meter_id),
                geo_data={'latitude': lat, 'longitude': lng},
                zone=meter.config.get('zone', 'Village')
            ))
            
        # 2. Build the street-aligned network (Backbone & Drop)
        net = self.topology_builder.build_street_aligned_network(
            bus_configs=bus_configs,
            voltage_kv=0.4,
            add_grid=True
        )
        
        meter_to_bus_map = {}
        
        # 3. Finalize meter integration (loads/sgens/coords)
        for meter in meters:
            bus_idx = self.topology_builder.get_bus_index(meter.meter_id)
            if bus_idx is not None:
                meter_to_bus_map[meter.meter_id] = bus_idx
                
                # Set metadata in pandapower bus table
                loc_name = meter.config.get('location_name')
                phase = meter.config.get('phase')
                if loc_name:
                    full_name = f"{loc_name} (Phase {phase})" if phase else loc_name
                    net.bus.at[bus_idx, 'name'] = full_name
                
                # Ensure coordinates are in bus_geocoord
                lat = meter.config.get('latitude')
                lng = meter.config.get('longitude')
                if lat is not None and lng is not None:
                    if 'bus_geocoord' not in net or net.bus_geocoord is None:
                        net.bus_geocoord = pd.DataFrame(columns=['x', 'y'])
                    net.bus_geocoord.loc[bus_idx] = [lng, lat]
                
                # Create placeholder load and sgen elements
                pp.create_load(net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"Load_{meter.meter_id}")
                pp.create_sgen(net, bus=bus_idx, p_mw=0, q_mvar=0, name=f"Solar_{meter.meter_id}")
                
        return net, meter_to_bus_map
    
    def add_meter_to_network(
        self,
        net: pp.pandapowerNet,
        meter: SmartMeter,
        reading: EnergyReading,
        bus_index: int
    ) -> Dict[str, int]:
        """
        Add a smart meter's load/generation and measurements to network.
        
        Args:
            net: pandapower network
            meter: SmartMeter instance
            reading: Current energy reading from meter
            bus_index: Bus to connect meter to
            
        Returns:
            Dictionary with 'load_index' and/or 'sgen_index'
        """
        indices = {}
        
        # Convert kWh to MW using the actual interval
        # Power (kW) = Energy (kWh) / (interval_seconds / 3600.0)
        hours = reading.interval_seconds / 3600.0
        p_kw = reading.energy_consumed / hours if hours > 0 else 0.0
        p_mw = p_kw / 1000.0  # Consumption
        
        # Create load element
        if p_mw > 0:
            load_idx = pp.create_load(
                net,
                bus=bus_index,
                p_mw=p_mw,
                q_mvar=p_mw * 0.3,  # Assume 0.3 power factor for reactive
                name=f"Load_{meter.meter_id}"
            )
            indices['load_index'] = load_idx
            
            # Add measurements for this load
            self.builder.add_active_power_measurement(
                meter.meter_id,
                load_idx,
                p_mw,
                meter.config.get('meter_type', MeterType.GRID_CONSUMER),
                is_generation=False
            )
            self.builder.add_reactive_power_measurement(
                meter.meter_id,
                load_idx,
                p_mw * 0.3,
                meter.config.get('meter_type', MeterType.GRID_CONSUMER),
                is_generation=False
            )
        
        # Create sgen element for generation
        if reading.energy_generated > 0:
            p_gen_kw = reading.energy_generated / (reading.interval_seconds / 3600.0)
            p_gen_mw = p_gen_kw / 1000.0
            sgen_idx = pp.create_sgen(
                net,
                bus=bus_index,
                p_mw=p_gen_mw,
                q_mvar=0.0,  # PV typically unity power factor
                name=f"Solar_{meter.meter_id}"
            )
            indices['sgen_index'] = sgen_idx
            
            # Add measurements for generation
            self.builder.add_active_power_measurement(
                meter.meter_id + "_GEN",
                sgen_idx,
                p_gen_mw,
                meter.config.get('meter_type', MeterType.SOLAR_PROSUMER),
                is_generation=True
            )
        
        # Add voltage measurement at bus
        # Convert from nominal voltage to p.u. (0.4 kV nominal)
        # Assuming reading.voltage is phase-to-neutral (e.g. 240V), 
        # convert to p.u. for a phase-to-phase grid (e.g. 400V).
        v_nominal_kv = net.bus.vn_kv.at[bus_index]
        voltage_pu = (reading.voltage * np.sqrt(3)) / (v_nominal_kv * 1000)
        
        self.builder.add_voltage_measurement(
            meter.meter_id,
            bus_index,
            voltage_pu,
            meter.config.get('meter_type', MeterType.GRID_CONSUMER)
        )
        
        return indices
    
    def get_measurement_table(self) -> pd.DataFrame:
        """
        Get the complete measurement table.
        
        Returns:
            DataFrame compatible with pandapower net.measurement
        """
        return self.builder.to_dataframe()
