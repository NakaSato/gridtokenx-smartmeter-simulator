#!/usr/bin/env python3
"""Test all Rust core modules"""

import smartmeter_core as core

print('=== Testing Rust Core Modules ===')

# 1. Test WeatherSystem
print('\n1. WeatherSystem')
weather = core.WeatherSystem()
print(f'   Initial state: {weather.current_state}')
irr, temp, state = weather.step()
print(f'   After step: irradiance={irr:.1f}, temp={temp:.1f}, state={state}')

# 2. Test PowerQuality
print('\n2. PowerQuality')
pq = core.PowerQuality()
thd_v, thd_i = pq.estimate_thd(has_ev_charger=True, has_solar_inverter=True, ev_power_kw=7.0, solar_power_kw=5.0)
print(f'   THD estimate: V={thd_v:.2f}%, I={thd_i:.2f}%')
assessment = pq.get_assessment(thd_v, thd_i)
print(f'   Assessment: {assessment}')

# 3. Test Trading/Matching
print('\n3. MatchingEngine')
engine = core.MatchingEngine()
bid = core.TradeBid('buyer1', 1, 100.0, 3.5, 'wallet1')  # id, zone, amount, price, wallet
ask = core.TradeAsk('seller1', 1, 80.0, 3.0, 'wallet2')   # id, zone, amount, price, wallet
matches, welfare = engine.match_greedy([bid], [ask])
print(f'   Matches: {len(matches)}, Welfare: {welfare:.2f}')
if matches:
    m = matches[0]
    print(f'   Match: buyer={m.buyer_id}, seller={m.seller_id}, qty={m.amount_kwh}, price={m.price_per_kwh}')

# 4. Test ZoningService
print('\n4. ZoningService')
zoning = core.ZoningService(3)
coords = [
    (13.75, 100.52),
    (13.76, 100.53),
    (13.80, 100.60),
    (13.81, 100.61),
]
zones = zoning.fit(coords)
print(f'   Fitted {len(coords)} meters to zones: {zones}')
zone_info = zoning.get_zone_info(zones[0])
if zone_info:
    print(f'   Zone {zones[0]} info: centroid=({zone_info.centroid_lat:.4f}, {zone_info.centroid_lon:.4f})')

# 5. Test MeterSim
print('\n5. MeterSim')
meter = core.MeterSim(
    meter_id='test-meter-001',
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
print(f'   Meter: {meter.meter_id}, type={meter.meter_type}')

# Update weather before generating reading
meter.update_weather('Sunny', 0.9, 2.0)  # weather, irradiance_factor, temp_offset

reading = meter.generate_reading('2024-01-15T12:00:00Z')
print(f'   Reading: gen={reading.energy_generated:.3f}, cons={reading.energy_consumed:.3f}')
print(f'   Power: gen={reading.power_generated:.1f}W, cons={reading.power_consumed:.1f}W')
print(f'   Grid: V={reading.voltage:.1f}, f={reading.frequency:.2f}Hz')
print(f'   Battery: {reading.battery_level_pct:.1f}%')

print('\n=== All tests passed! ===')
