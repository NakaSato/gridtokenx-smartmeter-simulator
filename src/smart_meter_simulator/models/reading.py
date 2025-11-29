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
        # Only submit if there's surplus energy to tokenize (for legacy logic)
        # But we send full data now for monitoring
        kwh_amount = max(0.0, self.surplus_energy)

        return {
            "meter_serial": self.meter_id,
            "reading_timestamp": self.timestamp.isoformat(),
            "meter_signature": self.meter_signature,
            "wallet_address": self.wallet_address,
            # Tokenization Data
            "kwh_amount": f"{kwh_amount:.6f}",
            # Full Telemetry
            "energy_generated": f"{self.energy_generated:.6f}",
            "energy_consumed": f"{self.energy_consumed:.6f}",
            "surplus_energy": f"{self.surplus_energy:.6f}",
            "deficit_energy": f"{self.deficit_energy:.6f}",
            "battery_level": f"{self.battery_level:.2f}",
            # Electrical Params
            "voltage": f"{self.voltage:.2f}",
            "current": f"{self.current:.3f}",
            "frequency": f"{self.frequency:.2f}",
            "power_factor": f"{self.power_factor:.2f}",
            "temperature": f"{self.temperature:.1f}",
            # Metadata & Market
            "location": self.location,
            "latitude": str(self.latitude) if self.latitude is not None else None,
            "longitude": str(self.longitude) if self.longitude is not None else None,
            "meter_type": self.meter_type,
            "user_type": self.user_type,
            "weather_condition": self.weather_condition,
            "max_sell_price": f"{self.max_sell_price:.4f}"
            if self.max_sell_price is not None
            else None,
            "max_buy_price": f"{self.max_buy_price:.4f}"
            if self.max_buy_price is not None
            else None,
            "rec_eligible": self.rec_eligible,
            "carbon_offset": f"{self.carbon_offset:.4f}",
            "net_emission": f"{self.net_emission:.4f}",
        }

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
