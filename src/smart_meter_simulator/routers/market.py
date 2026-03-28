from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from .dependencies import get_engine
from ..config.thai_market import (
    TariffCategory,
    UtilityProvider,
    get_ft_for_month,
    GRID_BUYBACK_RATE,
    GRID_PURCHASE_RATE_HIGH_TIER,
    RESIDENTIAL_WHEELING_COST_AVG,
    TYPICAL_P2P_PRICE,
)
from ..core.price_comparison import (
    PriceComparisonEngine,
    BlockchainP2PPricingModel,
    SingleBuyerPricingModel,
)
from ..transport.websocket import WebSocketManager
from ..core import app_state
from ..core.price_history import PriceHistoryManager

router = APIRouter(tags=["Market"])


# ============================================================================
# Request/Response Models
# ============================================================================

class PriceComparisonRequest(BaseModel):
    """Request model for price comparison between utility and P2P."""
    energy_kwh: float = Field(..., description="Energy amount in kWh")
    utility_provider: str = Field(default="PEA", description="Utility provider (PEA or MEA)")
    tariff_category: str = Field(default="1.1.2", description="Tariff category (1.1.1, 1.1.2, 1.2)")
    billing_month: int = Field(default=1, ge=1, le=12, description="Billing month (1-12)")
    billing_year: int = Field(default=2026, description="Billing year")
    p2p_price: Optional[float] = Field(default=None, description="P2P price (auto-calculated if None)")
    wheeling_cost: float = Field(default=1.76, description="Wheeling cost (Baht/kWh)")
    market_clearing_price: Optional[float] = Field(default=None, description="Market clearing price")
    market_volume: float = Field(default=100.0, description="Market volume (kWh)")
    market_sentiment: str = Field(default="Stable", description="Market sentiment")


class UtilityPriceResponse(BaseModel):
    """Utility price breakdown."""
    provider: str
    tariff_category: str
    tariff_type: str  # "Ladder" or "TOU"
    energy_charge_baht: float
    ft_charge_baht: float
    service_charge_baht: float
    total_before_vat_baht: float
    vat_baht: float
    total_amount_baht: float
    average_rate_baht_kwh: float
    ft_rate_baht_kwh: float


class P2PPriceResponse(BaseModel):
    """P2P price breakdown."""
    market_clearing_price_baht_kwh: float
    wheeling_cost_baht_kwh: float
    buyer_total_baht_kwh: float
    seller_net_baht_kwh: float
    energy_cost_baht: float
    wheeling_charge_baht: float
    buyer_total_cost_baht: float
    seller_net_revenue_baht: float
    market_sentiment: str


class PriceComparisonResponse(BaseModel):
    """Complete price comparison response."""
    timestamp: str
    energy_kwh: float
    
    # Utility pricing
    utility: UtilityPriceResponse
    
    # P2P pricing
    p2p: P2PPriceResponse
    
    # Comparison analysis
    analysis: dict
    
    # Recommendation
    recommendation: str


# ============================================================================
# Price Comparison API Endpoints
# ============================================================================

