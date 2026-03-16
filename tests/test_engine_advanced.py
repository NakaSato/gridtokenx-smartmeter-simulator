import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from smart_meter_simulator.core.engine import SimulationEngine, SimulationMode
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.models.reading import EnergyReading

@pytest.fixture
def mock_transport():
    transport = MagicMock()
    transport.connect = AsyncMock()
    transport.disconnect = AsyncMock()
    transport.send_readings = AsyncMock()
    transport.send_batch = AsyncMock()
    transport.send_auction_bid = AsyncMock()
    transport.send_alert = AsyncMock()
    return transport

@pytest.fixture
def engine(mock_transport):
    m1 = SmartMeter({"meter_id": "M1", "meter_type": "Residential", "has_battery": True, "battery_capacity": 10.0})
    engine = SimulationEngine(meters=[m1], transport=mock_transport)
    engine.current_sim_time = datetime.now(timezone.utc)
    return engine

@pytest.mark.asyncio
async def test_adr_activation_in_tick(engine):
    # Setup ADR event
    from smart_meter_simulator.core.adr import ADREventType
    engine.adr.trigger_event(
        event_type=ADREventType.PRICE_SPIKE,
        start_time=engine.current_sim_time,
        duration_minutes=60,
        payload=2.0
    )
    
    # Add a cluster so the loop runs
    mock_cluster = MagicMock()
    mock_cluster.total_capacity_kwh = 10.0
    mock_cluster.current_stored_kwh = 5.0
    mock_cluster.max_flexibility_up_kw = 5.0
    engine.vpp.clusters = {"F1": mock_cluster}
    
    # Run tick
    with patch.object(engine.vpp, 'dispatch_cluster', return_value={"M1": 2.0}) as mock_dispatch:
        await engine.tick()
        
        # Verify ADR affected prices
        assert engine.meters[0].current_tariff is not None
        assert engine.meters[0].current_tariff.import_rate > 0
        
        # Verify VPP was triggered due to ADR peak
        assert mock_dispatch.called

@pytest.mark.asyncio
async def test_grid_islanding_flow(engine):
    # Mock adapter and net for islanding
    engine.adapter = MagicMock()
    engine.net = MagicMock()
    
    with patch.object(engine.island_manager, 'disconnect', return_value=True) as mock_disconnect:
        success = await engine.disconnect_grid()
        assert success is True
        assert mock_disconnect.called
        # Verify alert sent
        assert engine.transport.send_alert.called
        assert engine.transport.send_alert.call_args[0][0]["subtype"] == "ISLANDING"

@pytest.mark.asyncio
async def test_grid_reconnection_flow(engine):
    engine.adapter = MagicMock()
    engine.net = MagicMock()
    
    mock_cluster = MagicMock()
    mock_cluster.total_capacity_kwh = 10.0
    mock_cluster.current_stored_kwh = 5.0
    engine.vpp.clusters = {"F1": mock_cluster}
    
    with patch.object(engine.island_manager, 'reconnect', return_value=True) as mock_reconnect:
        success = await engine.reconnect_grid()
        assert success is True
        assert mock_reconnect.called
        # Verify alert sent
        assert engine.transport.send_alert.called
        assert engine.transport.send_alert.call_args[0][0]["subtype"] == "RECONNECTION"

@pytest.mark.asyncio
async def test_microgrid_stability_in_tick(engine):
    # Force islanded state
    engine.island_manager.state.is_islanded = True
    
    mock_cluster = MagicMock()
    mock_cluster.total_capacity_kwh = 10.0
    mock_cluster.current_stored_kwh = 5.0
    mock_cluster.max_flexibility_up_kw = 5.0
    mock_cluster.max_flexibility_down_kw = 5.0
    engine.vpp.clusters = {"F1": mock_cluster}
    
    with patch.object(engine.vpp, 'orchestrate_microgrid_stability') as mock_orchestrate:
        await engine.tick()
        assert mock_orchestrate.called
