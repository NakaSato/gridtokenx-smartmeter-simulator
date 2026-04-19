import logging
import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class MeterConfigModel(Base):
    __tablename__ = "meter_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    meter_id = Column(String(50), unique=True, nullable=False)
    meter_type = Column(String(50))
    location = Column(String(100))
    accuracy_class = Column(String(20))
    config_params = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SimulationSessionModel(Base):
    __tablename__ = "simulation_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    config = Column(JSON)
    status = Column(String(20), default="active")

class SolarPanelInventoryModel(Base):
    __tablename__ = "solar_panel_inventory"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    geometry = Column(JSON, nullable=False) # store GeoJSON geometry
    area_sqm = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class GridMetricsModel(Base):
    __tablename__ = "grid_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    imbalance_mw = Column(Float)
    avg_voltage_pu = Column(Float)
    health_score = Column(Float)
    avg_nodal_price = Column(Float)
    carbon_intensity = Column(Float)
    total_loss_mw = Column(Float)
    frequency_hz = Column(Float)

class GridEventModel(Base):
    """Stores grid instability events like bottlenecks and frequency deviations."""
    __tablename__ = "grid_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False) # e.g., "bottleneck", "frequency_deviation"
    severity = Column(String(20)) # "info", "warning", "critical"
    message = Column(String(500))
    metadata_json = Column(JSON) # Detailed stats (loading%, dispatch counts)

class GridNodeStateModel(Base):
    """Destination table for the ETL pipeline, tracking metrics per node."""
    __tablename__ = "grid_node_states"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    node_id = Column(String(50), nullable=False, index=True) # e.g., "samui_hub", "tao_node"
    
    # Metrics
    load_demand_mw = Column(Float)
    grid_import_mw = Column(Float)
    bess_discharge_mw = Column(Float)
    local_gen_mw = Column(Float)
    
    # Constraints
    utilization_pct = Column(Float)
    soc_pct = Column(Float)
    export_mw = Column(Float)
    
    # Economic/Environmental
    marginal_cost = Column(Float)
    carbon_intensity = Column(Float)

