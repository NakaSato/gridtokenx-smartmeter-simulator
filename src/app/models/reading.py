from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

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
    
    # Electrical Parameters (Optional based on meter capabilities)
    voltage: Optional[float] = Field(None, ge=0)
    current: Optional[float] = Field(None, ge=0)
    power_factor: Optional[float] = Field(None, ge=0, le=1)
    frequency: Optional[float] = Field(None, ge=0)
    temperature: Optional[float] = Field(None, ge=-50, le=60)  # Temperature in Celsius
    
    # Metadata
    location: str
    meter_type: str
    user_type: str
    wallet_address: Optional[str] = None  # Solana wallet address for token minting
    
    # Trading Data
    max_sell_price: Optional[float] = Field(None, ge=0)
    max_buy_price: Optional[float] = Field(None, ge=0)
    rec_eligible: bool = False
    carbon_offset: float = Field(0.0, ge=0)
    weather_condition: str = "Sunny"
    
    # Security
    meter_signature: Optional[str] = None
    
    def to_submission_payload(self) -> dict:
        """
        Convert to API Gateway submission format.
        For prosumers: send surplus energy (net generation after consumption)
        For consumers: skip submission (no surplus to tokenize)
        """
        # Only submit if there's surplus energy to tokenize
        kwh_amount = max(0.0, self.surplus_energy)
        
        return {
            "wallet_address": self.wallet_address,  # Solana wallet for token minting
            "kwh_amount": f"{kwh_amount:.6f}",  # String format for precision
            "reading_timestamp": self.timestamp.isoformat(),
            "meter_signature": self.meter_signature,
            "meter_serial": self.meter_id  # Send as serial for legacy support
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
