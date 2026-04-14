"""
Meter type to measurement channel configuration
"""

from .enums import MeterType

# Measurement channel sets per meter type
# v=voltage, p=active power, q=reactive power, i=current, ia=current angle, va=voltage angle, soc=state of charge
METER_TYPE_CHANNELS = {
    MeterType.GRID_CONSUMER: {"v", "p", "q"},
    MeterType.RESIDENTIAL: {"v", "p", "q"},
    MeterType.SOLAR_PROSUMER: {"v", "p", "q"},
    MeterType.HYBRID_PROSUMER: {"v", "p", "q"},
    MeterType.BATTERY_STORAGE: {"v", "p", "q"},
    MeterType.COMMERCIAL: {"v", "p", "q", "i"},
    MeterType.FEEDER: {"v", "p", "q", "i"},
    MeterType.SUBSTATION: {"v", "p", "q", "i", "ia", "va"},
    MeterType.EV_CHARGER: {"v", "p", "q", "i", "soc"},
    MeterType.DC_FAST_CHARGER: {"v", "p", "q", "i", "soc", "connector_count", "port_status"},
}
