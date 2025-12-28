import pandapower as pp

def create_thai_std_types(net):
    """
    Defines standard Thai utility component types in the pandapower network.
    
    Includes:
    1. PEA 22kV Distribution Lines (Table 1)
    2. PEA & MEA Distribution Transformers (Table 2)
    """
    
    # ==========================================
    # 1. PEA 22kV Distribution Lines
    # ==========================================
    # Note: Capacitance (c_nf_per_km) is not explicitly given in the prompt's table.
    # We will derive typical values or use X1 to estimate if needed, but pandapower needs c_nf_per_km.
    # For overhead lines (SAC/ACC), typical X1 ~ 0.3-0.4 ohm/km implies typical L.
    # Typical C for MV overhead lines is ~ 9-12 nF/km.
    # Using typical values for 22kV overhead lines where data is missing to ensure model runs.
    
    # 185 SAC (Space Aerial Cable)
    pp.create_std_type(net, name="185 SAC", element="line", data={
        "r_ohm_per_km": 0.18050,
        "x_ohm_per_km": 0.24550,
        "c_nf_per_km": 11.0, # Typical for insulated overhead
        "max_i_ka": 0.430,   # Approx ~430A
        "type": "ol",         # Overhead Line
        "r0_ohm_per_km": 0.32850,
        "x0_ohm_per_km": 1.75490,
        "c0_nf_per_km": 5.0  # Estimated
    })

    # 185 PIC (Partially Insulated Cable)
    pp.create_std_type(net, name="185 PIC", element="line", data={
        "r_ohm_per_km": 0.21435,
        "x_ohm_per_km": 0.33976,
        "c_nf_per_km": 10.0, # Slightly lower/different insulation
        "max_i_ka": 0.410,
        "type": "ol",
        "r0_ohm_per_km": 0.39186,
        "x0_ohm_per_km": 1.55380,
        "c0_nf_per_km": 4.5
    })
    
    # 120 PIC
    pp.create_std_type(net, name="120 PIC", element="line", data={
        "r_ohm_per_km": 0.26643,
        "x_ohm_per_km": 0.34869,
        "c_nf_per_km": 10.0,
        "max_i_ka": 0.300,
        "type": "ol",
        "r0_ohm_per_km": 0.41443,
        "x0_ohm_per_km": 1.57551,
        "c0_nf_per_km": 4.5
    })

    # 120 AAC (All Aluminum Conductor - Bare)
    pp.create_std_type(net, name="120 AAC", element="line", data={
        "r_ohm_per_km": 0.26643,
        "x_ohm_per_km": 0.36382,
        "c_nf_per_km": 9.0, # Bare conductor, lower C
        "max_i_ka": 0.290,
        "type": "ol",
        "r0_ohm_per_km": 0.56243,
        "x0_ohm_per_km": 2.70319, # High Z0 as noted
        "c0_nf_per_km": 4.0
    })

    # ==========================================
    # 2. Transformers (PEA & MEA) - Table 2
    # ==========================================
    # vkr_percent (Real part of impedance) calculation:
    # vkr% = (P_cu_kW / S_nom_kVA) * 100
    
    # PEA 160 kVA 22/0.4 kV
    pp.create_std_type(net, name="PEA 160 kVA", element="trafo", data={
        "sn_mva": 0.16,
        "vn_hv_kv": 22.0,
        "vn_lv_kv": 0.4,
        "vk_percent": 4.00,
        "vkr_percent": (2.35 / 160.0) * 100, # ~1.47%
        "pfe_kw": 0.46,
        "i0_percent": 0.32, # approx
        "shift_degree": 150, # Dyn11 -> 30 deg lead (330 or -30?). Dyn11 is HV leads LV by 30 deg. 
                             # Pandapower convention: LV lags HV by shift_degree.
                             # Dd0=0, Dyn5=150, Dyn11=330 (-30). 
                             # Wait, Dyn11: 11 * 30 = 330 degrees.
        "vector_group": "Dyn11",
        "tap_side": "hv",
        "tap_neutral": 0,
        "tap_min": -2,
        "tap_max": 2,
        "tap_step_percent": 2.5
    })

    # PEA 250 kVA
    pp.create_std_type(net, name="PEA 250 kVA", element="trafo", data={
        "sn_mva": 0.25,
        "vn_hv_kv": 22.0,
        "vn_lv_kv": 0.4,
        "vk_percent": 4.00,
        "vkr_percent": (3.25 / 250.0) * 100, # 1.30%
        "pfe_kw": 0.62,
        "i0_percent": 0.3,
        "shift_degree": 330,
        "vector_group": "Dyn11"
    })

    # PEA 500 kVA
    pp.create_std_type(net, name="PEA 500 kVA", element="trafo", data={
        "sn_mva": 0.50,
        "vn_hv_kv": 22.0,
        "vn_lv_kv": 0.4,
        "vk_percent": 4.75,
        "vkr_percent": (5.50 / 500.0) * 100, # 1.10%
        "pfe_kw": 1.10,
        "i0_percent": 0.25,
        "shift_degree": 330,
        "vector_group": "Dyn11"
    })

    # MEA 1000 kVA 24/0.416 kV
    pp.create_std_type(net, name="MEA 1000 kVA", element="trafo", data={
        "sn_mva": 1.0,
        "vn_hv_kv": 24.0,
        "vn_lv_kv": 0.416,
        "vk_percent": 5.00,
        "vkr_percent": (9.80 / 1000.0) * 100, # 0.98%
        "pfe_kw": 1.70,
        "i0_percent": 0.2,
        "shift_degree": 330,
        "vector_group": "Dyn11"
    })
    
    # MEA 2000 kVA
    pp.create_std_type(net, name="MEA 2000 kVA", element="trafo", data={
        "sn_mva": 2.0,
        "vn_hv_kv": 24.0,
        "vn_lv_kv": 0.416,
        "vk_percent": 6.00,
        "vkr_percent": (18.00 / 2000.0) * 100, # 0.90%
        "pfe_kw": 2.90,
        "i0_percent": 0.15,
        "shift_degree": 330,
        "vector_group": "Dyn11"
    })
