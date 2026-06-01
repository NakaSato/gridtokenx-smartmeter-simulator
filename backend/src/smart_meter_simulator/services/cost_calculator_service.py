"""
Operational Cost Calculator Service.
Calculates direct costs, avoided costs, and carbon tax for smart meter readings.
Tracks history in-memory as a fallback for the analytics API.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from .strategy_service import GridFinancials
from ..models.reading import EnergyReading

logger = logging.getLogger(__name__)


class CostCalculatorService:
    """
    Service to calculate the operational costs, carbon taxes, and avoided costs
    (diesel displacement savings) from smart meter simulation readings.
    """

    def __init__(
        self,
        financials: Optional[GridFinancials] = None,
        carbon_tax_rate: float = 0.04,  # THB per kg of CO2
        history_limit: int = 2000,
    ):
        self.financials = financials or GridFinancials()
        self.carbon_tax_rate = carbon_tax_rate
        self.history: List[Dict[str, Any]] = []
        self.history_limit = history_limit

    def calculate_step_costs(
        self, readings: List[EnergyReading], strategy_mode: str = "NORMAL"
    ) -> List[Dict[str, Any]]:
        """
        Calculate operational costs, savings, and carbon taxes for a batch of readings.
        
        Returns:
            A list of dictionary records containing operational cost points.
        """
        records = []

        for r in readings:
            m_id = r.meter_id
            m_type = r.meter_type
            location = r.location
            time_factor = r.interval_seconds / 3600.0
            timestamp = r.timestamp.isoformat()

            # 1. Solar Generation
            # If the meter has solar generation, we record solar metrics
            if r.energy_generated > 0 and "solar" in m_type.lower():
                solar_kwh = r.energy_generated
                # Solar direct fuel cost is 0. Avoided cost vs Diesel is 13.0 THB/kWh
                savings = solar_kwh * self.financials.diesel_gen_cost
                displaced_liters = solar_kwh * 0.33  # ~0.33 liters of diesel per kWh displaced
                carbon_offset = solar_kwh * 0.74  # 0.74 kg CO2 saved per kWh vs diesel gen
                records.append(
                    {
                        "timestamp": timestamp,
                        "zone": location,
                        "source": "Solar",
                        "cost_thb": 0.0,
                        "savings_thb": round(savings, 2),
                        "carbon_tax_thb": 0.0,
                        "strategy_mode": strategy_mode,
                        "meter_id": m_id,
                        "diesel_displaced_liters": round(displaced_liters, 2),
                        "carbon_offset_kg": round(carbon_offset, 2),
                    }
                )

            # 2. BESS Discharge / Battery Storage
            # If the meter is a battery and it is discharging (surplus energy generated from battery)
            if r.energy_generated > 0 and "battery" in m_type.lower():
                bess_kwh = r.energy_generated
                cost = bess_kwh * self.financials.bess_lcos
                # Avoided cost vs Diesel: BESS LCOS vs Diesel Gen Cost
                savings = bess_kwh * (self.financials.diesel_gen_cost - self.financials.bess_lcos)
                displaced_liters = bess_kwh * 0.33
                carbon_offset = bess_kwh * 0.74
                records.append(
                    {
                        "timestamp": timestamp,
                        "zone": location,
                        "source": "BESS",
                        "cost_thb": round(cost, 2),
                        "savings_thb": round(max(0.0, savings), 2),
                        "carbon_tax_thb": 0.0,
                        "strategy_mode": strategy_mode,
                        "meter_id": m_id,
                        "diesel_displaced_liters": round(displaced_liters, 2),
                        "carbon_offset_kg": round(carbon_offset, 2),
                    }
                )

            # 3. Diesel Generation
            if r.energy_generated > 0 and ("diesel" in m_id.lower() or "generator" in m_type.lower()):
                diesel_kwh = r.energy_generated
                cost = diesel_kwh * self.financials.diesel_gen_cost
                # Carbon tax: diesel carbon intensity is roughly 740 g/kWh = 0.74 kg/kWh
                co2_kg = diesel_kwh * 0.74
                carbon_tax = co2_kg * self.carbon_tax_rate
                records.append(
                    {
                        "timestamp": timestamp,
                        "zone": location,
                        "source": "Diesel",
                        "cost_thb": round(cost, 2),
                        "savings_thb": 0.0,
                        "carbon_tax_thb": round(carbon_tax, 2),
                        "strategy_mode": strategy_mode,
                        "meter_id": m_id,
                        "diesel_displaced_liters": 0.0,
                        "carbon_offset_kg": 0.0,
                    }
                )

            # 4. Grid Consumption / Net Import
            # A meter consumes grid energy if it has a deficit (energy_consumed > energy_generated)
            # Or for general consumers, we track the net grid import.
            grid_import_kwh = max(0.0, r.energy_consumed - r.energy_generated)
            if grid_import_kwh > 0:
                # Rate is locational marginal price (nodal_price) if available, else retail reference
                rate = r.nodal_price if r.nodal_price > 0 else self.financials.retail_price
                cost = grid_import_kwh * rate
                
                # Carbon tax: Grid carbon intensity (in g/kWh) converted to kg
                co2_kg = grid_import_kwh * (r.carbon_intensity / 1000.0)
                carbon_tax = co2_kg * self.carbon_tax_rate
                
                records.append(
                    {
                        "timestamp": timestamp,
                        "zone": location,
                        "source": "Grid",
                        "cost_thb": round(cost, 2),
                        "savings_thb": 0.0,
                        "carbon_tax_thb": round(carbon_tax, 2),
                        "strategy_mode": strategy_mode,
                        "meter_id": m_id,
                        "diesel_displaced_liters": 0.0,
                        "carbon_offset_kg": 0.0,
                    }
                )

        # Store in local history
        self.history.extend(records)
        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit :]

        return records

    def get_costs(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Filter historical records by range."""
        if not start_time and not end_time:
            return self.history

        filtered = []
        for r in self.history:
            try:
                dt = datetime.fromisoformat(r["timestamp"])
                if start_time and dt < start_time:
                    continue
                if end_time and dt > end_time:
                    continue
                filtered.append(r)
            except ValueError:
                filtered.append(r)
        return filtered

    def get_savings_summary(self) -> Dict[str, Any]:
        """Aggregate total avoided costs and offsets from history."""
        total_savings = 0.0
        total_diesel_liters = 0.0
        total_carbon_offset = 0.0

        for r in self.history:
            total_savings += r.get("savings_thb", 0.0)
            total_diesel_liters += r.get("diesel_displaced_liters", 0.0)
            total_carbon_offset += r.get("carbon_offset_kg", 0.0)

        return {
            "total_savings_thb": round(total_savings, 2),
            "diesel_displaced_liters": round(total_diesel_liters, 2),
            "carbon_offset_kg": round(total_carbon_offset, 2),
        }