@router.post("/v1/price/compare", response_model=PriceComparisonResponse)
async def compare_prices(request: PriceComparisonRequest):
    """
    Compare utility (PEA/MEA) prices with blockchain P2P dynamic prices.
    
    This endpoint provides a comprehensive economic analysis of:
    - Traditional utility billing (Single-Buyer model)
    - Blockchain P2P trading (Decentralized model)
    - Cost savings and welfare analysis
    - Trading recommendations
    
    ## Example Usage:
    ```json
    {
        "energy_kwh": 500,
        "utility_provider": "PEA",
        "tariff_category": "1.1.2",
        "billing_month": 3,
        "billing_year": 2026,
        "wheeling_cost": 1.76
    }
    ```
    """
    # Map tariff category string to enum
    tariff_map = {
        "1.1.1": TariffCategory.TYPE_1_1_1,
        "1.1.2": TariffCategory.TYPE_1_1_2,
        "1.2": TariffCategory.TYPE_1_2,
        "1.3": TariffCategory.TYPE_1_3,
    }
    tariff_category = tariff_map.get(request.tariff_category, TariffCategory.TYPE_1_1_2)
    
    # Map utility provider string to enum
    provider_map = {
        "PEA": UtilityProvider.PEA,
        "MEA": UtilityProvider.MEA,
        "EGAT": UtilityProvider.EGAT,
    }
    utility_provider = provider_map.get(request.utility_provider, UtilityProvider.PEA)
    
    # Get Ft rate for billing month
    ft_rate = get_ft_for_month(request.billing_month)
    
    # Initialize comparison engine
    engine = PriceComparisonEngine(
        tariff_category=tariff_category,
        utility_provider=utility_provider,
        ft_rate=ft_rate,
        wheeling_cost=request.wheeling_cost,
    )
    
    # Get current timestamp
    timestamp = datetime.now(timezone.utc)
    
    # Calculate P2P price if not provided
    if request.p2p_price is None:
        p2p_model = BlockchainP2PPricingModel(wheeling_cost_baht_kwh=request.wheeling_cost)
        
        # Use market clearing price if provided, otherwise simulate
        mcp = request.market_clearing_price or p2p_model.simulate_market_price(
            timestamp=timestamp,
            supply_kwh=request.market_volume,
            demand_kwh=request.market_volume * 1.1,  # Slightly higher demand
            base_price=TYPICAL_P2P_PRICE,
        )
        
        # Get P2P price with market context
        p2p_price = p2p_model.get_price(
            timestamp=timestamp,
            market_clearing_price=mcp,
            market_volume=request.market_volume,
            market_sentiment=request.market_sentiment,
        )
    else:
        # Use provided P2P price
        p2p_model = BlockchainP2PPricingModel(
            wheeling_cost_baht_kwh=request.wheeling_cost,
            grid_reference_rate=GRID_PURCHASE_RATE_HIGH_TIER,
            feedin_reference_rate=GRID_BUYBACK_RATE,
        )
        p2p_price = p2p_model.get_price(
            timestamp=timestamp,
            market_clearing_price=request.p2p_price,
            market_volume=request.market_volume,
            market_sentiment=request.market_sentiment,
        )
    
    # Compare prices
    comparison = engine.compare_prices(
        timestamp=timestamp,
        energy_kwh=request.energy_kwh,
        market_clearing_price=p2p_price.market_clearing_price_baht_kwh,
        market_volume=request.market_volume,
        market_sentiment=request.market_sentiment,
    )
    
    # Build utility price response
    tariff_type_str = "TOU" if tariff_category == TariffCategory.TYPE_1_2 else "Ladder"
    
    utility_response = UtilityPriceResponse(
        provider=request.utility_provider,
        tariff_category=request.tariff_category,
        tariff_type=tariff_type_str,
        energy_charge_baht=comparison.single_buyer_cost_baht * 0.9,  # Approximate
        ft_charge_baht=request.energy_kwh * ft_rate,
        service_charge_baht=24.62 if tariff_category == TariffCategory.TYPE_1_1_2 else 8.19,
        total_before_vat_baht=comparison.single_buyer_cost_baht,
        vat_baht=comparison.single_buyer_cost_baht * 0.07,
        total_amount_baht=comparison.single_buyer_cost_baht * 1.07,
        average_rate_baht_kwh=comparison.single_buyer_rate_baht_kwh,
        ft_rate_baht_kwh=ft_rate,
    )
    
    # Build P2P price response
    p2p_response = P2PPriceResponse(
        market_clearing_price_baht_kwh=p2p_price.market_clearing_price_baht_kwh,
        wheeling_cost_baht_kwh=request.wheeling_cost,
        buyer_total_baht_kwh=p2p_price.buyer_total_baht_kwh,
        seller_net_baht_kwh=p2p_price.seller_net_baht_kwh,
        energy_cost_baht=comparison.p2p_buyer_cost_baht,
        wheeling_charge_baht=request.energy_kwh * request.wheeling_cost * 0.5,
        buyer_total_cost_baht=comparison.p2p_buyer_cost_baht + (request.energy_kwh * request.wheeling_cost * 0.5),
        seller_net_revenue_baht=comparison.p2p_seller_revenue_baht - (request.energy_kwh * request.wheeling_cost * 0.5),
        market_sentiment=p2p_price.market_sentiment,
    )
    
    # Build analysis
    analysis = {
        "buyer_savings_baht": comparison.buyer_savings_baht,
        "buyer_savings_percent": comparison.buyer_savings_percent,
        "seller_gain_baht": comparison.seller_gain_baht,
        "seller_gain_percent": comparison.seller_gain_percent,
        "total_welfare_gain_baht": comparison.total_welfare_gain_baht,
        "is_p2p_beneficial": comparison.is_p2p_beneficial,
        "break_even_price_baht_kwh": comparison.single_buyer_rate_baht_kwh - request.wheeling_cost,
    }
    
    # Generate recommendation
    if comparison.is_p2p_beneficial:
        if comparison.buyer_savings_percent > 20:
            recommendation = "STRONG BUY - P2P trading offers significant savings (>20%)"
        elif comparison.buyer_savings_percent > 10:
            recommendation = "BUY - P2P trading offers moderate savings (10-20%)"
        else:
            recommendation = "HOLD - P2P trading offers marginal savings (<10%)"
    else:
        recommendation = "AVOID - Utility rates are more economical for this scenario"
    
    return PriceComparisonResponse(
        timestamp=timestamp.isoformat(),
        energy_kwh=request.energy_kwh,
        utility=utility_response,
        p2p=p2p_response,
        analysis=analysis,
        recommendation=recommendation,
    )


