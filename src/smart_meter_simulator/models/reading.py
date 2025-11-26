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
    meter_type: str
    user_type: str
    
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
        """
        return {
            "kwh_amount": f"{self.energy_generated:.6f}",  # String format for precision
            "reading_timestamp": self.timestamp.isoformat(),
            "meter_signature": self.meter_signature
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
