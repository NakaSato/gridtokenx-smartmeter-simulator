"""
Benchmark: Rust vs Python VPP Dispatch Performance

Measures dispatch performance across different cluster sizes.
Expected: 3-10x speedup for Rust implementation.
"""

import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smart_meter_simulator.core.rust_vpp_engine import RustAcceleratedVPP, USE_RUST_VPP


def create_resources(n: int) -> list:
    """Create n DER resources for testing."""
    return [
        {
            'meter_id': f'BATTERY_{i:04d}',
            'capacity_kwh': 20.0,
            'current_soc_kwh': 10.0 + (i % 10),
            'max_charge_kw': 5.0,
            'max_discharge_kw': 5.0,
            'is_controllable': True,
            'enabled': True,
            'reputation_score': 0.9 + (i % 10) * 0.01,
        }
        for i in range(n)
    ]


def benchmark_dispatch(engine: RustAcceleratedVPP, resources: list, n_iterations: int = 100) -> dict:
    """Benchmark dispatch performance."""
    nodal_prices = {r['meter_id']: 0.25 + (i % 10) * 0.01 for i, r in enumerate(resources)}
    
    # Warmup
    engine.dispatch(resources[:10], 5.0, nodal_prices, carbon_intensity=350.0)
    
    # Benchmark
    start = time.perf_counter()
    for _ in range(n_iterations):
        engine.dispatch(resources, 25.0, nodal_prices, carbon_intensity=350.0)
    elapsed = time.perf_counter() - start
    
    avg_time_us = (elapsed / n_iterations) * 1e6
    return {
        'total_time_ms': elapsed * 1000,
        'avg_time_us': avg_time_us,
        'iterations': n_iterations,
    }


def main():
    print("=" * 80)
    print("🦀 VPP Dispatch Performance Benchmark")
    print("=" * 80)
    print(f"Rust Engine: {'✅ Available' if USE_RUST_VPP else '❌ Unavailable (Python fallback)'}")
    print()
    
    engine = RustAcceleratedVPP(seed=42)
    
    scales = [10, 50, 100, 250, 500]
    results = []
    
    for n_resources in scales:
        print(f"\n📊 Testing {n_resources} resources...")
        resources = create_resources(n_resources)
        
        result = benchmark_dispatch(engine, resources, n_iterations=50)
        
        speedup = "N/A (Python)"
        if USE_RUST_VPP:
            # Benchmark Python for comparison
            engine_python = RustAcceleratedVPP(seed=42)
            # Force Python by temporarily disabling Rust
            import smart_meter_simulator.core.rust_vpp_engine as vpp_module
            original_rust = vpp_module.USE_RUST_VPP
            vpp_module.USE_RUST_VPP = False
            engine_python.rust_engine = None
            
            result_python = benchmark_dispatch(engine_python, resources, n_iterations=50)
            vpp_module.USE_RUST_VPP = original_rust
            
            speedup = f"{result_python['avg_time_us'] / result['avg_time_us']:.1f}x"
        
        results.append({
            'scale': n_resources,
            'rust_avg_us': result['avg_time_us'],
            'speedup': speedup,
        })
        
        print(f"   ⚡ Average: {result['avg_time_us']:.2f} µs/dispatch")
        print(f"   📈 Speedup: {speedup}")
    
    print("\n" + "=" * 80)
    print("📈 Summary")
    print("=" * 80)
    print(f"{'Scale':<10} {'Rust (µs)':<15} {'Speedup':<15}")
    print("-" * 40)
    for r in results:
        print(f"{r['scale']:<10} {r['rust_avg_us']:<15.2f} {r['speedup']:<15}")
    
    print("\n✅ Benchmark complete!")


if __name__ == "__main__":
    main()
