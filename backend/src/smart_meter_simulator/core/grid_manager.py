import logging
import math
from typing import Any, Dict, List, Optional

from smart_meter_simulator.config import get_config

from .topology import GridTopology

logger = logging.getLogger(__name__)


class GridManager:
    """
    Grid Manager. Handles core topology state and approximate grid updates.
    Provides bus voltage, line flow, congestion, and loss metrics.
    """

    def __init__(
        self,
        adapter: Optional[Any] = None,
        topology: Optional[GridTopology] = None,
    ):
        self.adapter = adapter
        self.topology: Optional[GridTopology] = topology
        self.net = topology.to_legacy_net() if topology else None
        self.meter_to_bus = {}

        # Topology and state
        self.topology_graph = None
        self.bus_voltages: Dict[str, float] = {}
        self.line_flows: Dict[str, Dict] = {}
        self.lv_nodes = set()
        self.hv_nodes = set()
        self.bus_load: Dict[str, float] = {}
        self.bus_reactive_load: Dict[str, float] = {}
        self.bus_generation: Dict[str, float] = {}

        self.total_losses_kw = 0.0
        self.total_curtailed_kw = 0.0
        self.total_reactive_support_kvar = 0.0
        self.pv_capacity_by_bus: Dict[str, float] = {}
        self.transformer_loss_kw = 0.0
        self.transformer_loading_pct = 0.0
        self.transformer_tap_pos = 0
        self.pp_trafo_idx = None
        self.pp_trafo_lv_idx: Optional[int] = None
        self.pp_line_map: Dict[str, int] = {}

        # Fault/outage injection. Faulted lines/buses are taken out of service
        # before each solve, so the feeder reroutes or islands like an N-1
        # contingency. ``islanded_buses`` is recomputed each tick: in-service
        # buses that lost all paths to the substation slack (voltage undefined).
        self.faulted_lines: set[str] = set()
        self.faulted_buses: set[str] = set()
        self.islanded_buses: set[str] = set()

    def initialize_network(self, meters: List[Any]):
        """Initialize grid state from the core topology model when available."""
        self.topology_graph = None
        self.bus_voltages.clear()
        self.line_flows.clear()
        self.lv_nodes.clear()
        self.hv_nodes.clear()
        self.bus_load.clear()
        self.bus_reactive_load.clear()
        self.bus_generation.clear()

        if self.topology:
            logger.info("Initializing Grid Topology using core model.")
            self.net = self.topology.to_legacy_net()
            self.meter_to_bus = self._map_meters_to_topology_buses(meters)
            self.topology_graph = self.topology.to_networkx()
            self._initialize_graph_state()
        else:
            logger.info("GridManager initialized in simplified mode (AMI only)")

    def _map_meters_to_topology_buses(self, meters: List[Any]) -> Dict[str, str]:
        """Map meters directly to core topology buses."""
        mapping: Dict[str, str] = {}
        if not self.topology or not self.topology.buses:
            return mapping

        buses = self.topology.buses
        bus_names = {bus.name for bus in buses}
        for offset, meter in enumerate(meters):
            config = getattr(meter, "config", {})
            # Prefer an explicit bus name (registry-pinned meters); fall back to index.
            name = config.get("bus_name") or config.get("node_id")
            if name in bus_names:
                mapping[meter.meter_id] = name
                continue
            raw_idx = config.get("bus_idx", offset)
            try:
                idx = int(raw_idx)
            except (TypeError, ValueError):
                idx = offset
            idx = idx if 0 <= idx < len(buses) else 0
            mapping[meter.meter_id] = buses[idx].name
        return mapping

    def _initialize_graph_state(self) -> None:
        """Initialize bus and line state from the current topology graph."""
        if self.topology_graph is None:
            return

        for node_id, data in self.topology_graph.nodes(data=True):
            self.bus_voltages[node_id] = 1.0
            v_nom = data.get("nominal_voltage", 0.0)
            if v_nom < 1000:
                self.lv_nodes.add(node_id)
            else:
                self.hv_nodes.add(node_id)

        for u, v, data in self.topology_graph.edges(data=True):
            line_name = data.get("name", f"Line_{u}_{v}")
            length_km = self._line_length_km(data)
            resistance_ohm_per_km = (
                float(data.get("resistance_ohm_per_km") or 0.0)
                or get_config().line_resistance_ohm_per_km
            )
            reactance_ohm_per_km = (
                float(data.get("reactance_ohm_per_km") or 0.0)
                or get_config().line_reactance_ohm_per_km
            )
            self.line_flows[line_name] = {
                "from": u,
                "to": v,
                "length": data.get("weight", 1.0),
                "length_km": length_km,
                "resistance_ohm": resistance_ohm_per_km * length_km,
                "reactance_ohm": reactance_ohm_per_km * length_km,
                "flow_kw": 0.0,
                "flow_kvar": 0.0,
                "utilization_pct": 0.0,
                "loss_kw": 0.0,
                "voltage_drop_pu": 0.0,
                "capacity_kw": float(data.get("capacity_kw") or 0.0)
                or get_config().line_capacity_kw,
            }

        self._build_pandapower_network()

    def _build_pandapower_network(self) -> None:
        try:
            import pandapower as pp
        except ImportError:
            self.pp_net = None
            self.pp_bus_map = {}
            logger.info("Pandapower not installed. Using fallback distflow.")
            return

        logger.info("Building Pandapower network for exact physical simulation.")
        cfg = get_config()
        net = pp.create_empty_network()
        bus_map = {}
        self.pp_line_map = {}
        # PV inverter nameplate per bus (kW), summed when a bus hosts several PVs.
        # Used by the volt-VAR pass to size each inverter's reactive headroom.
        self.pv_capacity_by_bus = {}
        for pv in self.topology.pvs:
            self.pv_capacity_by_bus[pv.bus] = (
                self.pv_capacity_by_bus.get(pv.bus, 0.0) + pv.capacity_kw
            )
        for bus in self.topology.buses:
            # GridLAB-D nominal_voltage is line-to-neutral; pandapower vn_kv is the
            # nominal line-to-line voltage. Scale 3-phase (ABC) buses by sqrt(3) so
            # a 230 V L-N service models as a ~0.4 kV LV bus — using the raw 230 V
            # under-rates the base, inflating per-unit currents and breaking the
            # power-flow convergence.
            vn_ln = bus.nominal_voltage or 230.0
            phases = (bus.phases or "").upper()
            three_phase = sum(p in phases for p in ("A", "B", "C")) >= 2
            vn_kv = (vn_ln * (3.0**0.5) if three_phase else vn_ln) / 1000.0
            bus_idx = pp.create_bus(net, vn_kv=vn_kv, name=bus.name)
            bus_map[bus.name] = bus_idx

        for line in self.topology.lines:
            if line.from_bus in bus_map and line.to_bus in bus_map:
                from_idx = bus_map[line.from_bus]
                to_idx = bus_map[line.to_bus]
                # Unitless GLM lengths resolve to LINE_LENGTH_UNIT (default ft),
                # consistent with the distflow fallback (_line_length_km).
                unit = line.length_unit or cfg.line_length_unit
                l_km = max(self._convert_length_km(line.length, unit), 0.001)
                r = line.resistance_ohm_per_km or cfg.line_resistance_ohm_per_km
                x = line.reactance_ohm_per_km or cfg.line_reactance_ohm_per_km
                line_idx = pp.create_line_from_parameters(
                    net,
                    from_idx,
                    to_idx,
                    length_km=l_km,
                    r_ohm_per_km=r,
                    x_ohm_per_km=x,
                    c_nf_per_km=10,
                    max_i_ka=cfg.line_ampacity_ka,
                    # Match the key used in self.line_flows (set in
                    # _initialize_graph_state from the networkx edge name == line.name)
                    # so _run_pandapower can write results back to the right line.
                    name=line.name,
                )
                self.pp_line_map[line.name] = line_idx

        root_bus = self.topology.get_substation_bus() or self.topology.buses[0].name
        self.pp_trafo_idx = None
        self.pp_trafo_lv_idx = None
        if cfg.transformer_enabled and root_bus in bus_map:
            # Real MV/LV distribution transformer: MV external-grid slack on the
            # HV side -> transformer (short-circuit + iron losses) -> LV substation
            # bus. The slack moves upstream of the transformer, so the LV bus is no
            # longer a stiff 1.0 pu source — it sags under load and rises on PV
            # backfeed across the transformer impedance, like a real feeder head.
            lv_idx = bus_map[root_bus]
            lv_kv = float(net.bus.vn_kv.at[lv_idx])
            hv_idx = pp.create_bus(net, vn_kv=cfg.transformer_mv_kv, name="mv_source")
            pp.create_ext_grid(net, hv_idx, vm_pu=1.0, name="mv_grid")
            # HV-side tap so an on-load tap changer can regulate the LV feeder
            # head (see the OLTC loop in _run_pandapower). Neutral tap = nominal
            # ratio; the solver steps tap_pos within [tap_min, tap_max].
            tap_max = cfg.transformer_tap_max
            self.pp_trafo_idx = pp.create_transformer_from_parameters(
                net,
                hv_bus=hv_idx,
                lv_bus=lv_idx,
                sn_mva=cfg.transformer_sn_mva,
                vn_hv_kv=cfg.transformer_mv_kv,
                vn_lv_kv=lv_kv,
                vkr_percent=cfg.transformer_vkr_percent,
                vk_percent=cfg.transformer_vk_percent,
                pfe_kw=cfg.transformer_pfe_kw,
                i0_percent=cfg.transformer_i0_percent,
                tap_side="hv",
                tap_neutral=0,
                tap_min=-tap_max,
                tap_max=tap_max,
                tap_step_percent=cfg.transformer_tap_step_percent,
                tap_pos=0,
                # pandapower 3.x only applies the tap ratio when the changer type
                # is set; left at the NaN default the tap_step_percent is ignored.
                tap_changer_type="Ratio",
                name="dist_transformer",
            )
            self.pp_trafo_lv_idx = lv_idx
        elif root_bus in bus_map:
            # Ideal LV slack — no upstream transformer modeled.
            pp.create_ext_grid(net, bus_map[root_bus], vm_pu=1.0)

        self.pp_net = net
        self.pp_bus_map = bus_map

    @staticmethod
    def _convert_length_km(length: Any, unit: str) -> float:
        """Convert a line length in the given unit to kilometers.

        Single source of truth shared by the pandapower build and the distflow
        fallback so both solvers agree on line length (and therefore impedance).
        An unrecognized/blank unit is treated as feet, matching the
        ``LINE_LENGTH_UNIT`` default that callers resolve before calling here.
        """
        length = float(length or 0.0)
        unit = (unit or "").lower()
        if unit in {"km", "kilometer", "kilometers"}:
            return length
        if unit in {"m", "meter", "meters"}:
            return length / 1000.0
        if unit in {"mi", "mile", "miles"}:
            return length * 1.609344
        return length * 0.0003048  # ft / feet / foot / blank

    @staticmethod
    def _voltvar_q_factor(
        vm: float, v1: float, v2: float, v3: float, v4: float
    ) -> float:
        """IEEE 1547 Q(V) curve. Returns a reactive factor in [-1, 1] in load
        convention: -1 = full injection (raise a low bus), +1 = full absorption
        (pull down a high bus), 0 in the v2..v3 deadband.
        """
        if vm <= v1:
            return -1.0
        if vm < v2:
            return -(v2 - vm) / (v2 - v1)
        if vm <= v3:
            return 0.0
        if vm < v4:
            return (vm - v3) / (v4 - v3)
        return 1.0

    def _line_length_km(self, data: Dict[str, Any]) -> float:
        length = data.get("weight") or 0.0
        unit = data.get("length_unit") or get_config().line_length_unit
        return self._convert_length_km(length, unit)

    def update_grid_state(self, meters: List[Any], readings: List[Any]):
        """Update grid metrics using the approximate topology solver."""
        # Map current readings to buses
        self.bus_load.clear()
        self.bus_reactive_load.clear()
        self.bus_generation.clear()
        for r in readings:
            bus = self.meter_to_bus.get(r.meter_id)
            if bus is not None:
                hours = r.interval_seconds / 3600.0
                net_load_kw = (
                    (r.energy_consumed - r.energy_generated) / hours
                    if hours > 0
                    else 0.0
                )
                self.bus_load[bus] = self.bus_load.get(bus, 0.0) + net_load_kw
                # Track gross PV generation per bus separately so volt-watt can
                # curtail the generation component without touching consumption.
                gen_kw = r.energy_generated / hours if hours > 0 else 0.0
                self.bus_generation[bus] = self.bus_generation.get(bus, 0.0) + gen_kw
                reactive_kvar = self._reading_reactive_kvar(r, net_load_kw)
                self.bus_reactive_load[bus] = (
                    self.bus_reactive_load.get(bus, 0.0) + reactive_kvar
                )

        self.total_losses_kw = 0.0
        self.total_curtailed_kw = 0.0
        self.total_reactive_support_kvar = 0.0
        self.transformer_loss_kw = 0.0
        self.transformer_loading_pct = 0.0
        self.transformer_tap_pos = 0
        self.islanded_buses = set()

        if self.topology_graph:
            import networkx as nx

            try:
                success = False
                if getattr(self, "pp_net", None):
                    success = self._run_pandapower()

                if not success:
                    substation = (
                        self.topology.get_substation_bus() if self.topology else None
                    )
                    if substation and substation in self.topology_graph:
                        graph = self._faulted_undirected_graph()
                        if graph.has_node(substation):
                            tree = nx.bfs_tree(graph, substation)
                            self._run_distflow(tree, substation)
                            # Buses cut off from the slack (or faulted) are
                            # de-energized; record the in-service ones as islanded.
                            reachable = set(tree.nodes())
                            for node in self.topology_graph.nodes():
                                if node not in reachable:
                                    self.bus_voltages[node] = 0.0
                                    if node not in self.faulted_buses:
                                        self.islanded_buses.add(node)
            except Exception as e:
                logger.warning(f"Approximate GLM topology update failed: {e}")

    def _faulted_undirected_graph(self):
        """Undirected topology graph with faulted buses and lines removed.

        Used by the distflow fallback so an outage reroutes/islands the feeder
        the same way the out-of-service flags do in the pandapower solve.
        """
        graph = self.topology_graph.to_undirected()
        graph.remove_nodes_from([b for b in self.faulted_buses if graph.has_node(b)])
        for line_name in self.faulted_lines:
            state = self.line_flows.get(line_name)
            if state and graph.has_edge(state["from"], state["to"]):
                graph.remove_edge(state["from"], state["to"])
        return graph

    def _reading_reactive_kvar(self, reading: Any, net_load_kw: float) -> float:
        if reading.reactive_power_kvar is not None:
            return float(reading.reactive_power_kvar)
        pf = float(reading.power_factor or 0.95)
        pf = max(0.1, min(1.0, pf))
        q_abs = abs(net_load_kw) * math.sqrt(max(0.0, 1.0 - pf * pf)) / pf
        return q_abs if net_load_kw >= 0 else -q_abs

    def _run_pandapower(self) -> bool:
        try:
            import pandapower as pp
            import pandas as pd

            if not getattr(self, "pp_net", None):
                return False

            net = self.pp_net
            cfg = get_config()

            # Apply fault/outage injection: take faulted lines and buses out of
            # service before the solve. Reset every element first so cleared
            # faults restore on the next tick. mv_source/ext-grid stay in service.
            net.line["in_service"] = True
            net.bus["in_service"] = True
            for line_name in self.faulted_lines:
                idx = self.pp_line_map.get(line_name)
                if idx is not None:
                    net.line.at[idx, "in_service"] = False
            for bus_name in self.faulted_buses:
                idx = self.pp_bus_map.get(bus_name)
                if idx is not None:
                    net.bus.at[idx, "in_service"] = False

            # Effective net load per bus (kW); negative = PV export. Volt-watt
            # curtailment mutates this working copy, never the raw telemetry.
            effective_load: Dict[str, float] = dict(self.bus_load)

            def rebuild_loads() -> None:
                net.load.drop(net.load.index, inplace=True)
                for bus_name, kw in effective_load.items():
                    if (
                        bus_name in self.pp_bus_map
                        and bus_name not in self.faulted_buses
                    ):
                        kvar = self.bus_reactive_load.get(bus_name, 0.0)
                        if abs(kw) > 0.001 or abs(kvar) > 0.001:
                            pp.create_load(
                                net,
                                self.pp_bus_map[bus_name],
                                p_mw=kw / 1000.0,
                                q_mvar=kvar / 1000.0,
                                name=f"Load-{bus_name}",
                            )

            # Run the exact power flow. This is a radial LV distribution feeder,
            # so backward/forward sweep (bfsw) is the right algorithm — plain
            # Newton-Raphson diverges on the high per-unit impedance of a 230 V
            # radial chain and silently dumps us onto the approximate distflow
            # fallback. Try bfsw first, then NR with a DC-power-flow seed, before
            # giving up. Convergence yields physical voltages, I^2R losses, and
            # signed flows (negative = reverse flow when a bus exports PV).
            def solve() -> bool:
                for kwargs in (
                    {"algorithm": "bfsw"},
                    {"algorithm": "nr", "init": "dc", "max_iteration": 50},
                ):
                    try:
                        pp.runpp(net, numba=False, **kwargs)
                        return True
                    except Exception:
                        continue
                return False

            rebuild_loads()
            if not solve():
                # Genuine non-convergence (e.g. voltage collapse under overload).
                # Let update_grid_state fall back to the approximate solver.
                return False

            # On-load tap changer (OLTC). Regulate the LV feeder-head voltage to a
            # target by stepping the transformer's HV-side tap and re-solving until
            # the head is within the deadband or the tap saturates. Runs before
            # volt-watt so bulk regulation acts first; local PV curtailment then
            # only handles residual overvoltage the tap cannot reach. Tap is on the
            # HV side, so raising tap_pos adds HV turns and lowers the LV voltage.
            self.transformer_tap_pos = 0
            if (
                cfg.transformer_oltc_enabled
                and self.pp_trafo_idx is not None
                and self.pp_trafo_lv_idx is not None
            ):
                v_target = cfg.transformer_oltc_v_target
                db = cfg.transformer_oltc_deadband
                tap_min = int(net.trafo.tap_min.at[self.pp_trafo_idx])
                tap_max = int(net.trafo.tap_max.at[self.pp_trafo_idx])
                for _ in range(cfg.transformer_oltc_max_steps):
                    vm = float(net.res_bus.vm_pu.at[self.pp_trafo_lv_idx])
                    if pd.isna(vm) or abs(vm - v_target) <= db:
                        break
                    tap = int(net.trafo.tap_pos.at[self.pp_trafo_idx])
                    step = 1 if vm > v_target else -1
                    new_tap = max(tap_min, min(tap_max, tap + step))
                    if new_tap == tap:
                        break  # tap saturated
                    net.trafo.tap_pos.at[self.pp_trafo_idx] = new_tap
                    if not solve():
                        net.trafo.tap_pos.at[self.pp_trafo_idx] = tap
                        if not solve():
                            return False
                        break
                self.transformer_tap_pos = int(net.trafo.tap_pos.at[self.pp_trafo_idx])

            # IEEE 1547 volt-VAR (Q(V)) response. Before any real-power
            # curtailment, each PV inverter trades reactive power against local
            # voltage: inject (raise) a sagging bus, absorb (pull down) an
            # overvoltage one, bounded by inverter headroom sqrt(sn^2 - p^2) and
            # q_max_frac of the apparent rating. Iterated to a fixed point. Load
            # convention: +q absorbs (lowers V), -q injects (raises V).
            self.total_reactive_support_kvar = 0.0
            if cfg.pv_voltvar_enabled:
                v1 = cfg.pv_voltvar_v1
                v2 = max(cfg.pv_voltvar_v2, v1 + 1e-6)
                v3 = max(cfg.pv_voltvar_v3, v2)
                v4 = max(cfg.pv_voltvar_v4, v3 + 1e-6)
                base_reactive = dict(self.bus_reactive_load)
                vv_q: Dict[str, float] = {}
                for _ in range(cfg.pv_voltvar_max_iter):
                    changed = False
                    for bus_name, b_idx in self.pp_bus_map.items():
                        sn = (
                            self.pv_capacity_by_bus.get(bus_name, 0.0)
                            * cfg.pv_voltvar_inverter_oversize
                        )
                        if sn <= 0.0 or bus_name in self.faulted_buses:
                            continue
                        vm = float(net.res_bus.vm_pu.at[b_idx])
                        if pd.isna(vm):
                            continue
                        p_kw = self.bus_generation.get(bus_name, 0.0)
                        headroom = math.sqrt(max(0.0, sn * sn - p_kw * p_kw))
                        q_max = min(headroom, sn * cfg.pv_voltvar_q_max_frac)
                        q_target = self._voltvar_q_factor(vm, v1, v2, v3, v4) * q_max
                        if abs(q_target - vv_q.get(bus_name, 0.0)) > 0.001:
                            vv_q[bus_name] = q_target
                            self.bus_reactive_load[bus_name] = (
                                base_reactive.get(bus_name, 0.0) + q_target
                            )
                            changed = True
                    if not changed:
                        break
                    rebuild_loads()
                    if not solve():
                        return False
                self.total_reactive_support_kvar = sum(abs(q) for q in vv_q.values())

            # IEEE 1547 volt-watt response. A PV-exporting bus above v_start
            # throttles inverter real-power export, reaching zero export at
            # v_end. Only the generation component is curtailed (the bus keeps
            # consuming), so the curtailed kW is added back to net load. Curtailment
            # lowers voltage, which changes the curtailment, so iterate to a fixed
            # point. Per-bus curtailment is *ratcheted* (monotonically increasing
            # within a tick): an undamped curve oscillates — a curtailed bus drops
            # below the knee, un-curtails, overshoots, repeat — whereas ratcheting
            # to the peak requirement converges to the settled operating point.
            # The ext_grid (substation) is the slack and never curtails.
            self.total_curtailed_kw = 0.0
            if cfg.pv_voltwatt_enabled:
                v1 = cfg.pv_voltwatt_v_start
                v2 = max(cfg.pv_voltwatt_v_end, v1 + 1e-6)
                curtail_kw: Dict[str, float] = {}
                for _ in range(cfg.pv_voltwatt_max_iter):
                    changed = False
                    for bus_name, b_idx in self.pp_bus_map.items():
                        gen = self.bus_generation.get(bus_name, 0.0)
                        if gen <= 0.0:
                            continue
                        vm = float(net.res_bus.vm_pu.at[b_idx])
                        if vm <= v1:
                            factor = 1.0
                        elif vm >= v2:
                            factor = 0.0
                        else:
                            factor = (v2 - vm) / (v2 - v1)
                        target = gen * (1.0 - factor)
                        applied = curtail_kw.get(bus_name, 0.0)
                        if target - applied > 0.001:
                            curtail_kw[bus_name] = target
                            effective_load[bus_name] = (
                                self.bus_load.get(bus_name, 0.0) + target
                            )
                            changed = True
                    if not changed:
                        break
                    rebuild_loads()
                    if not solve():
                        return False
                self.total_curtailed_kw = sum(curtail_kw.values())

            # Extract results. A NaN bus voltage means the bus is de-energized:
            # either faulted out of service, or islanded — still in service but
            # cut off from the slack by an upstream line/bus fault.
            islanded: set[str] = set()
            for bus_name, b_idx in self.pp_bus_map.items():
                vm_pu = net.res_bus.vm_pu.at[b_idx]
                if pd.isna(vm_pu):
                    self.bus_voltages[bus_name] = 0.0
                    if bus_name not in self.faulted_buses:
                        islanded.add(bus_name)
                else:
                    self.bus_voltages[bus_name] = float(vm_pu)
            self.islanded_buses = islanded

            # Extract line results
            for line_idx, res in net.res_line.iterrows():
                line_name = net.line.name.at[line_idx]
                if line_name in self.line_flows:
                    self.line_flows[line_name]["utilization_pct"] = (
                        float(res.loading_percent)
                        if not pd.isna(res.loading_percent)
                        else 0.0
                    )
                    self.line_flows[line_name]["loss_kw"] = (
                        float(res.pl_mw * 1000.0) if not pd.isna(res.pl_mw) else 0.0
                    )
                    self.line_flows[line_name]["flow_kw"] = (
                        float(res.p_from_mw * 1000.0)
                        if not pd.isna(res.p_from_mw)
                        else 0.0
                    )
                    self.line_flows[line_name]["flow_kvar"] = (
                        float(res.q_from_mvar * 1000.0)
                        if not pd.isna(res.q_from_mvar)
                        else 0.0
                    )

            # Transformer losses + loading add to the system totals when a real
            # MV/LV transformer is modeled (copper + iron loss on the feeder head).
            line_loss_kw = float(net.res_line.pl_mw.sum() * 1000.0)
            trafo_loss_kw = 0.0
            self.transformer_loading_pct = 0.0
            if getattr(self, "pp_trafo_idx", None) is not None and len(net.res_trafo):
                pl = net.res_trafo.pl_mw.at[self.pp_trafo_idx]
                lp = net.res_trafo.loading_percent.at[self.pp_trafo_idx]
                trafo_loss_kw = float(pl * 1000.0) if not pd.isna(pl) else 0.0
                self.transformer_loading_pct = float(lp) if not pd.isna(lp) else 0.0
            self.transformer_loss_kw = trafo_loss_kw
            self.total_losses_kw = line_loss_kw + trafo_loss_kw
            return True

        except Exception as e:
            logger.warning(
                f"Pandapower execution failed, falling back to distflow: {e}"
            )
            return False

    def _run_distflow(self, tree: Any, substation: str) -> None:
        import networkx as nx

        p_downstream = {node: self.bus_load.get(node, 0.0) for node in tree.nodes()}
        q_downstream = {
            node: self.bus_reactive_load.get(node, 0.0) for node in tree.nodes()
        }

        for node in reversed(list(nx.topological_sort(tree))):
            for child in tree.successors(node):
                p_downstream[node] += p_downstream[child]
                q_downstream[node] += q_downstream[child]

        for node in tree.nodes():
            self.bus_voltages[node] = (
                1.0 if node == substation else self.bus_voltages.get(node, 1.0)
            )

        for parent in nx.topological_sort(tree):
            parent_voltage = self.bus_voltages.get(parent, 1.0)
            for child in tree.successors(parent):
                state = self._line_state_between(parent, child)
                if state is None:
                    continue

                p_kw = p_downstream[child]
                q_kvar = q_downstream[child]
                nominal_voltage = self._nominal_voltage(child)
                resistance = state["resistance_ohm"]
                reactance = state["reactance_ohm"]
                drop_pu = (
                    (p_kw * 1000.0 * resistance) + (q_kvar * 1000.0 * reactance)
                ) / max(nominal_voltage * nominal_voltage, 1.0)
                current_squared = ((p_kw * 1000.0) ** 2 + (q_kvar * 1000.0) ** 2) / max(
                    (parent_voltage * nominal_voltage) ** 2, 1.0
                )
                loss_kw = current_squared * resistance / 1000.0
                # Physical bound: series I^2R loss on a line cannot exceed the
                # real power flowing through it. Without this the LV (230 V)
                # base inflates currents and the approximate solver reports
                # losses many times larger than throughput.
                loss_kw = min(loss_kw, abs(p_kw))
                apparent_kw = math.sqrt((p_kw * p_kw) + (q_kvar * q_kvar))

                state["flow_kw"] = p_kw
                state["flow_kvar"] = q_kvar
                state["loss_kw"] = loss_kw
                state["voltage_drop_pu"] = drop_pu
                state["utilization_pct"] = min(
                    100.0, apparent_kw / state["capacity_kw"] * 100.0
                )
                self.total_losses_kw += loss_kw
                self.bus_voltages[child] = max(0.7, min(1.2, parent_voltage - drop_pu))

    def _line_state_between(self, bus_a: str, bus_b: str) -> Optional[Dict[str, Any]]:
        for state in self.line_flows.values():
            if (state["from"], state["to"]) in ((bus_a, bus_b), (bus_b, bus_a)):
                return state
        return None

    def _nominal_voltage(self, bus_name: str) -> float:
        if self.topology_graph and self.topology_graph.has_node(bus_name):
            return float(
                self.topology_graph.nodes[bus_name].get("nominal_voltage") or 230.0
            )
        return 230.0

    def get_bus_state(self, bus_name: str) -> Dict:
        """Return the current state of a specific bus."""
        return {
            "voltage_pu": self.bus_voltages.get(bus_name, 1.0),
            "load_kw": self.bus_load.get(bus_name, 0.0),
            "load_kvar": self.bus_reactive_load.get(bus_name, 0.0),
            "connected_meters": [
                m_id for m_id, b in self.meter_to_bus.items() if b == bus_name
            ],
        }

    def get_line_state(self, line_name: str) -> Dict:
        """Return the current state of a specific line."""
        return self.line_flows.get(
            line_name, {"flow_kw": 0.0, "utilization_pct": 0.0, "loss_kw": 0.0}
        )

    def get_congested_lines(self) -> List[str]:
        """Return names of lines with utilization > 80%."""
        return [
            name
            for name, state in self.line_flows.items()
            if state.get("utilization_pct", 0) > 80.0
        ]

    def get_total_losses(self) -> float:
        """Return total system losses in kW."""
        return self.total_losses_kw

    # --- Fault / outage injection ------------------------------------------

    def _known_line_names(self) -> set[str]:
        names = set(self.line_flows.keys()) | set(self.pp_line_map.keys())
        if self.topology:
            names |= {line.name for line in self.topology.lines}
        return names

    def _known_bus_names(self) -> set[str]:
        if self.topology:
            return set(self.topology.bus_names)
        return set(self.bus_voltages.keys())

    def apply_fault(self, element_type: str, name: str) -> bool:
        """Trip a line or bus out of service. Returns False if the name is unknown.

        Takes effect on the next tick's power-flow solve (and the distflow
        fallback): the element is removed, rerouting or islanding the feeder.
        """
        element_type = (element_type or "").lower()
        if element_type == "line":
            if name not in self._known_line_names():
                return False
            self.faulted_lines.add(name)
            return True
        if element_type == "bus":
            if name not in self._known_bus_names():
                return False
            self.faulted_buses.add(name)
            return True
        return False

    def clear_fault(self, element_type: str, name: str) -> bool:
        """Restore a faulted line or bus. Returns False if it was not faulted."""
        element_type = (element_type or "").lower()
        if element_type == "line" and name in self.faulted_lines:
            self.faulted_lines.discard(name)
            return True
        if element_type == "bus" and name in self.faulted_buses:
            self.faulted_buses.discard(name)
            return True
        return False

    def clear_all_faults(self) -> int:
        """Restore every faulted element. Returns the number cleared."""
        count = len(self.faulted_lines) + len(self.faulted_buses)
        self.faulted_lines.clear()
        self.faulted_buses.clear()
        return count

    def fault_status(self) -> Dict[str, Any]:
        """Current faults and the resulting islanded buses (from the last tick)."""
        return {
            "faulted_lines": sorted(self.faulted_lines),
            "faulted_buses": sorted(self.faulted_buses),
            "islanded_buses": sorted(self.islanded_buses),
            "fault_count": len(self.faulted_lines) + len(self.faulted_buses),
            "islanded_count": len(self.islanded_buses),
        }

    def get_topology_summary(self) -> Dict:
        """Return a summary of the grid topology."""
        if self.topology:
            summary = self.topology.summary(include_validation=True)
            summary.update(
                {
                    "mode": "glm_topology",
                    "num_loads": summary["num_static_loads"],
                    "active_load_buses": len(
                        [n for n in self.bus_load if self.bus_load[n] > 0]
                    ),
                    "total_load_kw": sum(self.bus_load.values()),
                    "total_losses_kw": self.total_losses_kw,
                    "total_curtailed_kw": self.total_curtailed_kw,
                    "total_reactive_support_kvar": self.total_reactive_support_kvar,
                    "transformer_loss_kw": self.transformer_loss_kw,
                    "transformer_loading_pct": self.transformer_loading_pct,
                    "transformer_tap_pos": self.transformer_tap_pos,
                    "mapped_meters": len(self.meter_to_bus),
                }
            )
            return summary

        return {
            "source": "ami_only",
            "mode": "ami_only",
            "num_buses": 0,
            "num_lines": 0,
            "num_loads": 0,
            "total_load_kw": 0.0,
            "total_losses_kw": 0.0,
            "mapped_meters": len(self.meter_to_bus),
        }