class DatabaseManager:
    """Manages PostgreSQL persistence for metadata."""
    
    def __init__(self, db_url: str):
        # SQLAlchemy async requirement: replace postgresql:// with postgresql+asyncpg://
        if db_url.startswith("postgresql://"):
            self.db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            self.db_url = db_url
            
        self.engine = create_async_engine(self.db_url, echo=False)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        """Initialize database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            if "Connect call failed" in str(e) or "Connection refused" in str(e):
                logger.warning(f"Database unavailable at {self.db_url}. Persistence features will be disabled.")
            else:
                logger.error(f"Failed to initialize database: {e}")
            return False

    async def close(self):
        """Dispose of the database engine and clean up pooled connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine disposed")

    async def save_meter_config(self, meter_id: str, meter_type: str, location: str, accuracy: str, params: dict):
        """Save or update meter configuration."""
        async with self.SessionLocal() as session:
            try:
                # Check if exists
                stmt = select(MeterConfigModel).where(MeterConfigModel.meter_id == meter_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                
                if model:
                    model.meter_type = meter_type
                    model.location = location
                    model.accuracy_class = accuracy
                    model.config_params = params
                else:
                    model = MeterConfigModel(
                        meter_id=meter_id,
                        meter_type=meter_type,
                        location=location,
                        accuracy_class=accuracy,
                        config_params=params
                    )
                    session.add(model)
                
                await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error saving meter config: {e}")
                await session.rollback()
                return False

    async def create_session(self, session_id: str, config: dict):
        """Start a new simulation session."""
        async with self.SessionLocal() as session:
            try:
                model = SimulationSessionModel(
                    session_id=session_id,
                    config=config
                )
                session.add(model)
                await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error creating session: {e}")
                await session.rollback()
                return False

    async def close_session(self, session_id: str):
        """Close an existing simulation session."""
        async with self.SessionLocal() as session:
            try:
                stmt = select(SimulationSessionModel).where(SimulationSessionModel.session_id == session_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    model.end_time = datetime.datetime.utcnow()
                    model.status = "completed"
                    await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error closing session: {e}")
                await session.rollback()
                return False
                
    async def get_all_meters(self) -> List[dict]:
        """Retrieve all registered meters."""
        async with self.SessionLocal() as session:
            stmt = select(MeterConfigModel)
            result = await session.execute(stmt)
            meters = result.scalars().all()
            return [
                {
                    "meter_id": m.meter_id,
                    "meter_type": m.meter_type,
                    "location": m.location,
                    "accuracy": m.accuracy_class
                } for m in meters
            ]

    async def save_solar_inventory(self, geometry: dict, area_sqm: Optional[float] = None, confidence_score: Optional[float] = None):
        """Save a detected solar panel feature to the inventory."""
        async with self.SessionLocal() as session:
            try:
                model = SolarPanelInventoryModel(
                    geometry=geometry,
                    area_sqm=area_sqm,
                    confidence_score=confidence_score
                )
                session.add(model)
                await session.commit()
                return model.id
            except Exception as e:
                logger.error(f"Error saving solar panel inventory: {e}")
                await session.rollback()
                return None

    async def get_all_solar_inventory(self) -> List[dict]:
        """Retrieve all detected solar panel features."""
        async with self.SessionLocal() as session:
            try:
                stmt = select(SolarPanelInventoryModel)
                result = await session.execute(stmt)
                panels = result.scalars().all()
                return [
                    {
                        "id": p.id,
                        "geometry": p.geometry,
                        "area_sqm": p.area_sqm,
                        "confidence_score": p.confidence_score,
                        "created_at": p.created_at.isoformat() if p.created_at else None
                    } for p in panels
                ]
            except Exception as e:
                logger.error(f"Error retrieving solar panel inventory: {e}")
                return []

    async def save_grid_metrics(self, data: dict):
        """Save a snapshot of grid metrics."""
        async with self.SessionLocal() as session:
            try:
                model = GridMetricsModel(
                    timestamp=data.get('timestamp', datetime.datetime.now(datetime.timezone.utc)),
                    imbalance_mw=data.get('imbalance_mw'),
                    avg_voltage_pu=data.get('avg_voltage_pu'),
                    health_score=data.get('health_score'),
                    avg_nodal_price=data.get('avg_nodal_price'),
                    carbon_intensity=data.get('carbon_intensity'),
                    total_loss_mw=data.get('total_loss_mw'),
                    frequency_hz=data.get('frequency_hz')
                )
                session.add(model)
                await session.commit()
                return model.id
            except Exception as e:
                logger.error(f"Error saving grid metrics: {e}")
                await session.rollback()
                return None

    async def get_grid_history(self, limit: int = 100) -> List[dict]:
        """Retrieve historical grid metrics."""
        async with self.SessionLocal() as session:
            try:
                stmt = select(GridMetricsModel).order_by(GridMetricsModel.timestamp.desc()).limit(limit)
                result = await session.execute(stmt)
                metrics = result.scalars().all()
                return [
                    {
                        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                        "imbalance_mw": m.imbalance_mw,
                        "avg_voltage_pu": m.avg_voltage_pu,
                        "health_score": m.health_score,
                        "avg_nodal_price": m.avg_nodal_price,
                        "carbon_intensity": m.carbon_intensity,
                        "total_loss_mw": m.total_loss_mw,
                        "frequency_hz": m.frequency_hz
                    } for m in metrics
                ]
            except Exception as e:
                logger.error(f"Error retrieving grid history: {e}")
                return []

    async def save_grid_event(self, event_type: str, severity: str, message: str, metadata: dict = None):
        """Save a grid event to the database."""
        async with self.SessionLocal() as session:
            try:
                model = GridEventModel(
                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                    event_type=event_type,
                    severity=severity,
                    message=message,
                    metadata_json=metadata or {}
                )
                session.add(model)
                await session.commit()
                return model.id
            except Exception as e:
                logger.error(f"Error saving grid event: {e}")
                await session.rollback()
                return None

    async def get_grid_events(self, limit: int = 50) -> List[dict]:
        """Retrieve historical grid events."""
        async with self.SessionLocal() as session:
            try:
                stmt = select(GridEventModel).order_by(GridEventModel.timestamp.desc()).limit(limit)
                result = await session.execute(stmt)
                events = result.scalars().all()
                return [
                    {
                        "id": e.id,
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        "event_type": e.event_type,
                        "severity": e.severity,
                        "message": e.message,
                        "metadata": e.metadata_json
                    } for e in events
                ]
            except Exception as e:
                logger.error(f"Error retrieving grid events: {e}")
                return []

    async def save_node_state(self, data: dict):
        """Save a structured node state (ETL Destination)."""
        async with self.SessionLocal() as session:
            try:
                metrics = data.get('metrics', {})
                constraints = data.get('constraints', {})
                econ = data.get('economic_indicators', {})
                
                model = GridNodeStateModel(
                    timestamp=data.get('timestamp', datetime.datetime.now(datetime.timezone.utc)),
                    node_id=data.get('node_id'),
                    load_demand_mw=metrics.get('load_demand_mw'),
                    grid_import_mw=metrics.get('grid_import_115kv_mw'),
                    bess_discharge_mw=metrics.get('bess_discharge_mw'),
                    local_gen_mw=metrics.get('local_gen_diesel_mw'),
                    utilization_pct=constraints.get('cable_115kv_kmb_utilization_pct'),
                    soc_pct=constraints.get('bess_soc_pct'),
                    export_mw=constraints.get('export_33kv_phangan_mw'),
                    marginal_cost=econ.get('marginal_cost_per_mwh'),
                    carbon_intensity=econ.get('carbon_intensity_gco2_kwh')
                )
                session.add(model)
                await session.commit()
                return model.id
            except Exception as e:
                logger.error(f"Error saving node state: {e}")
                await session.rollback()
                return None

    async def get_node_history(self, node_id: str, limit: int = 100) -> List[dict]:
        """Retrieve historical states for a specific node."""
        async with self.SessionLocal() as session:
            try:
                stmt = select(GridNodeStateModel).where(GridNodeStateModel.node_id == node_id).order_by(GridNodeStateModel.timestamp.desc()).limit(limit)
                result = await session.execute(stmt)
                states = result.scalars().all()
                return [
                    {
                        "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                        "node_id": s.node_id,
                        "metrics": {
                            "load_demand_mw": s.load_demand_mw,
                            "grid_import_mw": s.grid_import_mw,
                            "bess_discharge_mw": s.bess_discharge_mw,
                            "local_gen_mw": s.local_gen_mw
                        },
                        "constraints": {
                            "utilization_pct": s.utilization_pct,
                            "soc_pct": s.soc_pct,
                            "export_mw": s.export_mw
                        },
                        "economic_indicators": {
                            "marginal_cost": s.marginal_cost,
                            "carbon_intensity": s.carbon_intensity
                        }
                    } for s in states
                ]
            except Exception as e:
                logger.error(f"Error retrieving node history: {e}")
                return []
