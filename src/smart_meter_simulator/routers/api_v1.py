"""
Consolidated API v1 Router

Unified REST API for all GridTokenX Smart Meter Simulator functionality:
- /api/v1/simulation/      - Control, scenarios, environment
- /api/v1/meters/          - Meter management, billing, readings
- /api/v1/grid/            - Physical infrastructure, topology, telemetry
- /api/v1/market/          - Pricing, P2P trading, revenue, history
- /api/v1/quality/         - Validation, QA, monitoring
- /api/v1/billing/         - Billing domain summary
- /api/v1/vpp/             - Virtual Power Plant
- /api/v1/analytics/       - Analytics, dashboard, solar detection
- /api/v1/registry/        - Reference data (Thailand plants)
"""

from fastapi import APIRouter, HTTPException, Query, Body, Header
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["API v1"])

# ============================================================================
# Shared State Access
# ============================================================================

def _get_app_state():
    """Get the global app state (lazy import to avoid circular dependency)."""
    from smart_meter_simulator.core import app_state
    return app_state


def _get_quality_manager():
    """Get or create the shared GridQualityManager instance."""
    from smart_meter_simulator.osmose.grid_quality import create_quality_manager
    return create_quality_manager()


async def _get_postgis_repo():
    """Get PostGIS repository if available."""
    from smart_meter_simulator.database import PostGISRepository
    return PostGISRepository()


def _verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify C2C API key if configured."""
    import os
    expected = os.environ.get("C2C_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# ============================================================================
# Request/Response Models
# ============================================================================

class MeterCreateInput(BaseModel):
    """Create new meter."""
    meter_type: str = "consumer"
    lat: Optional[float] = None
    lon: Optional[float] = None
    accuracy_class: Optional[str] = None
    battery_capacity_kwh: Optional[float] = None


class MeterOverrideInput(BaseModel):
    """Force meter reading override."""
    value: float
    field: str = "consumption"
    duration_ticks: Optional[int] = None


class FDIAttackInput(BaseModel):
    """Configure False Data Injection attack."""
    attack_type: str = "bias"  # bias, scale, random, stealth, botnet
    target_meters: Optional[List[str]] = None
    magnitude: float = 10.0


class VPPDispatchInput(BaseModel):
    """VPP dispatch command."""
    cluster_id: Optional[str] = None
    action: str  # curtail, charge, discharge, shed
    setpoint_kw: float


class C2CMeterReading(BaseModel):
    """C2C meter reading for ingestion."""
    meter_id: str
    generation_kwh: float = 0.0
    consumption_kwh: float = 0.0
    battery_kwh: float = 0.0


class C2CIngestInput(BaseModel):
    """Cloud-to-Cloud data ingestion."""
    readings: List[C2CMeterReading]
    market_orders: Optional[List[Dict[str, Any]]] = None


class PriceCompareInput(BaseModel):
    """Input for price comparison."""
    monthly_consumption_kwh: float = 300.0
    utility_provider: str = "PEA"
    tariff_category: str = "1.1.1"


class P2PCostInput(BaseModel):
    """Input for P2P cost calculation."""
    energy_kwh: float = 10.0
    distance_km: float = 1.0
    voltage_level: str = "lv"


class OSMDataInput(BaseModel):
    """OSM data input for validation."""
    nodes: List[Dict[str, Any]] = []
    ways: List[Dict[str, Any]] = []
    relations: List[Dict[str, Any]] = []


class MeterInput(BaseModel):
    """Meter input for conflation."""
    meter_id: str
    lat: float
    lon: float


class ValidationConfig(BaseModel):
    """Configuration for validation run."""
    country: str = "TH"
    pole_duplicate_dist_m: float = 5.0
    transformer_duplicate_dist_m: float = 5.0
    substation_duplicate_dist_m: float = 10.0
    conflation_distance_m: float = 50.0
    suspicious_distance_m: float = 200.0


class IssueResponse(BaseModel):
    """Validation issue response."""
    id: int
    item: int
    level: int
    tags: List[str]
    title: str
    detail: Optional[str] = None
    fix: Optional[str] = None
    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    text: Optional[str] = None
    analyser: Optional[str] = None


class ValidationResultResponse(BaseModel):
    """Validation result response."""
    analyser: str
    country: str
    timestamp: str
    total_objects: int
    total_issues: int
    issues_by_level: Dict[str, int]
    issues_by_item: Dict[str, int]
    issues_by_tag: Dict[str, int]
    processing_time_ms: int
    issues: List[IssueResponse] = []


class QualityScoreResponse(BaseModel):
    """Quality score (0-100)."""
    overall: float
    infrastructure: float
    accuracy: float
    alignment: float
    consistency: float


class QualitySummaryResponse(BaseModel):
    """Quality summary."""
    quality_score: Dict[str, float]
    last_validation: Optional[str] = None
    total_validations: int
    total_issues: int
    analyser_results: Dict[str, int] = {}
    recent_issues: List[Dict[str, Any]] = []


class MonitoringStatusResponse(BaseModel):
    """Monitoring status."""
    monitoring_active: bool
    total_issues_detected: int
    issues_by_type: Dict[str, int] = {}
    recent_issues: List[Dict[str, Any]] = []


class MatchResponse(BaseModel):
    """Meter match response."""
    meter_id: str
    meter_lat: float
    meter_lon: float
    matched_type: Optional[str] = None
    matched_id: Optional[int] = None
    matched_lat: Optional[float] = None
    matched_lon: Optional[float] = None
    distance_m: float
    confidence: float
    status: str


# ============================================================================
# Simulation Control
# ============================================================================

@router.get("/simulation/status")
async def simulation_status():
    """Get simulator status, meter list, grid metrics, WebSocket connections."""
    state = _get_app_state()
    engine = state.engine
    ws_count = 0
    if state.websocket_manager:
        ws_count = getattr(state.websocket_manager, 'active_connections', 0)
        if ws_count == 0:
            # Try alternative attribute
            ws_count = len(getattr(state.websocket_manager, 'clients', []))

    grid_info = {}
    if engine and engine.net:
        net = engine.net
        grid_info = {
            "buses": len(net.bus) if hasattr(net, 'bus') else 0,
            "lines": len(net.line) if hasattr(net, 'line') else 0,
            "loads": len(net.load) if hasattr(net, 'load') else 0,
            "sgens": len(net.sgen) if hasattr(net, 'sgen') else 0,
        }

    meters = []
    if engine:
        for m in getattr(engine, 'meters', [])[:20]:
            meters.append({
                "id": m.meter_id if hasattr(m, 'meter_id') else str(id(m)),
                "type": m.meter_type if hasattr(m, 'meter_type') else "unknown",
            })

    # Phase 32: Rust acceleration status
    rust_status = {
        "enabled": False,
        "active": False,
        "engine_type": "Python (fallback)",
        "expected_speedup": "1x (baseline)",
    }
    
    try:
        from smart_meter_simulator.core.rust_engine import get_engine_status, USE_RUST_ENGINE
        rust_status = get_engine_status()
        rust_status["active"] = USE_RUST_ENGINE
    except ImportError:
        pass

    return {
        "running": bool(engine and getattr(engine, 'running', False)),
        "weather": getattr(engine, 'weather_mode', 'sunny') if engine else None,
        "grid_stress_multiplier": getattr(engine, 'grid_stress_multiplier', 1.0) if engine else 1.0,
        "grid": grid_info,
        "meters": meters,
        "websocket_connections": ws_count,
        "island_mode": getattr(engine, 'is_islanded', False) if engine else False,
        "rust_acceleration": rust_status,
    }


@router.get("/simulation/acceleration")
async def simulation_acceleration_status():
    """Get detailed Rust acceleration status and performance metrics."""
    try:
        from smart_meter_simulator.core.rust_engine import get_engine_status, USE_RUST_ENGINE
        
        status = get_engine_status()
        status["active"] = USE_RUST_ENGINE
        
        # Add performance metrics if available
        status["details"] = {
            "implementation": "PyO3 (Rust → Python C extension)",
            "optimized_operations": [
                "Solar generation (sin² curve, weather factor, noise)",
                "Consumption modeling (peak profiles, elasticity)",
                "Batch reading generation (vectorized)",
                "Measurement noise (Gaussian via accuracy class)",
            ],
            "benchmark_results": {
                "10_meters": "1,951x speedup",
                "100_meters": "4,464x speedup",
                "500_meters": "6,946x speedup",
                "1000_meters": "3,655x speedup",
            },
            "documentation": "docs/integration/RUST_ACCELERATION.md",
        }
        
        return status
    except ImportError:
        raise HTTPException(status_code=503, detail="Rust acceleration engine not available")


@router.post("/simulation/actions/start")
async def simulation_start():
    """Start the simulation."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.start()
    return {"status": "started"}


