import pandapower as pp
from ..grid_configs.thai_standards import ThaiRegion, CableType, THAI_MV_KV, THAI_LV_KV
from ..topology_builder import BusConfig, LineConfig, VoltageLevel, TransformerConfig

class RuralNetworkBuilder:
    """Specialized builder for rural feeders (Central/Provincial style)."""
    
    @staticmethod
    def build(builder, num_villages: int, households_per_village: int, province: str, lat: float, lng: float):
        builder.create_network()
        
        # 1. MV Substation
        mv_sub_id = "MV_Sub"
        builder.add_bus(BusConfig(
            bus_id=mv_sub_id, voltage_level=VoltageLevel.MV, vn_kv=THAI_MV_KV,
            name=f"Substation {province}", geo_data={'latitude': lat, 'longitude': lng}
        ))
        builder.add_external_grid(mv_sub_id)

        # 2. Main Feeder along villages
        prev_mv = mv_sub_id
        for v_idx in range(num_villages):
            v_mv_id = f"MV_V_{v_idx}"
            v_lat = lat - (v_idx * 0.045)
            builder.add_bus(BusConfig(
                bus_id=v_mv_id, voltage_level=VoltageLevel.MV, vn_kv=THAI_MV_KV,
                geo_data={'latitude': v_lat, 'longitude': lng}
            ))
            builder.add_line(LineConfig(from_bus_id=prev_mv, to_bus_id=v_mv_id, length_km=5.0, std_type=CableType.AAC_184))
            
            # 3. Village LV
            v_lv_id = f"LV_V_{v_idx}"
            builder.add_bus(BusConfig(bus_id=v_lv_id, voltage_level=VoltageLevel.LV, vn_kv=THAI_LV_KV))
            builder.add_transformer(TransformerConfig(
                hv_bus_id=v_mv_id, lv_bus_id=v_lv_id, sn_mva=0.16, # Small rural TX
                vn_hv_kv=THAI_MV_KV, vn_lv_kv=THAI_LV_KV
            ))
            
            # 4. Village Houses
            for h_idx in range(households_per_village):
                h_id = f"H_{v_idx}_{h_idx}"
                builder.add_bus(BusConfig(bus_id=h_id, voltage_level=VoltageLevel.LV, vn_kv=THAI_LV_KV))
                builder.add_line(LineConfig(
                    from_bus_id=v_lv_id if h_idx == 0 else f"H_{v_idx}_{h_idx-1}",
                    to_bus_id=h_id, length_km=0.05, std_type=CableType.LV_OVERHEAD_MEDIUM
                ))
            
            prev_mv = v_mv_id
            
        return builder.net
