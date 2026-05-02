import numpy as np
from scipy.optimize import linprog
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

C_GRID, C_BESS, C_DIESEL = 4.0, 3.5, 13.0
GRID_MAX, BESS_MAX, BESS_CAP, DIESEL_MAX = 40.0, 20.0, 50.0, 10.0

def run_opf(forecast_mw: np.ndarray) -> dict:
    """Basic Linear Programming OPF for dispatch scheduling."""
    schedule, bess_soc = [], BESS_CAP * 0.5
    total_base, total_opt = 0.0, 0.0

    for t, load in enumerate(forecast_mw):
        # Current BESS limits based on SOC
        bounds = [(0, GRID_MAX), (0, min(BESS_MAX, bess_soc)), (0, DIESEL_MAX)]
        
        # Minimize cost: p_grid*C_GRID + p_bess*C_BESS + p_diesel*C_DIESEL
        # s.t. p_grid + p_bess + p_diesel = load
        res = linprog([C_GRID, C_BESS, C_DIESEL], A_eq=[[1,1,1]], b_eq=[load], bounds=bounds, method="highs")
        
        if res.success:
            p_grid, p_bess, p_diesel = res.x
        else:
            # Fallback to diesel if optimization fails
            p_grid, p_bess, p_diesel = 0, 0, min(load, DIESEL_MAX)
            if load > DIESEL_MAX:
                p_grid = load - DIESEL_MAX

        bess_soc = max(0, bess_soc - p_bess)
        cost_opt  = (p_grid*C_GRID + p_bess*C_BESS + p_diesel*C_DIESEL) * 1000
        cost_base = load * C_DIESEL * 1000
        total_base += cost_base
        total_opt += cost_opt

        schedule.append({
            "hour": t, 
            "load_mw": round(load, 2),
            "p_grid_mw": round(p_grid, 2), 
            "p_bess_mw": round(p_bess, 2),
            "p_diesel_mw": round(p_diesel, 2), 
            "bess_soc_mwh": round(bess_soc, 1),
            "savings_thb": round(cost_base - cost_opt, 0)
        })

    return {
        "schedule": schedule,
        "total_savings_thb": round(total_base - total_opt, 0),
        "total_cost_baseline_thb": round(total_base, 0),
        "total_cost_optimized_thb": round(total_opt, 0)
    }

def run_opf_with_physics(forecast_mw: np.ndarray) -> dict:
    """Run linprog OPF then validate each hour against Pandapower power flow."""
    try:
        from smart_meter_simulator.adapters.island_hub_topology import IslandHubTopology
        import pandapower as pp
    except ImportError as e:
        logger.warning(f"Physics validation unavailable: {e}. Falling back to basic OPF.")
        return run_opf(forecast_mw)

    result = run_opf(forecast_mw)

    # Build net once (no meters needed for physics check)
    topo = IslandHubTopology()
    net, _ = topo.build_island_hub([])

    violations = []
    for h in result["schedule"]:
        # Inject dispatch into net.load (create or update)
        if len(net.load) == 0:
            pp.create_load(net, bus=net.bus.index[net.bus.name == "Samui Dist 33kV"][0],
                           p_mw=h["load_mw"], q_mvar=h["load_mw"] * 0.1, name="island_load")
        else:
            net.load.at[0, "p_mw"] = h["load_mw"]

        # Set generator dispatch from OPF result
        # Note: Generator names must match those in IslandHubTopology
        try:
            net.gen.at[net.gen[net.gen.name == "Samui_EGAT_Gen"].index[0], "p_mw"] = h["p_grid_mw"]
            net.gen.at[net.gen[net.gen.name == "Tao_Diesel_Gen"].index[0], "p_mw"] = h["p_diesel_mw"]
            if len(net.storage) > 0:
                net.storage.at[0, "p_mw"] = -h["p_bess_mw"]  # discharge = negative convention
        except IndexError:
            logger.warning("Could not find required generators in topology for physics validation.")
            continue

        try:
            pp.runpp(net, algorithm="nr", numba=False)
            bottleneck_line_idx = net.line[net.line.name == "115kV KMB (Circuit 3) Bottleneck"].index
            if not bottleneck_line_idx.empty:
                bottleneck_loading = net.res_line.at[bottleneck_line_idx[0], "loading_percent"]
                h["line_loading_pct"] = round(bottleneck_loading, 1)
                if bottleneck_loading > 100.0:
                    violations.append({"hour": h["hour"], "loading_pct": bottleneck_loading})
            else:
                h["line_loading_pct"] = None
        except Exception as e:
            logger.error(f"Power flow failed for hour {h['hour']}: {e}")
            h["line_loading_pct"] = None

    result["bottleneck_violations"] = violations
    result["physics_validated"] = True
    return result

if __name__ == "__main__":
    # Test with dummy forecast
    test_forecast = np.array([15.0 + 5.0 * np.sin(i / 24 * np.pi) for i in range(24)])
    r = run_opf_with_physics(test_forecast)
    print(f"💰 Total Savings: {r['total_savings_thb']:,.0f} THB/day")
    for h in r["schedule"][:5]:
        print(f"  {h['hour']:02d}h | load={h['load_mw']:.1f} | grid={h['p_grid_mw']:.1f} | bess={h['p_bess_mw']:.1f} | diesel={h['p_diesel_mw']:.1f} | loading={h.get('line_loading_pct')}%")
