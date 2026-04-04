"""
Example: Using Rust-accelerated meter reading generation.

This shows how to integrate the Rust engine into your simulation.
"""

from datetime import datetime
from smart_meter_simulator.core.rust_engine import RustAcceleratedMeter, get_engine_status


def main():
    # 1. Check if Rust is enabled
    status = get_engine_status()
    print("=" * 60)
    print("🔍 Rust Engine Status")
    print("=" * 60)
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()
    
    # 2. Create meter configurations
    meters = [
        {
            'meter_id': 'AMI_METER_0001',
            'meter_type': 'Solar_Prosumer',
            'has_solar': True,
            'has_battery': False,
            'solar_capacity': 5.0,
            'battery_capacity': 0.0,
            'base_consumption': 1.0,
            'panel_efficiency': 0.18,
            'current_battery_level': 0.0,
            'price_elasticity': 0.15,
            'accuracy_class': 2.0,
        },
        {
            'meter_id': 'AMI_METER_0002',
            'meter_type': 'Residential',
            'has_solar': False,
            'has_battery': False,
            'solar_capacity': 0.0,
            'battery_capacity': 0.0,
            'base_consumption': 1.5,
            'panel_efficiency': 0.0,
            'current_battery_level': 0.0,
            'price_elasticity': 0.15,
            'accuracy_class': 2.0,
        },
        {
            'meter_id': 'AMI_METER_0003',
            'meter_type': 'Commercial',
            'has_solar': False,
            'has_battery': True,
            'solar_capacity': 0.0,
            'battery_capacity': 20.0,
            'base_consumption': 10.0,
            'panel_efficiency': 0.0,
            'current_battery_level': 10.0,
            'price_elasticity': 0.20,
            'accuracy_class': 1.0,
        },
    ]
    
    print(f"📊 Created {len(meters)} meter configurations")
    print()
    
    # 3. Generate readings (automatically uses Rust if available)
    timestamp = datetime(2024, 1, 15, 12, 30, 0)  # Noon, weekday
    weather_factor = 0.8  # Partly cloudy
    
    print(f"⏰ Timestamp: {timestamp}")
    print(f"🌤️  Weather factor: {weather_factor}")
    print()
    
    print("🔄 Generating readings...")
    readings = RustAcceleratedMeter.generate_readings_batch(
        meters=meters,
        timestamp=timestamp,
        weather_factor=weather_factor,
        interval_seconds=900,
    )
    
    # 4. Display results
    print()
    print("=" * 60)
    print("📈 Generated Readings")
    print("=" * 60)
    
    for reading in readings:
        print(f"\n⚡ Meter: {reading['meter_id']}")
        print(f"   Generated: {reading['energy_generated_kwh']:.4f} kWh")
        print(f"   Consumed:  {reading['energy_consumed_kwh']:.4f} kWh")
        print(f"   Surplus:   {reading['surplus_energy']:.4f} kWh")
        print(f"   Deficit:   {reading['deficit_energy']:.4f} kWh")
        print(f"   Battery:   {reading['battery_level']:.1f} kWh")
        print(f"   Voltage:   {reading['voltage']:.2f} V")
        print(f"   Current:   {reading['current']:.3f} A")
        print(f"   Frequency: {reading['frequency']:.2f} Hz")
    
    print()
    print("=" * 60)
    print("✅ Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
