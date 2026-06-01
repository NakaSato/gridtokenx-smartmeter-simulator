import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from smart_meter_simulator.adapters.helics_adapter import HelicsAdapter
from smart_meter_simulator.core.engine import SimulationEngine
from smart_meter_simulator.devices.ami import SmartMeter
from smart_meter_simulator.transport.base import TransportLayer


class MockTransport(TransportLayer):
    """Mock transport for testing."""
    async def connect(self): pass
    async def disconnect(self): pass
    def is_connected(self) -> bool: return True
    async def send_reading(self, reading): pass
    async def send_batch(self, readings): pass
    async def send_grid_status(self, status): pass
    async def send_frequency_event(self, event): pass
    async def send_carbon_intensity(self, ci): pass
    async def send_weather(self, weather): pass
    async def send_simulation_step(self, step): pass
    async def send_alert(self, alert): pass


@pytest.fixture
def mock_meters():
    return [
        SmartMeter({
            "meter_id": "meter_001",
            "meter_type": "Residential",
            "location": "Samui",
            "accuracy_class": "Class 1.0",
            "base_consumption": 1.5,
            "base_generation": 0.0,
            "latitude": 9.53,
            "longitude": 99.93,
        }),
        SmartMeter({
            "meter_id": "meter_002",
            "meter_type": "Solar_Prosumer",
            "location": "Samui",
            "accuracy_class": "Class 0.5",
            "base_consumption": 1.0,
            "base_generation": 3.0,
            "latitude": 9.53,
            "longitude": 99.93,
        })
    ]


def test_helics_adapter_fallback():
    """Verify that HelicsAdapter handles cases where HELICS is not installed without throwing errors."""
    adapter = HelicsAdapter(fed_name="TestFed")
    
    # If the real helics module is not installed, it should not crash.
    # It should report is_available() according to whether the module is installed.
    available = adapter.is_available()
    
    # Test methods should fail or return default states safely
    if not available:
        assert adapter.initialize([]) is False
        # finalize, request_time, update_subscriptions should run safely as no-ops
        adapter.publish_meter_data([])
        adapter.publish_frequency(50.0)


@patch("smart_meter_simulator.adapters.helics_adapter.HELICS_AVAILABLE", True)
@patch("smart_meter_simulator.adapters.helics_adapter.h")
def test_helics_adapter_mocked_lifecycle(mock_h):
    """Test HELICS adapter lifecycle with a mocked HELICS module."""
    # Set up mock returns
    mock_h.helicsCreateFederateInfo.return_value = MagicMock()
    mock_h.helicsCreateValueFederate.return_value = MagicMock()
    mock_h.helicsFederateRegisterGlobalPublication.return_value = "mock_pub"
    mock_h.helicsFederateRegisterSubscription.return_value = "mock_sub"
    mock_h.helicsFederateRequestTime.return_value = 900.0
    mock_h.helicsInputIsUpdated.return_value = True
    mock_h.helicsInputGetDouble.return_value = 0.35

    adapter = HelicsAdapter(
        fed_name="TestFed",
        core_type="zmq",
        broker_address="127.0.0.1",
        broker_port=23404,
        time_period=900.0,
        data_flow="individual"
    )
    
    # 1. Initialize
    meters = [
        MagicMock(meter_id="m1"),
        MagicMock(meter_id="m2")
    ]
    assert adapter.initialize(meters) is True
    
    # Verify mock calls
    mock_h.helicsCreateFederateInfo.assert_called_once()
    mock_h.helicsCreateValueFederate.assert_called_once()
    
    # Assert aggregated and individual publications registered
    assert "total_p_mw" in adapter.publications
    assert "net_p_mw" in adapter.publications
    assert "m1/p_kw" in adapter.publications
    assert "m2/p_kw" in adapter.publications
    
    # Assert subscriptions registered
    assert "retail_price" in adapter.subscriptions

    # 2. Enter execution mode
    # We mock enter_exec since it has an async runner wrapper
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(adapter.enter_execution_mode())
    assert adapter.is_connected is True
    mock_h.helicsFederateEnterExecutingMode.assert_called_once()

    # 3. Request time
    granted = loop.run_until_complete(adapter.request_time(900.0))
    assert granted == 900.0
    mock_h.helicsFederateRequestTime.assert_called_once_with(adapter.fed, 900.0)

    # 4. Read subscriptions
    adapter.update_subscriptions()
    mock_h.helicsInputIsUpdated.assert_called()
    mock_h.helicsInputGetDouble.assert_called()
    assert adapter.get_subscription_value("retail_price") == 0.35

    # 5. Publish data
    readings = [
        MagicMock(meter_id="m1", active_power_kw=5.0, energy_consumed=1.2, energy_generated=0.0),
        MagicMock(meter_id="m2", active_power_kw=10.0, energy_consumed=2.5, energy_generated=4.0)
    ]
    adapter.publish_meter_data(readings)
    # 2 aggregated active/net/generation power, 1 frequency, 6 individual (3 per meter)
    assert mock_h.helicsPublicationPublishDouble.call_count >= 5

    # 6. Finalize
    loop.run_until_complete(adapter.finalize())
    assert adapter.is_connected is False
    mock_h.helicsFederateFinalize.assert_called_once()
    mock_h.helicsFederateFree.assert_called_once()
    mock_h.helicsCloseLibrary.assert_called_once()
    
    loop.close()


