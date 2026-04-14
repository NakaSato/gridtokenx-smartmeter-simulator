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
    Zone, NetworkTopology, PowerPlant, Base
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

    async def get_all_meters(
        self,
        limit: int = 1000,
        meter_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all meters with optional filters"""
        async with self.async_session_factory() as session:
            from sqlalchemy import select
            
            stmt = select(Meter)
            if meter_type:
                stmt = stmt.where(Meter.meter_type == meter_type)
            if status:
                stmt = stmt.where(Meter.status == status)
            stmt = stmt.limit(limit)
            
            result = await session.execute(stmt)
            meters = result.scalars().all()
            
            out = []
            for m in meters:
                lon, lat = m.get_coordinates()
                out.append({
                    "meter_id": m.meter_id,
                    "meter_type": m.meter_type,
                    "accuracy_class": m.accuracy_class,
                    "status": m.status,
                    "latitude": lat,
                    "longitude": lon,
                    "province": m.province,
                    "district": m.district,
                    "rated_voltage_v": float(m.rated_voltage_v) if m.rated_voltage_v else None,
                    "phase_count": m.phase_count,
                })
            return out

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

    # =========================================================================
    # Power Plants
    # =========================================================================

    async def create_power_plant(self, plant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new power plant record.

        Args:
            plant_data: Dictionary with plant fields including 'latitude', 'longitude'

        Returns:
            Created plant data with ID
        """
        async with self.async_session_factory() as session:
            try:
                plant = PowerPlant(
                    plant_id=plant_data['plant_id'],
                    name=plant_data['name'],
                    name_th=plant_data.get('name_th'),
                    plant_type=plant_data['plant_type'],
                    fuel_type=plant_data.get('fuel_type'),
                    technology=plant_data.get('technology'),
                    capacity_mw=plant_data['capacity_mw'],
                    units=plant_data.get('units', 1),
                    status=plant_data.get('status', 'operating'),
                    start_year=plant_data.get('start_year'),
                    operator=plant_data.get('operator', 'EGAT'),
                    province=plant_data.get('province'),
                    region=plant_data.get('region'),
                    location_accuracy=plant_data.get('location_accuracy', 'exact'),
                    voltage_level_kv=plant_data.get('voltage_level_kv'),
                    grid_connection_type=plant_data.get('grid_connection_type'),
                    carbon_intensity_gco2_kwh=plant_data.get('carbon_intensity_gco2_kwh'),
                    source=plant_data.get('source', 'GeoJSON Import'),
                    osm_id=plant_data.get('osm_id'),
                )

                # Set location from coordinates
                plant.set_coordinates(
                    plant_data['longitude'],
                    plant_data['latitude']
                )

                session.add(plant)
                await session.commit()
                await session.refresh(plant)

                return {
                    'id': plant.id,
                    'plant_id': plant.plant_id,
                    'name': plant.name,
                    'plant_type': plant.plant_type,
                    'capacity_mw': float(plant.capacity_mw),
                    'status': plant.status,
                    'latitude': float(plant.latitude) if plant.latitude else plant_data['latitude'],
                    'longitude': float(plant.longitude) if plant.longitude else plant_data['longitude'],
                }
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create power plant: {e}")
                raise

    async def create_power_plants_batch(self, plants_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple power plants in a batch.

        Args:
            plants_data: List of plant data dictionaries

        Returns:
            Summary with created count and errors
        """
        created = 0
        errors = []

        async with self.async_session_factory() as session:
            for idx, plant_data in enumerate(plants_data):
                try:
                    plant = PowerPlant(
                        plant_id=plant_data['plant_id'],
                        name=plant_data['name'],
                        name_th=plant_data.get('name_th'),
                        plant_type=plant_data['plant_type'],
                        fuel_type=plant_data.get('fuel_type'),
                        technology=plant_data.get('technology'),
                        capacity_mw=plant_data['capacity_mw'],
                        units=plant_data.get('units', 1),
                        status=plant_data.get('status', 'operating'),
                        start_year=plant_data.get('start_year'),
                        operator=plant_data.get('operator', 'EGAT'),
                        province=plant_data.get('province'),
                        region=plant_data.get('region'),
                        location_accuracy=plant_data.get('location_accuracy', 'exact'),
                        voltage_level_kv=plant_data.get('voltage_level_kv'),
                        grid_connection_type=plant_data.get('grid_connection_type'),
                        carbon_intensity_gco2_kwh=plant_data.get('carbon_intensity_gco2_kwh'),
                        source=plant_data.get('source', 'GeoJSON Import'),
                        osm_id=plant_data.get('osm_id'),
                    )

                    plant.set_coordinates(
                        plant_data['longitude'],
                        plant_data['latitude']
                    )

                    session.add(plant)
                    created += 1
                except Exception as e:
                    error_msg = f"Plant {idx} ({plant_data.get('name', 'unknown')}): {str(e)}"
                    errors.append(error_msg)
                    logger.warning(f"Skipping {error_msg}")

            try:
                await session.commit()
                logger.info(f"Batch import complete: {created} plants created, {len(errors)} errors")
            except Exception as e:
                await session.rollback()
                logger.error(f"Batch import failed: {e}")
                raise

        return {
            'created': created,
            'errors': len(errors),
            'error_details': errors[:10]  # Limit error details
        }

    async def get_power_plant(self, plant_id: str) -> Optional[Dict[str, Any]]:
        """Get a single power plant by ID"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(PowerPlant).where(PowerPlant.plant_id == plant_id)
            )
            plant = result.scalar_one_or_none()

            if not plant:
                return None

            return {
                'id': plant.id,
                'plant_id': plant.plant_id,
                'name': plant.name,
                'name_th': plant.name_th,
                'plant_type': plant.plant_type,
                'fuel_type': plant.fuel_type,
                'technology': plant.technology,
                'capacity_mw': float(plant.capacity_mw),
                'units': plant.units,
                'status': plant.status,
                'start_year': plant.start_year,
                'operator': plant.operator,
                'latitude': float(plant.latitude) if plant.latitude else None,
                'longitude': float(plant.longitude) if plant.longitude else None,
                'province': plant.province,
                'region': plant.region,
                'voltage_level_kv': float(plant.voltage_level_kv) if plant.voltage_level_kv else None,
                'grid_connection_type': plant.grid_connection_type,
                'is_renewable': plant.is_renewable,
                'carbon_intensity_gco2_kwh': float(plant.carbon_intensity_gco2_kwh) if plant.carbon_intensity_gco2_kwh else None,
                'source': plant.source,
                'created_at': plant.created_at.isoformat() if plant.created_at else None,
            }

    async def get_power_plants(
        self,
        plant_type: Optional[str] = None,
        status: Optional[str] = None,
        region: Optional[str] = None,
        operator: Optional[str] = None,
        renewable_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Query power plants with filters.

        Returns:
            Tuple of (plants list, total count)
        """
        async with self.async_session_factory() as session:
            # Build query
            query = select(PowerPlant)

            if plant_type:
                query = query.where(PowerPlant.plant_type == plant_type)
            if status:
                query = query.where(PowerPlant.status == status)
            if region:
                query = query.where(PowerPlant.region == region)
            if operator:
                query = query.where(PowerPlant.operator == operator)
            if renewable_only:
                query = query.where(
                    PowerPlant.plant_type.in_(['hydropower', 'solar', 'wind', 'bioenergy', 'geothermal'])
                )

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()

            # Apply pagination
            query = query.limit(limit).offset(offset)
            result = await session.execute(query)
            plants = result.scalars().all()

            plants_list = []
            for plant in plants:
                plants_list.append({
                    'id': plant.id,
                    'plant_id': plant.plant_id,
                    'name': plant.name,
                    'plant_type': plant.plant_type,
                    'capacity_mw': float(plant.capacity_mw),
                    'status': plant.status,
                    'start_year': plant.start_year,
                    'operator': plant.operator,
                    'latitude': float(plant.latitude) if plant.latitude else None,
                    'longitude': float(plant.longitude) if plant.longitude else None,
                    'is_renewable': plant.is_renewable,
                })

            return plants_list, total

    async def get_power_plants_near(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 50,
        plant_type: Optional[str] = None,
        status: str = 'operating'
    ) -> List[Dict[str, Any]]:
        """Find power plants within radius using PostGIS spatial query"""
        async with self.async_session_factory() as session:
            query = text("""
                SELECT 
                    plant_id,
                    name,
                    plant_type,
                    capacity_mw,
                    status,
                    start_year,
                    operator,
                    ST_Y(location::geometry) as latitude,
                    ST_X(location::geometry) as longitude,
                    ST_Distance(
                        location,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                    ) / 1000 as distance_km
                FROM grid.power_plants
                WHERE ST_DWithin(
                    location,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                    :radius_m
                )
                AND (:plant_type IS NULL OR plant_type = :plant_type)
                AND (:status IS NULL OR status = :status)
                ORDER BY distance_km
            """)

            result = await session.execute(query, {
                'lat': latitude,
                'lon': longitude,
                'radius_m': radius_km * 1000,
                'plant_type': plant_type,
                'status': status if status else None
            })

            return [dict(row._mapping) for row in result]

    async def get_power_plant_stats(self) -> Dict[str, Any]:
        """Get aggregate power plant statistics"""
        async with self.async_session_factory() as session:
            # By type
            type_query = text("""
                SELECT 
                    plant_type,
                    COUNT(*) as plant_count,
                    SUM(capacity_mw) as total_capacity_mw,
                    ROUND(AVG(capacity_mw), 2) as avg_capacity_mw
                FROM grid.power_plants
                WHERE status = 'operating'
                GROUP BY plant_type
                ORDER BY total_capacity_mw DESC
            """)
            type_result = await session.execute(type_query)
            by_type = {row.plant_type: dict(row._mapping) for row in type_result}

            # Renewable summary
            renewable_query = text("""
                SELECT 
                    COUNT(*) FILTER (WHERE plant_type IN ('hydropower', 'solar', 'wind', 'bioenergy', 'geothermal')) as renewable_count,
                    SUM(capacity_mw) FILTER (WHERE plant_type IN ('hydropower', 'solar', 'wind', 'bioenergy', 'geothermal')) as renewable_capacity_mw,
                    COUNT(*) as total_count,
                    SUM(capacity_mw) as total_capacity_mw
                FROM grid.power_plants
                WHERE status = 'operating'
            """)
            renewable_result = await session.execute(renewable_query)
            renewable_row = renewable_result.first()

            total_capacity = float(renewable_row.total_capacity_mw) if renewable_row.total_capacity_mw else 0
            renewable_capacity = float(renewable_row.renewable_capacity_mw) if renewable_row.renewable_capacity_mw else 0

            return {
                'by_type': by_type,
                'renewable': {
                    'count': renewable_row.renewable_count,
                    'capacity_mw': renewable_capacity,
                    'percentage': round(renewable_capacity / total_capacity * 100, 2) if total_capacity > 0 else 0
                },
                'total': {
                    'count': renewable_row.total_count,
                    'capacity_mw': total_capacity
                }
            }

    async def delete_power_plant(self, plant_id: str) -> bool:
        """Delete a power plant"""
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(PowerPlant).where(PowerPlant.plant_id == plant_id)
            )
            plant = result.scalar_one_or_none()

            if not plant:
                return False

            await session.delete(plant)
            await session.commit()
            return True
