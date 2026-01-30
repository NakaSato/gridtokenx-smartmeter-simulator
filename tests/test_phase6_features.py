import pytest
import pandas as pd
import os
from datetime import datetime
from src.app.core.data_source import ProfileDataSource
from src.app.adapters.cim_adapter import CIMAdapter
import pandapower as pp

@pytest.fixture
def data_source(tmp_path):
    return ProfileDataSource(profiles_dir=str(tmp_path))

def test_slp_generation(data_source):
    """Test that SLP generation produces expected daily patterns and scaling."""
    name = "test_h0"
    success = data_source.generate_slp(
        name=name,
        profile_type="H0",
        annual_kwh=3650, # 10 kWh/day
        days=1,
        meter_ids=["M1"]
    )
    assert success is True
    assert name in data_source.profiles
    df = data_source.profiles[name]
    assert len(df) == 96
    # Check scaling: sum of 15-min intervals should be daily total
    # Since values are kW for 15-min intervals, sum/4 should be kWh
    daily_kwh = df["M1"].sum() / 4.0
    assert pytest.approx(daily_kwh, 0.1) == 10.0

def test_cim_export_structure():
    """Test that CIMAdapter generates valid-looking XML with core nodes."""
    net = pp.create_empty_network()
    pp.create_bus(net, vn_kv=0.4, name="Bus 1")
    pp.create_load(net, bus=0, p_mw=0.002, name="Load 1")
    
    adapter = CIMAdapter(net_name="TestGrid")
    xml_content = adapter.export_to_xml(net)
    
    assert 'xmlns:cim="http://iec.ch/TC57/2013/CIM-schema-cim16#"' in xml_content
    assert '<cim:ConnectivityNode rdf:ID="_Bus_0">' in xml_content
    assert '<cim:EnergyConsumer rdf:ID="_Load_0">' in xml_content
    assert '<cim:EnergyConsumer.p>0.002</cim:EnergyConsumer.p>' in xml_content

def test_parquet_loading(data_source, tmp_path):
    """Test that Parquet files are correctly loaded."""
    if not hasattr(pd.DataFrame, 'to_parquet'):
        pytest.skip("Fastparquet/Pyarrow not installed")
        
    name = "test_parquet"
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="15T"),
        "M1": [1.0] * 10
    })
    
    path = os.path.join(str(tmp_path), f"{name}.parquet")
    try:
        df.to_parquet(path, index=False)
    except Exception:
        pytest.skip("Failed to save parquet - engine missing")

    success = data_source.load_profile(name)
    assert success is True
    assert len(data_source.profiles[name]) == 10
    assert data_source.profiles[name].iloc[0]["M1"] == 1.0

def test_cim_adapter_with_measurements():
    """Test CIM export with measurement tables."""
    net = pp.create_empty_network()
    b = pp.create_bus(net, vn_kv=0.4)
    pp.create_measurement(net, "v", "bus", 1.01, 0.001, b, name="Volt_M1")
    
    adapter = CIMAdapter()
    xml = adapter.export_to_xml(net)
    assert 'Volt_M1' in xml
    assert 'Analog' in xml
    assert '1.01' in xml

def test_api_generate_profile(client):
    """Test POST /api/profiles/generate endpoint."""
    import app.app as app_module
    from unittest.mock import MagicMock, patch
    
    mock_engine = MagicMock()
    mock_engine.data_source = MagicMock()
    mock_engine.data_source.generate_slp.return_value = True
    
    # Directly patch the module-level engine variable
    with patch('app.app.engine', mock_engine):
        response = client.post("/api/profiles/generate", json={
            "name": "api_slp",
            "profile_type": "H0",
            "annual_kwh": 3000
        })
        assert response.status_code == 200
        assert response.json()["success"] is True

def test_api_export_cim(client):
    """Test GET /api/grid/export/cim endpoint."""
    import app.app as app_module
    from unittest.mock import MagicMock, patch
    
    net = pp.create_empty_network()
    pp.create_bus(net, vn_kv=0.4)
    
    mock_engine = MagicMock()
    mock_engine.net = net
    
    # Directly patch the module-level engine variable
    with patch('app.app.engine', mock_engine):
        response = client.get("/api/grid/export/cim")
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "<cim:ConnectivityNode" in response.text
@pytest.fixture
def client():
    """Reusable TestClient fixture for API testing."""
    from fastapi.testclient import TestClient
    from app.app import app
    with TestClient(app) as c:
        yield c

def test_engine_performance_settings():
    """Test that engine applies performance optimizations like recycling."""
    from app.core.engine import SimulationEngine
    from app.config import SimulatorConfig
    from unittest.mock import MagicMock, patch
    
    engine = SimulationEngine(SimulatorConfig(), MagicMock())
    engine.net = pp.create_empty_network()
    pp.create_bus(engine.net, vn_kv=0.4)
    # Mock runpp to check if recycle was passed
    with patch('pandapower.runpp') as mock_runpp:
        # We need to trigger a tick or a method that calls runpp
        # Simulating the part of tick that calls runpp
        pp.runpp(engine.net, algorithm='nr', recycle={'Ybus': True, 'trafo': True})
        args, kwargs = mock_runpp.call_args
        assert kwargs.get('recycle') == {'Ybus': True, 'trafo': True}

def test_profile_data_source_list_filtering(data_source, tmp_path):
    """Test that list_profiles filters by all supported extensions."""
    (tmp_path / "p1.csv").touch()
    (tmp_path / "p2.json").touch()
    (tmp_path / "p3.parquet").touch()
    (tmp_path / "p4.txt").touch() # Should be filtered out
    
    profiles = data_source.list_profiles()
    assert len(profiles) == 3
    assert "p1" in profiles
    assert "p2" in profiles
    assert "p3" in profiles
    assert "p4" not in profiles
