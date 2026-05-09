"""
SQLAlchemy ORM models for Thai electrical distribution network (Simplified - No GeoAlchemy2).
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date, Text,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    PrimaryKeyConstraint, text
)
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class Substation(Base):
    """High/Medium voltage substations (EGAT, MEA, PEA)"""
    
    __tablename__ = 'substations'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    voltage_level_kv: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    operator: Mapped[Optional[str]] = mapped_column(String(100))
    type: Mapped[Optional[str]] = mapped_column(String(50))
    capacity_mva: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    status: Mapped[Optional[str]] = mapped_column(String(20), default='in_service')
    
    # Replaced spatial column with plain numeric
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    
    # Address fields
    address: Mapped[Optional[str]] = mapped_column(Text)
    province: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    subdistrict: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    power_lines_from: Mapped[List["PowerLine"]] = relationship(
        "PowerLine", foreign_keys="PowerLine.from_substation_id", back_populates="from_substation"
    )
    power_lines_to: Mapped[List["PowerLine"]] = relationship(
        "PowerLine", foreign_keys="PowerLine.to_substation_id", back_populates="to_substation"
    )
    transformers: Mapped[List["Transformer"]] = relationship("Transformer", back_populates="substation")
    
    def get_coordinates(self) -> tuple[float, float]:
        return (float(self.longitude), float(self.latitude))
    
    def set_coordinates(self, longitude: float, latitude: float):
        self.longitude = longitude
        self.latitude = latitude
    
    def __repr__(self):
        return f"<Substation(id={self.id}, name='{self.name}', voltage={self.voltage_level_kv}kV)>"


class Transformer(Base):
    """Distribution transformers (MV/LV)"""
    
    __tablename__ = 'transformers'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    substation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('grid.substations.id'), nullable=True
    )
    
    voltage_primary_kv: Mapped[Decimal] = mapped_column(Numeric(6, 1), default=22.0)
    voltage_secondary_kv: Mapped[Decimal] = mapped_column(Numeric(6, 1), default=0.4)
    capacity_kva: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    
    status: Mapped[Optional[str]] = mapped_column(String(20), default='in_service')
    pole_number: Mapped[Optional[str]] = mapped_column(String(50))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    substation: Mapped[Optional["Substation"]] = relationship(
        "Substation", foreign_keys=[substation_id], back_populates="transformers"
    )
    meters: Mapped[List["Meter"]] = relationship("Meter", back_populates="transformer")
    
    def get_coordinates(self) -> tuple[float, float]:
        return (float(self.longitude), float(self.latitude))
    
    def set_coordinates(self, longitude: float, latitude: float):
        self.longitude = longitude
        self.latitude = latitude
    
    def __repr__(self):
        return f"<Transformer(id={self.id}, code='{self.code}', capacity={self.capacity_kva}kVA)>"


class PowerLine(Base):
    """Transmission and distribution power lines"""
    
    __tablename__ = 'power_lines'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    
    from_substation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('grid.substations.id'), nullable=True
    )
    to_substation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('grid.substations.id'), nullable=True
    )
    
    voltage_level_kv: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    line_type: Mapped[Optional[str]] = mapped_column(String(50))
    length_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Path stored as JSON instead of Geometry LineString
    path_json: Mapped[Optional[Dict]] = mapped_column(JSONB)
    
    status: Mapped[Optional[str]] = mapped_column(String(20), default='in_service')
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    from_substation: Mapped[Optional["Substation"]] = relationship(
        "Substation", foreign_keys=[from_substation_id], back_populates="power_lines_from"
    )
    to_substation: Mapped[Optional["Substation"]] = relationship(
        "Substation", foreign_keys=[to_substation_id], back_populates="power_lines_to"
    )
    
    def __repr__(self):
        return f"<PowerLine(id={self.id}, code='{self.code}', voltage={self.voltage_level_kv}kV)>"


class Meter(Base):
    """Smart meters (AMI) connected to the grid"""
    
    __tablename__ = 'meters'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meter_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    
    meter_type: Mapped[Optional[str]] = mapped_column(String(50))
    transformer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('grid.transformers.id'), nullable=True
    )
    
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    
    province: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    
    status: Mapped[Optional[str]] = mapped_column(String(20), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transformer: Mapped[Optional["Transformer"]] = relationship(
        "Transformer", back_populates="meters"
    )
    readings: Mapped[List["MeterReading"]] = relationship(
        "MeterReading", back_populates="meter", cascade="all, delete-orphan"
    )
    
    def get_coordinates(self) -> tuple[float, float]:
        return (float(self.longitude), float(self.latitude))
    
    def set_coordinates(self, longitude: float, latitude: float):
        self.longitude = longitude
        self.latitude = latitude
    
    def __repr__(self):
        return f"<Meter(meter_id='{self.meter_id}', type='{self.meter_type}')>"


class MeterReading(Base):
    """Time-series meter readings"""
    
    __tablename__ = 'meter_readings'
    __table_args__ = (
        Index('idx_meter_readings_meter_ts', 'meter_id', 'timestamp', postgresql_using='btree'),
        {'schema': 'grid'}
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meter_id: Mapped[str] = mapped_column(
        String(100), ForeignKey('grid.meters.meter_id'), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    energy_generated_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    energy_consumed_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    battery_level_kwh: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    
    voltage_v: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    current_a: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    meter: Mapped["Meter"] = relationship("Meter", back_populates="readings")
    
    def __repr__(self):
        return f"<MeterReading(meter_id='{self.meter_id}', timestamp={self.timestamp})>"


class PowerPlant(Base):
    """Real-world power plants"""

    __tablename__ = 'power_plants'
    __table_args__ = {'schema': 'grid'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    plant_type: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity_mw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='operating')
    operator: Mapped[Optional[str]] = mapped_column(String(255), default='EGAT')
    province: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_coordinates(self) -> tuple[float, float]:
        return (float(self.longitude), float(self.latitude))

    def set_coordinates(self, longitude: float, latitude: float):
        self.longitude = longitude
        self.latitude = latitude

    def __repr__(self):
        return f"<PowerPlant(plant_id='{self.plant_id}', name='{self.name}', capacity={self.capacity_mw}MW)>"



# ============================================================================
# Helper functions
# ============================================================================

def point_to_geojson(longitude: float, latitude: float) -> dict:
    """Convert coordinates to GeoJSON Point"""
    return {
        "type": "Point",
        "coordinates": [longitude, latitude]
    }


def linestring_to_geojson(coordinates: List[tuple[float, float]]) -> dict:
    """Convert coordinate list to GeoJSON LineString"""
    return {
        "type": "LineString",
        "coordinates": [[lon, lat] for lon, lat in coordinates]
    }


def polygon_to_geojson(coordinates: List[List[tuple[float, float]]]) -> dict:
    """Convert nested coordinate list to GeoJSON Polygon"""
    return {
        "type": "Polygon",
        "coordinates": [[[lon, lat] for lon, lat in ring] for ring in coordinates]
    }