@router.get("/v1/price/utility-rates")
async def get_utility_rates(
    provider: str = Query(default="PEA", description="Utility provider (PEA/MEA)"),
    tariff_category: str = Query(default="1.1.2", description="Tariff category"),
    billing_month: int = Query(default=1, ge=1, le=12, description="Billing month"),
    energy_kwh: float = Query(default=500.0, description="Energy consumption for calculation"),
):
    """
    Get current utility rates for PEA or MEA.
    
    Returns detailed tariff information including:
    - Ladder rates or TOU rates
    - Ft charge for the billing month
    - Service charges
    - Example bill calculation
    """
    tariff_map = {
        "1.1.1": TariffCategory.TYPE_1_1_1,
        "1.1.2": TariffCategory.TYPE_1_1_2,
        "1.2": TariffCategory.TYPE_1_2,
    }
    tariff_category_enum = tariff_map.get(tariff_category, TariffCategory.TYPE_1_1_2)
    
    ft_rate = get_ft_for_month(billing_month)
    
    # Calculate sample bill using ladder tariff (simplified for API)
    # For TOU, we use an equivalent ladder calculation
    model = SingleBuyerPricingModel(
        tariff_category=tariff_category_enum,
        utility_provider=UtilityProvider.PEA if provider == "PEA" else UtilityProvider.MEA,
        ft_rate=ft_rate,
    )
    
    # For TOU tariffs, use a simplified flat rate approximation
    if tariff_category_enum == TariffCategory.TYPE_1_2:
        # TOU average rate approximation (weighted average of peak/off-peak)
        avg_rate = 4.0  # Approximate average Baht/kWh
        total_amount = energy_kwh * avg_rate + energy_kwh * ft_rate + 33.29
        average_rate = avg_rate + ft_rate
    else:
        bill = model.calculate_monthly_bill(
            consumption_kwh=energy_kwh,
            month=billing_month,
            year=2026,
        )
        total_amount = bill["total_amount_baht"]
        average_rate = bill["average_rate_baht_kwh"]
    
    return {
        "provider": provider,
        "tariff_category": tariff_category,
        "billing_month": billing_month,
        "ft_rate_baht_kwh": ft_rate,
        "grid_buyback_rate_baht_kwh": GRID_BUYBACK_RATE,
        "grid_purchase_rate_baht_kwh": GRID_PURCHASE_RATE_HIGH_TIER,
        "sample_bill": {
            "total_kwh": energy_kwh,
            "total_amount_baht": total_amount,
            "average_rate_baht_kwh": average_rate,
            "ft_charge_baht": energy_kwh * ft_rate,
        },
        "average_rate_baht_kwh": average_rate,
    }


