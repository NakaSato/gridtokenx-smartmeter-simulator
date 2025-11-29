#!/usr/bin/env python3
"""
Test script to get individual meter status
"""

import asyncio
import aiohttp
import json
import sys

API_URL = "http://localhost:8000"


async def get_meter_status(meter_id: str = None):
    """Get status for a specific meter or list all meters"""

    print("=" * 70)
    print("Individual Meter Status")
    print("=" * 70)
    print()

    try:
        async with aiohttp.ClientSession() as session:
            # If no meter_id provided, list all meters first
            if not meter_id:
                async with session.get(f"{API_URL}/api/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        meters = data.get("meters", [])

                        if not meters:
                            print("No meters found in simulator")
                            return

                        print("Available Meters:")
                        print("-" * 70)
                        for i, meter in enumerate(meters, 1):
                            status = "✅" if meter.get("is_connected") else "❌"
                            print(
                                f"{i}. {status} {meter['meter_id'][:36]} - {meter.get('location', 'Unknown')}"
                            )
                        print("-" * 70)
                        print()

                        # Use first meter as example
                        meter_id = meters[0]["meter_id"]
                        print(f"Showing details for first meter: {meter_id[:36]}...")
                        print()

            # Get detailed status for specific meter
            async with session.get(
                f"{API_URL}/api/meters/{meter_id}/status"
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # Display meter information
                    print(f"Meter ID: {data['meter_id']}")
                    print(f"Type: {data['meter_type']}")
                    print(f"Location: {data['location']}")
                    print(f"User Type: {data['user_type']}")
                    print()

                    # Connection status
                    print(f"Connection Status: {data['connection_status']}")
                    print()

                    # Configuration
                    config = data["config"]
                    print("Configuration:")
                    print(f"  Solar Panel: {'Yes' if config['has_solar'] else 'No'}")
                    if config["has_solar"]:
                        print(f"  Solar Capacity: {config['solar_capacity']} kW")
                    print(f"  Battery: {'Yes' if config['has_battery'] else 'No'}")
                    if config["has_battery"]:
                        print(f"  Battery Capacity: {config['battery_capacity']} kWh")
                    print(f"  Trading Preference: {config['trading_preference']}")
                    print()

                    # Current state
                    state = data["current_state"]
                    print("Current State:")
                    print(f"  Battery Level: {state['battery_level']}%")
                    print(f"  Weather: {state['current_weather']}")
                    print(f"  Sell Price: ${state['current_sell_price']}/kWh")
                    print(f"  Buy Price: ${state['current_buy_price']}/kWh")
                    print()

                    # Latest reading
                    if data["latest_reading"]:
                        reading = data["latest_reading"]
                        print("Latest Reading:")
                        print(f"  Timestamp: {reading['timestamp']}")
                        print(f"  Generated: {reading['energy_generated']} kWh")
                        print(f"  Consumed: {reading['energy_consumed']} kWh")
                        print(f"  Surplus: {reading['surplus_energy']} kWh")
                        print(f"  Deficit: {reading['deficit_energy']} kWh")
                        print(f"  Battery: {reading['battery_level']}%")
                        print(f"  Voltage: {reading['voltage']} V")
                        print(f"  Current: {reading['current']} A")
                        print(f"  Temperature: {reading['temperature']} °C")
                        print(f"  Net Emission: {reading['net_emission']} kgCO2")
                        print(
                            f"  REC Eligible: {'Yes' if reading['rec_eligible'] else 'No'}"
                        )
                    else:
                        print("Latest Reading: No data available yet")
                    print()

                    # GPS coordinates
                    coords = data["coordinates"]
                    if coords["latitude"] and coords["longitude"]:
                        print(f"GPS: {coords['latitude']}, {coords['longitude']}")

                elif response.status == 404:
                    error_data = await response.json()
                    print(f"❌ Error: {error_data.get('error', 'Meter not found')}")
                    print(f"Meter ID: {meter_id}")
                else:
                    print(f"❌ Failed to get meter status: HTTP {response.status}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Make sure the simulator is running at {API_URL}")

    print()
    print("=" * 70)


async def main():
    """Main entry point"""
    meter_id = None
    if len(sys.argv) > 1:
        meter_id = sys.argv[1]

    await get_meter_status(meter_id)


if __name__ == "__main__":
    print()
    print("Usage: python get_meter_status.py [meter_id]")
    print("If no meter_id is provided, will show first meter's status")
    print()
    asyncio.run(main())
