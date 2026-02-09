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
