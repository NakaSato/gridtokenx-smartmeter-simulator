"""
Scenario Runner — loads and applies scenario configurations.

Takes a ScenarioConfig and configures the SimulationEngine accordingly:
grid topology, market behavior, HELICS settings, meter population, etc.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from ..config import get_config
from ..scenarios.base import ScenarioConfig

logger = logging.getLogger(__name__)

# Registry of built-in scenario factories
_BUILTIN_SCENARIOS: Dict[str, Callable[[], ScenarioConfig]] = {}


def _register_builtins():
    """Populate the built-in scenario registry."""
    global _BUILTIN_SCENARIOS
    if _BUILTIN_SCENARIOS:
        return  # Already registered

    from ..scenarios.loadshed import loadshed_standalone, loadshed_cosim
    from ..scenarios.te30 import te30_standalone
    from ..scenarios.dsot import dsot_thai, dsot_cosim
    from ..scenarios.thai_feeder import thai_feeder_default, thai_feeder_market

    _BUILTIN_SCENARIOS = {
        "loadshed_standalone": loadshed_standalone,
        "loadshed_cosim": loadshed_cosim,
        "te30_standalone": te30_standalone,
        "dsot_thai": dsot_thai,
        "dsot_cosim": dsot_cosim,
        "thai_feeder": thai_feeder_default,
        "thai_feeder_market": thai_feeder_market,
    }


def list_scenarios() -> Dict[str, str]:
    """List all available scenario names and their descriptions.

    Returns:
        Dict mapping scenario name → description.
    """
    _register_builtins()
    result = {}
    for name, factory in _BUILTIN_SCENARIOS.items():
        try:
            config = factory()
            result[name] = config.description
        except Exception as e:
            result[name] = f"(error loading: {e})"
    return result


def get_scenario(name: str) -> Optional[ScenarioConfig]:
    """Get a scenario configuration by name.

    Args:
        name: Scenario name (e.g., "loadshed_standalone").

    Returns:
        ScenarioConfig if found, else None.
    """
    _register_builtins()
    factory = _BUILTIN_SCENARIOS.get(name)
    if factory is None:
        return None
    return factory()


class ScenarioRunner:
    """Loads a ScenarioConfig and applies it to the simulator configuration.

    The ScenarioRunner modifies the application's runtime configuration
    (environment variables, settings) to match the scenario parameters.
    It does NOT directly create or start the SimulationEngine — that's
    handled by the existing lifespan/startup code.

    Usage::

        runner = ScenarioRunner()
        config = get_scenario("loadshed_standalone")
        runner.apply(config)
        # The simulator will start with the scenario's settings
    """

    def __init__(self):
        self._current_scenario: Optional[ScenarioConfig] = None

    def apply(self, scenario: ScenarioConfig) -> None:
        """Apply a scenario configuration to the simulator settings.

        Modifies the global config singleton to match the scenario parameters.

        Args:
            scenario: The scenario configuration to apply.
        """
        import os

        self._current_scenario = scenario

        # Apply simulation parameters
        os.environ["SIMULATION_INTERVAL"] = str(scenario.simulation_interval)
        os.environ["NUM_METERS"] = str(scenario.meter_count)

        # Apply market settings
        mc = scenario.market
        os.environ["MARKET_ENABLED"] = str(mc.enabled).lower()
        os.environ["MARKET_TYPE"] = mc.market_type
        os.environ["MARKET_PRICE_CAP"] = str(mc.price_cap)
        os.environ["MARKET_PRICE_FLOOR"] = str(mc.price_floor)
        os.environ["TOU_ON_PEAK_RATE"] = str(mc.on_peak_rate)
        os.environ["TOU_OFF_PEAK_RATE"] = str(mc.off_peak_rate)
        os.environ["TOU_ON_PEAK_START"] = str(mc.on_peak_start)
        os.environ["TOU_ON_PEAK_END"] = str(mc.on_peak_end)
        os.environ["FT_ADJUSTMENT"] = str(mc.ft_adjustment)

        # Apply HELICS settings
        hc = scenario.helics
        os.environ["HELICS_ENABLED"] = str(hc.enabled).lower()
        os.environ["HELICS_FEDERATE_NAME"] = hc.federate_name
        os.environ["HELICS_BROKER_ADDRESS"] = hc.broker_address
        os.environ["HELICS_BROKER_PORT"] = str(hc.broker_port)
        os.environ["HELICS_DATA_FLOW"] = hc.data_flow

        # Apply GridLAB-D settings
        gc = scenario.gridlabd
        os.environ["GRIDLBD_ENABLED"] = str(gc.enabled).lower()
        os.environ["GRIDLBD_MODE"] = gc.mode
        if gc.glm_file:
            os.environ["GRIDLBD_GLM_FILE"] = gc.glm_file

        # Apply custom overrides
        for key, value in scenario.overrides.items():
            env_key = key.upper()
            os.environ[env_key] = str(value)

        # Reload config
        from ..config.settings import _config_instance, SimulatorConfig
        global _config_instance
        # Reset singleton so next get_config() picks up new env vars
        import smart_meter_simulator.config.settings as settings_mod
        settings_mod._config_instance = None

        logger.info(f"Applied scenario '{scenario.name}': {scenario.description}")

    def get_current_scenario(self) -> Optional[ScenarioConfig]:
        """Get the currently active scenario configuration."""
        return self._current_scenario

    def get_status(self) -> Dict[str, Any]:
        """Get the current scenario status."""
        if self._current_scenario is None:
            return {"active": False, "scenario": None}

        s = self._current_scenario
        return {
            "active": True,
            "scenario": s.name,
            "description": s.description,
            "grid_topology": s.grid_topology,
            "meter_count": s.meter_count,
            "duration_hours": s.duration_hours,
            "market_enabled": s.market.enabled,
            "helics_enabled": s.helics.enabled,
            "gridlabd_mode": s.gridlabd.mode if s.gridlabd.enabled else "off",
            "tags": s.tags,
        }
