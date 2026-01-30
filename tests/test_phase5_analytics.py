import pytest
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.core.engine import SimulationEngine, SimulationMode
from app.core.meter import SmartMeter
from app.transport.base import TransportLayer
from app.models.reading import EnergyReading
from app.core.analytics import GridAnalytics

@pytest.fixture
def mock_transport():
    transport = AsyncMock(spec=TransportLayer)
    transport.send_reading.return_value = True
    transport.send_batch.return_value = True
    transport.send_grid_status.return_value = True
    transport.connect.return_value = None
    return transport

@pytest.fixture
def sample_engine(mock_transport):
    meter = SmartMeter({
        "meter_id": "METER_TEST", 
        "location": "Test", 
        "meter_type": "Residential", 
        "user_type": "Consumer",
        "has_solar": False
    })
    engine = SimulationEngine([meter], mock_transport)
    engine.adapter = MagicMock()
    # Use a real data frame for buses to avoid mock comparison errors
    engine.net = MagicMock()
    engine.net.bus = pd.DataFrame({'name': ['Bus 0'], 'vn_kv': [20.0]})
    engine.net.res_bus = pd.DataFrame({'vm_pu': [1.0], 'va_degree': [0.0]})
    
    # Mock line/trafo results for losses
    engine.net.res_line = pd.DataFrame({'pl_mw': [0.05]})
    engine.net.res_trafo = pd.DataFrame({'pl_mw': [0.01]})
    
    # Mock sgen/ext_grid for total gen
    engine.net.res_sgen = pd.DataFrame({'p_mw': [0.0]})
    engine.net.res_ext_grid = pd.DataFrame({'p_mw': [10.0]})
    
    return engine

@pytest.mark.asyncio
async def test_analytics_calculation(sample_engine):
    """Test that GridAnalytics correctly calculates losses and violations."""
    analytics = GridAnalytics(voltage_low=0.95, voltage_high=1.05)
    
    # 1. Normal state
    report = analytics.analyze_step(sample_engine.net, None)
    assert report.total_loss_mw == pytest.approx(0.06)
    assert report.num_violations == 0
    
    # 2. Trigger violation
    sample_engine.net.res_bus.at[0, 'vm_pu'] = 1.06
    report = analytics.analyze_step(sample_engine.net, None)
    assert report.num_violations == 1
    assert report.violations[0]["type"] == "overvoltage"

@pytest.mark.asyncio
async def test_fdi_attacker_interception(sample_engine):
    """Test that FDI_Attacker modifies readings before they reach transport/SE."""
    sample_engine.attacker.configure(active=True, targets=["METER_TEST"], bias=10.0)
    
    now = datetime.now(timezone.utc)
    reading = sample_engine.meters[0].generate_reading(now)
    original_cons = reading.energy_consumed
    
    intercepted = sample_engine.attacker.intercept([reading])
    # bias/4 for 15m
    assert intercepted[0].energy_consumed == pytest.approx(original_cons + 2.5)

@pytest.mark.asyncio
async def test_engine_integration_broadcast(sample_engine):
    """Test that analytics summary is included in the grid status broadcast."""
    mock_results = MagicMock()
    mock_results.converged = True
    mock_results.num_measurements = 10
    mock_results.mean_absolute_error = 0.001
    mock_results.max_residual = 0.005
    mock_results.v_deviation_avg = 0.002
    mock_results.total_losses_mw = 0.06
    
    sample_engine.adapter.estimate_state.return_value = mock_results
    sample_engine.adapter.get_grid_status.return_value = {"converged": True}
    
    # Trigger a violation so summary has one
    sample_engine.net.res_bus.at[0, 'vm_pu'] = 1.06
    sample_engine.analytics.analyze_step(sample_engine.net, mock_results)
    
    summary = sample_engine.analytics.get_summary()
    assert "latest" in summary
    assert summary["latest"]["violations"] == 1
    assert summary["latest"]["loss_mw"] == pytest.approx(0.06)
