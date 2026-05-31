"""
Scenario Configuration Base Class.

Defines the data model for simulation scenario presets, covering
grid topology, market behavior, meter population, and co-simulation settings.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MarketConfig:
    """Market configuration for a scenario.

    Attributes:
        enabled: Whether the transactive market is active.
        market_type: Market clearing algorithm ("double_auction", "tou_only", "p2p").
        price_cap: Maximum price (Baht/kWh).
        price_floor: Minimum price (Baht/kWh).
        on_peak_rate: TOU on-peak rate (Baht/kWh).
        off_peak_rate: TOU off-peak rate (Baht/kWh).
        on_peak_start: On-peak start hour (0-23).
        on_peak_end: On-peak end hour (0-23).
        ft_adjustment: FT fuel tariff adjustment (Baht/kWh).
    """
    enabled: bool = False
    market_type: str = "double_auction"
    price_cap: float = 8.0
    price_floor: float = 0.0
    on_peak_rate: float = 5.79
    off_peak_rate: float = 2.65
    on_peak_start: int = 9
    on_peak_end: int = 22
    ft_adjustment: float = 0.94


@dataclass
class HelicsConfig:
    """HELICS co-simulation configuration.

    Attributes:
        enabled: Whether HELICS co-simulation is active.
        federate_name: Name for the simulator federate.
        broker_address: HELICS broker address.
        broker_port: HELICS broker port.
        data_flow: "individual" or "aggregate" data exchange mode.
    """
    enabled: bool = False
    federate_name: str = "SmartMeterSimulator"
    broker_address: str = "localhost"
    broker_port: int = 23404
    data_flow: str = "individual"


@dataclass
class GridlabdConfig:
    """GridLAB-D configuration for a scenario.

    Attributes:
        enabled: Whether GridLAB-D adapter is active.
        mode: "standalone", "co_sim", or "hybrid".
        glm_file: Path to the GLM model file.
    """
    enabled: bool = False
    mode: str = "standalone"
    glm_file: str = ""


@dataclass
class ScenarioConfig:
    """Base configuration for a simulation scenario.

    Attributes:
        name: Unique scenario identifier.
        description: Human-readable description.
        grid_topology: Grid topology source — one of:
            - ``"egat"``: Thai EGAT national transmission backbone
            - ``"island_hub"``: Khanom–Samui–Phangan–Tao island network
            - ``"glm:<path>"``: Load from a specific GLM file
            - ``"tesp:loadshed"``: TESP loadshed demonstration feeder
            - ``"tesp:te30"``: TESP TE30 transactive challenge
        meter_count: Number of meters to simulate.
        duration_hours: Total simulation duration in hours.
        market: Market configuration.
        helics: HELICS co-simulation configuration.
        gridlabd: GridLAB-D adapter configuration.
        simulation_interval: Tick interval in seconds.
        tags: Arbitrary tags for categorization.
        overrides: Additional config overrides as key-value pairs.
    """
    name: str = ""
    description: str = ""
    grid_topology: str = "island_hub"
    meter_count: int = 20
    duration_hours: int = 24
    market: MarketConfig = field(default_factory=MarketConfig)
    helics: HelicsConfig = field(default_factory=HelicsConfig)
    gridlabd: GridlabdConfig = field(default_factory=GridlabdConfig)
    simulation_interval: int = 900
    tags: List[str] = field(default_factory=list)
    overrides: Dict[str, Any] = field(default_factory=dict)
