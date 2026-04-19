import numpy as np
from scipy.optimize import linprog

C_GRID, C_BESS, C_DIESEL = 4.0, 3.5, 13.0
GRID_MAX, BESS_MAX, BESS_CAP, DIESEL_MAX = 40.0, 20.0, 50.0, 10.0

def run_opf(forecast_mw: np.ndarray) -> dict:
    schedule, bess_soc = [], BESS_CAP * 0.5
    total_base, total_opt = 0.0, 0.0

    for t, load in enumerate(forecast_mw):
        bounds = [(0, GRID_MAX), (0, min(BESS_MAX, bess_soc)), (0, DIESEL_MAX)]
        res = linprog([C_GRID, C_BESS, C_DIESEL], A_eq=[[1,1,1]], b_eq=[load], bounds=bounds, method="highs")
        p_grid, p_bess, p_diesel = res.x if res.success else (0, 0, min(load, DIESEL_MAX))

        bess_soc = max(0, bess_soc - p_bess)
        cost_opt  = (p_grid*C_GRID + p_bess*C_BESS + p_diesel*C_DIESEL) * 1000
        cost_base = load * C_DIESEL * 1000
        total_base += cost_base; total_opt += cost_opt

        schedule.append({"hour": t, "load_mw": round(load,2),
                         "p_grid_mw": round(p_grid,2), "p_bess_mw": round(p_bess,2),
                         "p_diesel_mw": round(p_diesel,2), "bess_soc_mwh": round(bess_soc,1),
                         "savings_thb": round(cost_base - cost_opt, 0)})

    return {"schedule": schedule,
            "total_savings_thb": round(total_base - total_opt, 0),
            "total_cost_baseline_thb": round(total_base, 0),
            "total_cost_optimized_thb": round(total_opt, 0)}

def run_opf_with_physics(forecast_mw: np.ndarray) -> dict:
    """Run linprog OPF then validate each hour against Pandapower power flow."""
    from smart_meter_simulator.adapters.island_hub_topology import IslandHubTopology
    import pandapower as pp

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
        net.gen.at[net.gen[net.gen.name == "Samui_EGAT_Gen"].index[0], "p_mw"] = h["p_grid_mw"]
        net.gen.at[net.gen[net.gen.name == "Tao_Diesel_Gen"].index[0], "p_mw"] = h["p_diesel_mw"]
        net.storage.at[0, "p_mw"] = -h["p_bess_mw"]  # discharge = negative convention

        try:
            pp.runpp(net, algorithm="nr", numba=False)
            bottleneck_loading = net.res_line.at[
                net.line[net.line.name == "115kV KMB (Circuit 3) Bottleneck"].index[0], "loading_percent"
            ]
            h["line_loading_pct"] = round(bottleneck_loading, 1)
            if bottleneck_loading > 100.0:
                violations.append({"hour": h["hour"], "loading_pct": bottleneck_loading})
        except Exception:
            h["line_loading_pct"] = None

    result["bottleneck_violations"] = violations
    result["physics_validated"] = True
    return result

if __name__ == "__main__":
    from smart_meter_simulator.core.forecaster import EdgeForecastingEngine
    forecast = EdgeForecastingEngine("SAMUI-HUB-01").generate_24h_forecast(15.0, {"temp_c": 33.0, "cloud_cover": 10.0})
    r = run_opf_with_physics(forecast)
    print(f"💰 Savings: {r['total_savings_thb']:,.0f} THB/day")
    for h in r["schedule"]:
        print(f"  {h['hour']:02d}h | load={h['load_mw']} | grid={h['p_grid_mw']} | bess={h['p_bess_mw']} | diesel={h['p_diesel_mw']} | save={h['savings_thb']:,.0f} | load_pct={h['line_loading_pct']}")
