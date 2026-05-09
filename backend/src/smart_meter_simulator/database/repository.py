"""
Repository for Thai grid network data (Simplified - No GeoAlchemy2).
"""

import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal

from sqlalchemy import text, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import (
    Substation, Transformer, PowerLine, Meter, MeterReading,
    PowerPlant, Base
)

logger = logging.getLogger(__name__)


class PostGISRepository:
    """
    Simplified repository for Thai grid network data.
    (Spatial queries removed/simplified)
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_substation(self, substation_id: int) -> Optional[Substation]:
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(Substation).where(Substation.id == substation_id)
            )
            return result.scalar_one_or_none()
    
    async def get_all_meters(
        self,
        limit: int = 1000,
        meter_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        async with self.async_session_factory() as session:
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
                out.append({
                    "meter_id": m.meter_id,
                    "meter_type": m.meter_type,
                    "status": m.status,
                    "latitude": float(m.latitude),
                    "longitude": float(m.longitude),
                })
            return out

    async def store_reading(
        self,
        meter_id: str,
        timestamp: datetime,
        energy_generated_kwh: float,
        energy_consumed_kwh: float,
        **kwargs
    ) -> MeterReading:
        async with self.async_session_factory() as session:
            reading = MeterReading(
                meter_id=meter_id,
                timestamp=timestamp,
                energy_generated_kwh=energy_generated_kwh,
                energy_consumed_kwh=energy_consumed_kwh,
                **kwargs
            )
            session.add(reading)
            await session.commit()
            return reading

    async def check_connection(self) -> bool:
        try:
            async with self.async_session_factory() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def batch_import_plants(self, plants_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch import power plants.
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
                        latitude=plant_data.get('latitude'),
                        longitude=plant_data.get('longitude')
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
            'error_details': errors[:10]
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
        """
        async with self.async_session_factory() as session:
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

            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()

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
        """Find power plants using simple distance approximation (no PostGIS)."""
        async with self.async_session_factory() as session:
            # Simple bounding box check + Pythagorean distance for simulation
            # 1 degree lat is approx 111km
            lat_delta = radius_km / 111.0
            lon_delta = radius_km / (111.0 * 0.97) # approx for Thailand latitude
            
            stmt = select(PowerPlant).where(and_(
                PowerPlant.latitude >= latitude - lat_delta,
                PowerPlant.latitude <= latitude + lat_delta,
                PowerPlant.longitude >= longitude - lon_delta,
                PowerPlant.longitude <= longitude + lon_delta
            ))
            
            if plant_type:
                stmt = stmt.where(PowerPlant.plant_type == plant_type)
            if status:
                stmt = stmt.where(PowerPlant.status == status)
                
            result = await session.execute(stmt)
            plants = result.scalars().all()
            
            out = []
            for p in plants:
                dist = ((float(p.latitude) - latitude)**2 + (float(p.longitude) - longitude)**2)**0.5 * 111.0
                if dist <= radius_km:
                    out.append({
                        'plant_id': p.plant_id,
                        'name': p.name,
                        'plant_type': p.plant_type,
                        'capacity_mw': float(p.capacity_mw),
                        'latitude': float(p.latitude),
                        'longitude': float(p.longitude),
                        'distance_km': round(dist, 2)
                    })
            
            return sorted(out, key=lambda x: x['distance_km'])

    async def get_power_plant_stats(self) -> Dict[str, Any]:
        """Get aggregate power plant statistics (Simplified)."""
        async with self.async_session_factory() as session:
            type_query = text("""
                SELECT 
                    plant_type,
                    COUNT(*) as plant_count,
                    SUM(capacity_mw) as total_capacity_mw
                FROM grid.power_plants
                WHERE status = 'operating'
                GROUP BY plant_type
            """)
            type_result = await session.execute(type_query)
            by_type = {row.plant_type: dict(row._mapping) for row in type_result}

            total_query = select(func.count(), func.sum(PowerPlant.capacity_mw)).where(PowerPlant.status == 'operating')
            total_res = await session.execute(total_query)
            total_count, total_cap = total_res.first()

            return {
                'by_type': by_type,
                'total': {
                    'count': total_count,
                    'capacity_mw': float(total_cap) if total_cap else 0
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
