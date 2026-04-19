"""
Grid Analytics Service

Handles aggregate forecasting, ETL processing, and performance tracking.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any
from smart_meter_simulator.config import MeterType
from smart_meter_simulator.config import MeterType
from .strategy_service import StrategyService

logger = logging.getLogger(__name__)

class GridAnalyticsService:
    """
    Service for grid-wide analytics and forecasting.
    """

    @staticmethod
    def calculate_aggregate_forecast(meters, start_time: datetime, horizon_steps: int = 24) -> Dict[str, List[float]]:
        """
        Calculate aggregate generation and consumption forecast for the next N steps.
        """
        gen_forecast = []
        cons_forecast = []
        
        for i in range(horizon_steps):
            future_time = start_time + timedelta(minutes=15 * i)
            step_gen = 0.0
            step_cons = 0.0
            
            for meter in meters:
                # 1. Solar forecast
                if meter.config.get('has_solar'):
                    hour = future_time.hour + future_time.minute / 60.0
                    if 6 <= hour <= 18:
                        time_factor = math.sin(math.pi * (hour - 6) / 12) ** 2
                        capacity = meter.config.get('solar_capacity', 5.0)
                        efficiency = meter.config.get('panel_efficiency', 0.18)
                        step_gen += (capacity * time_factor * efficiency * 2)
                
                # 2. Consumption forecast
                meter_type = MeterType(meter.config['meter_type'])
                base = meter.config.get('base_consumption', 1.0)
                meter_offset = (hash(meter.meter_id) % 100) / 100.0
                hour = future_time.hour + future_time.minute / 60.0
                weekday = future_time.weekday() < 5
                
                factor = 1.0
                if meter_type in [MeterType.RESIDENTIAL, MeterType.SOLAR_PROSUMER, MeterType.HYBRID_PROSUMER]:
                    m_peak_time = 7.5 + (meter_offset * 1.5)
                    e_peak_time = 18.5 + (meter_offset * 2.0)
                    m_peak = 0.8 * math.exp(-((hour - m_peak_time) ** 2) / (2 * 1.2 ** 2))
                    e_peak = 1.5 * math.exp(-((hour - e_peak_time) ** 2) / (2 * 2.5 ** 2))
                    factor = (1.2 + m_peak * 0.5 + e_peak * 1.2 + 0.3 * math.sin(math.pi * hour / 24)) if not weekday else (0.6 + m_peak + e_peak)
                elif meter_type == MeterType.COMMERCIAL:
                    business_hours = 1.8 if (9 <= hour <= 17) else 0.4
                    if 7 <= hour < 9: business_hours = 0.4 + (1.4 * (hour - 7) / 2.0)
                    elif 17 < hour <= 19: business_hours = 1.8 - (1.4 * (hour - 17) / 2.0)
                    factor = business_hours + meter_offset * 0.2 if weekday else (0.3 + meter_offset * 0.1)
                else:
                    factor = 1.0 + 0.2 * math.sin(2 * math.pi * hour / 24) + meter_offset
                
                step_cons += (base * factor)
                
            # Convert units (kWh -> MW)
            gen_forecast.append(round((step_gen / 1000.0) * 4.0, 4))
            cons_forecast.append(round((step_cons / 1000.0) * 4.0, 4))
            
        # 3. Financial Impact Analysis (New Assumption) & 4. AI Load Forecasting
        ai_forecast = []
        financial_schedule = []
        
        try:
            import sys
            import math
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent.parent.parent))
            from src.smart_meter_simulator.routers.forecast_v1 import get_24h_forecast
            from scripts.pea_opf_optimizer import run_opf_with_physics
            
            # Use current load from our simulation or default to 15.0 MW
            current_load_mw = (cons_forecast[0] * 1000.0) / 1000.0 if cons_forecast else 15.0
            
            # Fetch Dual-Target AI Forecast
            f_res = get_24h_forecast(node_id="SAMUI-HUB-01", current_load_mw=current_load_mw, temp_c=33.0, cloud_cover=10.0)
            
            load_mw = f_res["forecast_load_tao_mw"]
            capacity_mw = f_res["forecast_capacity_115kv_mw"]
            delta_mw = f_res["delta_mw"]
            
            for i in range(24):
                ts = start_time + timedelta(hours=i)
                ai_forecast.append({
                    "timestamp": ts.isoformat(),
                    "hour_offset": i,
                    "Load_Tao": round(load_mw[i] * 1000, 2), # Convert to kW for UI
                    "Capacity_115kV": round(capacity_mw[i] * 1000, 2),
                    "delta": round(delta_mw[i] * 1000, 2),
                    "constraint_active": delta_mw[i] < 0,
                    "DAP_d": int(12000 + (1000 * math.sin(i / 24.0 * math.pi * 2))),
                    "T_active": int(4500 + (500 * math.sin(i / 24.0 * math.pi))),
                    "thermal_derating_kw": max(0, (40.0 - capacity_mw[i]) * 1000)
                })
                
            # Fetch Physics-Validated OPF Schedule
            opt_res = run_opf_with_physics(load_mw)
            
            for h in opt_res["schedule"]:
                financial_schedule.append({
                    "hour": h["hour"],
                    "p_grid_mw": h["p_grid_mw"],
                    "p_bess_mw": h["p_bess_mw"],
                    "p_diesel_mw": h["p_diesel_mw"],
                    "hourly_cost_thb": (h["p_grid_mw"] * 4.0 + h["p_bess_mw"] * 3.5 + h["p_diesel_mw"] * 13.0) * 1000,
                    "savings_vs_diesel_thb": h["savings_thb"]
                })
                
        except Exception as e:
            logger.error(f"AI Forecasting or OPF failed: {e}")
            ai_forecast = []
            financial_schedule = []
            
        return {
            "generation": gen_forecast,
            "consumption": cons_forecast,
            "carbon_intensity": [round(max(50.0, 500.0 - (g * 50.0)), 1) for g in gen_forecast],
            "financial_optimization": financial_schedule,
            "ai_forecast": ai_forecast
        }

    @staticmethod
    def process_island_hub_etl(vpp, net, timestamp: datetime, bottleneck_loading: float) -> List[Dict[str, Any]]:
        """
        ETL Pipeline: Transforms raw simulation data into a unified schema for 'New Assumption' analysis.
        """
        results = []
        try:
            # 1. Samui Hub ETL
            samui_cluster = vpp.clusters.get("SAMUI-FEEDER")
            samui_load = samui_cluster.total_cons_kw / 1000.0 if samui_cluster else 0.0
            
            grid_import = 0.0
            bottleneck_line = net.line[net.line.name == "115kV KMB (Circuit 3) Bottleneck"]
            if not bottleneck_line.empty:
                line_res = getattr(net, 'res_line_est', getattr(net, 'res_line', None))
                if line_res is not None:
                    grid_import = line_res.p_from_mw.at[bottleneck_line.index[0]]

            bess_discharge = 0.0
            bess_soc = 0.0
            if samui_cluster:
                bess = samui_cluster.resources.get("SAMUI-BESS-01")
                if bess:
                    bess_discharge = bess.current_gen_kw / 1000.0
                    bess_soc = bess.soc_percent
                else:
                    status = vpp.get_cluster_status("SAMUI-FEEDER")
                    bess_soc = status.get("current_soc_percent", 0.0)

            phangan_export = 0.0
            phangan_line = net.line[net.line.name == "33kV Samui-Phangan XLPE"]
            if not phangan_line.empty:
                line_res = getattr(net, 'res_line_est', getattr(net, 'res_line', None))
                if line_res is not None:
                    phangan_export = line_res.p_from_mw.at[phangan_line.index[0]]

            results.append({
                "timestamp": timestamp,
                "node_id": "koh_samui_hub_1",
                "metrics": {
                    "load_demand_mw": float(samui_load),
                    "grid_import_mw": float(grid_import),
                    "bess_discharge_mw": float(bess_discharge),
                    "bess_soc_pct": float(bess_soc),
                    "phangan_export_mw": float(phangan_export),
                    "line_loading_pct": float(bottleneck_loading),
                    "potential_savings_thb": float(bess_discharge * 1000.0 * 9.5) # 9.5 THB/kWh delta
                }
            })
        except Exception as e:
            logger.error(f"ETL failed: {e}")
        
        return results
