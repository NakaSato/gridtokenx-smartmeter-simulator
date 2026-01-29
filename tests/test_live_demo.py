#!/usr/bin/env python3
"""
Live demonstration of multiple smart meters generating readings
Shows Step 1 in action with 3 different meter types
"""
import asyncio
from datetime import datetime, timezone
from app.core.meter import SmartMeter

async def live_demo():
    """Run a live demonstration with multiple meters"""
    
    print("\n" + "="*80)
    print("🔋 LIVE SMART METER SIMULATOR - STEP 1 DEMONSTRATION")
    print("="*80 + "\n")
    
    # Create 3 different meter types manually
    meter_configs = [
        {
            'meter_id': 'SOLAR-PRO-001',
            'location': 'Zone_1_Building_A',
            'meter_type': 'Solar_Prosumer',
            'user_type': 'Prosumer',
            'has_solar': True,
            'solar_capacity': 6.0,
            'panel_efficiency': 0.18,
            'base_consumption': 2.5,
            'has_battery': True,
            'battery_capacity': 12.0,
            'current_battery_level': 6.0
        },
        {
            'meter_id': 'GRID-CON-002',
            'location': 'Zone_2_Building_B',
            'meter_type': 'Grid_Consumer',
            'user_type': 'Consumer',
            'has_solar': False,
            'base_consumption': 3.0,
            'has_battery': False,
        },
        {
            'meter_id': 'HYBRID-003',
            'location': 'Zone_3_Building_C',
            'meter_type': 'Hybrid_Prosumer',
            'user_type': 'Prosumer',
            'has_solar': True,
            'solar_capacity': 4.5,
            'panel_efficiency': 0.20,
            'base_consumption': 2.0,
            'has_battery': True,
            'battery_capacity': 15.0,
            'current_battery_level': 10.0
        }
    ]
    
    print("📊 Creating Smart Meters...\n")
    meters = [SmartMeter(config) for config in meter_configs]
    
    for i, (meter, config) in enumerate(zip(meters, meter_configs), 1):
        print(f"   {i}. {meter.meter_id}")
        print(f"      Type: {config['meter_type']}")
        print(f"      Location: {config['location']}")
        print(f"      Solar: {'Yes (' + str(config.get('solar_capacity', 0)) + ' kW)' if config.get('has_solar') else 'No'}")
        print(f"      Battery: {'Yes (' + str(config.get('battery_capacity', 0)) + ' kWh)' if config.get('has_battery') else 'No'}")
        print()
    
    print("⚡ Generating readings every 3 seconds...\n")
    print("="*80 + "\n")
    
    # Generate 5 rounds of readings
    for round_num in range(1, 6):
        timestamp = datetime.now(timezone.utc)
        
        print(f"📍 Round {round_num} - {timestamp.strftime('%H:%M:%S UTC')}")
        print("-" * 80)
        
        for meter in meters:
            # Update weather
            meter.update_weather("Sunny")
            
            # Generate reading
            reading = meter.generate_reading(timestamp)
            
            # Display compact reading
            status = "🟢 SURPLUS" if reading.surplus_energy > 0 else "🔴 DEFICIT"
            net = reading.energy_generated - reading.energy_consumed
            
            print(f"{meter.meter_id:20} | "
                  f"Gen: {reading.energy_generated:6.2f} kWh | "
                  f"Con: {reading.energy_consumed:6.2f} kWh | "
                  f"Net: {net:+7.2f} kWh | "
                  f"Bat: {reading.battery_level:5.1f}% | "
                  f"{status}")
        
        print()
        
        # Wait 3 seconds before next round
        if round_num < 5:
            print("   ⏳ Waiting 3 seconds...\n")
            await asyncio.sleep(3)
    
    print("="*80)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*80)
    print()
    print("Summary:")
    print("  • 3 meters (Solar Prosumer, Grid Consumer, Hybrid) generated 5 readings each")
    print("  • Total: 15 signed energy readings")
    print("  • Each reading includes:")
    print("    - Production & consumption measurements")
    print("    - Net surplus/deficit calculation")
    print("    - Battery state tracking")
    print("    - Ed25519 cryptographic signature")
    print("  • Data is ready for Step 3: API Gateway Submission")
    print()

if __name__ == "__main__":
    asyncio.run(live_demo())
