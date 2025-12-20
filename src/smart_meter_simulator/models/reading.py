from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EnergyReading(BaseModel):
    """
    Data model for a single smart meter reading.
    """

    meter_id: str
    timestamp: datetime

    # Energy Data (kWh)
    energy_generated: float = Field(..., ge=0)
    energy_consumed: float = Field(..., ge=0)
    surplus_energy: float = Field(..., ge=0)
    deficit_energy: float = Field(..., ge=0)

    # Battery Data
    battery_level: float = Field(0.0, ge=0, le=100)

    # Electrical Parameters
    voltage: float = Field(240.0, ge=0)
    current: float = Field(0.0, ge=0)
    power_factor: float = Field(1.0, ge=0, le=1)
    frequency: float = Field(50.0, ge=0)
    temperature: float = Field(20.0, ge=-50, le=60)  # Temperature in Celsius

    # Metadata
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    meter_type: str
    user_type: str

    # Trading Data
    max_sell_price: Optional[float] = Field(None, ge=0)
    max_buy_price: Optional[float] = Field(None, ge=0)
    rec_eligible: bool = False
    carbon_offset: float = Field(0.0, ge=0)
    net_emission: float = Field(0.0)  # Net carbon emission in kgCO2
    weather_condition: str = "Sunny"

    # Security
    meter_signature: Optional[str] = None
    wallet_address: Optional[str] = None

    def to_submission_payload(self) -> dict:
        """
        Convert to API Gateway submission format.
        Includes full telemetry data for monitoring and tokenization.
        """
        # Calculate net energy for tokenization (Positive = Mint, Negative = Burn)
        kwh_amount = self.surplus_energy - self.deficit_energy

        return {
            # Fields required by API Gateway CreateReadingRequest
            "kwh": float(kwh_amount),  # Must be float, not string
            "timestamp": self.timestamp.isoformat(),
            "wallet_address": self.wallet_address,
            
            # Additional Telemetry (Ignored by API Gateway but good for debugging/future)
            "meter_serial": self.meter_id,
            "reading_timestamp": self.timestamp.isoformat(), # Legacy support
            "meter_signature": self.meter_signature,
            "energy_generated": self.energy_generated,
            "energy_consumed": self.energy_consumed,
            "battery_level": self.battery_level,
            "weather_condition": self.weather_condition,
        }

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
