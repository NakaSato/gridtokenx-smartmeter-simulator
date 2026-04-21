import logging
from typing import List, Any, Dict
from .vpp import VPPManager
from .frequency import FrequencyModel
from .island import IslandManager

logger = logging.getLogger(__name__)

class VPPHandler:
    """
    Manages Virtual Power Plant (VPP) operations, including dispatch,
    frequency response, and microgrid stability.
    """
    def __init__(self, vpp_manager: VPPManager, frequency_model: FrequencyModel, island_manager: IslandManager):
        self.vpp = vpp_manager
        self.frequency_model = frequency_model
        self.island_manager = island_manager

    def register_meters(self, meters: List[Any]):
        """Register all meters with the VPP clusters."""
        for meter in meters:
            self.vpp.register_meter(
                meter.meter_id, 
                meter.config, 
                {"battery_level": meter.battery_level}
            )

    def handle_frequency_response(self, meters: List[Any], nodal_prices: Dict[int, float], meter_to_bus: Dict[str, int], carbon_intensity: float):
        """Respond to frequency deviations via AFRR dispatch."""
        freq = self.frequency_model.state.frequency
        if abs(freq - 50.0) > 0.02:
            for cluster_id in self.vpp.clusters:
                target_kw = self.vpp.calculate_afrr_response(cluster_id, freq)
                if target_kw != 0:
                    meter_prices = {m.meter_id: nodal_prices.get(meter_to_bus.get(m.meter_id), 0.25) for m in meters}
                    dispatches = self.vpp.dispatch_cluster(
                        cluster_id,
                        target_kw,
                        nodal_prices=meter_prices,
                        carbon_intensity=carbon_intensity,
                    )
                    self._apply_dispatches(meters, dispatches)
        else:
            self._reset_dispatches(meters)

    def handle_island_stability(self, meters: List[Any]):
        """Maintain microgrid stability when islanded."""
        if not self.island_manager.state.is_islanded:
            return

        freq = self.frequency_model.state.frequency
        if freq < 47.0:
            self.island_manager.black_start_sequence(self.vpp)

        for cluster_id in self.vpp.clusters:
            status = self.vpp.get_cluster_status(cluster_id)
            dispatches = self.vpp.orchestrate_microgrid_stability(
                cluster_id, freq,
                total_cons=status.get("total_cons_kw", 0),
                total_gen=status.get("total_gen_kw", 0)
            )
            if dispatches:
                self._apply_dispatches(meters, dispatches)

    def _apply_dispatches(self, meters: List[Any], dispatches: Dict[str, float]):
        """Apply dispatch values to meter objects."""
        for mid, kw in dispatches.items():
            m_obj = next((m for m in meters if m.meter_id == mid), None)
            if m_obj: m_obj.receive_dispatch(kw)

    def _reset_dispatches(self, meters: List[Any]):
        """Reset all VPP dispatches when frequency is healthy."""
        for m in meters:
            if m.vpp_dispatch_kw != 0:
                m.receive_dispatch(0.0)

    def update_vpp_states(self, meters: List[Any], readings: List[Any]):
        """Sync VPP internal state with current meter readings."""
        for meter, reading in zip(meters, readings):
            hours = reading.interval_seconds / 3600.0
            p_cons = (reading.energy_consumed / hours) if hours > 0 else 0.0
            p_gen = (reading.energy_generated / hours) if hours > 0 else 0.0
            self.vpp.update_meter_state(meter.meter_id, meter.battery_level, p_cons=p_cons, p_gen=p_gen)
            
            # Sync Shedding State
            if meter.meter_id in self.vpp.meter_map:
                cid = self.vpp.meter_map[meter.meter_id]
                meter.is_shed = self.vpp.clusters[cid].resources[meter.meter_id].is_shed
