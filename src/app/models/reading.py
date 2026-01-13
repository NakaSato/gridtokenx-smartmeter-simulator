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
    # Simulated Power (kW) - Instantaneous
    power_generated: float = Field(0.0, ge=0)
    power_consumed: float = Field(0.0, ge=0)
    
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

    def to_grid_monitoring_payload(self) -> dict:
        """
        Optimized payload for grid physics monitoring and optimization.
        Focuses on essential grid state data without P2P trading fields.
        Smaller payload size for efficient real-time monitoring.
        """
        kwh_amount = self.surplus_energy - self.deficit_energy
        
        return {
            # Core Identity & Energy
            "meter_serial": self.meter_id,
            "meter_id": self.meter_id,
            "kwh": float(self.energy_generated),
            "timestamp": self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
            
            # Energy Metrics (essential for grid balance)
            "energy_generated": self.energy_generated,
            "energy_consumed": self.energy_consumed,
            
            # Power Metrics (instantaneous kW)
            "power_generated": self.power_generated,
            "power_consumed": self.power_consumed,
            
            # Electrical Parameters
            "voltage": self.voltage,
            "current": self.current,
            "frequency": self.frequency,
            "power_factor": self.power_factor,
            
            # Power Quality (THD monitoring)
            "thd_voltage": self.thd_voltage,
            "thd_current": self.thd_current,
            
            # Location (for zone-based optimization)
            "zone_id": self.grid_zone_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            
            # Battery State (for dispatch optimization)
            "battery_level": self.battery_level,
        }
    
    def to_full_telemetry_payload(self) -> dict:
        """
        Complete telemetry payload including all sensor data.
        Used for detailed analysis, reporting, and blockchain integration.
        """
        kwh_amount = self.surplus_energy - self.deficit_energy
        
        return {
            # Identity & Blockchain
            "meter_serial": self.meter_id,
            "meter_id": self.meter_id,
            "meter_type": self.meter_type,
            "wallet_address": self.wallet_address,
            "meter_signature": self.meter_signature,
            
            # Timestamps
            "timestamp": self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "reading_timestamp": self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
            
            # Energy Data
            "kwh": float(kwh_amount),
            "energy_generated": self.energy_generated,
            "energy_consumed": self.energy_consumed,
            "surplus_energy": self.surplus_energy,
            "deficit_energy": self.deficit_energy,
            "total_energy_generated": self.total_energy_generated,
            "total_energy_consumed": self.total_energy_consumed,
            
            # Electrical Parameters
            "voltage": self.voltage,
            "current": self.current,
            "power_factor": self.power_factor,
            "frequency": self.frequency,
            "temperature": self.temperature,
            
            # Power Quality
            "thd_voltage": self.thd_voltage,
            "thd_current": self.thd_current,
            
            # Location & Zone
            "latitude": self.latitude,
            "longitude": self.longitude,
            "zone_id": self.grid_zone_id,
            
            # Battery & Environmental
            "battery_level": self.battery_level,
            "weather_condition": self.weather_condition,
            
            # Renewable Energy Certification
            "rec_eligible": self.rec_eligible,
            "carbon_offset": self.carbon_offset,
            "net_emission": self.net_emission,
        }
    
    def to_submission_payload(self) -> dict:
        """
        Default payload for API Gateway submission.
        Uses grid monitoring format for efficiency.
        For full telemetry, use to_full_telemetry_payload() explicitly.
        """
        return self.to_grid_monitoring_payload()

    class Config:
        json_encoders = {datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%SZ')}