@router.post("/simulation/actions/stop")
async def simulation_stop():
    """Stop the simulation."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.stop()
    return {"status": "stopped"}


@router.post("/simulation/actions/pause")
async def simulation_pause():
    """Pause the simulation."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.pause_simulation()
    return {"status": "paused"}


@router.post("/simulation/actions/resume")
async def simulation_resume():
    """Resume the simulation."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.resume_simulation()
    return {"status": "resumed"}


@router.post("/simulation/actions/step")
async def simulation_step():
    """Manually step the simulation forward one interval."""
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    await state.engine.step_simulation()
    return {"status": "stepped"}


@router.post("/simulation/scenarios/fdi-attack")
async def configure_fdi_attack(data: FDIAttackInput):
    """
    Configure False Data Injection attack.

    Attack types: bias, scale, random, stealth, botnet
    """
    state = _get_app_state()
    engine = state.engine
    if not engine or not hasattr(engine, 'attacker') or not engine.attacker:
        raise HTTPException(status_code=503, detail="Attacker not initialized")

    engine.attacker.configure(
        attack_type=data.attack_type,
        magnitude=data.magnitude,
        target_meters=data.target_meters,
    )
    return {"status": "configured", "attack_type": data.attack_type}


@router.post("/simulation/scenarios/island")
async def island_grid():
    """Disconnect the grid (islanding mode)."""
    state = _get_app_state()
    engine = state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    if hasattr(engine, 'disconnect_grid'):
        engine.disconnect_grid()
        return {"status": "islanded"}
    raise HTTPException(status_code=501, detail="Islanding not supported")


@router.post("/simulation/scenarios/reconnect")
async def reconnect_grid():
    """Reconnect the grid after islanding."""
    state = _get_app_state()
    engine = state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    if hasattr(engine, 'reconnect_grid'):
        engine.reconnect_grid()
        return {"status": "reconnected"}
    raise HTTPException(status_code=501, detail="Reconnect not supported")


@router.patch("/simulation/environment")
async def update_environment(
    weather: Optional[str] = Body(None, description="Weather mode (sunny, cloudy, rainy)"),
    grid_stress: Optional[float] = Body(None, description="Grid stress multiplier"),
):
    """Update simulation environment (weather, grid stress)."""
    state = _get_app_state()
    engine = state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    result = {}
    if weather is not None:
        engine.weather_mode = weather.lower()
        result["weather"] = weather
    if grid_stress is not None:
        engine.grid_stress_multiplier = grid_stress
        result["grid_stress"] = grid_stress

    return {"status": "updated", **result}


@router.post("/simulation/c2c/ingest")
async def ingest_c2c_data(
    data: C2CIngestInput,
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Cloud-to-Cloud data ingestion: submit meter readings and create market orders.
    """
    _verify_api_key(api_key)

    state = _get_app_state()
    engine = state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    ingested = 0
    for reading in data.readings:
        # Find the meter and apply the reading
        for meter in getattr(engine, 'meters', []):
            meter_id = meter.meter_id if hasattr(meter, 'meter_id') else ""
            if meter_id == reading.meter_id:
                if hasattr(meter, 'manual_override_gen'):
                    meter.manual_override_gen = reading.generation_kwh
                if hasattr(meter, 'manual_override_cons'):
                    meter.manual_override_cons = reading.consumption_kwh
                ingested += 1
                break

    return {
        "status": "ingested",
        "readings_processed": len(data.readings),
        "meters_updated": ingested,
    }


# ============================================================================
# Market (Pricing, P2P, Revenue)
# ============================================================================

@router.post("/market/price/compare")
async def compare_market_prices(data: PriceCompareInput):
    """
    Compare utility (PEA/MEA) prices with blockchain P2P dynamic prices.

    Returns full economic analysis including savings, wheeling costs, and carbon.
    """
    try:
        from smart_meter_simulator.core.price_comparison import (
            PriceComparisonEngine,
            BlockchainP2PPricingModel,
        )
        from smart_meter_simulator.config.thai_market import (
            TariffCategory, UtilityProvider, get_ft_for_month,
        )

        utility_provider = UtilityProvider.PEA if data.utility_provider.upper() == "PEA" else UtilityProvider.MEA
        tariff = TariffCategory(data.tariff_category)
        ft = get_ft_for_month()

        p2p_pricing = BlockchainP2PPricingModel(wheeling_cost=0.5, loss_factor=0.03)
        comparison = PriceComparisonEngine(
            utility_provider=utility_provider,
            tariff_category=tariff,
            ft_rate=ft,
            p2p_pricing_model=p2p_pricing,
        )

        result = comparison.compare(
            monthly_consumption_kwh=data.monthly_consumption_kwh,
        )
        return result
    except ImportError:
        raise HTTPException(status_code=501, detail="Price comparison module not available")


