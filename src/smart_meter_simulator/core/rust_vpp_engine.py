"""
Python wrapper for Rust-accelerated VPP Dispatch Engine

Provides transparent fallback to Python implementation if Rust is unavailable.
VPP Dispatch optimization in Rust (3-10x speedup expected).
"""

import logging
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

# Try to import Rust VPP engine
try:
    from gridtokenx_sim import VPPDispatchEngine as RustVPPDispatchEngine, DERResource as RustDERResource
    USE_RUST_VPP = True
    logger.info("🦀 Rust VPP Dispatch Engine loaded")
except ImportError as e:
    USE_RUST_VPP = False
    RustVPPDispatchEngine = None
    RustDERResource = None
    logger.warning(f"⚠️  Rust VPP engine unavailable ({e}), using Python fallback")


class RustAcceleratedVPP:
    """
    Rust-accelerated VPP Dispatch wrapper.
    
    Provides transparent fallback to Python if Rust extension is not available.
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rust_engine: Optional[RustVPPDispatchEngine] = None
        
        if USE_RUST_VPP:
            try:
                self.rust_engine = RustVPPDispatchEngine(seed=seed)
                logger.info(f"🦀 Rust VPP engine initialized (seed={seed})")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize Rust VPP engine: {e}")
    
    def calculate_afrr(
        self,
        frequency_hz: float,
        max_flexibility_up_kw: float,
        max_flexibility_down_kw: float,
    ) -> float:
        """
        Calculate automatic Frequency Restoration Reserve (aFRR) response.
        
        Args:
            frequency_hz: Current grid frequency (nominal 50 Hz)
            max_flexibility_up_kw: Maximum upward flexibility (discharge)
            max_flexibility_down_kw: Maximum downward flexibility (charge)
        
        Returns:
            Required power adjustment in kW (positive=discharge, negative=charge)
        """
        if self.rust_engine:
            return self.rust_engine.calculate_afrr(
                frequency_hz,
                max_flexibility_up_kw,
                max_flexibility_down_kw,
            )
        else:
            # Python fallback
            deadband = 0.02
            deviation = frequency_hz - 50.0
            
            if abs(deviation) < deadband:
                return 0.0
            
            gain = 10.0
            target = -deviation * gain
            
            if target > 0:
                return min(target, max_flexibility_up_kw)
            else:
                return max(target, -max_flexibility_down_kw)
    
    def dispatch(
        self,
        resources: List[Dict[str, Any]],
        target_kw: float,
        nodal_prices: Dict[str, float],
        carbon_intensity: Optional[float] = None,
        interval_hours: float = 0.25,
    ) -> Dict[str, Any]:
        """
        Multi-objective VPP dispatch: SOC (30%), Price (40%), Carbon (30%).
        
        Args:
            resources: List of resource dicts with keys:
                - meter_id: str
                - capacity_kwh: float
                - current_soc_kwh: float
                - max_charge_kw: float
                - max_discharge_kw: float
                - is_controllable: bool
                - enabled: bool
                - reputation_score: float
            target_kw: Total target power (positive=discharge, negative=charge)
            nodal_prices: Dict mapping meter_id to nodal price
            carbon_intensity: Grid carbon intensity (gCO2/kWh), optional
            interval_hours: Dispatch interval in hours (default 0.25 = 15 min)
        
        Returns:
            Dict with keys:
                - dispatches: Dict[str, float] (meter_id -> dispatch_kw)
                - carbon_saved_g: float
                - cluster_health: float (0-100)
                - execution_time_us: int
        """
        start = time.perf_counter()
        
        if self.rust_engine:
            # Rust path
            rust_resources = []
            for r in resources:
                rust_r = RustDERResource(
                    meter_id=r['meter_id'],
                    capacity_kwh=r.get('capacity_kwh', 20.0),
                    current_soc_kwh=r.get('current_soc_kwh', 10.0),
                    max_charge_kw=r.get('max_charge_kw', 5.0),
                    max_discharge_kw=r.get('max_discharge_kw', 5.0),
                    is_controllable=r.get('is_controllable', True),
                    enabled=r.get('enabled', True),
                    reputation_score=r.get('reputation_score', 1.0),
                )
                rust_resources.append(rust_r)
            
            result = self.rust_engine.dispatch(
                resources=rust_resources,
                target_kw=target_kw,
                nodal_prices=nodal_prices,
                carbon_intensity=carbon_intensity,
                interval_hours=interval_hours,
            )
            
            execution_time_us = int((time.perf_counter() - start) * 1e6)
            
            return {
                'dispatches': result.dispatches,
                'carbon_saved_g': result.carbon_saved_g,
                'cluster_health': result.cluster_health,
                'execution_time_us': execution_time_us,
                'engine': 'Rust',
            }
        else:
            # Python fallback
            dispatches = {}
            total_weight = 0.0
            weights = []
            
            for r in resources:
                soc_percent = (r.get('current_soc_kwh', 0) / r.get('capacity_kwh', 1)) * 100.0 if r.get('capacity_kwh', 0) > 0 else 0.0
                
                soc_w = soc_percent / 100.0 if target_kw > 0 else (100.0 - soc_percent) / 100.0
                price = nodal_prices.get(r['meter_id'], 0.25)
                price_w = price / 0.5 if target_kw > 0 else 1.0 - (price / 0.5)
                c_intensity = carbon_intensity if carbon_intensity is not None else 250.0
                carbon_w = c_intensity / 500.0 if target_kw > 0 else 1.0 - (c_intensity / 500.0)
                
                weight = (soc_w * 0.3 + price_w * 0.4 + carbon_w * 0.3) * r.get('reputation_score', 1.0)
                total_weight += weight
                weights.append((r['meter_id'], weight))
            
            if total_weight > 0:
                for meter_id, weight in weights:
                    dispatches[meter_id] = (weight / total_weight) * target_kw
            elif resources:
                equal = target_kw / len(resources)
                for r in resources:
                    dispatches[r['meter_id']] = equal
            
            carbon_saved = 0.0
            if target_kw > 0 and carbon_intensity is not None:
                carbon_saved = target_kw * interval_hours * carbon_intensity
            
            execution_time_us = int((time.perf_counter() - start) * 1e6)
            
            return {
                'dispatches': dispatches,
                'carbon_saved_g': carbon_saved,
                'cluster_health': 0.0,
                'execution_time_us': execution_time_us,
                'engine': 'Python',
            }


def get_engine_status() -> Dict[str, Any]:
    """Get current VPP engine status."""
    return {
        'vpp_rust_enabled': USE_RUST_VPP,
        'vpp_engine_type': 'Rust (PyO3)' if USE_RUST_VPP else 'Python (fallback)',
        'vpp_expected_speedup': '3-10x' if USE_RUST_VPP else '1x (baseline)',
    }
