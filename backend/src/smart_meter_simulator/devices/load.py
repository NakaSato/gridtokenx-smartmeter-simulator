from typing import Any, Dict

from smart_meter_simulator.config import get_config

from ..core.meter_logic import profiles


class Load:
    """
    General Load Model.
    Models consumption based on meter type and profile.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.meter_id = config.get("meter_id", "unknown")
        self.last_noise = 0.0

    def get_consumption_kw(self, timestamp: Any, voltage_pu: float = 1.0) -> float:
        """Calculate consumption with a ZIP voltage response."""
        cons, self.last_noise = profiles.calculate_consumption(
            timestamp, self.config, self.meter_id, self.last_noise
        )
        adjusted = self.apply_zip_voltage_response(
            cons,
            voltage_pu,
            z_fraction=float(
                self.config.get(
                    "zip_impedance_fraction", get_config().zip_impedance_fraction
                )
            ),
            i_fraction=float(
                self.config.get(
                    "zip_current_fraction", get_config().zip_current_fraction
                )
            ),
            p_fraction=float(
                self.config.get("zip_power_fraction", get_config().zip_power_fraction)
            ),
        )
        min_load = self.config.get("min_load_kw", get_config().min_load_kw)
        max_load = self.config.get("max_load_kw", get_config().max_load_kw)
        return max(min_load, min(max_load, adjusted))

    @staticmethod
    def apply_zip_voltage_response(
        base_kw: float,
        voltage_pu: float,
        z_fraction: float,
        i_fraction: float,
        p_fraction: float,
    ) -> float:
        """Apply ZIP load behavior: Z scales V^2, I scales V, P is constant."""
        total = z_fraction + i_fraction + p_fraction
        if total <= 0:
            z_fraction, i_fraction, p_fraction = 0.0, 0.0, 1.0
            total = 1.0

        z = z_fraction / total
        i = i_fraction / total
        p = p_fraction / total
        v = max(0.0, min(1.5, voltage_pu))
        return base_kw * ((z * v * v) + (i * v) + p)
