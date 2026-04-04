"""
Benchmark: Rust vs Python meter reading generation performance.

This script compares the performance of:
1. Rust-accelerated meter reading generation (via PyO3)
2. Pure Python meter reading generation

Run: uv run python tests/benchmark_rust_performance.py
"""

import time
import statistics
from datetime import datetime
from typing import List, Dict, Any


def generate_test_meters(count: int) -> List[Dict[str, Any]]:
    """Generate test meter configurations."""
    meters = []
    for i in range(count):
        meter_type = ["Residential", "Solar_Prosumer", "Commercial", "EV_Charger"][i % 4]
        meters.append({
            'meter_id': f'AMI_METER_{i:04d}',
            'meter_type': meter_type,
            'has_solar': meter_type in ['Solar_Prosumer', 'Hybrid_Prosumer'],
            'has_battery': meter_type in ['Battery_Storage', 'Hybrid_Prosumer'],
            'solar_capacity': 5.0 if meter_type == 'Solar_Prosumer' else 0.0,
            'battery_capacity': 10.0,
            'base_consumption': 1.0,
            'panel_efficiency': 0.18,
            'current_battery_level': 5.0,
            'price_elasticity': 0.15,
            'accuracy_class': 2.0,
        })
    return meters


def benchmark_rust(meters: List[Dict[str, Any]], iterations: int = 10) -> Dict[str, float]:
    """Benchmark Rust implementation."""
    try:
        from gridtokenx_sim import MeterConfig, generate_readings
    except ImportError:
        return {'error': 'Rust extension not available'}
    
    times = []
    timestamp = datetime(2024, 1, 15, 12, 30, 0)  # Noon, weekday
    hour = timestamp.hour + timestamp.minute / 60.0
    weekday = timestamp.weekday() < 5
    weather_factor = 0.8  # Partly cloudy
    
    # Convert meters to Rust configs once
    rust_configs = []
    for m in meters:
        rust_configs.append(MeterConfig(
            meter_id=m['meter_id'],
            meter_type=m['meter_type'],
            has_solar=m['has_solar'],
            has_battery=m['has_battery'],
            solar_capacity=m['solar_capacity'],
            battery_capacity=m['battery_capacity'],
            base_consumption=m['base_consumption'],
            panel_efficiency=m['panel_efficiency'],
            current_battery_level=m['current_battery_level'],
            price_elasticity=m['price_elasticity'],
            accuracy_class=m['accuracy_class'],
        ))
    
    # Warm-up
    generate_readings(rust_configs, hour, weekday, weather_factor, True, 900.0)
    
    # Benchmark
    for _ in range(iterations):
        start = time.perf_counter()
        readings = generate_readings(rust_configs, hour, weekday, weather_factor, True, 900.0)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times),
        'total_readings': len(readings) * iterations,
    }


def benchmark_python(meters: List[Dict[str, Any]], iterations: int = 10) -> Dict[str, float]:
    """Benchmark Python implementation."""
    try:
        from smart_meter_simulator.core.meter import SmartMeter
    except ImportError:
        return {'error': 'Python implementation not available'}
    
    times = []
    timestamp = datetime(2024, 1, 15, 12, 30, 0)
    total_readings = 0
    
    # Warm-up
    for m in meters[:10]:
        meter = SmartMeter(m)
        meter.update_weather("Partly Cloudy")
        meter.generate_reading(timestamp, interval_seconds=900)
    
    # Benchmark
    for _ in range(iterations):
        start = time.perf_counter()
        for m in meters:
            meter = SmartMeter(m)
            meter.update_weather("Partly Cloudy")
            reading = meter.generate_reading(timestamp, interval_seconds=900)
            total_readings += 1
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times),
        'total_readings': total_readings,
    }


def format_time(seconds: float) -> str:
    """Format seconds to human-readable string."""
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f} µs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.3f} s"


def run_benchmark():
    """Run comprehensive benchmark."""
    print("=" * 80)
    print("🚀 GridTokenX Simulator: Rust vs Python Performance Benchmark")
    print("=" * 80)
    
    # Test different scales
    scales = [10, 100, 500, 1000]
    iterations = 10
    
    for num_meters in scales:
        print(f"\n{'─' * 80}")
        print(f"📊 Testing with {num_meters} meters ({iterations} iterations each)")
        print(f"{'─' * 80}")
        
        meters = generate_test_meters(num_meters)
        
        # Benchmark Rust
        print("\n🦀 Benchmarking Rust extension...")
        rust_result = benchmark_rust(meters, iterations)
        if 'error' in rust_result:
            print(f"   ❌ {rust_result['error']}")
            continue
        
        print(f"   ✅ Mean:   {format_time(rust_result['mean'])}")
        print(f"   ✅ Median: {format_time(rust_result['median'])}")
        print(f"   ✅ Min:    {format_time(rust_result['min'])}")
        print(f"   ✅ Max:    {format_time(rust_result['max'])}")
        
        # Benchmark Python
        print("\n🐍 Benchmarking Python implementation...")
        python_result = benchmark_python(meters, iterations)
        if 'error' in python_result:
            print(f"   ❌ {python_result['error']}")
            continue
        
        print(f"   ✅ Mean:   {format_time(python_result['mean'])}")
        print(f"   ✅ Median: {format_time(python_result['median'])}")
        print(f"   ✅ Min:    {format_time(python_result['min'])}")
        print(f"   ✅ Max:    {format_time(python_result['max'])}")
        
        # Calculate speedup
        speedup = python_result['mean'] / rust_result['mean']
        print(f"\n⚡ Speedup: {speedup:.1f}x faster with Rust")
        print(f"   Time saved per tick: {format_time(python_result['mean'] - rust_result['mean'])}")
        
        # Per-meter performance
        rust_per_meter = rust_result['mean'] / num_meters * 1000
        python_per_meter = python_result['mean'] / num_meters * 1000
        print(f"   Rust per meter:    {rust_per_meter:.2f} ms")
        print(f"   Python per meter:  {python_per_meter:.2f} ms")
    
    print(f"\n{'=' * 80}")
    print("✅ Benchmark complete!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    run_benchmark()
