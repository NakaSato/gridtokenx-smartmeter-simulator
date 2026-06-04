"""
Configuration enums for Smart Meter Simulator
Separated to avoid circular imports
"""

from enum import Enum


class MeterType(Enum):
    """Meter type enumeration"""

    SOLAR_PROSUMER = "Solar_Prosumer"
    GRID_CONSUMER = "Grid_Consumer"
    HYBRID_PROSUMER = "Hybrid_Prosumer"
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    FEEDER = "Feeder"
    SUBSTATION = "Substation"


class AccuracyClass(Enum):
    """
    Accuracy class definitions for measurement uncertainty.

    Per ANSI C12.20 standard:
    - CLASS_0_2: ±0.2% accuracy (high-precision, substation meters)
    - CLASS_0_5: ±0.5% accuracy (feeder head meters)
    - CLASS_1_0: ±1.0% accuracy (commercial meters)
    - CLASS_2_0: ±2.0% accuracy (residential meters)
    """

    CLASS_0_2 = 0.002
    CLASS_0_5 = 0.005
    CLASS_1_0 = 0.010
    CLASS_2_0 = 0.020


class WeatherCondition(Enum):
    """Weather condition enumeration"""

    SUNNY = "Sunny"
    PARTLY_CLOUDY = "Partly_Cloudy"
    CLOUDY = "Cloudy"
    OVERCAST = "Overcast"
    RAINY = "Rainy"


class GridConnectionStatus(Enum):
    """Grid connection status enumeration"""

    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    MAINTENANCE = "Maintenance"


class SimulationMode(Enum):
    """Simulation mode enumeration"""

    RANDOM = "random"
