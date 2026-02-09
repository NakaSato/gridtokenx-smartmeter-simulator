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
    
    # Advanced Grid & Security Metrics (Phase 3/8)
    voltage_pu: Optional[float] = None
    norm_residual: Optional[float] = None
    ewma_residual: Optional[float] = None
    is_compromised: bool = False
    
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
        Sends surplus energy for token minting plus full telemetry
        for dashboard, analytics, and grid health monitoring.
        """
        kwh_amount = max(0.0, self.surplus_energy)
        
        return {
            # Core fields for token minting
            "wallet_address": self.wallet_address,
            "kwh": round(kwh_amount, 6),  # Numeric for Rust Decimal deserialization
            "timestamp": self.timestamp.isoformat(),
            "meter_signature": self.meter_signature,
            "meter_serial": self.meter_id,
            
            # Energy telemetry (kWh)
            "energy_generated": round(self.energy_generated, 6),
            "energy_consumed": round(self.energy_consumed, 6),
            "surplus_energy": round(self.surplus_energy, 6),
            "deficit_energy": round(self.deficit_energy, 6),
            
            # Power telemetry (kW) — approximate from kWh over 15-min interval
            "power_generated": round(self.energy_generated * 4.0, 3),  # kWh * 4 = kW (15-min)
            "power_consumed": round(self.energy_consumed * 4.0, 3),
            
            # Electrical parameters
            "voltage": round(self.voltage, 2) if self.voltage is not None else None,
            "current": round(self.current, 3) if self.current is not None else None,
            "power_factor": round(self.power_factor, 4) if self.power_factor is not None else None,
            "frequency": round(self.frequency, 3) if self.frequency is not None else None,
            "temperature": round(self.temperature, 1) if self.temperature is not None else None,
            
            # Battery & environmental
            "battery_level": round(self.battery_level, 1),
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
