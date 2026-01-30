#!/usr/bin/env python3
"""
Pandapower Integration - Proof of Concept

This script validates Phase 2 approach by:
1. Creating 10 smart meters with diverse characteristics
2. Generating energy readings
3. Building a simple pandapower network
4. Converting readings to net.measurement table
5. Validating DataFrame schema and values

Success criteria (per Week 2 plan):
- ✓ net.measurement DataFrame created without errors
- ✓ 10+ meters successfully mapped
- ✓ Voltage, P, Q measurements present
- ✓ std_dev values calculated correctly
- ✓ Sign conventions enforced

Run with: python scripts/poc_pandapower.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.meter import SmartMeter
from app.models.reading import EnergyReading
from app.config import MeterType
from app.adapters.pandapower_adapter import PandapowerAdapter, AccuracyClass

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False
    print("⚠️  pandapower not installed. Running in simulation mode.")
    print("   To install: pip install pandapower>=2.14.0")
    print()


def create_test_meters(count: int = 10):
    """
    Create diverse smart meters for PoC.
    
    Returns:
        List of (meter, reading) tuples
    """
    meters_and_readings = []
    
    meter_configs = [
        # Grid consumers
        {
            "meter_id": "RES_001",
            "meter_type": MeterType.GRID_CONSUMER,
            "energy_consumed": 1.5,  # kWh for 15 min
            "energy_generated": 0.0,
            "voltage": 235.0,
        },
        {
            "meter_id": "RES_002",
            "meter_type": MeterType.GRID_CONSUMER,
            "energy_consumed": 2.1,
            "energy_generated": 0.0,
            "voltage": 238.0,
        },
        # Solar prosumers
        {
            "meter_id": "SOLAR_001",
            "meter_type": MeterType.SOLAR_PROSUMER,
            "energy_consumed": 0.5,
            "energy_generated": 3.2,
            "voltage": 240.0,
        },
        {
            "meter_id": "SOLAR_002",
            "meter_type": MeterType.SOLAR_PROSUMER,
            "energy_consumed": 0.8,
            "energy_generated": 2.5,
            "voltage": 239.0,
        },
        # More grid consumers
        {
            "meter_id": "COM_001",
            "meter_type": MeterType.GRID_CONSUMER,
            "energy_consumed": 8.5,
            "energy_generated": 0.0,
            "voltage": 237.0,
        },
        {
            "meter_id": "COM_002",
            "meter_type": MeterType.GRID_CONSUMER,
            "energy_consumed": 12.3,
            "energy_generated": 0.0,
            "voltage": 236.0,
        },
        # Hybrid (solar + battery)
        {
            "meter_id": "HYB_001",
            "meter_type": MeterType.HYBRID_PROSUMER,
            "energy_consumed": 1.2,
            "energy_generated": 4.5,
            "voltage": 241.0,
        },
        # Battery storage
        {
            "meter_id": "BAT_001",
            "meter_type": MeterType.BATTERY_STORAGE,
            "energy_consumed": 5.0,  # Charging
            "energy_generated": 0.0,
            "voltage": 238.5,
        },
        # More hybrid prosumers
        {
            "meter_id": "HYB_002",
            "meter_type": MeterType.HYBRID_PROSUMER,
            "energy_consumed": 2.0,
            "energy_generated": 3.0,
            "voltage": 239.5,
        },
        # Grid consumer (large)
        {
            "meter_id": "FEED_001",
            "meter_type": MeterType.GRID_CONSUMER,
            "energy_consumed": 150.0,
            "energy_generated": 0.0,
            "voltage": 400.0,  # Different voltage level
        },
    ]
    
    timestamp = datetime.now(timezone.utc)
    
    for config in meter_configs[:count]:
        # Create meter with config dict
        meter_config = {
            "meter_id": config["meter_id"],
            "meter_type": config["meter_type"],
            "interval_seconds": 900,  # 15 minutes
            "has_solar": config["energy_generated"] > 0,
            "has_battery": config["meter_type"] in [MeterType.BATTERY_STORAGE, MeterType.HYBRID_PROSUMER],
            "current_battery_level": 50.0 if config["meter_type"] == MeterType.BATTERY_STORAGE else 0.0,
        }
        meter = SmartMeter(config=meter_config)
        
        # Create reading with all required fields
        net_energy = config["energy_generated"] - config["energy_consumed"]
        reading = EnergyReading(
            meter_id=config["meter_id"],
            timestamp=timestamp,
            energy_consumed=config["energy_consumed"],
            energy_generated=config["energy_generated"],
            surplus_energy=max(0, net_energy),
            deficit_energy=max(0, -net_energy),
            voltage=config["voltage"],
            current=config["energy_consumed"] * 4000 / config["voltage"],  # I = P/V
            power_factor=0.95,
            frequency=50.0,
            temperature=20.0,
            location="Test Location",
            meter_type=config["meter_type"].value,
            user_type="Test User",
            battery_level=meter_config["current_battery_level"],
            weather_condition="Sunny",
        )
        
        meters_and_readings.append((meter, reading))
    
    return meters_and_readings


def run_poc():
    """
    Execute Pandapower integration PoC.
    """
    print("=" * 60)
    print("Pandapower Integration - Proof of Concept")
    print("=" * 60)
    print()
    
    # Step 1: Create test meters
    print("Step 1: Creating 10 test meters...")
    meters_and_readings = create_test_meters(10)
    print(f"✓ Created {len(meters_and_readings)} meters\n")
    
    # Step 2: Initialize pandapower adapter
    print("Step 2: Initializing PandapowerAdapter...")
    if not PANDAPOWER_AVAILABLE:
        print("⚠️  Skipping network creation (pandapower not available)")
        print("   Will validate adapter logic only\n")
        # Create a mock adapter that doesn't require pandapower for network ops
        from app.adapters.pandapower_adapter import MeasurementTableBuilder
        builder = MeasurementTableBuilder(sigma_factor=3)
        adapter = None
        net = None
    else:
        adapter = PandapowerAdapter(sigma_factor=3)
        print("✓ Adapter initialized\n")
        
        # Step 3: Create network
        print("Step 3: Creating pandapower network...")
        net = adapter.create_simple_network(num_buses=10)
        print(f"✓ Network created with {len(net.bus)} buses\n")
        builder = adapter.builder
    
    # Step 4: Add meters to network
    print("Step 4: Adding meters to network and generating measurements...")
    if PANDAPOWER_AVAILABLE and adapter is not None and net is not None:
        for idx, (meter, reading) in enumerate(meters_and_readings):
            bus_idx = idx  # One meter per bus for simplicity
            indices = adapter.add_meter_to_network(net, meter, reading, bus_idx)
            print(f"  - {meter.meter_id} → Bus {bus_idx} (indices: {indices})")
    else:
        # Manual measurement generation without pandapower network
        print("  (Generating measurements without network - validation mode)")
        for idx, (meter, reading) in enumerate(meters_and_readings):
            # Add voltage measurement
            voltage_pu = reading.voltage / 400.0  # Assume 400V base
            builder.add_voltage_measurement(
                meter.meter_id,
                idx,  # bus_index
                voltage_pu,
                meter.config.get('meter_type', MeterType.GRID_CONSUMER)
            )
            
            # Add power measurements
            p_mw = reading.energy_consumed * 4.0 / 1000.0
            if p_mw > 0:
                builder.add_active_power_measurement(
                    meter.meter_id, idx, p_mw,
                    meter.config.get('meter_type', MeterType.GRID_CONSUMER),
                    is_generation=False
                )
                builder.add_reactive_power_measurement(
                    meter.meter_id, idx, p_mw * 0.3,
                    meter.config.get('meter_type', MeterType.GRID_CONSUMER),
                    is_generation=False
                )
            
            # Add generation measurements
            if reading.energy_generated > 0:
                p_gen_mw = reading.energy_generated * 4.0 / 1000.0
                builder.add_active_power_measurement(
                    meter.meter_id + "_GEN", idx, p_gen_mw,
                    meter.config.get('meter_type', MeterType.SOLAR_PROSUMER),
                    is_generation=True
                )
            
            print(f"  - {meter.meter_id} → measurements generated")
    print()
    
    # Step 5: Get measurement table
    print("Step 5: Generating measurement table...")
    if PANDAPOWER_AVAILABLE and adapter is not None:
        measurement_df = adapter.get_measurement_table()
    else:
        measurement_df = builder.to_dataframe()
    print(f"✓ Generated {len(measurement_df)} measurements\n")
    
    # Step 6: Validate schema
    print("Step 6: Validating DataFrame schema...")
    required_columns = ['name', 'meas_type', 'element_type', 'element', 'value', 'std_dev', 'side']
    missing_columns = set(required_columns) - set(measurement_df.columns)
    
    if missing_columns:
        print(f"❌ Missing columns: {missing_columns}")
        return False
    
    print("✓ All required columns present")
    print(f"  Columns: {list(measurement_df.columns)}\n")
    
    # Step 7: Validate measurement types
    print("Step 7: Validating measurement types...")
    meas_types = measurement_df['meas_type'].value_counts()
    print("  Measurement distribution:")
    for meas_type, count in meas_types.items():
        print(f"    - {meas_type}: {count}")
    
    expected_types = {'v', 'p', 'q'}
    actual_types = set(measurement_df['meas_type'].unique())
    if not expected_types.issubset(actual_types):
        print(f"❌ Missing measurement types: {expected_types - actual_types}")
        return False
    
    print("✓ All measurement types present (v, p, q)\n")
    
    # Step 8: Validate std_dev calculation
    print("Step 8: Validating std_dev calculations...")
    invalid_std_dev = measurement_df[measurement_df['std_dev'] <= 0]
    if len(invalid_std_dev) > 0:
        print(f"❌ Found {len(invalid_std_dev)} measurements with invalid std_dev")
        return False
    
    # Check std_dev is reasonable (should be 0.2% - 6% of value for most measurements)
    measurement_df['std_dev_percent'] = (measurement_df['std_dev'] / measurement_df['value'].abs()) * 100
    high_uncertainty = measurement_df[measurement_df['std_dev_percent'] > 10]
    
    print(f"  std_dev statistics:")
    print(f"    - Mean: {measurement_df['std_dev_percent'].mean():.2f}%")
    print(f"    - Min: {measurement_df['std_dev_percent'].min():.2f}%")
    print(f"    - Max: {measurement_df['std_dev_percent'].max():.2f}%")
    
    if len(high_uncertainty) > 0:
        print(f"  ⚠ Warning: {len(high_uncertainty)} measurements with >10% uncertainty")
    else:
        print("✓ All std_dev values are reasonable\n")
    
    # Step 9: Display sample measurements
    print("Step 9: Sample measurements (first 5):")
    print(measurement_df.head().to_string(index=False))
    print()
    
    # Step 10: Validate sign conventions
    print("Step 10: Validating sign conventions...")
    load_measurements = measurement_df[measurement_df['element_type'] == 'load']
    sgen_measurements = measurement_df[measurement_df['element_type'] == 'sgen']
    
    print(f"  - Load measurements: {len(load_measurements)}")
    print(f"  - Generation measurements (sgen): {len(sgen_measurements)}")
    
    # Load consumption should be positive
    negative_loads = load_measurements[load_measurements['value'] < 0]
    if len(negative_loads) > 0:
        print(f"  ❌ Found {len(negative_loads)} negative load values (should be positive)")
        return False
    
    # Generation should be positive (at sgen element)
    negative_sgen = sgen_measurements[sgen_measurements['value'] < 0]
    if len(negative_sgen) > 0:
        print(f"  ❌ Found {len(negative_sgen)} negative sgen values (should be positive)")
        return False
    
    print("✓ Sign conventions are correct\n")
    
    # Success summary
    print("=" * 60)
    if PANDAPOWER_AVAILABLE:
        print("✅ PoC VALIDATION SUCCESSFUL (Full Mode)")
    else:
        print("✅ PoC VALIDATION SUCCESSFUL (Simulation Mode)")
    print("=" * 60)
    print("\nSummary:")
    print(f"  - Meters processed: {len(meters_and_readings)}")
    print(f"  - Measurements generated: {len(measurement_df)}")
    print(f"  - Voltage measurements: {len(measurement_df[measurement_df['meas_type'] == 'v'])}")
    print(f"  - Active power (P): {len(measurement_df[measurement_df['meas_type'] == 'p'])}")
    print(f"  - Reactive power (Q): {len(measurement_df[measurement_df['meas_type'] == 'q'])}")
    if net is not None:
        print(f"  - Network buses: {len(net.bus)}")
        print(f"  - Network loads: {len(net.load)}")
        print(f"  - Network sgen: {len(net.sgen)}")
    print()
    if not PANDAPOWER_AVAILABLE:
        print("Note: This was run in simulation mode without pandapower.")
        print("      Install pandapower to test full network integration:")
        print("      pip install pandapower>=2.14.0")
        print()
    print("Next steps (per implementation plan):")
    print("  1. Document findings in .github/PHASE2_ISSUES.md")
    print("  2. Proceed with full Phase 2 implementation")
    print("  3. Add grid topology creation (Week 3-4)")
    print("  4. Integrate state estimation (Week 5-6)")
    print()
    
    return True


if __name__ == "__main__":
    success = run_poc()
    sys.exit(0 if success else 1)
