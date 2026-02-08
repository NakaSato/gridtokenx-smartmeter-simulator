import numpy as np
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class OptimizationEngine:
    """
    Decision-making engine for grid asset optimization.
    Coordinates battery storage and demand response to mitigate grid violations.
    """
    
    def __init__(self, target_voltage_pu: float = 1.0):
        self.target_voltage = target_voltage_pu
        self.soc_min = 20.0 # 20% DoD
        self.soc_max = 95.0
        
    def optimize_battery_dispatch(self, 
                                 meter_id: str, 
                                 current_soc: float, 
                                 net_forecast: np.ndarray,
                                 price_forecast: Optional[np.ndarray] = None) -> float:
        """
        Determine the optimal charge/discharge rate for the current step.
        
        Args:
            meter_id: Unique meter identifier
            current_soc: Current State of Charge (%)
            net_forecast: Array of forecasted net power (Gen - Load) for the next N steps
            price_forecast: Forecasted energy prices ($/kWh)
            
        Returns:
            Preferred power (kW): Positive for DISCHARGE, Negative for CHARGE
        """
        # Simple Greedy Strategy with Look-ahead
        # 1. If we have surplus now (net_forecast[0] > 0), charge battery
        # 2. If we have deficit now, but high prices are expected later, save charge
        # 3. If grid is at risk (voltage violations), priority shifts to support
        
        current_net = net_forecast[0]
        
        # Power limits (assuming typical household battery)
        max_charge_kw = 5.0
        max_discharge_kw = 5.0
        
        # Safety: SOC constraints
        if current_soc >= self.soc_max and current_net > 0:
            return 0.0 # Full, can't charge more
        if current_soc <= self.soc_min and current_net < 0:
            return 0.0 # Empty, can't discharge
            
        # Decision Logic
        # Price Arbitrage Logic (Phase 11)
        if price_forecast is not None and len(price_forecast) > 0:
            current_price = price_forecast[0]
            avg_price = np.mean(price_forecast)
            
            # Arbitrage: Charge if price is low (< 80% of avg), even if no surplus
            if current_price < avg_price * 0.8:
                # Force charge from grid
                charge = min(max_charge_kw, (self.soc_max - current_soc) / 100.0 * 10.0 / 0.25)
                return -charge
                
            # Arbitrage: Discharge if price is high (> 120% of avg), even if surplus (sell to grid)
            if current_price > avg_price * 1.2:
                # Force discharge to grid
                discharge = min(max_discharge_kw, (current_soc - self.soc_min) / 100.0 * 10.0 / 0.25)
                return discharge

        # Fallback to Self-Consumption (Net Metering Logic)
        if current_net > 0: # Energy Surplus
            # Charge battery with surplus
            charge_power = min(current_net, max_charge_kw)
            available_headroom = (self.soc_max - current_soc) / 100.0 * 10.0 # 10kWh battery assumed
            # Scale by time step (15 min = 0.25h)
            charge_power = min(charge_power, available_headroom / 0.25)
            return -charge_power # Negative for charge
            
        elif current_net < 0: # Energy Deficit
            # Discharge to cover own load
            needed_power = abs(current_net)
            
            # Smart Discharge: Don't discharge if price is low (better to buy from grid and save battery)
            if price_forecast is not None and len(price_forecast) > 0:
                if price_forecast[0] < np.mean(price_forecast) * 0.9:
                    return 0.0 # Use Grid instead

            discharge_power = min(needed_power, max_discharge_kw)
            available_charge = (current_soc - self.soc_min) / 100.0 * 10.0
            discharge_power = min(discharge_power, available_charge / 0.25)
            return discharge_power
            
        return 0.0

    def calculate_peak_shaving_vpp(self, 
                                  meter_voltages: Dict[str, float], 
                                  meter_socs: Dict[str, float]) -> Dict[str, float]:
        """
        Coordinate multiple batteries as a Virtual Power Plant (VPP) to shave peaks
        and stabilize nodal voltages.
        """
        dispatch_corrections = {}
        
        for mid, v in meter_voltages.items():
            # If voltage is dropping (undervoltage), request discharge
            if v < 0.96:
                soc = meter_socs.get(mid, 0)
                if soc > self.soc_min + 5:
                    # Request support (shave the peak demand locally)
                    dispatch_corrections[mid] = 2.0 # kW boost
            
            # If voltage is too high (overvoltage from solar), request charge
            elif v > 1.04:
                soc = meter_socs.get(mid, 100)
                if soc < self.soc_max - 5:
                    dispatch_corrections[mid] = -2.0 # kW sink
                    
        return dispatch_corrections