@router.post("/v1/p2p/calculate-cost")
async def calculate_p2p_cost(request: dict, engine=Depends(get_engine)):
    """Calculate P2P transaction cost"""
    try:
        buyer_zone = int(request.get('buyer_zone_id', 0))
        seller_zone = int(request.get('seller_zone_id', 0))
        qty = float(request.get('energy_amount', 0.0))
        agreed_price = float(request.get('agreed_price', 0.25))
        
        distance = abs(buyer_zone - seller_zone)
        wheeling_rate = 0.02 + (0.015 * distance)
        loss_factor = 0.02 + (0.01 * distance)
        
        energy_cost = agreed_price * qty
        wheeling_charge = wheeling_rate * qty
        loss_cost = (energy_cost * loss_factor)
        
        return {
            "energy_cost": float(energy_cost),
            "wheeling_charge": float(wheeling_charge),
            "total_cost": float(energy_cost + wheeling_charge + loss_cost),
            "effective_energy": float(qty * (1.0 - loss_factor))
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/report")
async def get_analytics_report(engine=Depends(get_engine)):
    """Get summarized grid health report"""
    return jsonable_encoder(engine.analytics.get_summary())


# ============================================================================
# Revenue Comparison API Endpoints
# ============================================================================

class RevenueSimulationRequest(BaseModel):
    """Request for revenue simulation comparing single-buyer vs P2P."""
    # Prosumer profile
    solar_capacity_kwp: float = Field(default=5.0, description="Solar capacity (kWp)")
    battery_capacity_kwh: float = Field(default=0.0, description="Battery capacity (kWh)")
    
    # Simulation parameters
    simulation_days: int = Field(default=30, ge=1, le=365, description="Simulation duration (days)")
    billing_month: int = Field(default=3, ge=1, le=12, description="Billing month for tariff")
    
    # Market parameters
    self_consumption_ratio: float = Field(default=0.3, ge=0, le=1, description="Self-consumption ratio")
    p2p_participation_rate: float = Field(default=0.8, ge=0, le=1, description="P2P market participation")
    wheeling_cost: float = Field(default=1.76, description="Wheeling cost (Baht/kWh)")
    
    # Utility provider
    utility_provider: str = Field(default="PEA", description="Utility provider (PEA/MEA)")
    tariff_category: str = Field(default="1.1.2", description="Tariff category")


class RevenueComparisonResponse(BaseModel):
    """Revenue comparison response."""
    # Simulation metadata
    timestamp: str
    simulation_days: int
    solar_capacity_kwp: float
    
    # Single-buyer revenue
    single_buyer: Dict[str, Any]
    
    # P2P blockchain revenue
    p2p_blockchain: Dict[str, Any]
    
    # Comparison analysis
    comparison: Dict[str, Any]
    
    # Recommendations
    recommendations: List[str]


@router.post("/v1/revenue/compare", response_model=RevenueComparisonResponse)
async def compare_revenue(request: RevenueSimulationRequest):
    """
    Compare revenue between single-buyer (utility) and P2P blockchain models.
    
    This endpoint simulates energy trading over a period and compares:
    - **Single-Buyer Model**: Revenue from selling excess solar to utility at fixed feed-in tariff
    - **P2P Blockchain Model**: Revenue from selling excess solar via P2P market at dynamic prices
    
    ## Revenue Components:
    
    ### Single-Buyer:
    - Export revenue = Export kWh × Feed-in tariff (2.20 Baht/kWh)
    
    ### P2P Blockchain:
    - Export revenue = Export kWh × P2P price × P2P participation rate
    - Wheeling cost = Export kWh × Wheeling rate
    - Net revenue = Export revenue - Wheeling cost
    
    ## Example:
    ```json
    {
        "solar_capacity_kwp": 5.0,
        "battery_capacity_kwh": 10.0,
        "simulation_days": 30,
        "billing_month": 3,
        "self_consumption_ratio": 0.3,
        "p2p_participation_rate": 0.8
    }
    ```
    """
    # Map tariff category
    tariff_map = {
        "1.1.1": TariffCategory.TYPE_1_1_1,
        "1.1.2": TariffCategory.TYPE_1_1_2,
        "1.2": TariffCategory.TYPE_1_2,
    }
    tariff_category = tariff_map.get(request.tariff_category, TariffCategory.TYPE_1_1_2)
    
    # Simulation parameters
    days = request.simulation_days
    solar_kwp = request.solar_capacity_kwp
    
    # Estimate daily generation (Thailand: ~4-5 kWh/kWp/day average)
    daily_generation = solar_kwp * 4.5  # kWh/day
    total_generation = daily_generation * days
    
    # Self-consumption vs export
    self_consumed = total_generation * request.self_consumption_ratio
    available_for_export = total_generation - self_consumed
    
    # P2P vs utility export split
    p2p_export = available_for_export * request.p2p_participation_rate
    utility_export = available_for_export * (1 - request.p2p_participation_rate)
    
    # ========================================================================
    # Single-Buyer Model Revenue
    # ========================================================================
    # All export goes to utility at fixed feed-in tariff
    single_buyer_export_revenue = available_for_export * GRID_BUYBACK_RATE
    
    # Self-consumption savings (avoided purchase at retail rate)
    # Average retail rate for Type 1.1.2 high tier
    avg_retail_rate = GRID_PURCHASE_RATE_HIGH_TIER
    self_consumption_savings = self_consumed * avg_retail_rate
    
    single_buyer_total = {
        "export_revenue_baht": single_buyer_export_revenue,
        "self_consumption_savings_baht": self_consumption_savings,
        "total_revenue_baht": single_buyer_export_revenue + self_consumption_savings,
        "export_kwh": available_for_export,
        "self_consumed_kwh": self_consumed,
        "avg_export_rate_baht_kwh": GRID_BUYBACK_RATE,
        "model": "Single-Buyer (Utility Feed-in Tariff)",
    }
    
    # ========================================================================
    # P2P Blockchain Model Revenue
    # ========================================================================
    # Initialize P2P pricing model
    p2p_model = BlockchainP2PPricingModel(
        wheeling_cost_baht_kwh=request.wheeling_cost,
        grid_reference_rate=GRID_PURCHASE_RATE_HIGH_TIER,
        feedin_reference_rate=GRID_BUYBACK_RATE,
    )
    
    # Simulate daily P2P prices and calculate revenue
    daily_p2p_revenue = 0.0
    daily_prices = []
    
    for day in range(days):
        # Simulate daily supply/demand dynamics
        # Supply varies with weather (solar generation)
        weather_factor = 0.5 + 0.5 * ((day % 7) / 7)  # Weekly weather pattern
        daily_supply = daily_generation * weather_factor
        
        # Demand varies (higher on weekdays, lower on weekends)
        is_weekend = (day % 7) >= 5
        daily_demand = daily_generation * (0.8 if is_weekend else 1.2)
        
        # Calculate daily MCP using formula
        daily_mcp = p2p_model.simulate_market_price(
            timestamp=datetime.now(timezone.utc),
            supply_kwh=daily_supply,
            demand_kwh=daily_demand,
            base_price=TYPICAL_P2P_PRICE,
            use_formula=True,
        )
        daily_prices.append(daily_mcp)
        
        # Daily P2P export revenue
        daily_p2p_export = p2p_export / days
        daily_wheeling = daily_p2p_export * request.wheeling_cost * 0.5  # Split wheeling
        
        # Net revenue for this day
        daily_revenue = (daily_p2p_export * daily_mcp) - daily_wheeling
        daily_p2p_revenue += daily_revenue
    
    # P2P export revenue
    p2p_avg_price = sum(daily_prices) / len(daily_prices) if daily_prices else TYPICAL_P2P_PRICE
    p2p_gross_revenue = p2p_export * p2p_avg_price
    p2p_wheeling_cost = p2p_export * request.wheeling_cost * 0.5
    p2p_net_revenue = p2p_gross_revenue - p2p_wheeling_cost
    
    # Utility export (remaining not sold via P2P)
    utility_export_revenue = utility_export * GRID_BUYBACK_RATE
    
    # Self-consumption savings (same as single-buyer)
    self_consumption_savings_p2p = self_consumed * avg_retail_rate
    
    p2p_total = {
        "p2p_export_revenue_baht": p2p_gross_revenue,
        "p2p_wheeling_cost_baht": p2p_wheeling_cost,
        "p2p_net_revenue_baht": p2p_net_revenue,
        "utility_export_revenue_baht": utility_export_revenue,
        "self_consumption_savings_baht": self_consumption_savings_p2p,
        "total_revenue_baht": p2p_net_revenue + utility_export_revenue + self_consumption_savings_p2p,
        "p2p_export_kwh": p2p_export,
        "utility_export_kwh": utility_export,
        "self_consumed_kwh": self_consumed,
        "avg_p2p_price_baht_kwh": p2p_avg_price,
        "wheeling_cost_baht_kwh": request.wheeling_cost,
        "model": "P2P Blockchain (Dynamic Pricing)",
    }
    
    # ========================================================================
    # Comparison Analysis
    # ========================================================================
    revenue_difference = p2p_total["total_revenue_baht"] - single_buyer_total["total_revenue_baht"]
    revenue_increase_percent = (revenue_difference / single_buyer_total["total_revenue_baht"] * 100) if single_buyer_total["total_revenue_baht"] > 0 else 0
    
    # Per-kWh analysis
    single_buyer_per_kwh = single_buyer_total["total_revenue_baht"] / total_generation if total_generation > 0 else 0
    p2p_per_kwh = p2p_total["total_revenue_baht"] / total_generation if total_generation > 0 else 0
    
    comparison = {
        "revenue_difference_baht": revenue_difference,
        "revenue_increase_percent": revenue_increase_percent,
        "is_p2p_better": revenue_difference > 0,
        "single_buyer_total_baht": single_buyer_total["total_revenue_baht"],
        "p2p_total_baht": p2p_total["total_revenue_baht"],
        "single_buyer_per_kwh_baht": single_buyer_per_kwh,
        "p2p_per_kwh_baht": p2p_per_kwh,
        "break_even_p2p_price_baht_kwh": GRID_BUYBACK_RATE + (request.wheeling_cost * 0.5),
        "total_generation_kwh": total_generation,
        "export_ratio": available_for_export / total_generation if total_generation > 0 else 0,
    }
    
    # ========================================================================
    # Recommendations
    # ========================================================================
    recommendations = []
    
    if revenue_difference > 0:
        if revenue_increase_percent > 50:
            recommendations.append("EXCELLENT: P2P blockchain increases revenue by >50%")
        elif revenue_increase_percent > 20:
            recommendations.append("GOOD: P2P blockchain increases revenue by 20-50%")
        else:
            recommendations.append("MODERATE: P2P blockchain increases revenue by <20%")
        
        if request.p2p_participation_rate < 1.0:
            recommendations.append(f"Consider increasing P2P participation from {request.p2p_participation_rate*100:.0f}% to 100% for maximum revenue")
        
        if request.self_consumption_ratio < 0.4:
            recommendations.append("Consider adding battery storage to increase self-consumption ratio")
    else:
        recommendations.append("Single-buyer model currently more profitable")
        recommendations.append("Consider reducing wheeling costs or increasing P2P participation efficiency")
    
    # Battery recommendation
    if request.battery_capacity_kwh == 0 and solar_kwp > 3:
        recommendations.append(f"Adding battery storage for {solar_kwp} kWp system could increase self-consumption and revenue")
    
    return RevenueComparisonResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        simulation_days=days,
        solar_capacity_kwp=solar_kwp,
        single_buyer=single_buyer_total,
        p2p_blockchain=p2p_total,
        comparison=comparison,
        recommendations=recommendations,
    )


