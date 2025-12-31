from datetime import datetime
from typing import Optional, Any, Union, List
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
    # Accumulated Energy (Lifetime or Session)
    total_energy_generated: float = Field(0.0, ge=0)
    total_energy_consumed: float = Field(0.0, ge=0)
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
    
    # Power Quality (THD - Total Harmonic Distortion)
    thd_voltage: float = Field(0.0, ge=0, le=100)  # THD-V in %
    thd_current: float = Field(0.0, ge=0, le=100)  # THD-I in %

    # Metadata
    location: Any
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    meter_type: str
    user_type: str
    grid_zone_id: Optional[int] = None

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
    balance_gtx: Optional[float] = None
    balance_nrg: Optional[float] = None

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
            "timestamp": self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "wallet_address": self.wallet_address,
            
            # Core Meter Identity
            "meter_serial": self.meter_id,
            "meter_id": self.meter_id,
            "meter_type": self.meter_type,
            
            # Energy Data
            "energy_generated": self.energy_generated,
            "energy_consumed": self.energy_consumed,
            "surplus_energy": self.surplus_energy,
            "deficit_energy": self.deficit_energy,
            
            # Electrical Parameters
            "voltage": self.voltage,
            "current": self.current,
            "power_factor": self.power_factor,
            "frequency": self.frequency,
            "temperature": self.temperature,
            
            # Power Quality
            "thd_voltage": self.thd_voltage,
            "thd_current": self.thd_current,
            
            # Location (GPS)
            "latitude": self.latitude,
            "longitude": self.longitude,
            
            # Battery & Environmental
            "battery_level": self.battery_level,
            "weather_condition": self.weather_condition,
            
            # Trading & Certification
            "rec_eligible": self.rec_eligible,
            "carbon_offset": self.carbon_offset,
            "max_sell_price": self.max_sell_price,
            "max_buy_price": self.max_buy_price,
            
            # Security
            "meter_signature": self.meter_signature,
            "reading_timestamp": self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }

    class Config:
        json_encoders = {datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%SZ')}
