import math
import random
from typing import Optional, Tuple


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
    gen: float,
    cons: float,
    accuracy_class_val: float,
    channels: set,
    grid_voltage_pu: float = 1.0,
    nominal_voltage: float = 230.0,
    rng: Optional[random.Random] = None,
) -> dict:
    """Calculate V, I, Q, PF, Freq with accuracy-based noise.

    ``rng`` is the per-meter random stream (for deterministic runs); falls back
    to the global ``random`` module when not supplied.
    """
    rng = rng or random

    def add_noise(val, mult=1.0):
        if val == 0:
            return 0.0
        return rng.gauss(val, (accuracy_class_val / 300.0) * abs(val) * mult)

    params = {}
    if "v" in channels:
        base_voltage = nominal_voltage * grid_voltage_pu
        params["voltage"] = add_noise(
            base_voltage, 0.1
        )  # tiny noise on top of grid voltage
        params["frequency"] = add_noise(50.0, 0.1)

    if "i" in channels:
        net_p = cons - gen
        # We assume net_p > 0 means importing (lagging typical load), net_p < 0 means exporting
        # Apparent power S = P / PF
        params["power_factor"] = (
            min(1.0, add_noise(0.95, 0.5))
            if cons > 0
            else (min(1.0, add_noise(0.99, 0.1)) if gen > 0 else 1.0)
        )

        pf = params["power_factor"]
        # Simplified: apparent power = |net_p| / pf
        apparent = abs(net_p) / pf if pf > 0 else 0.0

        v = params.get("voltage", nominal_voltage)
        current_mag = add_noise((apparent * 1000) / v) if v > 0 else 0.0
        # If exporting, current is conceptually negative (flowing back)
        params["current"] = -current_mag if net_p < 0 else current_mag

    if "p" in channels or "q" in channels:
        if "power_factor" not in params:
            params["power_factor"] = (
                min(1.0, add_noise(0.95, 0.5))
                if cons > 0
                else (min(1.0, add_noise(0.99, 0.1)) if gen > 0 else 1.0)
            )

        if "q" in channels:
            pf = params["power_factor"]
            q_factor = math.sqrt(1 - pf**2) / pf if pf > 0 else 0
            # Exporting reactive power typically depends on inverter settings, we simplify to proportional
            params["reactive_power"] = (cons - gen) * q_factor

    return params
