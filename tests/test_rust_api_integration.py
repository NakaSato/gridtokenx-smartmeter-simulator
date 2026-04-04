"""
Test Suite: Rust-Accelerated API Integration

Verifies all Rust-accelerated endpoints work correctly through the API.
"""

import time
import requests
from typing import Dict, Any

BASE_URL = "http://localhost:8082"

def test_health():
    """Test basic health endpoint."""
    resp = requests.get(f"{BASE_URL}/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    print("✅ Health endpoint working")

def test_rust_acceleration_status():
    """Test Rust acceleration status endpoint."""
    resp = requests.get(f"{BASE_URL}/api/v1/simulation/acceleration", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    
    print("\n🦀 Rust Acceleration Status:")
    print(f"   - Enabled: {data.get('rust_enabled', False)}")
    print(f"   - Engine: {data.get('engine_type', 'Unknown')}")
    print(f"   - Active: {data.get('active', False)}")
    print(f"   - Expected Speedup: {data.get('expected_speedup', 'Unknown')}")
    
    if 'details' in data:
        print(f"\n   Details:")
        print(f"   - Implementation: {data['details'].get('implementation', 'Unknown')}")
        benchmarks = data['details'].get('benchmark_results', {})
        print(f"   - Benchmarks:")
        for scale, speedup in benchmarks.items():
            print(f"     • {scale}: {speedup}")
    
    assert data.get('rust_enabled') == True, "Rust should be enabled"
    assert data.get('active') == True, "Rust engine should be active"
    print("✅ Rust acceleration endpoint working")

def test_simulation_status_with_rust():
    """Test simulation status includes Rust acceleration info."""
    resp = requests.get(f"{BASE_URL}/api/v1/simulation/status", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    
    print("\n📊 Simulation Status:")
    print(f"   - Running: {data.get('running', False)}")
    print(f"   - Weather: {data.get('weather', 'Unknown')}")
    print(f"   - Grid Stress: {data.get('grid_stress_multiplier', 1.0)}")
    print(f"   - Meters: {len(data.get('meters', []))}")
    print(f"   - WebSocket: {data.get('websocket_connections', 0)}")
    
    rust_info = data.get('rust_acceleration', {})
    print(f"\n   Rust Info:")
    print(f"   - Enabled: {rust_info.get('enabled', False)}")
    print(f"   - Engine: {rust_info.get('engine_type', 'Unknown')}")
    print(f"   - Speedup: {rust_info.get('expected_speedup', 'Unknown')}")
    
    assert data.get('running') == True, "Simulation should be running"
    assert 'rust_acceleration' in data, "Should include Rust acceleration info"
    print("✅ Simulation status endpoint working with Rust info")

def test_rust_engine_direct():
    """Test Rust engine directly through Python import."""
    print("\n🔧 Testing Rust Engine Directly:")
    
    try:
        from gridtokenx_sim import VPPDispatchEngine, DERResource
        
        engine = VPPDispatchEngine(seed=42)
        print("   ✅ VPPDispatchEngine imported and instantiated")
        
        # Test AFRR
        afrr = engine.calculate_afrr(49.95, 50.0, 50.0)
        print(f"   ✅ AFRR calculation: {afrr:.4f} kW")
        
        # Create test resources
        resources = [
            DERResource(
                meter_id=f'TEST_{i:03d}',
                capacity_kwh=20.0,
                current_soc_kwh=10.0 + i,
                max_charge_kw=5.0,
                max_discharge_kw=5.0,
                reputation_score=0.95,
            )
            for i in range(50)
        ]
        print(f"   ✅ Created {len(resources)} test resources")
        
        # Test dispatch
        nodal_prices = {r.meter_id: 0.25 for r in resources}
        start = time.perf_counter()
        result = engine.dispatch(
            resources=resources,
            target_kw=25.0,
            nodal_prices=nodal_prices,
            carbon_intensity=350.0,
            interval_hours=0.25,
        )
        elapsed = (time.perf_counter() - start) * 1e6
        
        print(f"   ✅ Dispatch completed in {elapsed:.2f} µs")
        print(f"   - Dispatches: {len(result.dispatches)}")
        print(f"   - Carbon saved: {result.carbon_saved_g:.2f} g CO2")
        print(f"   - Cluster health: {result.cluster_health:.1f}%")
        
        assert len(result.dispatches) == 50, "Should dispatch all 50 resources"
        print("✅ Direct Rust engine test passed")
        
    except ImportError as e:
        print(f"   ❌ Rust engine not available: {e}")
        raise

def test_reading_generation_performance():
    """Test Rust-accelerated reading generation performance."""
    print("\n⚡ Testing Reading Generation Performance:")
    
    try:
        from gridtokenx_sim import MeterConfig, generate_readings
        
        # Create test meters
        meters = [
            MeterConfig(
                meter_id=f'PERF_{i:03d}',
                meter_type='Solar_Prosumer' if i % 2 == 0 else 'Residential',
                has_solar=(i % 2 == 0),
                has_battery=(i % 3 == 0),
                solar_capacity=5.0,
                battery_capacity=10.0,
                base_consumption=1.5,
                panel_efficiency=0.18,
                current_battery_level=5.0,
                price_elasticity=0.15,
                accuracy_class=2.0,
            )
            for i in range(100)
        ]
        
        # Warmup
        generate_readings(meters[:10], 12.0, True, 1.0, False, 900.0)
        
        # Benchmark
        iterations = 10
        start = time.perf_counter()
        for _ in range(iterations):
            generate_readings(meters, 12.0, True, 1.0, False, 900.0)
        elapsed = time.perf_counter() - start
        
        avg_time_ms = (elapsed / iterations) * 1000
        print(f"   ✅ 100 meters: {avg_time_ms:.2f} ms/iteration")
        print(f"   ✅ Expected: <1 ms (Rust) vs ~300 ms (Python)")
        
        assert avg_time_ms < 50.0, f"Should be fast (Rust), got {avg_time_ms:.2f} ms"
        print("✅ Reading generation performance test passed")
        
    except ImportError as e:
        print(f"   ❌ Rust engine not available: {e}")
        raise

def main():
    """Run all tests."""
    print("=" * 80)
    print("🧪 Rust API Integration Test Suite")
    print("=" * 80)
    
    tests = [
        ("Health", test_health),
        ("Rust Acceleration Status", test_rust_acceleration_status),
        ("Simulation Status with Rust", test_simulation_status_with_rust),
        ("Rust Engine Direct", test_rust_engine_direct),
        ("Reading Generation Performance", test_reading_generation_performance),
    ]
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print('='*60)
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            failed += 1
            failed_tests.append(name)
    
    print(f"\n{'='*80}")
    print(f"📊 Test Results: {passed} passed, {failed} failed out of {len(tests)}")
    print('='*80)
    
    if failed == 0:
        print("\n✅ All Rust API integration tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed: {', '.join(failed_tests)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
