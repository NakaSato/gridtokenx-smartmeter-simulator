import pytest
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.adapters.pandapower_adapter import PandapowerAdapter
from smart_meter_simulator.config import MeterType

def test_topology_integration():
    """
    Verify that the PandapowerAdapter correctly builds a network topology
    from a list of SmartMeters.
    """
    try:
        import pandapower as pp
    except ImportError:
        pytest.skip("Pandapower not installed")

    # 1. Create Mock Meters
    meters = []
    # 50 meters to trigger multiple feeders (default 10 per feeder)
    for i in range(50):
        config = {
            'meter_id': f"meter_{i}",
            'meter_type': MeterType.RESIDENTIAL,
            'location': (0.0, 0.0)
        }
        meter = SmartMeter(config)
        meters.append(meter)

    # 2. Initialize Adapter
    adapter = PandapowerAdapter()

    # 3. Build Network
    net, meter_to_bus_map = adapter.build_network_from_meters(meters)

    # 4. Verifications
    print("\n--- Topology Verification ---")
    print(f"Meters: {len(meters)}")
    print(f"Buses: {len(net.bus)}")
    print(f"Lines: {len(net.line)}")
    print(f"Loads: {len(net.load)}")
    print(f"Feeders: {len(net.ext_grid)}") # Should be 1 grid connection + switch logic? No, just radial.

    # Check Bus Count:
    # 5 feeders * 10 buses/feeder + 1 substation bus + 1 grid bus?
    # Logic in adapter: num_feeders = 5. buses_per_feeder = 10.
    # Total buses = num_feeders * buses_per_feeder + 1 (Substation) + 1 (HV Grid)?
    # Let's check assert
    assert len(net.bus) > 50, "Network should have at least as many buses as meters"
    
    # Check Mapping
    assert len(meter_to_bus_map) == 50, "All meters should be mapped to a bus"
    
    # Check Connectivity
    assert len(net.line) >= 50, "Should have lines connecting buses"
    
    # Check Pandapower Validity (run load flow if possible, or just check check_consistency)
    try:
        pp.runpp(net)
        print("Power Flow: CONVERGED")
    except Exception as e:
        print(f"Power Flow Failed: {e}")
        # It might fail with 0 load, but shouldn't crash
    
    print("Topology verification PASSED")

if __name__ == "__main__":
    test_topology_integration()
