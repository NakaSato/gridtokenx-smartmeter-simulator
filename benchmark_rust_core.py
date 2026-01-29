#!/usr/bin/env python3
"""Benchmark Rust core vs Python implementation"""

import time
import smartmeter_core as core

def benchmark_meter_simulation(n_iterations=10000):
    """Benchmark meter reading generation"""
    meter = core.MeterSim(
        meter_id='bench-meter-001',
        meter_type='Prosumer',
        user_type='Residential',
        latitude=13.7563,
        longitude=100.5018,
        has_solar=True,
        solar_capacity_kw=5.0,
        has_battery=True,
        battery_capacity_kwh=10.0,
        base_consumption_kw=1.5,
        initial_battery_pct=50.0
    )
    
    meter.update_weather('Sunny', 0.9, 2.0)
    
    start = time.perf_counter()
    for i in range(n_iterations):
        reading = meter.generate_reading(f'2024-01-15T{12 + (i % 12):02d}:{(i*15) % 60:02d}:00Z')
    elapsed = time.perf_counter() - start
    
    return elapsed, n_iterations / elapsed

def benchmark_weather_system(n_iterations=50000):
    """Benchmark weather simulation"""
    weather = core.WeatherSystem()
    
    start = time.perf_counter()
    for _ in range(n_iterations):
        weather.step()
    elapsed = time.perf_counter() - start
    
    return elapsed, n_iterations / elapsed

def benchmark_matching_engine(n_iterations=5000):
    """Benchmark P2P matching"""
    engine = core.MatchingEngine()
    
    # Create 100 bids and asks per iteration
    bids = [core.TradeBid(f'buyer{i}', i % 5, 100.0, 3.5 - (i % 10) * 0.1, f'wallet{i}') for i in range(100)]
    asks = [core.TradeAsk(f'seller{i}', i % 5, 80.0, 3.0 + (i % 8) * 0.1, f'wallet{i}') for i in range(100)]
    
    start = time.perf_counter()
    for _ in range(n_iterations):
        matches, welfare = engine.match_greedy(bids, asks)
    elapsed = time.perf_counter() - start
    
    return elapsed, n_iterations / elapsed

def benchmark_zoning(n_iterations=1000):
    """Benchmark K-means zoning"""
    # 500 meter coordinates
    coords = [(13.7 + i * 0.01, 100.5 + i * 0.01) for i in range(500)]
    
    start = time.perf_counter()
    for _ in range(n_iterations):
        zoning = core.ZoningService(5)
        zones = zoning.fit(coords)
    elapsed = time.perf_counter() - start
    
    return elapsed, n_iterations / elapsed

def benchmark_power_quality(n_iterations=50000):
    """Benchmark THD calculation"""
    pq = core.PowerQuality()
    
    start = time.perf_counter()
    for i in range(n_iterations):
        thd_v, thd_i = pq.estimate_thd(
            has_ev_charger=(i % 2 == 0),
            has_solar_inverter=(i % 3 == 0),
            ev_power_kw=7.0,
            solar_power_kw=5.0
        )
    elapsed = time.perf_counter() - start
    
    return elapsed, n_iterations / elapsed

if __name__ == '__main__':
    print('=' * 60)
    print('Rust Core Performance Benchmark')
    print('=' * 60)
    
    print('\n1. MeterSim.generate_reading():')
    elapsed, ops = benchmark_meter_simulation()
    print(f'   {ops:,.0f} ops/sec ({elapsed:.3f}s for 10,000 iterations)')
    
    print('\n2. WeatherSystem.step():')
    elapsed, ops = benchmark_weather_system()
    print(f'   {ops:,.0f} ops/sec ({elapsed:.3f}s for 50,000 iterations)')
    
    print('\n3. MatchingEngine.match_greedy() (100 bids/asks):')
    elapsed, ops = benchmark_matching_engine()
    print(f'   {ops:,.0f} ops/sec ({elapsed:.3f}s for 5,000 iterations)')
    
    print('\n4. ZoningService.fit() (500 meters):')
    elapsed, ops = benchmark_zoning()
    print(f'   {ops:,.0f} ops/sec ({elapsed:.3f}s for 1,000 iterations)')
    
    print('\n5. PowerQuality.estimate_thd():')
    elapsed, ops = benchmark_power_quality()
    print(f'   {ops:,.0f} ops/sec ({elapsed:.3f}s for 50,000 iterations)')
    
    print('\n' + '=' * 60)
    print('Benchmark complete!')
    print('=' * 60)