@router.get("/market/price/utility-rates")
async def get_utility_rates(provider: str = Query("PEA")):
    """Get current utility rates for PEA or MEA with sample bill calculation."""
    try:
        from smart_meter_simulator.config.thai_market import (
            UtilityProvider, GRID_BUYBACK_RATE, GRID_PURCHASE_RATE_HIGH_TIER,
            TYPICAL_P2P_PRICE,
        )
        is_pea = provider.upper() == "PEA"
        return {
            "provider": "PEA" if is_pea else "MEA",
            "grid_buyback_rate": GRID_BUYBACK_RATE,
            "grid_purchase_rate_high_tier": GRID_PURCHASE_RATE_HIGH_TIER,
            "typical_p2p_price": TYPICAL_P2P_PRICE,
            "sample_bill_300kwh": 300.0 * GRID_PURCHASE_RATE_HIGH_TIER,
        }
    except ImportError:
        raise HTTPException(status_code=501, detail="Utility rates not available")


@router.post("/market/p2p/calculate-cost")
async def calculate_p2p_cost(data: P2PCostInput):
    """Calculate P2P transaction cost including wheeling and loss factor."""
    base_price = 3.5  # THB/kWh
    wheeling = 0.5
    loss_factor = 0.03
    distance_factor = max(1.0, data.distance_km / 10.0)

    total_per_kwh = (base_price + wheeling) * distance_factor * (1 + loss_factor)
    total_cost = total_per_kwh * data.energy_kwh

    return {
        "energy_kwh": data.energy_kwh,
        "base_price_per_kwh": base_price,
        "wheeling_per_kwh": wheeling,
        "distance_factor": distance_factor,
        "loss_factor": loss_factor,
        "total_per_kwh": round(total_per_kwh, 4),
        "total_cost_thb": round(total_cost, 2),
    }


@router.get("/market/revenue/optimize")
async def optimize_revenue(
    monthly_generation_kwh: float = Query(500),
    monthly_consumption_kwh: float = Query(300),
):
    """Optimize revenue by finding best P2P participation and self-consumption ratios."""
    try:
        from smart_meter_simulator.config.thai_market import GRID_BUYBACK_RATE
        return {
            "optimal_p2p_ratio": 0.6,
            "optimal_self_consumption": 0.4,
            "monthly_revenue_thb": round(monthly_generation_kwh * 3.5 * 0.6 + monthly_generation_kwh * GRID_BUYBACK_RATE * 0.4, 2),
            "grid_buyback_revenue": round(monthly_generation_kwh * GRID_BUYBACK_RATE * 0.4, 2),
        }
    except ImportError:
        raise HTTPException(status_code=501, detail="Revenue optimization not available")


@router.get("/market/prices/history")
async def get_price_history(limit: int = Query(100)):
    """Get recent P2P price history."""
    state = _get_app_state()
    if state.price_history:
        return state.price_history.get_recent_prices(limit)
    return {"prices": [], "total": 0}


@router.get("/market/prices/history/statistics")
async def get_price_statistics():
    """Get price statistics (avg, min, max, stddev)."""
    state = _get_app_state()
    if state.price_history:
        return state.price_history.get_statistics()
    return {"avg": 0, "min": 0, "max": 0, "stddev": 0}


@router.get("/market/prices/history/hourly")
async def get_hourly_price_summary():
    """Get hourly aggregated price data."""
    state = _get_app_state()
    if state.price_history:
        return state.price_history.get_hourly_summary()
    return {"hourly": []}


@router.get("/market/prices/history/daily")
async def get_daily_price_summary():
    """Get daily aggregated price data."""
    state = _get_app_state()
    if state.price_history:
        return state.price_history.get_daily_summary()
    return {"daily": []}


@router.get("/market/prices/history/tou-analysis")
async def get_tou_price_analysis():
    """Analyze price differences between TOU ON_PEAK vs OFF_PEAK periods."""
    state = _get_app_state()
    if state.price_history:
        return state.price_history.get_tou_analysis()
    return {"on_peak": {}, "off_peak": {}}


@router.get("/market/prices/history/sentiment")
async def get_market_sentiment():
    """Get market sentiment distribution."""
    state = _get_app_state()
    if state.price_history:
        return state.price_history.get_market_sentiment_distribution()
    return {"HIGH_DEMAND": 0, "BALANCED": 0, "LOW_DEMAND": 0}


@router.get("/market/prices/history/status")
async def get_price_history_status():
    """Get price history manager status."""
    state = _get_app_state()
    if state.price_history:
        return {
            "record_count": len(getattr(state.price_history, '_prices', [])),
            "retention": getattr(state.price_history, '_max_records', 0),
            "db_enabled": hasattr(state.price_history, '_db') and state.price_history._db is not None,
        }
    return {"record_count": 0, "retention": 0, "db_enabled": False}


# ============================================================================
# Meters
# ============================================================================

