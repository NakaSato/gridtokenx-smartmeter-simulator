"""
SQLAlchemy ORM models for Thai electrical distribution network with PostGIS support.

These models provide database access for:
- Substations (EGAT, MEA, PEA)
- Distribution transformers
- Power lines (transmission & distribution)
- Smart meters (AMI)
- Meter readings (time-series)
- Geographic zones
- Network topology
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date, Text,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    PrimaryKeyConstraint, text
)
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geography, Geometry
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point, LineString, Polygon

Base = declarative_base()


class Substation(Base):
    """High/Medium voltage substations (EGAT, MEA, PEA)"""
    
    __tablename__ = 'substations'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    voltage_level_kv: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    operator: Mapped[Optional[str]] = mapped_column(String(100))  # EGAT, MEA, PEA
    type: Mapped[Optional[str]] = mapped_column(String(50))  # transmission, sub_transmission, distribution
    capacity_mva: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    status: Mapped[Optional[str]] = mapped_column(String(20), default='in_service')
    
    # Spatial column (PostGIS)
    location: Mapped[Geography] = mapped_column(Geography('POINT', srid=4326), nullable=False)

    # Generated columns (read-only, computed by database)
    latitude: Mapped[Optional[float]] = mapped_column(
        Numeric,
        insert_default=text("ST_Y(location::geometry)"),
        insert_sentinel=False
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Numeric,
        insert_default=text("ST_X(location::geometry)"),
        insert_sentinel=False
    )
    
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
        """Get (longitude, latitude) tuple from geography column"""
        shape = to_shape(self.location)
        return (shape.x, shape.y)
    
    def set_coordinates(self, longitude: float, latitude: float):
        """Set location from coordinates"""
        point = Point(longitude, latitude)
        self.location = from_shape(point, srid=4326)
    
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
    
    # Electrical parameters
    voltage_primary_kv: Mapped[Decimal] = mapped_column(Numeric(6, 1), default=22.0)
    voltage_secondary_kv: Mapped[Decimal] = mapped_column(Numeric(6, 1), default=0.4)
    capacity_kva: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    phase_count: Mapped[Optional[int]] = mapped_column(Integer, default=3)
    
    # Technical details
    cooling_type: Mapped[Optional[str]] = mapped_column(String(50))  # ONAN, ONAF, etc.
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    serial_number: Mapped[Optional[str]] = mapped_column(String(100))
    installation_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(20), default='in_service')
    
    # Spatial column
    location: Mapped[Geography] = mapped_column(Geography('POINT', srid=4326), nullable=False)
    
    # Generated columns
    
    # Pole information
    pole_number: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    substation: Mapped[Optional["Substation"]] = relationship(
        "Substation", foreign_keys=[substation_id], back_populates="transformers"
    )
    meters: Mapped[List["Meter"]] = relationship("Meter", back_populates="transformer")
    
    def get_coordinates(self) -> tuple[float, float]:
        """Get (longitude, latitude) tuple"""
        shape = to_shape(self.location)
        return (shape.x, shape.y)
    
    def set_coordinates(self, longitude: float, latitude: float):
        """Set location from coordinates"""
        point = Point(longitude, latitude)
        self.location = from_shape(point, srid=4326)
    
    def __repr__(self):
        return f"<Transformer(id={self.id}, code='{self.code}', capacity={self.capacity_kva}kVA)>"


class PowerLine(Base):
    """Transmission and distribution power lines"""
    
    __tablename__ = 'power_lines'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    
    # Connections
    from_substation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('grid.substations.id'), nullable=True
    )
    to_substation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('grid.substations.id'), nullable=True
    )
    
    # Electrical parameters
    voltage_level_kv: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    line_type: Mapped[Optional[str]] = mapped_column(String(50))  # overhead, underground, submarine
    circuit_count: Mapped[Optional[int]] = mapped_column(Integer, default=1)
    
    # Conductor details
    conductor_type: Mapped[Optional[str]] = mapped_column(String(100))
    conductor_material: Mapped[Optional[str]] = mapped_column(String(50))  # AAC, AAAC, ACSR, Copper
    cross_section_mm2: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Length (generated from geometry)
    length_km: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), insert_default=text("ST_Length(geom::geography) / 1000")
    )
    
    # Impedance parameters
    resistance_ohm_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    reactance_ohm_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    capacitance_nf_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    ampacity_a: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(20), default='in_service')
    construction_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Spatial column
    geom: Mapped[Geography] = mapped_column(Geography('LINESTRING', srid=4326), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    from_substation: Mapped[Optional["Substation"]] = relationship(
        "Substation", foreign_keys=[from_substation_id], back_populates="power_lines_from"
    )
    to_substation: Mapped[Optional["Substation"]] = relationship(
        "Substation", foreign_keys=[to_substation_id], back_populates="power_lines_to"
    )
    
    def get_length_km(self) -> float:
        """Calculate line length in km"""
        shape = to_shape(self.geom)
        # For LineString, calculate length using PostGIS function via SQL
        return shape.length  # Approximate, use SQL for accurate calculation
    
    def get_coordinates(self) -> List[tuple[float, float]]:
        """Get list of (longitude, latitude) tuples"""
        shape = to_shape(self.geom)
        if isinstance(shape, LineString):
            return list(shape.coords)
        return []
    
    def __repr__(self):
        return f"<PowerLine(id={self.id}, code='{self.code}', voltage={self.voltage_level_kv}kV)>"


class Meter(Base):
    """Smart meters (AMI) connected to the grid"""
    
    __tablename__ = 'meters'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meter_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    
    # Meter type
    meter_type: Mapped[Optional[str]] = mapped_column(String(50))
    # solar_prosumer, grid_consumer, hybrid, battery, ev_charger
    accuracy_class: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Connection
    transformer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('grid.transformers.id'), nullable=True
    )
    
    # Electrical ratings
    phase_count: Mapped[Optional[int]] = mapped_column(Integer, default=1)
    rated_current_a: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    rated_voltage_v: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=230)
    
    # Communication
    communication_type: Mapped[Optional[str]] = mapped_column(String(50))  # WiFi, LoRaWAN, NB-IoT, PLC
    
    # Security
    public_key: Mapped[Optional[str]] = mapped_column(Text)  # Ed25519 public key
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(20), default='active')
    
    # Spatial column
    location: Mapped[Geography] = mapped_column(Geography('POINT', srid=4326), nullable=False)
    
    # Generated columns
    
    # Address
    address: Mapped[Optional[str]] = mapped_column(Text)
    province: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Customer information
    customer_id: Mapped[Optional[str]] = mapped_column(String(100))
    customer_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Installation
    installation_date: Mapped[Optional[date]] = mapped_column(Date)
    last_reading_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transformer: Mapped[Optional["Transformer"]] = relationship(
        "Transformer", back_populates="meters"
    )
    readings: Mapped[List["MeterReading"]] = relationship(
        "MeterReading", back_populates="meter", cascade="all, delete-orphan"
    )
    
    def get_coordinates(self) -> tuple[float, float]:
        """Get (longitude, latitude) tuple"""
        shape = to_shape(self.location)
        return (shape.x, shape.y)
    
    def set_coordinates(self, longitude: float, latitude: float):
        """Set location from coordinates"""
        point = Point(longitude, latitude)
        self.location = from_shape(point, srid=4326)
    
    def __repr__(self):
        return f"<Meter(meter_id='{self.meter_id}', type='{self.meter_type}')>"


class MeterReading(Base):
    """Time-series meter readings (partitioned by date)"""
    
    __tablename__ = 'meter_readings'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meter_id: Mapped[str] = mapped_column(
        String(100), ForeignKey('grid.meters.meter_id'), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Energy measurements
    energy_generated_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    energy_consumed_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    battery_level_kwh: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    
    # Electrical measurements
    voltage_v: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    current_a: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    frequency_hz: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    power_factor: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    active_power_kw: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    reactive_power_kvar: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    
    # Security
    signature: Mapped[Optional[str]] = mapped_column(Text)  # Ed25519 signature
    
    # Data quality
    quality_flag: Mapped[Optional[str]] = mapped_column(String(20))  # valid, estimated, invalid
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meter: Mapped["Meter"] = relationship("Meter", back_populates="readings")
    
    __table_args__ = (
        Index('idx_meter_readings_meter_ts', 'meter_id', 'timestamp', postgresql_using='btree'),
        {'schema': 'grid'}
    )
    
    def __repr__(self):
        return f"<MeterReading(meter_id='{self.meter_id}', timestamp={self.timestamp})>"


class Zone(Base):
    """Geographic zones (MEA/PEA service areas)"""
    
    __tablename__ = 'zones'
    __table_args__ = {'schema': 'grid'}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    zone_type: Mapped[Optional[str]] = mapped_column(String(50))  # mea_area, pea_area, province, district
    operator: Mapped[Optional[str]] = mapped_column(String(100))  # MEA, PEA
    
    # Area (generated from geometry)
    area_km2: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), insert_default=text("ST_Area(geom::geography) / 1000000")
    )
    
    # Spatial column
    geom: Mapped[Geography] = mapped_column(Geography('POLYGON', srid=4326), nullable=False)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def get_area_km2(self) -> float:
        """Calculate area in km²"""
        shape = to_shape(self.geom)
        if isinstance(shape, Polygon):
            return shape.area  # Approximate, use SQL for accurate calculation
        return 0.0
    
    def __repr__(self):
        return f"<Zone(id={self.id}, name='{self.name}', type='{self.zone_type}')>"


class NetworkTopology(Base):
    """Graph representation for power flow analysis"""

    __tablename__ = 'network_topology'
    __table_args__ = {'schema': 'grid'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_node_id: Mapped[int] = mapped_column(Integer, nullable=False)
    to_node_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Component references
    line_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('grid.power_lines.id'), nullable=True
    )
    transformer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('grid.transformers.id'), nullable=True
    )

    # Impedance
    impedance_r: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))  # Resistance (ohm)
    impedance_x: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))  # Reactance (ohm)
    impedance_z: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 6), insert_default=text("SQRT(impedance_r^2 + impedance_x^2)")
    )

    # Status
    status: Mapped[Optional[str]] = mapped_column(String(20), default='closed')
    switch_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NetworkTopology(from={self.from_node_id}, to={self.to_node_id})>"


class PowerPlant(Base):
    """Real-world power plants (hydro, solar, wind, oil/gas, coal, biomass)"""

    __tablename__ = 'power_plants'
    __table_args__ = {'schema': 'grid'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    name_th: Mapped[Optional[str]] = mapped_column(String(500))  # Thai name

    # Plant classification
    plant_type: Mapped[str] = mapped_column(String(50), nullable=False)  # hydropower, solar, wind, oil/gas, coal, bioenergy
    fuel_type: Mapped[Optional[str]] = mapped_column(String(100))  # natural_gas, lignite, etc.
    technology: Mapped[Optional[str]] = mapped_column(String(100))  # combined_cycle, PV, CFB, etc.

    # Electrical specs
    capacity_mw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    units: Mapped[Optional[int]] = mapped_column(Integer, default=1)

    # Operational status
    status: Mapped[Optional[str]] = mapped_column(String(50), default='operating')
    start_year: Mapped[Optional[int]] = mapped_column(Integer)
    operator: Mapped[Optional[str]] = mapped_column(String(255), default='EGAT')

    # Location
    location: Mapped[Geography] = mapped_column(Geography('POINT', srid=4326), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(
        Numeric,
        insert_default=text("ST_Y(location::geometry)"),
        insert_sentinel=False
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Numeric,
        insert_default=text("ST_X(location::geometry)"),
        insert_sentinel=False
    )
    province: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(50))  # bangkok, central, north, northeast, south, east
    location_accuracy: Mapped[Optional[str]] = mapped_column(String(50), default='exact')

    # Grid integration
    voltage_level_kv: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1))
    grid_connection_type: Mapped[Optional[str]] = mapped_column(String(50))  # transmission, distribution

    # Environmental
    carbon_intensity_gco2_kwh: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Metadata
    source: Mapped[Optional[str]] = mapped_column(String(255), default='OpenStreetMap/Global Power Plant Tracker')
    osm_id: Mapped[Optional[int]] = mapped_column(Integer)
    imported_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_coordinates(self) -> tuple[float, float]:
        """Get (longitude, latitude) tuple"""
        shape = to_shape(self.location)
        return (shape.x, shape.y)

    def set_coordinates(self, longitude: float, latitude: float):
        """Set location from coordinates"""
        point = Point(longitude, latitude)
        self.location = from_shape(point, srid=4326)

    @property
    def is_renewable(self) -> bool:
        """Check if plant is renewable"""
        return self.plant_type in ('hydropower', 'solar', 'wind', 'bioenergy', 'geothermal')

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
