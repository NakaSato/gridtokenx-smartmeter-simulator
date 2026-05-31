"""
DSO+T (Distribution System Operator + Transactive) Market Scenario.

Replicates the TESP DSO+T study structure adapted for the Thai grid:
- EGAT as the wholesale (transmission) market operator
- PEA/MEA as the distribution system operator
- Dynamic retail pricing through double-auction market
- DER integration (solar, battery, EV) responding to price signals

Reference: https://tesp.readthedocs.io/en/latest/ (DSO+T Analysis)
"""

from .base import ScenarioConfig, MarketConfig, HelicsConfig, GridlabdConfig


def dsot_thai() -> ScenarioConfig:
    """DSO+T scenario with Thai grid topology and market structure.

    Configures:
    - EGAT transmission backbone grid
    - PEA/MEA retail double-auction market
    - TOU tariff with FT adjustment
    - DER integration (30% solar, 15% battery, 10% EV)
    """
    return ScenarioConfig(
        name="dsot_thai",
        description=(
            "DSO+T Thai Grid Scenario. Distribution System Operator + "
            "Transactive market structure with EGAT wholesale, PEA/MEA retail "
            "double-auction clearing, TOU tariffs, and DER integration."
        ),
        grid_topology="island_hub",
        meter_count=100,
        duration_hours=168,  # 1 week
        simulation_interval=900,
        market=MarketConfig(
            enabled=True,
            market_type="double_auction",
            price_cap=8.0,
            price_floor=0.5,
            on_peak_rate=5.79,
            off_peak_rate=2.65,
            on_peak_start=9,
            on_peak_end=22,
            ft_adjustment=0.94,
        ),
        helics=HelicsConfig(
            enabled=False,
        ),
        gridlabd=GridlabdConfig(enabled=False),
        tags=["dsot", "thai", "market", "der", "island_hub"],
        overrides={
            "solar_prosumer_ratio": 0.30,
            "hybrid_prosumer_ratio": 0.15,
            "battery_storage_ratio": 0.10,
            "ev_charger_ratio": 0.10,
            "grid_consumer_ratio": 0.35,
        },
    )


def dsot_cosim() -> ScenarioConfig:
    """DSO+T scenario with full HELICS co-simulation.

    Requires: HELICS broker, GridLAB-D, PYPOWER federates.
    """
    return ScenarioConfig(
        name="dsot_cosim",
        description=(
            "DSO+T with full HELICS co-simulation. GridLAB-D for distribution "
            "physics, PYPOWER for transmission, GridTokenX for meter simulation "
            "and transactive market."
        ),
        grid_topology="island_hub",
        meter_count=50,
        duration_hours=24,
        simulation_interval=900,
        market=MarketConfig(
            enabled=True,
            market_type="double_auction",
        ),
        helics=HelicsConfig(
            enabled=True,
            federate_name="SmartMeterSimulator",
            broker_address="localhost",
            broker_port=23404,
        ),
        gridlabd=GridlabdConfig(
            enabled=True,
            mode="hybrid",
        ),
        tags=["dsot", "cosim", "helics", "market"],
    )
