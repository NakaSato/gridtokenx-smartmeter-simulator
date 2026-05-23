import math
import random
from typing import Tuple


def apply_droop_control(
    gen: float, cons: float, frequency: float
) -> Tuple[float, float]:
    """Apply Frequency-Watt droop control (Primary Response)."""
    f_dev_pu = (frequency - 50.0) / 50.0
    if abs(f_dev_pu) > 0.001:  # Deadband 50mHz
        p_sadj_pu = -20.0 * f_dev_pu
        if gen > 0:
            adj_gen = max(-0.2, min(0.2, p_sadj_pu))
            gen *= 1 + adj_gen
    return gen, cons


def calculate_electrical_params(
    gen: float, cons: float, accuracy_class_val: float, channels: set
) -> dict:
    """Calculate V, I, Q, PF, Freq with accuracy-based noise."""

    def add_noise(val, mult=1.0):
        if val == 0:
            return 0.0
        return random.gauss(val, (accuracy_class_val / 300.0) * abs(val) * mult)

    params = {}
    if "v" in channels:
        params["voltage"] = add_noise(240.0)
        params["frequency"] = add_noise(50.0, 0.1)

    if "i" in channels:
        apparent = math.sqrt(cons**2 + gen**2)
        v = params.get("voltage", 240.0)
        params["current"] = add_noise((apparent * 1000) / v) if v > 0 else 0.0

    if "p" in channels or "q" in channels:
        params["power_factor"] = min(1.0, add_noise(0.95, 0.5))
        if "q" in channels:
            p_eff = cons - gen
            pf = params.get("power_factor", 0.95)
            q_factor = math.sqrt(1 - pf**2) / pf if pf > 0 else 0
            params["reactive_power"] = p_eff * q_factor

    return params
