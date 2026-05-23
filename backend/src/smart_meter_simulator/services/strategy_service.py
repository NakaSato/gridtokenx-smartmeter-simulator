"""
Strategy Service - Game Theory & Financial Optimization

Centralizes decision-making logic for grid bottleneck resolution and
financial optimization, formalizing the 'New Assumption' analysis for the
April 22nd presentation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class StrategyState(Enum):
    NORMAL = "NORMAL"
    PEAK = "PEAK"
    EMERGENCY = "EMERGENCY"


@dataclass
class GridFinancials:
    """PEA Financial Constraints (THB/kWh)"""

    retail_price: float = 4.0
    grid_import_cost: float = 2.5
    bess_lcos: float = 3.5
    diesel_gen_cost: float = 13.0
    blackout_penalty: float = 10000.0


class StrategyService:
    """
    Formalized Game Theory engine for grid operations.
    Unifies payoff calculations and optimal dispatch scheduling.
    """

    def __init__(self, financials: Optional[GridFinancials] = None):
        self.financials = financials or GridFinancials()

    def resolve_transmission_bottleneck(
        self, line_loading_pct: float, capacity_mw: float
    ) -> Tuple[str, float]:
        """
        Operator's Strategy Game for Transmission Bottleneck.

        Strategies:
        - S1_GRID: Import Max (Mainland)
        - S2_BESS: Discharge BESS (Optimal Peak Shaving)
        - S3_DIESEL: Run Local Gen (Legacy fallback, high loss)

        Returns:
            (best_strategy, reduction_needed_kw)
        """
        # State detection
        state = StrategyState.PEAK if line_loading_pct >= 95.0 else StrategyState.NORMAL

        # Payoff Matrix U(S_i) = Retail - Cost(S_i)
        payoff_matrix = {
            "S1_GRID": {
                StrategyState.NORMAL: self.financials.retail_price
                - self.financials.grid_import_cost,
                StrategyState.PEAK: -self.financials.blackout_penalty,
            },
            "S2_BESS": {
                StrategyState.NORMAL: self.financials.retail_price
                - self.financials.bess_lcos,
                StrategyState.PEAK: self.financials.retail_price
                - self.financials.bess_lcos,
            },
            "S3_DIESEL": {
                StrategyState.NORMAL: self.financials.retail_price
                - self.financials.diesel_gen_cost,
                StrategyState.PEAK: self.financials.retail_price
                - self.financials.diesel_gen_cost,
            },
        }

        # Decision: Maximize Utility
        payoffs = {s: p[state] for s, p in payoff_matrix.items()}
        best_strategy = max(payoffs, key=payoffs.get)

        reduction_needed_kw = 0.0
        if state == StrategyState.PEAK:
            overload_mw = capacity_mw * (line_loading_pct - 95.0) / 100.0
            reduction_needed_kw = max(0, overload_mw * 1000.0)

        logger.info(
            f"STRATEGY DECISION: State={state.value}, Selected={best_strategy}, "
            f"Payoff={payoffs[best_strategy]:.2f} THB/kWh"
        )

        return best_strategy, reduction_needed_kw

    def calculate_optimal_dispatch_schedule(
        self,
        load_forecast_mw: List[float],
        pv_forecast_mw: List[float],
        capacity_mw: float,
    ) -> List[Dict[str, Any]]:
        """
        Calculates the optimal 24-hour dispatch schedule to minimize PEA financial loss.
        """
        schedule = []
        n_steps = len(load_forecast_mw)

        for t in range(n_steps):
            demand = load_forecast_mw[t]
            pv_gen = pv_forecast_mw[t]
            net_load = demand - pv_gen

            p_grid = min(max(0, net_load), capacity_mw)
            overload = max(0, net_load - capacity_mw)

            p_bess = 0.0
            p_diesel = 0.0

            if overload > 0:
                # Prioritize BESS (Cost: 3.5 THB) over Diesel (Cost: 13 THB)
                p_bess = overload  # Assuming sufficient BESS capacity for the model
                # In reality, this would be capped by BESS max discharge

            cost_total = (
                (p_grid * self.financials.grid_import_cost)
                + (p_bess * self.financials.bess_lcos)
                + (p_diesel * self.financials.diesel_gen_cost)
            )

            # Saving calculation: vs a scenario with no BESS (where overload goes to diesel)
            # Delta = p_bess * (C_diesel - C_bess)
            savings_vs_legacy = p_bess * (
                self.financials.diesel_gen_cost - self.financials.bess_lcos
            )

            schedule.append(
                {
                    "hour": t + 1,
                    "net_load_mw": round(net_load, 2),
                    "p_grid_mw": round(p_grid, 2),
                    "p_bess_mw": round(p_bess, 2),
                    "p_diesel_mw": round(p_diesel, 2),
                    "cost_thb": round(cost_total * 1000.0, 2),
                    "savings_thb": round(savings_vs_legacy * 1000.0, 2),
                }
            )

        return schedule

    def get_financial_summary(
        self, dispatch_history: List[Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Aggregate total savings and costs from a history of dispatch events.
        """
        total_savings = 0.0
        total_cost = 0.0

        for event in dispatch_history:
            # event: {"p_bess_kw": 100, "p_diesel_kw": 0, "duration_h": 0.25}
            duration = event.get("duration_h", 0.25)
            p_bess = event.get("p_bess_kw", 0.0)
            p_diesel = event.get("p_diesel_kw", 0.0)

            total_savings += (
                p_bess
                * duration
                * (self.financials.diesel_gen_cost - self.financials.bess_lcos)
            )
            total_cost += (p_bess * duration * self.financials.bess_lcos) + (
                p_diesel * duration * self.financials.diesel_gen_cost
            )

        return {
            "total_savings_thb": round(total_savings, 2),
            "total_operational_cost_thb": round(total_cost, 2),
        }
