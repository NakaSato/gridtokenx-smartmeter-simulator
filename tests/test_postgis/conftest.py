"""
Test fixtures for PostGIS integration tests.

Provides:
- Test database setup/teardown
- Sample data fixtures
- Database connection fixtures
- Async test utilities
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from smart_meter_simulator.database.repository import PostGISRepository
from smart_meter_simulator.database.models import Base, Substation, Transformer, PowerLine, Meter


# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://gridtokenx:gridtokenx_password@localhost:5432/gridtokenx_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    
    # Create test database if not exists
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
    except Exception as e:
        print(f"Warning: Could not create extensions: {e}")
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_database(test_engine) -> AsyncGenerator[PostGISRepository, None]:
    """
    Create fresh test database for each test function.
    
    Creates tables before test, drops after.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create repository
    repo = PostGISRepository(TEST_DATABASE_URL)
    
    yield repo
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Close repository
    await repo.close() if hasattr(repo, 'close') else None


@pytest_asyncio.fixture(scope="function")
async def sample_substation(test_database: PostGISRepository) -> Substation:
    """Create a sample substation for testing"""
    substation = await test_database.create_substation(
        name="Test Substation",
        code="TEST-SUB-001",
        voltage_level_kv=22.0,
        operator="MEA",
        type="distribution",
        capacity_mva=20.0,
        longitude=100.5018,
        latitude=13.7563,
        province="Bangkok"
    )
    return substation


@pytest_asyncio.fixture(scope="function")
async def sample_transformer(test_database: PostGISRepository) -> Transformer:
    """Create a sample transformer for testing"""
    transformer = await test_database.create_transformer(
        code="TEST-TXN-001",
        voltage_primary_kv=22.0,
        voltage_secondary_kv=0.4,
        capacity_kva=500,
        longitude=100.5025,
        latitude=13.7570
    )
    return transformer


@pytest_asyncio.fixture(scope="function")
async def sample_power_line(test_database: PostGISRepository) -> PowerLine:
    """Create a sample power line for testing"""
    power_line = await test_database.create_power_line(
        code="TEST-LINE-001",
        voltage_level_kv=22.0,
        coordinates=[
            (100.5018, 13.7563),
            (100.5025, 13.7570),
            (100.5030, 13.7580)
        ],
        line_type="overhead",
        conductor_type="NA2XS2Y 1x185 RM/25 12/20 kV"
    )
    return power_line


@pytest_asyncio.fixture(scope="function")
async def sample_meter(test_database: PostGISRepository) -> Meter:
    """Create a sample meter for testing"""
    meter = await test_database.create_meter(
        meter_id="TEST-METER-000001",
        meter_type="solar_prosumer",
        serial_number="SN000000001",
        longitude=100.5020,
        latitude=13.7565,
        province="Bangkok"
    )
    return meter


@pytest_asyncio.fixture(scope="function")
async def sample_grid_data(test_database: PostGISRepository) -> dict:
    """
    Create a complete sample grid for integration testing.
    
    Includes:
    - 3 substations (500kV, 115kV, 22kV)
    - 10 transformers
    - 5 power lines
    - 50 meters
    """
    # Create substations
    substation_500 = await test_database.create_substation(
        name="500kV Bangkok Main",
        code="SUB-500-001",
        voltage_level_kv=500.0,
        operator="EGAT",
        type="transmission",
        capacity_mva=300.0,
        longitude=100.5000,
        latitude=13.7500,
        province="Bangkok"
    )
    
    substation_115 = await test_database.create_substation(
        name="115kV Bangkok North",
        code="SUB-115-001",
        voltage_level_kv=115.0,
        operator="EGAT",
        type="sub_transmission",
        capacity_mva=100.0,
        longitude=100.5100,
        latitude=13.7600,
        province="Bangkok"
    )
    
    substation_22 = await test_database.create_substation(
        name="22kV Distribution Center",
        code="SUB-22-001",
        voltage_level_kv=22.0,
        operator="MEA",
        type="distribution",
        capacity_mva=25.0,
        longitude=100.5050,
        latitude=13.7550,
        province="Bangkok"
    )
    
    # Create transformers
    transformers = []
    for i in range(10):
        txn = await test_database.create_transformer(
            code=f"TEST-TXN-{i+1:03d}",
            voltage_primary_kv=22.0,
            voltage_secondary_kv=0.4,
            capacity_kva=500,
            longitude=100.5000 + (i * 0.001),
            latitude=13.7500 + (i * 0.001)
        )
        transformers.append(txn)
    
    # Create power lines
    lines = []
    line_coords = [
        [(100.5000, 13.7500), (100.5050, 13.7550)],
        [(100.5050, 13.7550), (100.5100, 13.7600)],
        [(100.5100, 13.7600), (100.5150, 13.7650)],
        [(100.5150, 13.7650), (100.5200, 13.7700)],
        [(100.5200, 13.7700), (100.5250, 13.7750)],
    ]
    
    for i, coords in enumerate(line_coords):
        line = await test_database.create_power_line(
            code=f"TEST-LINE-{i+1:03d}",
            voltage_level_kv=22.0,
            coordinates=coords,
            line_type="overhead"
        )
        lines.append(line)
    
    # Create meters
    meters = []
    for i in range(50):
        meter = await test_database.create_meter(
            meter_id=f"TEST-METER-{i+1:06d}",
            meter_type="solar_prosumer" if i % 2 == 0 else "grid_consumer",
            serial_number=f"SN{i+1:012d}",
            longitude=100.5000 + (i * 0.0001),
            latitude=13.7500 + (i * 0.0001),
            transformer_id=transformers[i % len(transformers)].id if transformers else None
        )
        meters.append(meter)
    
    return {
        "substations": [substation_500, substation_115, substation_22],
        "transformers": transformers,
        "power_lines": lines,
        "meters": meters
    }


@pytest.fixture(scope="session")
def test_config() -> dict:
    """Test configuration"""
    return {
        "database_url": TEST_DATABASE_URL,
        "test_regions": ["bangkok", "central", "chiang_mai", "phuket"],
        "test_voltages": [500, 230, 115, 22, 0.4],
        "test_meter_types": [
            "solar_prosumer",
            "grid_consumer",
            "hybrid_prosumer",
            "battery",
            "ev_charger"
        ]
    }


# =============================================================================
# Helper Functions
# =============================================================================

def assert_coordinates_equal(coord1: tuple, coord2: tuple, tolerance: float = 0.0001):
    """Assert that two coordinate tuples are equal within tolerance"""
    assert abs(coord1[0] - coord2[0]) < tolerance, \
        f"Longitude mismatch: {coord1[0]} != {coord2[0]}"
    assert abs(coord1[1] - coord2[1]) < tolerance, \
        f"Latitude mismatch: {coord1[1]} != {coord2[1]}"


async def count_table_rows(repo: PostGISRepository, table_name: str) -> int:
    """Count rows in a table"""
    async with repo.get_session() as session:
        result = await session.execute(
            text(f"SELECT COUNT(*) FROM grid.{table_name}")
        )
        return result.scalar()


async def cleanup_test_data(repo: PostGISRepository):
    """Delete all test data from database"""
    async with repo.get_session() as session:
        await session.execute(text("DELETE FROM grid.meter_readings"))
        await session.execute(text("DELETE FROM grid.meters"))
        await session.execute(text("DELETE FROM grid.power_lines"))
        await session.execute(text("DELETE FROM grid.transformers"))
        await session.execute(text("DELETE FROM grid.substations"))
        await session.commit()