def test_engine_integration_with_helics_mocked(mock_meters):
    """Verify that SimulationEngine configures and triggers HELICS calls in its loop."""
    transport = MockTransport()
    from smart_meter_simulator.config import get_config
    config = get_config()
    
    # Patch HELICS helper to be available and mock the adapter's behavior
    with patch("smart_meter_simulator.adapters.helics_adapter.HELICS_AVAILABLE", True), \
         patch("smart_meter_simulator.adapters.helics_adapter.h") as mock_h, \
         patch.object(config, "helics_enabled", True):
        
        mock_h.helicsCreateFederateInfo.return_value = MagicMock()
        mock_h.helicsCreateValueFederate.return_value = MagicMock()
        mock_h.helicsFederateRequestTime.return_value = 900.0
        mock_h.helicsInputIsUpdated.return_value = True
        mock_h.helicsInputGetDouble.return_value = 0.30  # retail price

        engine = SimulationEngine(mock_meters, transport)
        assert engine.helics_adapter is not None
        
        # Test startup
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run startup logic
        loop.run_until_complete(engine.start())
        
        # Verify HELICS was initialized and entered executing mode
        assert engine.helics_adapter.is_connected is True
        mock_h.helicsFederateEnterExecutingMode.assert_called_once()
        
        # Simulate a single step through engine tick
        loop.run_until_complete(engine.tick(timestamp=datetime.now(timezone.utc)))
        
        # Verify that retail price got updated from subscription
        assert engine.grid.avg_nodal_price == 0.30
        
        # Clean up
        loop.run_until_complete(engine.stop())
        assert engine.helics_adapter.is_connected is False
        mock_h.helicsFederateFinalize.assert_called_once()
        
        loop.close()


