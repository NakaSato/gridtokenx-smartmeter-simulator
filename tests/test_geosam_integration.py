import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.config import MeterType

@pytest.mark.asyncio
async def test_geosam_spatial_matching():
    """Verify that solar features are correctly matched to the nearest grid bus."""
    # Mock meters and transport
    mock_meters = []
    mock_transport = AsyncMock()
    mock_adapter = MagicMock()
    
    # Create a net with geo-referenced buses
    import pandapower as pp
    net = pp.create_empty_network()
    pp.create_bus(net, vn_kv=0.4, name="Bus 0", geodata=(100.0, 13.0))
    pp.create_bus(net, vn_kv=0.4, name="Bus 1", geodata=(100.1, 13.1))
    
    # Add bus_geocoord (as engine expects it)
    net.bus_geocoord = pd.DataFrame({
        'x': [100.0, 100.1],
        'y': [13.0, 13.1]
    }, index=[0, 1])
    
    mock_adapter.build_network_from_meters.return_value = (net, {})
    
    # Mock DB manager with solar inventory
    mock_db = AsyncMock()
    mock_db.get_all_solar_inventory.return_value = [
        {
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [100.0001, 13.0001]}, # Near Bus 0
            "kwp_potential": 10.0
        },
        {
            "id": 2,
            "geometry": {"type": "Point", "coordinates": [100.1005, 13.1005]}, # Near Bus 1
            "kwp_potential": 5.0
        }
    ]
    
    engine = SimulationEngine(meters=mock_meters, transport=mock_transport, adapter=mock_adapter, db_manager=mock_db)
    
    # Manually trigger the initialization logic instead of full start()
    engine.net = net
    engine.solar_inventory = await mock_db.get_all_solar_inventory()
    engine._map_solar_to_grid()
    
    # Check mapping results
    assert engine.bus_solar_capacity[0] == 10.0
    assert engine.bus_solar_capacity[1] == 5.0
    assert len(engine.bus_solar_capacity) == 2

@pytest.mark.asyncio
async def test_geosam_pseudo_measurement_injection():
    """Verify that pseudo-measurements include the estimated solar generation."""
    mock_meters = []
    mock_transport = AsyncMock()
    mock_adapter = MagicMock()
    
    import pandapower as pp
    net = pp.create_empty_network()
    # Bus 0 has a load but no meter -> will trigger pseudo-measurement
    pp.create_bus(net, vn_kv=0.4, name="Bus 0")
    pp.create_load(net, bus=0, p_mw=0.05, q_mvar=0.01) # 50 kW load
    
    mock_adapter.build_network_from_meters.return_value = (net, {})
    
    engine = SimulationEngine(meters=mock_meters, transport=mock_transport, adapter=mock_adapter)
    engine.net = net
    engine.adapter = mock_adapter # Ensure adapter.builder is used
    
    # Manually set bus capacity and simulation time (Midday for max solar)
    engine.bus_solar_capacity = {0: 10.0} # 10 kWp
    engine.current_sim_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    # Mock measurement builder
    engine.adapter.builder = MagicMock()
    
    # Inject pseudo-measurements
    engine._inject_pseudo_measurements()
    
    # Expected: 50 kW load - (10 kW * ~1.0 factor * 0.8 weather) = ~42 kW
    # In MW: 0.05 - 0.008 = 0.042 MW
    
    # Find the call with "Pseudo_Bus0_P"
    p_call = None
    for call in engine.adapter.builder.add_active_power_measurement.call_args_list:
        if call[0][0] == "Pseudo_Bus0_P":
            p_call = call
            break
            
    assert p_call is not None
    injected_p = p_call[0][2]
    assert 0.040 < injected_p < 0.045
    print(f"Injected Pseudo P: {injected_p} MW")
