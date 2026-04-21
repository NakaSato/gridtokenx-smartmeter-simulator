import pandapower as pp
from ..grid_configs.thai_standards import ThaiRegion, CableType, THAI_MV_KV, THAI_LV_KV
from ..topology_builder import BusConfig, LineConfig, VoltageLevel, TransformerConfig

class UrbanNetworkBuilder:
    """Specialized builder for dense urban networks (Bangkok/MEA style)."""
    
    @staticmethod
    def build(builder, num_households: int, province: str, district: str, lat: float, lng: float):
        builder.create_network()
        
        # 1. MV Substation
        mv_bus_id = f"MV_{district}"
        builder.add_bus(BusConfig(
            bus_id=mv_bus_id, voltage_level=VoltageLevel.MV, vn_kv=THAI_MV_KV,
            name=f"Substation {district}", geo_data={'latitude': lat, 'longitude': lng}
        ))
        builder.add_external_grid(mv_bus_id)

        # 2. LV Network
        lv_bus_id = f"LV_{district}"
        builder.add_bus(BusConfig(
            bus_id=lv_bus_id, voltage_level=VoltageLevel.LV, vn_kv=THAI_LV_KV,
            name=f"LV Main {district}", geo_data={'latitude': lat-0.0005, 'longitude': lng}
        ))
        
        # 3. Transformer
        capacity = (num_households * 1.5 * 0.7) * 1.2
        builder.add_transformer(TransformerConfig(
            hv_bus_id=mv_bus_id, lv_bus_id=lv_bus_id, sn_mva=max(0.5, capacity/1000.0),
            vn_hv_kv=THAI_MV_KV, vn_lv_kv=THAI_LV_KV
        ))

        # 4. Feeders & Households
        for f_idx in range(4):
            f_bus_id = f"F_{f_idx}"
            builder.add_bus(BusConfig(bus_id=f_bus_id, voltage_level=VoltageLevel.LV, vn_kv=THAI_LV_KV))
            builder.add_line(LineConfig(from_bus_id=lv_bus_id, to_bus_id=f_bus_id, length_km=0.05, std_type=CableType.NAYY_150))
            
            for h_idx in range(num_households // 4):
                h_id = f"H_{f_idx}_{h_idx}"
                builder.add_bus(BusConfig(bus_id=h_id, voltage_level=VoltageLevel.LV, vn_kv=THAI_LV_KV))
                builder.add_line(LineConfig(
                    from_bus_id=f_bus_id if h_idx == 0 else f"H_{f_idx}_{h_idx-1}", 
                    to_bus_id=h_id, length_km=0.03, std_type=CableType.NAYY_50
                ))
        
        return builder.net