@router.get("/v1/revenue/optimize")
async def optimize_revenue(
    solar_capacity_kwp: float = Query(default=5.0, description="Solar capacity (kWp)"),
    simulation_days: int = Query(default=30, description="Simulation days"),
    billing_month: int = Query(default=3, description="Billing month"),
):
    """
    Optimize revenue by finding best P2P participation and self-consumption ratios.
    
    Returns optimal configuration for maximum revenue.
    """
    best_revenue = 0.0
    best_config = {}
    
    # Grid search over participation and self-consumption ratios
    for p2p_rate in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        for sc_ratio in [0.2, 0.3, 0.4, 0.5, 0.6]:
            request = RevenueSimulationRequest(
                solar_capacity_kwp=solar_capacity_kwp,
                simulation_days=simulation_days,
                billing_month=billing_month,
                self_consumption_ratio=sc_ratio,
                p2p_participation_rate=p2p_rate,
            )
            
            # Calculate revenue (simplified version of compare_revenue)
            days = simulation_days
            daily_generation = solar_capacity_kwp * 4.5
            total_generation = daily_generation * days
            
            self_consumed = total_generation * sc_ratio
            available = total_generation - self_consumed
            p2p_export = available * p2p_rate
            utility_export = available * (1 - p2p_rate)
            
            # P2P revenue
            p2p_model = BlockchainP2PPricingModel()
            mcp = p2p_model.simulate_market_price(
                timestamp=datetime.now(timezone.utc),
                supply_kwh=daily_generation,
                demand_kwh=daily_generation * 1.1,
                base_price=TYPICAL_P2P_PRICE,
            )
            
            p2p_revenue = p2p_export * (mcp - 1.76 * 0.5)
            utility_revenue = utility_export * GRID_BUYBACK_RATE
            sc_savings = self_consumed * GRID_PURCHASE_RATE_HIGH_TIER
            
            total = p2p_revenue + utility_revenue + sc_savings
            
            if total > best_revenue:
                best_revenue = total
                best_config = {
                    "p2p_participation_rate": p2p_rate,
                    "self_consumption_ratio": sc_ratio,
                    "avg_p2p_price_baht_kwh": mcp,
                }
    
    return {
        "optimal_revenue_baht": best_revenue,
        "optimal_configuration": best_config,
        "solar_capacity_kwp": solar_capacity_kwp,
        "simulation_days": simulation_days,
    }


