"""
Thai Grid Feeder Scenario.

Standard Thai distribution feeder scenario using the EGAT national
transmission backbone with PEA/MEA distribution grid parameters.
"""

from .base import ScenarioConfig, MarketConfig, HelicsConfig, GridlabdConfig


def thai_feeder_default() -> ScenarioConfig:
    """Default Thai feeder scenario with EGAT grid and TOU tariffs.

    Uses the EGAT transmission backbone loaded from GeoJSON data,
    with standard PEA TOU tariffs applied to all meters.
    """
    return ScenarioConfig(
        name="thai_feeder",
        description=(
            "Standard Thai distribution feeder scenario. "
            "EGAT national transmission backbone from GeoJSON, "
            "PEA/MEA distribution with TOU tariffs. "
            "Mix of residential, commercial, and prosumer meters."
        ),
        grid_topology="egat",
        meter_count=50,
        duration_hours=24,
        simulation_interval=900,
        market=MarketConfig(
            enabled=True,
            market_type="tou_only",
            on_peak_rate=5.79,
            off_peak_rate=2.65,
            on_peak_start=9,
            on_peak_end=22,
            ft_adjustment=0.94,
        ),
        helics=HelicsConfig(enabled=False),
        gridlabd=GridlabdConfig(enabled=False),
        tags=["thai", "egat", "pea", "feeder", "tou"],
        overrides={
            "base_latitude": 13.758252,
            "base_longitude": 100.687455,
        },
    )


def thai_feeder_market() -> ScenarioConfig:
    """Thai feeder with full transactive market.

    Adds double-auction market clearing on top of the standard Thai feeder,
    enabling dynamic pricing and DER response.
    """
    return ScenarioConfig(
        name="thai_feeder_market",
        description=(
            "Thai feeder with transactive double-auction market. "
            "EGAT grid + dynamic retail pricing with DER participation."
        ),
        grid_topology="egat",
        meter_count=100,
        duration_hours=168,  # 1 week
        simulation_interval=900,
        market=MarketConfig(
            enabled=True,
            market_type="double_auction",
            price_cap=8.0,
            on_peak_rate=5.79,
            off_peak_rate=2.65,
        ),
        helics=HelicsConfig(enabled=False),
        gridlabd=GridlabdConfig(enabled=False),
        tags=["thai", "market", "transactive"],
        overrides={
            "solar_prosumer_ratio": 0.25,
            "hybrid_prosumer_ratio": 0.15,
            "ev_charger_ratio": 0.10,
        },
    )
