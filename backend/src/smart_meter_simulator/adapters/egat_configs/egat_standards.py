from enum import Enum

class EGATVoltage(Enum):
    KV_500 = 500.0
    KV_230 = 230.0
    KV_115 = 115.0
    KV_69 = 69.0

class SubstationType(Enum):
    MAIN_500 = "500kV Main"
    MAIN_230 = "230kV Regional"
    SUB_115 = "115kV Sub"
    SUB_69 = "69kV Legacy"
    SWITCHING = "Switching Station"
    GENERATOR = "Generator Step-up"

# Typical EGAT transformer parameters
TRANSFORMER_DEFAULTS = {
    "500_230_vk": 12.0,
    "230_115_vk": 10.0,
    "500_115_vk": 14.0,
    "vkr": 0.5,
    "pfe_kw": 10.0,
    "i0": 0.1
}
