from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MeasurementChannel(str, Enum):
    """
    Available measurement channels for smart meters.
    """

    VOLTAGE = "v"
    ACTIVE_POWER = "p"
    REACTIVE_POWER = "q"
    CURRENT = "i"
    CURRENT_ANGLE = "ia"
    VOLTAGE_ANGLE = "va"


class EnergyReading(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
    """
    Data model for a single smart meter reading.
    """
    meter_id: str
    timestamp: datetime
    sequence_number: int = 0

    # Energy Data (kWh)
    energy_generated: float = Field(..., ge=0)
    energy_consumed: float = Field(..., ge=0)
    surplus_energy: float = Field(..., ge=0)
    deficit_energy: float = Field(..., ge=0)
    interval_seconds: int = Field(15, gt=0)

    # Electrical Parameters (Optional based on meter capabilities)
    voltage: Optional[float] = Field(None, ge=0)
    current: Optional[float] = Field(None, ge=0)
    reactive_power_kvar: Optional[float] = None
    power_factor: Optional[float] = Field(None, ge=0, le=1)
    frequency: Optional[float] = Field(None, ge=0)
    temperature: Optional[float] = Field(None, ge=-50, le=60)  # Temperature in Celsius

    # Metadata
    location: str
    meter_type: str
    user_type: str

    # Meter metadata
    manufacturer_id: str = "GXT"
    logical_device_name: str = "LDN-00000000"

    # Grid metrics
    voltage_pu: Optional[float] = None

    weather_condition: str = "Sunny"

    def to_telemetry_payload(self) -> dict:
        """Convert to an API-friendly meter telemetry payload."""
        hours = self.interval_seconds / 3600.0
        power_gen = self.energy_generated / hours if hours > 0 else 0.0
        power_cons = self.energy_consumed / hours if hours > 0 else 0.0

        return {
            "timestamp": self.timestamp.isoformat(),
            "meter_serial": self.meter_id,
            "reading_id": f"{self.meter_id}-{self.sequence_number}",
            "interval_seconds": self.interval_seconds,
            "energy_generated": round(self.energy_generated, 6),
            "energy_consumed": round(self.energy_consumed, 6),
            "surplus_energy": round(self.surplus_energy, 6),
            "deficit_energy": round(self.deficit_energy, 6),
            "power_generated": round(power_gen, 3),
            "power_consumed": round(power_cons, 3),
            "voltage": round(self.voltage, 2) if self.voltage is not None else None,
            "current": round(self.current, 3) if self.current is not None else None,
            "reactive_power_kvar": (
                round(self.reactive_power_kvar, 3)
                if self.reactive_power_kvar is not None
                else None
            ),
            "power_factor": (
                round(self.power_factor, 4) if self.power_factor is not None else None
            ),
            "frequency": (
                round(self.frequency, 3) if self.frequency is not None else None
            ),
            "temperature": (
                round(self.temperature, 1) if self.temperature is not None else None
            ),
        }
