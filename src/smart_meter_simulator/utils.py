"""
Utility functions for Smart Meter Simulator
Separates helper functions to reduce main file size
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EnergyReading:
    """Energy reading data structure"""
    timestamp: str
    meter_id: str
    meter_type: str
    location: str
    user_type: str

    # Energy Data (kWh)
    energy_generated: float
    energy_consumed: float
    energy_available_for_sale: float
    energy_needed_from_grid: float
    battery_level: float

    # Electrical Parameters
    voltage: float
    current: float
    power_factor: float
    frequency: float
    temperature: float

    # Solar Specific
    irradiance: Optional[float]
    panel_temperature: Optional[float]
    weather_condition: Optional[str]

    # Grid Connection
    grid_connection_status: str
    grid_feed_in_rate: float
    grid_purchase_rate: float

    # Trading Data
    surplus_energy: float
    deficit_energy: float
    trading_preference: str
    max_sell_price: float
    max_buy_price: float

    # REC Data (Renewable Energy Certificate)
    rec_eligible: bool
    carbon_offset: float


def format_reading(reading: EnergyReading) -> dict:
    """Convert EnergyReading to dictionary"""
    from dataclasses import asdict
    return asdict(reading)


def validate_reading(reading: EnergyReading) -> bool:
    """Validate energy reading data"""
    if reading.energy_generated < 0:
        return False
    if reading.energy_consumed < 0:
        return False
    if not (0 <= reading.battery_level <= 100):
        return False
    if reading.voltage < 0:
        return False
    return True


def calculate_surplus_deficit(
    generated: float,
    consumed: float
) -> tuple:
    """Calculate surplus and deficit energy"""
    if generated >= consumed:
        surplus = generated - consumed
        deficit = 0.0
    else:
        surplus = 0.0
        deficit = consumed - generated
    return surplus, deficit


def get_meter_type_ratio(meter_type: str) -> float:
    """Get meter type distribution ratio"""
    from config import SimulatorConfig
    ratios = {
        'Solar_Prosumer': SimulatorConfig.SOLAR_PROSUMER_RATIO,
        'Grid_Consumer': SimulatorConfig.GRID_CONSUMER_RATIO,
        'Hybrid_Prosumer': SimulatorConfig.HYBRID_PROSUMER_RATIO,
        'Battery_Storage': SimulatorConfig.BATTERY_STORAGE_RATIO,
    }
    return ratios.get(meter_type, 0.0)


def calculate_carbon_offset(
    generation: float,
    offset_rate: float
) -> float:
    """Calculate carbon offset for renewable energy"""
    return generation * offset_rate


def format_timestamp() -> str:
    """Get current timestamp in ISO format"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
