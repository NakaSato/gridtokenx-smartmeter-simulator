"""
TESP TE30 Transactive Energy Challenge Scenario.

Replicates the 30-node transactive energy challenge from TESP,
with dynamic pricing and demand response.

Reference: https://tesp.readthedocs.io/en/latest/Demonstrations_and_Examples.html
"""

from .base import ScenarioConfig, MarketConfig, HelicsConfig, GridlabdConfig
from .loadshed import _resolve_tesp_path


def te30_standalone() -> ScenarioConfig:
    """TE30 challenge in standalone mode with transactive market.

    Uses the TE30 GLM topology and enables the Thai double-auction market
    for dynamic pricing and demand response.
    """
    return ScenarioConfig(
        name="te30_standalone",
        description=(
            "TESP TE30 Transactive Energy Challenge. "
            "30-node feeder with double-auction market clearing, "
            "demand response, and TOU tariff integration. "
            "Standalone mode using pandapower."
        ),
        grid_topology=f"glm:{_resolve_tesp_path('examples/capabilities/te30/TE_Challenge.glm')}",
        meter_count=30,
        duration_hours=48,
        simulation_interval=300,  # 5-minute intervals for transactive market
        market=MarketConfig(
            enabled=True,
            market_type="double_auction",
            price_cap=8.0,
            on_peak_rate=5.79,
            off_peak_rate=2.65,
        ),
        helics=HelicsConfig(enabled=False),
        gridlabd=GridlabdConfig(
            enabled=True,
            mode="standalone",
            glm_file=_resolve_tesp_path("examples/capabilities/te30/TE_Challenge.glm"),
        ),
        tags=["tesp", "te30", "transactive", "market", "standalone"],
    )