def test_helics_dynamic_subscription_mapping(mock_meters):
    """Verify that dynamic HELICS subscription mappings are registered and resolved in engine.tick."""
    transport = MockTransport()
    from smart_meter_simulator.config import get_config
    config = get_config()
    
    custom_mappings = {
        "retail_price": "AMES_Transmission/ClearedPrice",
        "meter_001/dispatch_price": "CustomController/Dispatch_meter_001"
    }
    
    with patch("smart_meter_simulator.adapters.helics_adapter.HELICS_AVAILABLE", True), \
         patch("smart_meter_simulator.adapters.helics_adapter.h") as mock_h, \
         patch.object(config, "helics_enabled", True), \
         patch.object(config, "helics_subscription_mappings", custom_mappings):
         
        mock_h.helicsCreateFederateInfo.return_value = MagicMock()
        mock_h.helicsCreateValueFederate.return_value = MagicMock()
        mock_h.helicsFederateRequestTime.return_value = 900.0
        # Only report update for mock subs that actually have data
        def input_is_updated_mock(sub):
            return sub in ("sub_retail", "sub_dispatch_m1")
        mock_h.helicsInputIsUpdated = input_is_updated_mock
        
        # Mock input value resolution based on subscription object
        def get_double_mock(sub):
            if sub == "sub_retail":
                return 0.45
            elif sub == "sub_dispatch_m1":
                return 0.55
            return 0.28
            
        mock_h.helicsInputGetDouble = get_double_mock
        
        # Override subscription registration to return recognizable identifiers
        def register_sub_mock(fed, key, unit):
            if key == "AMES_Transmission/ClearedPrice":
                return "sub_retail"
            elif key == "CustomController/Dispatch_meter_001":
                return "sub_dispatch_m1"
            return MagicMock()
            
        mock_h.helicsFederateRegisterSubscription = register_sub_mock
        
        engine = SimulationEngine(mock_meters, transport)
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(engine.start())
        
        # Run tick to fetch subscriptions and set prices
        loop.run_until_complete(engine.tick(timestamp=datetime.now(timezone.utc)))
        
        # Assert average price is set to custom AMES_Transmission/ClearedPrice value (0.45)
        print("DEBUG: adapter subscriptions:", engine.helics_adapter.subscriptions)
        print("DEBUG: adapter subscription_cache:", engine.helics_adapter.subscription_cache)
        print("DEBUG: avg_nodal_price:", engine.grid.avg_nodal_price)
        print("DEBUG: meter_001 price:", engine.grid.nodal_prices.get("meter_001"))
        print("DEBUG: meter_002 price:", engine.grid.nodal_prices.get("meter_002"))
        
        assert engine.grid.avg_nodal_price == 0.45
        
        # Assert meter_001 got the mapped CustomController/Dispatch price (0.55)
        assert engine.grid.nodal_prices["meter_001"] == 0.55
        
        # Assert other meters without custom mappings got the fallback retail_price (0.45)
        assert engine.grid.nodal_prices["meter_002"] == 0.45
        
        loop.run_until_complete(engine.stop())
        loop.close()


def test_helics_load_shed_commands(mock_meters):
    """Verify that HELICS load shed commands (OPEN/CLOSED/SHED/RESTORE) are correctly received and applied."""
    transport = MockTransport()
    from smart_meter_simulator.config import get_config
    config = get_config()
    
    custom_mappings = {
        "meter_001/is_shed": "ControlFederate/Shed_meter_001"
    }
    
    with patch("smart_meter_simulator.adapters.helics_adapter.HELICS_AVAILABLE", True), \
         patch("smart_meter_simulator.adapters.helics_adapter.h") as mock_h, \
         patch.object(config, "helics_enabled", True), \
         patch.object(config, "helics_subscription_mappings", custom_mappings):
         
        mock_h.helicsCreateFederateInfo.return_value = MagicMock()
        mock_h.helicsCreateValueFederate.return_value = MagicMock()
        mock_h.helicsFederateRequestTime.return_value = 900.0
        
        # Track simulated message state
        msg_state = ["OPEN"]
        
        def input_is_updated_mock(sub):
            return sub == "sub_shed_m1"
        mock_h.helicsInputIsUpdated = input_is_updated_mock
        
        def get_string_mock(sub):
            if sub == "sub_shed_m1":
                return msg_state[0]
            return ""
        mock_h.helicsInputGetString = get_string_mock
        
        def register_sub_mock(fed, key, unit):
            if key == "ControlFederate/Shed_meter_001":
                return "sub_shed_m1"
            return MagicMock()
        mock_h.helicsFederateRegisterSubscription = register_sub_mock
        
        engine = SimulationEngine(mock_meters, transport)
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(engine.start())
        
        # 1. First tick with "OPEN" (load shed active)
        loop.run_until_complete(engine.tick(timestamp=datetime.now(timezone.utc)))
        assert engine.meters[0].is_shed is True
        
        # 2. Second tick with "CLOSED" (load restored)
        msg_state[0] = "CLOSED"
        loop.run_until_complete(engine.tick(timestamp=datetime.now(timezone.utc)))
        assert engine.meters[0].is_shed is False
        
        loop.run_until_complete(engine.stop())
        loop.close()


