"""
TESP Load Shedding Scenario.

Replicates the TESP loadshed demonstration using the IEEE 13-bus test feeder
with dynamic load shedding via HELICS or standalone control signals.

Reference: https://tesp.readthedocs.io/en/latest/Demonstrations_and_Examples.html
"""

from pathlib import Path
from .base import ScenarioConfig, MarketConfig, HelicsConfig, GridlabdConfig


def _resolve_tesp_path(relative_path: str) -> str:
    """Resolve a path relative to the tesp_repo directory."""
    # Try multiple locations for tesp_repo
    candidates = [
        Path(__file__).parent.parent.parent.parent.parent / "tesp_repo" / relative_path,
        Path(__file__).parent.parent.parent.parent / "tesp_repo" / relative_path,
        Path("tesp_repo") / relative_path,
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return str(candidates[0])


def loadshed_standalone() -> ScenarioConfig:
    """Loadshed scenario in standalone mode (no GridLAB-D binary needed).

    Uses GLM→pandapower conversion for grid modeling.
    """
    return ScenarioConfig(
        name="loadshed_standalone",
        description=(
            "TESP load shedding demonstration on IEEE 13-bus feeder. "
            "Standalone mode: GLM topology loaded via pandapower, "
            "no GridLAB-D binary required."
        ),
        grid_topology=f"glm:{_resolve_tesp_path('examples/capabilities/loadshed/loadshed.glm')}",
        meter_count=10,
        duration_hours=6,
        simulation_interval=900,
        market=MarketConfig(enabled=False),
        helics=HelicsConfig(enabled=False),
        gridlabd=GridlabdConfig(
            enabled=True,
            mode="standalone",
            glm_file=_resolve_tesp_path("examples/capabilities/loadshed/loadshed.glm"),
        ),
        tags=["tesp", "loadshed", "ieee13", "standalone"],
    )


def loadshed_cosim() -> ScenarioConfig:
    """Loadshed scenario in co-simulation mode with GridLAB-D.

    Requires: GridLAB-D binary, HELICS broker running on port 23404.
    """
    return ScenarioConfig(
        name="loadshed_cosim",
        description=(
            "TESP load shedding with GridLAB-D co-simulation. "
            "GridLAB-D runs as a HELICS federate providing physics, "
            "while the simulator provides meter load/generation data."
        ),
        grid_topology=f"glm:{_resolve_tesp_path('examples/capabilities/loadshed/loadshed.glm')}",
        meter_count=10,
        duration_hours=6,
        simulation_interval=900,
        market=MarketConfig(enabled=False),
        helics=HelicsConfig(
            enabled=True,
            federate_name="SmartMeterSimulator",
            broker_address="localhost",
            broker_port=23404,
        ),
        gridlabd=GridlabdConfig(
            enabled=True,
            mode="co_sim",
            glm_file=_resolve_tesp_path("examples/capabilities/loadshed/loadshed.glm"),
        ),
        tags=["tesp", "loadshed", "ieee13", "cosim", "helics"],
    )
