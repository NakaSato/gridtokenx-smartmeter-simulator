#!/usr/bin/env python3
"""
Test script to display meter connection status
"""

import asyncio
import aiohttp
import json
from datetime import datetime

API_URL = "http://localhost:8000"


async def check_meter_status():
    """Check and display meter connection status"""

    print("=" * 70)
    print("Smart Meter Connection Status Monitor")
    print("=" * 70)
    print()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/status") as response:
                if response.status == 200:
                    data = await response.json()

                    # Overall status
                    print(f"Simulator Status: {data['status'].upper()}")
                    print(f"API Gateway: {data.get('api_gateway', 'Unknown')}")
                    print(
                        f"API Gateway Connected: {'✅ YES' if data.get('api_gateway_connected') else '❌ NO'}"
                    )
                    print()

                    # Meter summary
                    total_meters = data.get("num_meters", 0)
                    connected = data.get("connected_meters", 0)
                    disconnected = data.get("disconnected_meters", 0)

                    print(f"Total Meters: {total_meters}")
                    print(f"Connected: {connected} ✅")
                    print(f"Disconnected: {disconnected} ❌")
                    print()

                    # Individual meter status
                    print("-" * 70)
                    print(f"{'Meter ID':<40} {'Location':<20} {'Status':<10}")
                    print("-" * 70)

                    meters = data.get("meters", [])
                    for meter in meters:
                        meter_id = meter["meter_id"][:36]  # Truncate for display
                        location = meter.get("location", "Unknown")[:18]
                        is_connected = meter.get("is_connected", False)
                        status = "✅ ONLINE" if is_connected else "❌ OFFLINE"

                        print(f"{meter_id:<40} {location:<20} {status:<10}")

                    print("-" * 70)
                    print()

                    # Connection details
                    if connected > 0:
                        print(
                            f"✅ {connected} meter(s) successfully connected to API gateway"
                        )
                    if disconnected > 0:
                        print(
                            f"⚠️  {disconnected} meter(s) not connected to API gateway"
                        )
                        print("   Check API gateway status and authentication")

                else:
                    print(f"❌ Failed to get status: HTTP {response.status}")

    except Exception as e:
        print(f"❌ Error connecting to simulator: {e}")
        print(f"   Make sure the simulator is running at {API_URL}")

    print()
    print("=" * 70)


async def main():
    """Main entry point"""
    await check_meter_status()


if __name__ == "__main__":
    asyncio.run(main())