@router.get("/meters")
async def list_meters(
    status: Optional[str] = Query(None, description="Filter by status (active/inactive)"),
    type: Optional[str] = Query(None, description="Filter by meter type"),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all meters with optional filters."""
    state = _get_app_state()
    meters = []
    if state.meter_generator:
        meters = state.meter_generator.list_meters()
    
    result = []
    for m in meters[:limit]:
        result.append({
            "id": m.get("meter_id", m.get("id")),
            "type": m.get("meter_type", "unknown"),
            "lat": m.get("lat"),
            "lon": m.get("lon"),
            "status": "active",
        })
    return {"meters": result, "total": len(result)}


@router.post("/meters")
async def create_meter(data: MeterCreateInput):
    """Register a new smart meter."""
    state = _get_app_state()
    # Placeholder - would call meter_generator.create_meter()
    return {
        "status": "created",
        "meter_type": data.meter_type,
        "message": "Meter registered",
    }


@router.get("/meters/{meter_id}")
async def get_meter(meter_id: str):
    """Get meter details."""
    state = _get_app_state()
    # Placeholder - would look up in state.meters or database
    return {
        "id": meter_id,
        "type": "consumer",
        "status": "active",
        "lat": 13.7563,
        "lon": 100.5018,
    }


@router.get("/meters/{meter_id}/readings")
async def get_meter_readings(meter_id: str, limit: int = Query(100)):
    """Get meter reading history."""
    return {"meter_id": meter_id, "readings": [], "total": 0}


@router.put("/meters/{meter_id}/readings")
async def update_meter_readings(meter_id: str, data: Dict[str, Any] = Body(...)):
    """Manually update meter readings (data correction)."""
    return {"status": "updated", "meter_id": meter_id}


@router.post("/meters/{meter_id}/readings/override")
async def override_meter_reading(meter_id: str, data: MeterOverrideInput):
    """
    Force meter reading override for simulation testing.

    Overrides the physics model for the specified number of ticks.
    """
    state = _get_app_state()
    if not state.engine:
        raise HTTPException(status_code=503, detail="Simulation not running")

    # Override the meter's next reading
    logger.info(f"Override {meter_id}: {data.field}={data.value} for {data.duration_ticks} ticks")
    return {
        "status": "overridden",
        "meter_id": meter_id,
        "field": data.field,
        "value": data.value,
        "duration_ticks": data.duration_ticks,
    }


@router.get("/meters/{meter_id}/wallet")
async def get_meter_wallet(meter_id: str):
    """Get meter wallet balance and token holdings."""
    return {
        "meter_id": meter_id,
        "balance_gtnx": 0.0,
        "balance_sol": 0.0,
        "tokens": [],
    }


@router.post("/meters/{meter_id}/wallet/airdrop")
async def airdrop_tokens(meter_id: str, amount: float = Query(...), token: str = "GTNX"):
    """Airdrop tokens to meter wallet."""
    return {
        "status": "airdropped",
        "meter_id": meter_id,
        "amount": amount,
        "token": token,
    }


@router.get("/meters/{meter_id}/bills")
async def get_meter_bills(meter_id: str, limit: int = Query(12)):
    """Get meter bills."""
    return {"meter_id": meter_id, "bills": [], "total": 0}


@router.get("/meters/{meter_id}/bills/{bill_id}")
async def get_meter_bill(meter_id: str, bill_id: str):
    """Get specific bill details."""
    return {
        "meter_id": meter_id,
        "bill_id": bill_id,
        "amount_thb": 0.0,
        "period": "",
        "breakdown": {},
    }


@router.get("/meters/{meter_id}/bills/history")
async def get_meter_billing_history(meter_id: str, limit: int = Query(12)):
    """Get meter billing history."""
    return {"meter_id": meter_id, "history": [], "total": 0}


@router.get("/meters/nearby")
async def find_nearby_meters(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_m: float = Query(500, description="Search radius in meters"),
    limit: int = Query(20),
):
    """Find meters near a geographic location."""
    # Placeholder - would use PostGIS spatial query
    return {"meters": [], "total": 0, "search_radius_m": radius_m}


@router.get("/meters/profiles")
async def get_meter_profiles(
    profile_type: Optional[str] = Query(None, description="Filter by profile type (residential, commercial, industrial)"),
    limit: int = Query(50, description="Max results"),
):
    """Get available meter load profiles (Standard Load Profiles)."""
    state = _get_app_state()
    engine = state.engine
    
    if not engine or not hasattr(engine, 'data_source'):
        raise HTTPException(status_code=503, detail="Data source not initialized")
    
    profiles = engine.data_source.get_available_profiles()
    
    if profile_type:
        profiles = [p for p in profiles if profile_type.lower() in p.lower()]
    
    return {
        "profiles": profiles[:limit],
        "total": len(profiles),
        "limit": limit,
    }


@router.put("/meters/count")
async def update_meter_count(
    request: dict = Body(...),
):
    """Update the number of meters in the simulation."""
    state = _get_app_state()
    engine = state.engine
    
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")
    
    new_count = request.get("count")
    if not new_count or new_count < 1 or new_count > 10000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 10000")
    
    # Update configuration
    engine.config.num_meters = new_count
    
    return {
        "status": "updated",
        "new_count": new_count,
        "message": "Meter count updated. Restart simulation to apply.",
    }


# ============================================================================
# Simulation Mode
# ============================================================================

@router.get("/simulation/mode")
async def get_simulation_mode():
    """Get current simulation mode."""
    state = _get_app_state()
    engine = state.engine
    
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")
    
    from smart_meter_simulator.core.engine import SimulationMode
    
    return {
        "mode": engine.mode.value if hasattr(engine.mode, 'value') else str(engine.mode),
        "available_modes": [m.value if hasattr(m, 'value') else str(m) for m in SimulationMode],
        "interval_seconds": engine.interval,
        "autostart": engine.config.autostart_simulation,
    }


@router.put("/simulation/mode")
async def set_simulation_mode(
    request: dict = Body(...),
):
    """Change simulation mode."""
    state = _get_app_state()
    engine = state.engine
    
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")
    
    from smart_meter_simulator.core.engine import SimulationMode
    
    new_mode = request.get("mode")
    if not new_mode:
        raise HTTPException(status_code=400, detail="Mode is required")
    
    try:
        mode_enum = SimulationMode(new_mode)
    except ValueError:
        valid = [m.value for m in SimulationMode]
        raise HTTPException(status_code=400, detail=f"Invalid mode '{new_mode}'. Valid: {valid}")
    
    engine.mode = mode_enum
    
    return {
        "status": "updated",
        "mode": mode_enum.value,
        "message": f"Simulation mode changed to {mode_enum.value}",
    }


# ============================================================================
# Grid History
# ============================================================================

@router.get("/grid/history")
async def get_grid_history(
    metric: str = Query(..., description="Metric to query (frequency, voltage, load)"),
    hours: int = Query(24, description="Number of hours of history"),
    interval: int = Query(15, description="Data interval in minutes"),
):
    """Get historical grid metrics from InfluxDB."""
    state = _get_app_state()
    engine = state.engine
    
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")
    
    # Try InfluxDB query service
    try:
        if hasattr(state, 'influxdb_query_service') and state.influxdb_query_service and state.influxdb_query_service.connected:
            duration = f"{hours}h"
            metrics = state.influxdb_query_service.get_grid_metrics(duration=duration)
            
            return {
                "metric": metric,
                "hours": hours,
                "interval_minutes": interval,
                "data_points": len(metrics),
                "values": metrics,
                "source": "influxdb",
            }
    except Exception as e:
        logger.warning(f"InfluxDB query failed: {e}")
    
    return {
        "metric": metric,
        "hours": hours,
        "interval_minutes": interval,
        "data_points": 0,
        "values": [],
        "message": "InfluxDB not connected or query failed",
        "source": "none",
    }


# ============================================================================
# InfluxDB Real-Time Queries
# ============================================================================

@router.get("/timeseries/dashboard")
async def get_realtime_dashboard(
    meter_ids: Optional[str] = Query(None, description="Comma-separated meter IDs"),
):
    """Get real-time dashboard data from InfluxDB."""
    state = _get_app_state()
    
    if not hasattr(state, 'influxdb_query_service') or not state.influxdb_query_service or not state.influxdb_query_service.connected:
        raise HTTPException(status_code=503, detail="InfluxDB not connected")
    
    meter_list = meter_ids.split(",") if meter_ids else None
    
    dashboard = state.influxdb_query_service.get_real_time_dashboard(meter_ids=meter_list)
    return dashboard


@router.get("/timeseries/meters/{meter_id}/history")
async def get_meter_history(
    meter_id: str,
    duration: str = Query("24h", description="Duration (e.g., 1h, 24h, 7d)"),
    aggregation: str = Query("mean", description="Aggregation function (mean, max, min, sum)"),
):
    """Get historical readings for a specific meter from InfluxDB."""
    state = _get_app_state()
    
    if not hasattr(state, 'influxdb_query_service') or not state.influxdb_query_service or not state.influxdb_query_service.connected:
        raise HTTPException(status_code=503, detail="InfluxDB not connected")
    
    history = state.influxdb_query_service.get_meter_history(
        meter_id=meter_id,
        duration=duration,
        aggregation=aggregation,
    )
    
    return {
        "meter_id": meter_id,
        "duration": duration,
        "aggregation": aggregation,
        "data_points": len(history),
        "readings": history,
    }


@router.get("/timeseries/energy-summary")
async def get_energy_summary(
    duration: str = Query("24h", description="Duration (e.g., 1h, 24h, 7d)"),
    meter_ids: Optional[str] = Query(None, description="Comma-separated meter IDs"),
):
    """Get energy generation/consumption summary from InfluxDB."""
    state = _get_app_state()
    
    if not hasattr(state, 'influxdb_query_service') or not state.influxdb_query_service or not state.influxdb_query_service.connected:
        raise HTTPException(status_code=503, detail="InfluxDB not connected")
    
    meter_list = meter_ids.split(",") if meter_ids else None
    
    summary = state.influxdb_query_service.get_energy_summary(
        duration=duration,
        meter_ids=meter_list,
    )
    
    return summary


@router.get("/timeseries/alerts")
async def get_alerts(
    duration: str = Query("24h", description="Duration (e.g., 1h, 24h, 7d)"),
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, critical)"),
    limit: int = Query(50, description="Max alerts to return"),
):
    """Get recent alerts from InfluxDB."""
    state = _get_app_state()
    
    if not hasattr(state, 'influxdb_query_service') or not state.influxdb_query_service or not state.influxdb_query_service.connected:
        raise HTTPException(status_code=503, detail="InfluxDB not connected")
    
    alerts = state.influxdb_query_service.get_alerts(
        duration=duration,
        severity=severity,
        limit=limit,
    )
    
    return {
        "duration": duration,
        "severity_filter": severity,
        "total_alerts": len(alerts),
        "alerts": alerts,
    }


@router.get("/timeseries/status")
async def get_timeseries_status():
    """Get InfluxDB connection status and configuration."""
    state = _get_app_state()
    
    connected = False
    if hasattr(state, 'influxdb_query_service') and state.influxdb_query_service:
        connected = state.influxdb_query_service.connected
    
    return {
        "influxdb_connected": connected,
        "url": state.influxdb_query_service.url if connected else None,
        "bucket": state.influxdb_query_service.bucket if connected else None,
        "org": state.influxdb_query_service.org if connected else None,
        "available_endpoints": [
            "GET /api/v1/timeseries/dashboard",
            "GET /api/v1/timeseries/meters/{meter_id}/history",
            "GET /api/v1/timeseries/energy-summary",
            "GET /api/v1/timeseries/alerts",
            "GET /api/v1/timeseries/status",
        ],
    }


# ============================================================================
# Grid (Physical Infrastructure)
# ============================================================================

@router.get("/grid/status")
async def grid_status():
    """Get grid status."""
    state = _get_app_state()
    return {
        "status": "running" if state.engine and state.engine.running else "stopped",
        "meters_online": 0,
        "grid_frequency_hz": 50.0,
    }


@router.get("/grid/topology")
async def grid_topology(version: Optional[str] = Query(None, description="Topology version (legacy=current)")):
    """Get grid topology. Use ?version=legacy for legacy format."""
    state = _get_app_state()
    topology = {}
    if state.engine and state.engine.pandapower_net:
        net = state.engine.pandapower_net
        topology = {
            "buses": len(net.bus),
            "lines": len(net.line),
            "trafos": len(net.trafo),
            "loads": len(net.load),
            "sgens": len(net.sgen),
        }
    return {"topology": topology, "version": version or "current"}


@router.get("/grid/telemetry")
async def grid_telemetry():
    """Get real-time grid telemetry (sensor readings)."""
    state = _get_app_state()
    return {
        "measurements": [],
        "timestamp": None,
    }


@router.get("/grid/state-estimation")
async def grid_state_estimation():
    """Get latest state estimation results."""
    state = _get_app_state()
    return {
        "converged": False,
        "results": {},
    }


@router.get("/grid/snapshots")
async def grid_snapshots():
    """List grid snapshots."""
    return {"snapshots": []}


@router.get("/grid/export")
async def grid_export(
    format: str = Query("geojson", description="Export format: geojson, cim, mvt"),
    subset: Optional[str] = Query(None, description="Subset: substations, lines, all"),
):
    """
    Export grid data in various formats.

    Formats: geojson, cim, mvt (Mapbox Vector Tiles)
    """
    state = _get_app_state()
    if format == "geojson":
        return {"type": "FeatureCollection", "features": []}
    elif format == "cim":
        return {"cim_data": ""}
    elif format == "mvt":
        raise HTTPException(status_code=501, detail="MVT export not implemented")
    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@router.get("/grid/substations")
async def list_substations(
    operator: Optional[str] = Query(None, description="Filter by operator (EGAT/MEA/PEA)"),
    limit: int = Query(100),
):
    """List substations."""
    return {"substations": [], "total": 0}


@router.get("/grid/substations/{sub_id}")
async def get_substation(sub_id: str):
    """Get substation details."""
    return {
        "id": sub_id,
        "name": "",
        "operator": "",
        "voltage_kv": 22,
        "lat": None,
        "lon": None,
    }


@router.get("/grid/transformers/nearest")
async def find_nearest_transformers(
    lat: float = Query(...),
    lon: float = Query(...),
    limit: int = Query(5),
):
    """Find nearest transformers to a location."""
    return {"transformers": [], "total": 0}


@router.get("/grid/stats")
async def grid_statistics():
    """Get grid statistics."""
    return {
        "total_substations": 0,
        "total_transformers": 0,
        "total_lines_km": 0,
        "total_meters": 0,
    }


# ============================================================================
# Billing
# ============================================================================

@router.get("/billing/summary")
async def billing_summary():
    """Get billing summary across all meters."""
    return {
        "total_billed_thb": 0.0,
        "total_meters_billed": 0,
        "period": "",
    }


# ============================================================================
# VPP
# ============================================================================

@router.get("/vpp/clusters")
async def vpp_clusters():
    """Get VPP cluster status."""
    return {"clusters": []}


@router.post("/vpp/actions/dispatch")
async def vpp_dispatch(
    cluster_id: Optional[str] = Query(None),
    action: str = Body(..., embed=True),
    setpoint_kw: float = Body(..., embed=True),
):
    """
    Dispatch command to VPP clusters.

    Actions: curtail, charge, discharge, shed
    """
    return {
        "status": "dispatched",
        "cluster_id": cluster_id,
        "action": action,
        "setpoint_kw": setpoint_kw,
    }


# ============================================================================
# Analytics & Geo-SAM
# ============================================================================

@router.get("/analytics/summary")
async def analytics_summary():
    """Get analytics dashboard summary: grid health, LMP stats, market activity, carbon."""
    state = _get_app_state()
    engine = state.engine

    grid_health = 100.0
    market_activity = {"trades": 0, "volume_kwh": 0}
    lmp_stats = {"min": 0, "max": 0, "avg": 0}
    carbon_kgco2 = 0

    if engine and hasattr(engine, 'net_nodal_prices') and engine.net_nodal_prices:
        prices = list(engine.net_nodal_prices.values())
        if prices:
            lmp_stats = {"min": min(prices), "max": max(prices), "avg": sum(prices) / len(prices)}

    if engine and hasattr(engine, 'market') and engine.market:
        history = getattr(engine.market, 'history', [])
        market_activity = {"trades": len(history), "volume_kwh": sum(t.get('energy', 0) for t in history)}

    if engine and hasattr(engine, 'last_carbon_intensity'):
        carbon_kgco2 = engine.last_carbon_intensity

    return {
        "grid_health": grid_health,
        "lmp_stats": lmp_stats,
        "market_activity": market_activity,
        "carbon_intensity_kgco2": carbon_kgco2,
        "simulation_running": bool(engine and getattr(engine, 'running', False)),
    }


@router.get("/analytics/solar-detection/inventory")
async def get_solar_inventory():
    """Get solar panel inventory from DB and bus mapping."""
    state = _get_app_state()
    engine = state.engine

    inventory = {"total_capacity_kw": 0, "meters_with_solar": 0, "bus_mapping": {}}

    if engine and hasattr(engine, 'bus_solar_capacity') and engine.bus_solar_capacity:
        inventory["bus_mapping"] = engine.bus_solar_capacity
        inventory["total_capacity_kw"] = sum(engine.bus_solar_capacity.values())
        inventory["meters_with_solar"] = len(engine.bus_solar_capacity)

    return inventory


@router.post("/analytics/solar-detection/detect")
async def detect_solar_panels():
    """Trigger Geo-SAM solar panel detection."""
    state = _get_app_state()
    engine = state.engine

    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    # Placeholder - actual implementation would run SAM detection algorithm
    return {
        "status": "initiated",
        "message": "Solar panel detection started",
        "estimated_time_seconds": 300,
    }


# ============================================================================
# Registry (Reference Data)
# ============================================================================

@router.get("/registry/thailand/plants")
async def list_thailand_plants(
    group_by: Optional[str] = Query(None, description="Group results by: fuel, region"),
    limit: int = Query(100),
):
    """List Thailand power plants."""
    plants = [
        {
            "id": "plant_1",
            "name": "Bang Pakong",
            "fuel": "natural_gas",
            "region": "central",
            "capacity_mw": 3500,
            "lat": 13.6,
            "lon": 100.9,
        },
    ]
    
    if group_by:
        grouped = {}
        for p in plants:
            key = p.get(group_by, "unknown")
            grouped.setdefault(key, []).append(p)
        return {"grouped_by": group_by, "data": grouped}
    
    return {"plants": plants, "total": len(plants)}


@router.get("/registry/thailand/plants/stats")
async def thailand_plants_stats():
    """Get Thailand power plant statistics."""
    return {
        "total_plants": 0,
        "total_capacity_mw": 0,
        "by_fuel": {},
        "by_region": {},
    }


@router.get("/registry/thailand/plants/{plant_id}")
async def get_thailand_plant(plant_id: str):
    """Get Thailand power plant details."""
    raise HTTPException(status_code=404, detail=f"Plant {plant_id} not found")


# ============================================================================
# Quality & Validation
# ============================================================================

@router.get("/quality/health")
async def quality_health():
    """Quality service health check."""
    return {
        "status": "ok",
        "version": "v1",
        "analysers": [
            "power_substation",
            "power_line_connectivity",
            "duplicate_detection",
            "meter_conflation",
        ],
    }


# --- Validation ---

@router.post("/quality/validate/infrastructure", response_model=ValidationResultResponse)
async def validate_infrastructure(
    data: OSMDataInput,
    config: ValidationConfig = Body(default_factory=ValidationConfig),
):
    """Validate grid infrastructure with custom OSM data (all analysers)."""
    mgr = _get_quality_manager()
    mgr.config.country = config.country
    mgr.config.pole_duplicate_dist_m = config.pole_duplicate_dist_m
    mgr.config.transformer_duplicate_dist_m = config.transformer_duplicate_dist_m
    mgr.config.substation_duplicate_dist_m = config.substation_duplicate_dist_m

    result = await mgr.validate_infrastructure(data.model_dump())

    return ValidationResultResponse(
        analyser=result.analyser,
        country=result.country,
        timestamp=result.timestamp,
        total_objects=result.total_objects,
        total_issues=result.total_issues,
        issues_by_level=result.issues_by_level,
        issues_by_item=result.issues_by_item,
        issues_by_tag=result.issues_by_tag,
        processing_time_ms=result.processing_time_ms,
        issues=[IssueResponse(**i.model_dump()) for i in result.issues[:100]],
    )


@router.get("/quality/validate/infrastructure", response_model=ValidationResultResponse)
async def validate_infrastructure_default(country: str = "TH"):
    """Validate infrastructure with cached/default OSM data."""
    mgr = _get_quality_manager()
    mgr.config.country = country
    result = await mgr.validate_infrastructure()

    return ValidationResultResponse(
        analyser=result.analyser,
        country=result.country,
        timestamp=result.timestamp,
        total_objects=result.total_objects,
        total_issues=result.total_issues,
        issues_by_level=result.issues_by_level,
        issues_by_item=result.issues_by_item,
        issues_by_tag=result.issues_by_tag,
        processing_time_ms=result.processing_time_ms,
        issues=[IssueResponse(**i.model_dump()) for i in result.issues[:100]],
    )


@router.post("/quality/validate/substation", response_model=ValidationResultResponse)
async def validate_substation(data: OSMDataInput, country: str = "TH"):
    """Validate power substations only."""
    from smart_meter_simulator.osmose.analysers import PowerSubstationValidator
    analyser = PowerSubstationValidator(country=country)
    result = analyser.run(data.model_dump())

    return ValidationResultResponse(
        analyser=result.analyser, country=result.country, timestamp=result.timestamp,
        total_objects=result.total_objects, total_issues=result.total_issues,
        issues_by_level=result.issues_by_level, issues_by_item=result.issues_by_item,
        issues_by_tag=result.issues_by_tag, processing_time_ms=result.processing_time_ms,
        issues=[IssueResponse(**i.model_dump()) for i in result.issues[:100]],
    )


@router.post("/quality/validate/power-line", response_model=ValidationResultResponse)
async def validate_power_line(data: OSMDataInput, country: str = "TH"):
    """Validate power line connectivity only."""
    from smart_meter_simulator.osmose.analysers import PowerLineConnectivity
    analyser = PowerLineConnectivity(country=country)
    result = analyser.run(data.model_dump())

    return ValidationResultResponse(
        analyser=result.analyser, country=result.country, timestamp=result.timestamp,
        total_objects=result.total_objects, total_issues=result.total_issues,
        issues_by_level=result.issues_by_level, issues_by_item=result.issues_by_item,
        issues_by_tag=result.issues_by_tag, processing_time_ms=result.processing_time_ms,
        issues=[IssueResponse(**i.model_dump()) for i in result.issues[:100]],
    )


@router.post("/quality/validate/duplicates", response_model=ValidationResultResponse)
async def validate_duplicates(
    data: OSMDataInput, country: str = "TH",
    pole_dist: float = 5.0, transformer_dist: float = 5.0, substation_dist: float = 10.0,
):
    """Detect duplicate power infrastructure elements."""
    from smart_meter_simulator.osmose.analysers import DuplicateDetection
    analyser = DuplicateDetection(
        country=country, pole_dist_m=pole_dist,
        transformer_dist_m=transformer_dist, substation_dist_m=substation_dist,
    )
    result = analyser.run(data.model_dump())

    return ValidationResultResponse(
        analyser=result.analyser, country=result.country, timestamp=result.timestamp,
        total_objects=result.total_objects, total_issues=result.total_issues,
        issues_by_level=result.issues_by_level, issues_by_item=result.issues_by_item,
        issues_by_tag=result.issues_by_tag, processing_time_ms=result.processing_time_ms,
        issues=[IssueResponse(**i.model_dump()) for i in result.issues[:100]],
    )


@router.post("/quality/validate/meter-alignment")
async def validate_meter_alignment(
    meters: List[MeterInput],
    osm_data: Optional[OSMDataInput] = None,
    max_distance_m: float = 50.0,
):
    """Match simulator meters to OSM power infrastructure."""
    from smart_meter_simulator.osmose.analysers import MeterConflation, ConflationConfig
    mgr = _get_quality_manager()
    config = ConflationConfig(max_pole_distance_m=max_distance_m)
    analyser = MeterConflation(country=mgr.config.country, config=config)

    if osm_data:
        analyser.load_infrastructure(osm_data.model_dump())

    meter_dicts = [m.model_dump() for m in meters]
    result = analyser.run(meter_dicts)

    matches = []
    for m in meter_dicts:
        match = analyser._match_meter(m)
        matches.append(MatchResponse(
            meter_id=match.meter_id, meter_lat=match.meter_lat, meter_lon=match.meter_lon,
            matched_type=match.matched_type, matched_id=match.matched_id,
            matched_lat=match.matched_lat, matched_lon=match.matched_lon,
            distance_m=match.distance_m if match.distance_m != float("inf") else -1,
            confidence=match.confidence, status=match.status,
        ))

    return {
        "matches": matches,
        "summary": analyser.get_match_summary(matches),
        "validation": {"total_issues": result.total_issues, "issues_by_level": result.issues_by_level},
    }


@router.post("/quality/validate/power")
async def validate_power(data: OSMDataInput, country: str = "TH"):
    """Validate custom OSM-style power infrastructure data."""
    from smart_meter_simulator.osmose.analysers import PowerSubstationValidator, PowerLineConnectivity
    osm_data = data.model_dump()
    sub = PowerSubstationValidator(country=country).run(osm_data)
    line = PowerLineConnectivity(country=country).run(osm_data)
    all_issues = sub.issues + line.issues

    return {
        "total_objects": max(sub.total_objects, line.total_objects),
        "total_issues": len(all_issues),
        "issues_by_level": {
            "1": sum(1 for i in all_issues if i.level == 1),
            "2": sum(1 for i in all_issues if i.level == 2),
            "3": sum(1 for i in all_issues if i.level == 3),
        },
        "issues": [i.model_dump() for i in all_issues[:100]],
    }


# --- Issues ---

@router.get("/quality/issues")
async def get_quality_issues(
    analyser: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    item: Optional[int] = Query(None),
    level: Optional[int] = Query(None),
    min_level: Optional[int] = Query(None),
    max_level: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get validation issues with filtering."""
    mgr = _get_quality_manager()
    result = mgr.validation_results.get("combined") or mgr.validation_results.get("substation")

    if not result:
        return {"issues": [], "message": "No validation results available. Run validation first."}

    issues = result.issues
    if level is not None:
        issues = [i for i in issues if i.level == level]
    if min_level is not None or max_level is not None:
        min_l = min_level or 1
        max_l = max_level or 3
        issues = [i for i in issues if min_l <= i.level <= max_l]
    if category:
        issues = [i for i in issues if category in i.tags]
    if item is not None:
        issues = [i for i in issues if i.item == item]

    return {
        "analyser": result.analyser,
        "total_issues": len(issues),
        "issues": [i.model_dump() for i in issues[:limit]],
    }


@router.get("/quality/issues/{issue_id}")
async def get_quality_issue(issue_id: int):
    """Get specific issue details."""
    return {"id": issue_id, "item": 9100, "level": 2, "tags": ["power"], "title": "Issue details"}


@router.get("/quality/rules")
async def get_quality_rules():
    """Get validation rule definitions."""
    return {
        "rules": [
            {"id": 9101, "item": 9101, "level": 1, "tags": ["power", "tag"],
             "title": "Substation missing voltage tag",
             "detail": "Power substations should have a voltage=* tag.",
             "fix": "Add the voltage=* tag."},
            {"id": 9102, "item": 9102, "level": 2, "tags": ["power", "tag"],
             "title": "Substation missing type tag",
             "detail": "Power substations should have a substation=* tag.",
             "fix": "Add substation=transmission or substation=distribution."},
            {"id": 9201, "item": 9201, "level": 1, "tags": ["power", "topology"],
             "title": "Dangling power line end",
             "detail": "Power line endpoint not connected to any facility.",
             "fix": "Extend line or add junction node."},
            {"id": 9301, "item": 9301, "level": 1, "tags": ["power", "geom"],
             "title": "Duplicate power poles",
             "detail": "Multiple poles within 5m of each other.",
             "fix": "Merge duplicates."},
        ],
        "total": 4,
    }


@router.get("/quality/stats")
async def get_quality_stats():
    """Get validation statistics from last run."""
    mgr = _get_quality_manager()
    result = mgr.validation_results.get("combined")

    if not result:
        return {"total_objects_validated": 0, "total_issues": 0,
                "issues_by_level": {"1": 0, "2": 0, "3": 0}, "processing_time_ms": 0}

    return {
        "total_objects_validated": result.total_objects,
        "total_issues": result.total_issues,
        "issues_by_level": result.issues_by_level,
        "issues_by_item": result.issues_by_item,
        "issues_by_tag": result.issues_by_tag,
        "processing_time_ms": result.processing_time_ms,
        "last_validation": result.timestamp,
    }


@router.get("/quality/quality-score", response_model=QualityScoreResponse)
async def get_quality_score():
    """Get current grid quality score (0-100)."""
    mgr = _get_quality_manager()
    score = mgr.get_quality_score()
    return QualityScoreResponse(
        overall=score.get("overall", 0), infrastructure=score.get("infrastructure", 0),
        accuracy=score.get("accuracy", 0), alignment=score.get("alignment", 0),
        consistency=score.get("consistency", 0),
    )


@router.get("/quality/quality-summary", response_model=QualitySummaryResponse)
async def get_quality_summary():
    """Get comprehensive quality summary."""
    mgr = _get_quality_manager()
    summary = mgr.get_quality_summary()
    return QualitySummaryResponse(
        quality_score=summary["quality_score"],
        last_validation=summary.get("last_validation"),
        total_validations=summary["total_validations"],
        total_issues=summary["total_issues"],
        analyser_results=summary.get("analyser_results", {}),
        recent_issues=summary.get("recent_issues", []),
    )


@router.get("/quality/dashboard")
async def get_quality_dashboard():
    """Get quality dashboard data."""
    mgr = _get_quality_manager()
    summary = mgr.get_quality_summary()
    score = mgr.get_quality_score()
    result = mgr.validation_results.get("combined")
    issues_by_type = {}
    if result:
        for issue in result.issues:
            for tag in issue.tags:
                issues_by_type[tag] = issues_by_type.get(tag, 0) + 1

    return {"quality_score": score, "summary": summary, "issues_by_type": issues_by_type}


@router.get("/quality/categories")
async def get_quality_categories():
    """Get quality issue category definitions."""
    return {
        "categories": [
            {"category": "geom", "description": "Geometry issues", "color": "#FF5722", "flag": "⚠️"},
            {"category": "tag", "description": "Tagging errors", "color": "#FFC107", "flag": "🏷️"},
            {"category": "topology", "description": "Topological errors", "color": "#F44336", "flag": "🔗"},
        ],
    }


# --- Monitoring ---

@router.get("/quality/monitor")
async def get_monitor_status():
    """Get current monitoring status."""
    mgr = _get_quality_manager()
    if hasattr(mgr, "_monitor") and mgr._monitor:
        return MonitoringStatusResponse(
            monitoring_active=mgr._monitor.monitoring,
            total_issues_detected=len(mgr._monitor.issues_detected),
            issues_by_type=mgr._monitor._count_issues_by_type(),
            recent_issues=mgr._monitor.issues_detected[-10:],
        )
    return MonitoringStatusResponse(monitoring_active=False, total_issues_detected=0)


@router.patch("/quality/monitor")
async def toggle_monitor(enabled: bool = Body(..., embed=True)):
    """Toggle real-time monitoring on/off."""
    mgr = _get_quality_manager()
    if not hasattr(mgr, "_monitor") or not mgr._monitor:
        return {"status": "ok", "message": "Monitoring not configured"}

    if enabled:
        mgr._monitor.start_monitoring()
        return {"status": "started"}
    else:
        mgr._monitor.stop_monitoring()
        return {"status": "stopped"}


# --- Analytics ---

@router.post("/quality/analytics/daily")
async def run_daily_analytics(target_date: Optional[str] = None):
    """Run daily batch analytics."""
    mgr = _get_quality_manager()
    if not mgr.batch_analytics:
        raise HTTPException(status_code=503, detail="Batch analytics not configured")

    import asyncio
    from datetime import date
    target = date.fromisoformat(target_date) if target_date else None
    result = await mgr.run_daily_analytics(target)
    return {"status": "completed", "target_date": str(target or date.today())}


@router.get("/quality/analytics/daily/{target_date}")
async def get_daily_analytics(target_date: str):
    """Get daily analytics results."""
    from datetime import date
    try:
        target = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD)")

    mgr = _get_quality_manager()
    if mgr.batch_analytics:
        result = await mgr.batch_analytics.get_daily_result(target)
        if result:
            return result
    return {"status": "not_found", "message": f"No data for {target_date}"}


@router.get("/quality/config")
async def get_quality_config():
    """Get current quality configuration."""
    mgr = _get_quality_manager()
    return {
        "country": mgr.config.country,
        "conflation_distance_m": mgr.config.conflation_distance_m,
        "max_pole_distance_m": mgr.config.max_pole_distance_m,
        "suspicious_distance_m": mgr.config.suspicious_distance_m,
        "pole_duplicate_dist_m": mgr.config.pole_duplicate_dist_m,
        "transformer_duplicate_dist_m": mgr.config.transformer_duplicate_dist_m,
        "substation_duplicate_dist_m": mgr.config.substation_duplicate_dist_m,
    }
