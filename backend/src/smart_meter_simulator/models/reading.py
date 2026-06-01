from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


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
    SOC = "soc"


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
    interval_seconds: int = Field(900, gt=0)  # Default to 15 mins

    # Battery Data (kWh)
    battery_level: float = Field(0.0, ge=0, le=1000000)  # Current energy in kWh

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

    # Industrial Metadata (Real World AMI)
    manufacturer_id: str = "GXT"
    logical_device_name: str = "LDN-00000000"

    # Advanced Grid & Security Metrics
    voltage_pu: Optional[float] = None
    norm_residual: Optional[float] = None
    ewma_residual: Optional[float] = None
    is_compromised: bool = False

    rec_eligible: bool = False
    carbon_offset: float = Field(0.0, ge=0)
    weather_condition: str = "Sunny"
    nodal_price: float = Field(0.50, ge=0)  # GXT/kWh
    carbon_intensity: float = Field(0.0, ge=0)  # g CO2/kWh

    # Security
    meter_signature: Optional[str] = None
    device_key: Optional[bytes] = Field(None, exclude=True) # Used for Protocol v4 encryption in transport layer

    def to_submission_payload(self) -> dict:
        """
        Convert to API Gateway submission format.
        Sends surplus energy for token minting plus full telemetry
        for dashboard, analytics, and grid health monitoring.
        """
        kwh_amount = max(0.0, self.surplus_energy)

        # Power telemetry (kW) — dynamically calculated from interval
        hours = self.interval_seconds / 3600.0
        power_gen = self.energy_generated / hours if hours > 0 else 0.0
        power_cons = self.energy_consumed / hours if hours > 0 else 0.0

        return {
            "kwh": round(kwh_amount, 6),  # Numeric for Rust Decimal deserialization
            "timestamp": self.timestamp.isoformat(),
            "meter_signature": self.meter_signature,
            "meter_serial": self.meter_id,
            "user_id": self.meter_id,
            "wallet_address": self.meter_id,
            "reading_id": f"{self.meter_id}-{self.sequence_number}",
            "interval_seconds": self.interval_seconds,
            # Energy telemetry (kWh)
            "energy_generated": round(self.energy_generated, 6),
            "energy_consumed": round(self.energy_consumed, 6),
            "surplus_energy": round(self.surplus_energy, 6),
            "deficit_energy": round(self.deficit_energy, 6),
            # Power telemetry (kW)
            "power_generated": round(power_gen, 3),
            "power_consumed": round(power_cons, 3),
            # Electrical parameters
            "voltage": round(self.voltage, 2) if self.voltage is not None else None,
            "current": round(self.current, 3) if self.current is not None else None,
            "reactive_power_kvar": round(self.reactive_power_kvar, 3)
            if self.reactive_power_kvar is not None
            else None,
            "power_factor": round(self.power_factor, 4)
            if self.power_factor is not None
            else None,
            "frequency": round(self.frequency, 3)
            if self.frequency is not None
            else None,
            "temperature": round(self.temperature, 1)
            if self.temperature is not None
            else None,
            # Battery & environmental
            "battery_level": round(self.battery_level, 1),
            "nodal_price": round(self.nodal_price, 3),
            "carbon_intensity": round(self.carbon_intensity, 1),
        }

    def generate_dlms_payload(self) -> bytes:
        """
        Generate an industrial DLMS/COSEM (IEC 62056) binary payload
        using the OBIS-coded DlmsEncoder.
        """
        from ..core.dlms import DlmsEncoder

        return DlmsEncoder.encode_reading(self)

    def generate_protocol_v4_payload(self, device_key: bytes) -> bytes:
        """
        Generate a Protocol v4 (UTT-S+) binary payload.
        """
        from ..core.protocol_v4 import ProtocolV4Encoder

        return ProtocolV4Encoder.encode(self, device_key)

    def get_v4_signature_canonical_string(self) -> str:
        """
        Generates the canonical string for Protocol v4 Hardware Signing.
        Format: "{meter_id}:{kwh}:{timestamp_ms}:{sequence}"
        """
        timestamp_ms = int(self.timestamp.timestamp() * 1000)
        kwh = max(0.0, self.surplus_energy)
        # Use 6 decimal places for kWh to match Rust Decimal expectations if needed, 
        # but spec says "canonical string", usually means a specific format.
        # Given to_submission_payload uses round(kwh, 6), I'll use that.
        return f"{self.meter_id}:{kwh:.6f}:{timestamp_ms}:{self.sequence_number}"