# ============================================================================
# WebSocket Price Streaming Endpoints
# ============================================================================

@router.websocket("/ws/prices")
async def websocket_price_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time P2P price streaming.
    
    Connect to receive continuous price updates based on market dynamics.
    
    ## Message Format
    
    Server → Client:
    ```json
    {
        "type": "price_update",
        "timestamp": "2026-03-21T12:00:00Z",
        "data": {
            "market_clearing_price_baht_kwh": 3.30,
            "buyer_total_baht_kwh": 4.18,
            "seller_net_baht_kwh": 2.42,
            "market_sentiment": "BALANCED",
            "tou_period": "ON_PEAK"
        },
        "formula": {
            "name": "GridTokenX Dynamic Pricing",
            "equation": "p_t = arctan(e^D_t) + arctan(R_t)/10 + p_min"
        },
        "comparison": {
            "p2p_savings_percent": 15.5,
            "seller_premium_percent": 50.0
        }
    }
    ```
    
    ## Example (JavaScript)
    ```javascript
    const ws = new WebSocket('ws://localhost:8082/api/v1/market/ws/prices');
    ws.onmessage = (event) => {
        const price = JSON.parse(event.data);
        console.log('Current P2P price:', price.data.market_clearing_price_baht_kwh);
    };
    ```
    """
    await app_state.websocket_manager.connect(websocket)
    try:
        # Send initial price update immediately
        from ..core.price_streamer import PriceStreamer
        streamer = PriceStreamer(app_state.websocket_manager)
        initial_price = streamer._calculate_price()
        await websocket.send_json(initial_price)
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await app_state.websocket_manager.disconnect(websocket)


# ============================================================================
# Price History API Endpoints
# ============================================================================

@router.get("/v1/price/history")
async def get_price_history(
    limit: int = Query(default=100, ge=1, le=1000, description="Number of records"),
):
    """
    Get recent P2P price history.
    
    Returns most recent price records up to the specified limit.
    """
    if not app_state.price_history:
        raise HTTPException(status_code=503, detail="Price history not initialized")
    
    records = app_state.price_history.get_recent_prices(limit=limit)
    return {
        "count": len(records),
        "records": [
            {
                "timestamp": r.timestamp,
                "market_clearing_price_baht_kwh": r.market_clearing_price_baht_kwh,
                "buyer_total_baht_kwh": r.buyer_total_baht_kwh,
                "seller_net_baht_kwh": r.seller_net_baht_kwh,
                "supply_kwh": r.supply_kwh,
                "demand_kwh": r.demand_kwh,
                "demand_ratio": r.demand_ratio,
                "market_sentiment": r.market_sentiment,
                "tou_period": r.tou_period,
            }
            for r in records
        ],
    }


@router.get("/v1/price/history/statistics")
async def get_price_statistics(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours"),
):
    """
    Get price statistics for a time period.
    
    Returns statistical metrics (avg, min, max, std dev) for the specified period.
    """
    if not app_state.price_history:
        raise HTTPException(status_code=503, detail="Price history not initialized")
    
    stats = app_state.price_history.get_statistics(hours=hours)
    return {
        "period_hours": hours,
        "statistics": stats,
    }


@router.get("/v1/price/history/hourly")
async def get_hourly_summary(
    hours: int = Query(default=24, ge=1, le=168, description="Number of hours"),
):
    """
    Get hourly aggregated price data.
    
    Returns hourly summaries with avg, min, max prices.
    """
    if not app_state.price_history:
        raise HTTPException(status_code=503, detail="Price history not initialized")
    
    summary = app_state.price_history.get_hourly_summary(hours=hours)
    return {
        "period_hours": hours,
        "hourly_data": summary,
    }


@router.get("/api/v1/price/history/daily")
async def get_daily_summary(
    days: int = Query(default=7, ge=1, le=30, description="Number of days"),
):
    """
    Get daily aggregated price data.
    
    Returns daily summaries with avg, min, max prices.
    """
    if not app_state.price_history:
        raise HTTPException(status_code=503, detail="Price history not initialized")
    
    summary = app_state.price_history.get_daily_summary(days=days)
    return {
        "period_days": days,
        "daily_data": summary,
    }


@router.get("/api/v1/price/history/tou-analysis")
async def get_tou_analysis(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours"),
):
    """
    Analyze price differences between TOU periods.
    
    Compares ON_PEAK vs OFF_PEAK pricing.
    """
    if not app_state.price_history:
        raise HTTPException(status_code=503, detail="Price history not initialized")
    
    analysis = app_state.price_history.get_tou_analysis(hours=hours)
    return {
        "period_hours": hours,
        "tou_analysis": analysis,
    }


@router.get("/api/v1/price/history/sentiment")
async def get_market_sentiment(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours"),
):
    """
    Get market sentiment distribution.
    
    Returns count of HIGH_DEMAND, BALANCED, and LOW_DEMAND periods.
    """
    if not app_state.price_history:
        raise HTTPException(status_code=503, detail="Price history not initialized")
    
    distribution = app_state.price_history.get_market_sentiment_distribution(hours=hours)
    return {
        "period_hours": hours,
        "sentiment_distribution": distribution,
    }


@router.get("/api/v1/price/history/status")
async def get_history_status():
    """
    Get price history manager status.
    
    Returns storage metrics and configuration.
    """
    if not app_state.price_history:
        raise HTTPException(status_code=503, detail="Price history not initialized")
    
    return {
        "record_count": app_state.price_history.get_record_count(),
        "retention_hours": app_state.price_history.retention_hours,
        "max_records": app_state.price_history.max_records,
        "database_enabled": app_state.price_history.use_database,
    }


# ============================================================================
# Persistent Price History API Endpoints (Database-backed)
# ============================================================================

@router.get("/api/v1/price/history/db/records")
async def get_db_price_records(
    limit: int = Query(default=100, ge=1, le=10000, description="Number of records"),
):
    """
    Get recent price records from database.
    
    Supports larger limits than in-memory storage.
    """
    if not app_state.price_history or not app_state.price_history._db:
        raise HTTPException(status_code=503, detail="Price database not initialized")
    
    records = await app_state.price_history._db.get_recent_records(limit=limit)
    return {
        "count": len(records),
        "source": "database",
        "records": records,
    }


@router.get("/api/v1/price/history/db/statistics")
async def get_db_price_statistics(
    hours: int = Query(default=168, ge=1, le=720, description="Time window in hours"),
):
    """
    Get price statistics from database.
    
    Supports longer time periods than in-memory (up to 30 days).
    """
    if not app_state.price_history or not app_state.price_history._db:
        raise HTTPException(status_code=503, detail="Price database not initialized")
    
    stats = await app_state.price_history._db.get_statistics(hours=hours)
    return {
        "period_hours": hours,
        "source": "database",
        "statistics": stats,
    }


@router.get("/api/v1/price/history/db/export")
async def export_price_history(
    format: str = Query(default="csv", description="Export format (csv)"),
):
    """
    Export price history to file.
    
    Returns download link or file content.
    """
    if not app_state.price_history or not app_state.price_history._db:
        raise HTTPException(status_code=503, detail="Price database not initialized")
    
    import tempfile
    from pathlib import Path
    
    # Export to temp file
    temp_dir = Path(tempfile.gettempdir())
    filepath = temp_dir / f"price_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    count = await app_state.price_history._db.export_to_csv(str(filepath))
    
    return {
        "format": format,
        "record_count": count,
        "filepath": str(filepath),
        "message": f"Exported {count} records to {filepath}",
    }
