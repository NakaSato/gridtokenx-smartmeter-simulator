import pandapower as pp
from ..grid_configs.thai_standards import ThaiRegion, CableType, THAI_MV_KV, THAI_LV_KV
from ..topology_builder import BusConfig, LineConfig, VoltageLevel, TransformerConfig

class CommercialNetworkBuilder:
    """Specialized builder for commercial/mixed-use urban networks."""
    
    @staticmethod
    def build(builder, num_shops: int, transformer_capacity_kva: float, province: str, district: str, lat: float, lng: float):
        builder.create_network()
        
        # 1. MV Substation
        mv_bus_id = f"MV_{district}"
        builder.add_bus(BusConfig(
            bus_id=mv_bus_id, voltage_level=VoltageLevel.MV, vn_kv=THAI_MV_KV,
            name=f"Substation {district}", geo_data={'latitude': lat, 'longitude': lng}
        ))
        builder.add_external_grid(mv_bus_id)

        # 2. LV Commercial Hub
        lv_bus_id = f"LV_{district}"
        builder.add_bus(BusConfig(
            bus_id=lv_bus_id, voltage_level=VoltageLevel.LV, vn_kv=THAI_LV_KV,
            name=f"LV Commercial Hub {district}", geo_data={'latitude': lat-0.0005, 'longitude': lng}
        ))
        
        # 3. Transformer
        builder.add_transformer(TransformerConfig(
            hv_bus_id=mv_bus_id, lv_bus_id=lv_bus_id, sn_mva=transformer_capacity_kva/1000.0,
            vn_hv_kv=THAI_MV_KV, vn_lv_kv=THAI_LV_KV
        ))

        # 4. Commercial Feeders
        for f_idx in range(2):
            f_bus_id = f"F_{f_idx}"
            builder.add_bus(BusConfig(bus_id=f_bus_id, voltage_level=VoltageLevel.LV, vn_kv=THAI_LV_KV))
            builder.add_line(LineConfig(from_bus_id=lv_bus_id, to_bus_id=f_bus_id, length_km=0.1, std_type=CableType.NAYY_150))
            
            for s_idx in range(num_shops // 2):
                s_id = f"S_{f_idx}_{s_idx}"
                builder.add_bus(BusConfig(bus_id=s_id, voltage_level=VoltageLevel.LV, vn_kv=THAI_LV_KV))
                builder.add_line(LineConfig(
                    from_bus_id=f_bus_id if s_idx == 0 else f"S_{f_idx}_{s_idx-1}",
                    to_bus_id=s_id, length_km=0.02, std_type=CableType.NAYY_120
                ))
        
        return builder.net
