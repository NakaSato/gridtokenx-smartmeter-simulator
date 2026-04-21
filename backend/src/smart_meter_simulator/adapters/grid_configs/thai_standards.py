from enum import Enum

class ThaiRegion(Enum):
    BANGKOK = "bangkok"
    CENTRAL = "central"
    NORTH = "north"
    NORTHEAST = "northeast"
    SOUTH = "south"

class CableType:
    # MV Cables (22 kV)
    AAC_34 = "34-AL1/6-ST1A 20.0"
    AAC_70 = "70-AL1/11-ST1A 20.0"
    AAC_184 = "184-AL1/30-ST1A 20.0"
    XLPE_185 = "NA2XS2Y 1x185 RM/25 12/20 kV"
    
    # LV Cables (0.4 kV)
    NAYY_50 = "NAYY 4x50 SE"
    NAYY_120 = "NAYY 4x120 SE"
    NAYY_150 = "NAYY 4x150 SE"
    LV_OVERHEAD_MEDIUM = "48-AL1/8-ST1A 0.4"

class TransformerType:
    TX_160 = 160.0
    TX_250 = 250.0
    TX_315 = 315.0
    TX_500 = 500.0
    TX_800 = 800.0
    TX_1000 = 1000.0

THAI_MV_KV = 22.0
THAI_LV_KV = 0.4

TRANSFORMER_DEFAULTS = {
    "vk_percent": 4.0,
    "vkr_percent": 1.2,
    "pfe_kw": 0.8,
    "i0_percent": 0.3
}
