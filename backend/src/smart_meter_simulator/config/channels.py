"""
Meter type to measurement channel configuration
"""

from .enums import MeterType

# Measurement channel sets per meter type
# v=voltage, p=active power, q=reactive power, i=current, ia=current angle, va=voltage angle
METER_TYPE_CHANNELS = {
    MeterType.GRID_CONSUMER: {"v", "p", "q"},
    MeterType.RESIDENTIAL: {"v", "p", "q"},
    MeterType.SOLAR_PROSUMER: {"v", "p", "q"},
    MeterType.HYBRID_PROSUMER: {"v", "p", "q"},
    MeterType.COMMERCIAL: {"v", "p", "q", "i"},
    MeterType.FEEDER: {"v", "p", "q", "i"},
    MeterType.SUBSTATION: {"v", "p", "q", "i", "ia", "va"},
    # BESS discharges (exports), so it omits the current channel like the PV
    # prosumers — the signed-current model reports magnitude only. EV stations
    # are pure load (positive current), so they carry the current channel.
    MeterType.BESS: {"v", "p", "q"},
    MeterType.EV_CHARGER: {"v", "p", "q", "i"},
    MeterType.DC_FAST_CHARGER: {"v", "p", "q", "i"},
}
