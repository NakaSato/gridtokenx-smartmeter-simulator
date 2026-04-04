"""
PostGIS repository for Thai electrical distribution network.

Provides database access methods for:
- Spatial queries (nearest transformer, meters in radius)
- GeoJSON export
- Network topology loading
- Meter data persistence
"""

import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal

from sqlalchemy import text, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point, LineString

from .models import (
    Substation, Transformer, PowerLine, Meter, MeterReading,
    Zone, NetworkTopology, Base
)

logger = logging.getLogger(__name__)


class PostGISRepository:
    """
    Repository for Thai grid network data in PostGIS.
    
    Provides methods for:
    - CRUD operations on grid assets
    - Spatial queries (nearest neighbor, radius search)
    - GeoJSON export
    - Network topology loading for pandapower
    - Time-series meter data
    """
    
    def __init__(self, database_url: str):
        """
        Initialize PostGIS repository.
        
        Args:
            database_url: PostgreSQL connection URL with PostGIS
                Example: postgresql+asyncpg://user:pass@localhost:5432/gridtokenx
        """
        self.database_url = database_url
        
        # Create async engine
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        
        # Create session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Sync session for non-async operations
        self.sync_engine = self.engine.sync_engine
        self.sync_session_factory = sessionmaker(
            self.sync_engine,
            class_=Session,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        """Get async database session"""
        async with self.async_session_factory() as session:
            yield session
    
    def get_sync_session(self) -> Session:
        """Get sync database session"""
        with self.sync_session_factory() as session:
            yield session
    
    # =========================================================================
    # Substation Operations
    # =========================================================================
    
    async def get_substation(self, substation_id: int) -> Optional[Substation]:
        """Get substation by ID"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(Substation).where(Substation.id == substation_id)
            )
            return result.scalar_one_or_none()
    
    async def get_substation_by_code(self, code: str) -> Optional[Substation]:
        """Get substation by code"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(Substation).where(Substation.code == code)
            )
            return result.scalar_one_or_none()
    
    async def get_substations_by_voltage(
        self,
        voltage_level_kv: float,
        province: Optional[str] = None
    ) -> List[Substation]:
        """Get substations by voltage level"""
        async with self.async_session_factory() as session:
            query = select(Substation).where(
                Substation.voltage_level_kv == voltage_level_kv
            )
            
            if province:
                query = query.where(Substation.province == province)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def get_substations_in_bbox(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float
    ) -> List[Substation]:
        """Get substations within bounding box"""
        async with self.async_session_factory() as session:
            # Use ST_MakeEnvelope for spatial query
            query = text("""
                SELECT * FROM grid.substations
                WHERE ST_Intersects(
                    location,
                    ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
                )
            """)
            
            result = await session.execute(
                query,
                {"min_lon": min_lon, "min_lat": min_lat, "max_lon": max_lon, "max_lat": max_lat}
            )
            
            # Map to Substation objects
            substations = []
            for row in result.mappings():
                substation = Substation(**dict(row))
                substations.append(substation)
            
            return substations
    
    async def create_substation(
        self,
        name: str,
        voltage_level_kv: float,
        longitude: float,
        latitude: float,
        code: Optional[str] = None,
        operator: Optional[str] = None,
        type: Optional[str] = None,
        capacity_mva: Optional[float] = None,
        province: Optional[str] = None,
        **kwargs
    ) -> Substation:
        """Create new substation"""
        async with self.async_session_factory() as session:
            substation = Substation(
                name=name,
                voltage_level_kv=voltage_level_kv,
                code=code,
                operator=operator,
                type=type,
                capacity_mva=capacity_mva,
                province=province,
                **kwargs
            )
            substation.set_coordinates(longitude, latitude)
            
            session.add(substation)
            await session.commit()
            await session.refresh(substation)
            
            logger.info(f"Created substation: {substation.name} ({substation.code})")
            return substation
    
    # =========================================================================
    # Transformer Operations
    # =========================================================================
    
    async def get_transformer(self, transformer_id: int) -> Optional[Transformer]:
        """Get transformer by ID"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(Transformer).where(Transformer.id == transformer_id)
            )
            return result.scalar_one_or_none()
    
    async def get_transformers_by_substation(
        self,
        substation_id: int
    ) -> List[Transformer]:
        """Get transformers connected to substation"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(Transformer).where(
                    Transformer.substation_id == substation_id
                )
            )
            return list(result.scalars().all())
    
    async def find_nearest_transformer(
        self,
        longitude: float,
        latitude: float,
        max_distance_m: float = 500
    ) -> Optional[Dict[str, Any]]:
        """
        Find nearest transformer to a point.
        
        Uses PostGIS spatial function for efficient nearest-neighbor search.
        """
        async with self.async_session_factory() as session:
            query = text("""
                SELECT * FROM grid.find_nearest_transformer(
                    :longitude, :latitude, :max_distance
                )
            """)
            
            result = await session.execute(
                query,
                {
                    "longitude": longitude,
                    "latitude": latitude,
                    "max_distance": max_distance_m
                }
            )
            
            row = result.first()
            if row:
                return {
                    "transformer_id": row.transformer_id,
                    "code": row.code,
                    "distance_m": float(row.distance_m),
                    "capacity_kva": float(row.capacity_kva) if row.capacity_kva else None
                }
            
            return None
    
    async def create_transformer(
        self,
        longitude: float,
        latitude: float,
        voltage_primary_kv: float = 22.0,
        voltage_secondary_kv: float = 0.4,
        capacity_kva: Optional[float] = None,
        substation_id: Optional[int] = None,
        code: Optional[str] = None,
        **kwargs
    ) -> Transformer:
        """Create new transformer"""
        async with self.async_session_factory() as session:
            transformer = Transformer(
                voltage_primary_kv=voltage_primary_kv,
                voltage_secondary_kv=voltage_secondary_kv,
                capacity_kva=capacity_kva,
                substation_id=substation_id,
                code=code,
                **kwargs
            )
            transformer.set_coordinates(longitude, latitude)
            
            session.add(transformer)
            await session.commit()
            await session.refresh(transformer)
            
            logger.info(f"Created transformer: {transformer.code}")
            return transformer
    
    # =========================================================================
    # Power Line Operations
    # =========================================================================
    
    async def get_power_line(self, line_id: int) -> Optional[PowerLine]:
        """Get power line by ID"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(PowerLine).where(PowerLine.id == line_id)
            )
            return result.scalar_one_or_none()
    
    async def get_power_lines_by_voltage(
        self,
        voltage_level_kv: float
    ) -> List[PowerLine]:
        """Get power lines by voltage level"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(PowerLine).where(
                    PowerLine.voltage_level_kv == voltage_level_kv
                )
            )
            return list(result.scalars().all())
    
    async def create_power_line(
        self,
        voltage_level_kv: float,
        coordinates: List[Tuple[float, float]],
        from_substation_id: Optional[int] = None,
        to_substation_id: Optional[int] = None,
        code: Optional[str] = None,
        line_type: str = "overhead",
        conductor_type: Optional[str] = None,
        **kwargs
    ) -> PowerLine:
        """
        Create new power line.
        
        Args:
            voltage_level_kv: Line voltage in kV
            coordinates: List of (longitude, latitude) tuples
            from_substation_id: Starting substation ID
            to_substation_id: Ending substation ID
            code: Unique line code
            line_type: overhead, underground, or submarine
        """
        async with self.async_session_factory() as session:
            # Create LineString geometry
            line_string = LineString(coordinates)
            geom = from_shape(line_string, srid=4326)
            
            power_line = PowerLine(
                voltage_level_kv=voltage_level_kv,
                geom=geom,
                from_substation_id=from_substation_id,
                to_substation_id=to_substation_id,
                code=code,
                line_type=line_type,
                conductor_type=conductor_type,
                **kwargs
            )
            
            session.add(power_line)
            await session.commit()
            await session.refresh(power_line)
            
            logger.info(f"Created power line: {power_line.code}")
            return power_line
    
    # =========================================================================
    # Meter Operations
    # =========================================================================
    
    async def get_meter(self, meter_id: str) -> Optional[Meter]:
        """Get meter by meter_id"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(Meter).where(Meter.meter_id == meter_id)
            )
            return result.scalar_one_or_none()
    
    async def get_meters_by_transformer(
        self,
        transformer_id: int
    ) -> List[Meter]:
        """Get meters connected to transformer"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(Meter).where(Meter.transformer_id == transformer_id)
            )
            return list(result.scalars().all())
    
    async def get_meters_in_radius(
        self,
        longitude: float,
        latitude: float,
        radius_m: float = 1000,
        meter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get meters within radius of a point.
        
        Uses PostGIS spatial function for efficient radius search.
        """
        async with self.async_session_factory() as session:
            query = text("""
                SELECT * FROM grid.get_meters_in_radius(
                    :longitude, :latitude, :radius, :meter_type
                )
            """)
            
            result = await session.execute(
                query,
                {
                    "longitude": longitude,
                    "latitude": latitude,
                    "radius": radius_m,
                    "meter_type": meter_type
                }
            )
            
            meters = []
            for row in result.mappings():
                meters.append({
                    "meter_id": row.meter_id,
                    "meter_type": row.meter_type,
                    "distance_m": float(row.distance_m),
                    "location": row.location
                })
            
            return meters
    
    async def create_meter(
        self,
        meter_id: str,
        meter_type: str,
        longitude: float,
        latitude: float,
        transformer_id: Optional[int] = None,
        serial_number: Optional[str] = None,
        accuracy_class: Optional[str] = None,
        public_key: Optional[str] = None,
        **kwargs
    ) -> Meter:
        """Create new smart meter"""
        async with self.async_session_factory() as session:
            meter = Meter(
                meter_id=meter_id,
                meter_type=meter_type,
                transformer_id=transformer_id,
                serial_number=serial_number,
                accuracy_class=accuracy_class,
                public_key=public_key,
                **kwargs
            )
            meter.set_coordinates(longitude, latitude)
            
            session.add(meter)
            await session.commit()
            await session.refresh(meter)
            
            logger.info(f"Created meter: {meter.meter_id}")
            return meter
    
    async def store_reading(
        self,
        meter_id: str,
        timestamp: datetime,
        energy_generated_kwh: float,
        energy_consumed_kwh: float,
        voltage_v: Optional[float] = None,
        current_a: Optional[float] = None,
        frequency_hz: Optional[float] = None,
        signature: Optional[str] = None,
        **kwargs
    ) -> MeterReading:
        """Store meter reading"""
        async with self.async_session_factory() as session:
            reading = MeterReading(
                meter_id=meter_id,
                timestamp=timestamp,
                energy_generated_kwh=energy_generated_kwh,
                energy_consumed_kwh=energy_consumed_kwh,
                voltage_v=voltage_v,
                current_a=current_a,
                frequency_hz=frequency_hz,
                signature=signature,
                **kwargs
            )
            
            session.add(reading)
            await session.commit()
            
            return reading
    
    # =========================================================================
    # GeoJSON Export
    # =========================================================================
    
    async def export_network_geojson(
        self,
        voltage_min: float = 0,
        voltage_max: float = 500
    ) -> Dict[str, Any]:
        """
        Export network as GeoJSON FeatureCollection.
        
        Uses PostgreSQL function for efficient export.
        """
        async with self.async_session_factory() as session:
            query = text("""
                SELECT grid.export_network_geojson(:voltage_min, :voltage_max) as geojson
            """)
            
            result = await session.execute(
                query,
                {"voltage_min": voltage_min, "voltage_max": voltage_max}
            )
            
            row = result.first()
            if row and row.geojson:
                return row.geojson
            
            # Fallback: manual export
            return await self._export_geojson_manual(voltage_min, voltage_max)
    
    async def _export_geojson_manual(
        self,
        voltage_min: float,
        voltage_max: float
    ) -> Dict[str, Any]:
        """Manual GeoJSON export if PostgreSQL function unavailable"""
        async with self.async_session_factory() as session:
            features = []
            
            # Export substations
            result = await session.execute(
                select(Substation).where(
                    and_(
                        Substation.voltage_level_kv >= voltage_min,
                        Substation.voltage_level_kv <= voltage_max
                    )
                )
            )
            
            for substation in result.scalars().all():
                lon, lat = substation.get_coordinates()
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "type": "substation",
                        "name": substation.name,
                        "code": substation.code,
                        "voltage_level_kv": float(substation.voltage_level_kv),
                        "operator": substation.operator,
                        "capacity_mva": float(substation.capacity_mva) if substation.capacity_mva else None,
                        "status": substation.status
                    }
                })
            
            # Export power lines
            result = await session.execute(
                select(PowerLine).where(
                    and_(
                        PowerLine.voltage_level_kv >= voltage_min,
                        PowerLine.voltage_level_kv <= voltage_max
                    )
                )
            )
            
            for line in result.scalars().all():
                coords = line.get_coordinates()
                if coords:
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coords
                        },
                        "properties": {
                            "type": "line",
                            "name": line.name,
                            "code": line.code,
                            "voltage_level_kv": float(line.voltage_level_kv),
                            "line_type": line.line_type,
                            "length_km": float(line.length_km) if line.length_km else None,
                            "conductor_type": line.conductor_type,
                            "status": line.status
                        }
                    })
            
            # Export transformers
            result = await session.execute(select(Transformer))
            
            for transformer in result.scalars().all():
                lon, lat = transformer.get_coordinates()
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "type": "transformer",
                        "name": transformer.name,
                        "code": transformer.code,
                        "voltage_primary_kv": float(transformer.voltage_primary_kv),
                        "voltage_secondary_kv": float(transformer.voltage_secondary_kv),
                        "capacity_kva": float(transformer.capacity_kva) if transformer.capacity_kva else None,
                        "status": transformer.status
                    }
                })
            
            return {
                "type": "FeatureCollection",
                "features": features
            }
    
    # =========================================================================
    # Network Statistics
    # =========================================================================
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        async with self.async_session_factory() as session:
            # Count by voltage level
            query = text("""
                SELECT voltage_level_kv, COUNT(*) as count
                FROM grid.substations
                GROUP BY voltage_level_kv
                ORDER BY voltage_level_kv DESC
            """)
            
            result = await session.execute(query)
            substations_by_voltage = {
                float(row.voltage_level_kv): row.count
                for row in result.mappings()
            }
            
            # Total line length
            query = text("""
                SELECT voltage_level_kv,
                       SUM(ST_Length(geom::geography) / 1000) as length_km
                FROM grid.power_lines
                GROUP BY voltage_level_kv
            """)
            
            result = await session.execute(query)
            lines_by_voltage = {
                float(row.voltage_level_kv): float(row.length_km)
                for row in result.mappings()
            }
            
            # Meter counts by type
            query = text("""
                SELECT meter_type, COUNT(*) as count
                FROM grid.meters
                GROUP BY meter_type
            """)
            
            result = await session.execute(query)
            meters_by_type = {
                row.meter_type: row.count
                for row in result.mappings()
            }
            
            return {
                "substations_by_voltage": substations_by_voltage,
                "lines_by_voltage_km": lines_by_voltage,
                "meters_by_type": meters_by_type,
                "total_substations": sum(substations_by_voltage.values()),
                "total_lines_km": sum(lines_by_voltage.values()),
                "total_meters": sum(meters_by_type.values())
            }
    
    # =========================================================================
    # Database Management
    # =========================================================================
    
    async def create_tables(self):
        """Create all tables (for development/testing)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """Drop all tables (for development/testing)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")
    
    async def check_connection(self) -> bool:
        """Check database connection"""
        try:
            async with self.async_session_factory() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    async def get_postgis_version(self) -> Optional[str]:
        """Get PostGIS version"""
        async with self.async_session_factory() as session:
            result = await session.execute(text("SELECT PostGIS_Version()"))
            row = result.first()
            return row[0] if row else None
