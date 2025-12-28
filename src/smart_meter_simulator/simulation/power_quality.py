"""
Power Quality Module for THD (Total Harmonic Distortion) Modeling.

This module provides functions to estimate THD based on the types of loads
connected to a bus in the grid simulation.

Background:
- THD-V (Voltage THD): Typically limited to 5% at the PCC (Point of Common Coupling)
  by grid codes (IEEE 519, PEA Grid Code).
- THD-I (Current THD): Can be much higher for non-linear loads like EV chargers
  and inverters (10-30% typical).
  
Sources of Harmonics in Smart Grid Context:
1. EV Chargers (especially DC fast chargers with AC/DC rectifiers)
2. Solar Inverters (switching harmonics)
3. LED Lighting (switched-mode power supplies)
4. Variable Frequency Drives (Industrial)
"""

import random
import numpy as np
from typing import Dict, Tuple


def estimate_thd_for_bus(
    has_ev_charger: bool = False,
    has_solar_inverter: bool = False,
    ev_power_kw: float = 0.0,
    solar_power_kw: float = 0.0,
    base_thd_v: float = 1.5,  # Background THD-V in distribution grid
    base_thd_i: float = 5.0   # Background THD-I
) -> Tuple[float, float]:
    """
    Estimates THD-V and THD-I based on connected loads.
    
    Returns:
        Tuple of (thd_voltage_percent, thd_current_percent)
    """
    thd_v = base_thd_v
    thd_i = base_thd_i
    
    # EV Charger Contribution
    # DC Fast Chargers inject significant current harmonics (5th, 7th, 11th, 13th)
    # THD-I can be 15-30% for older chargers, 5-10% for modern PWM-controlled ones
    if has_ev_charger and ev_power_kw > 0:
        # Scale with power (larger chargers = more harmonics, but also more filtering)
        ev_thd_contribution = 8.0 + random.gauss(0, 2.0)  # ~8% +/- 2%
        # Voltage THD impact (upstream impedance * current harmonics)
        thd_i += ev_thd_contribution * (ev_power_kw / 50.0)  # Normalized to 50kW base
        thd_v += 0.5 * (ev_power_kw / 100.0)  # Small voltage THD increase
    
    # Solar Inverter Contribution
    # Modern inverters are quite clean (THD-I < 5%), but older/cheap ones can be 10%+
    if has_solar_inverter and solar_power_kw > 0:
        inverter_thd = 3.0 + random.gauss(0, 1.0)  # ~3% +/- 1%
        thd_i += inverter_thd * (solar_power_kw / 10.0)  # Normalized to 10kW
        thd_v += 0.2 * (solar_power_kw / 50.0)
    
    # Add some random noise to simulate real-world variation
    thd_v = max(0.5, thd_v + random.gauss(0, 0.3))
    thd_i = max(1.0, thd_i + random.gauss(0, 1.0))
    
    # Cap at realistic maximums
    thd_v = min(thd_v, 15.0)  # Severe distortion threshold
    thd_i = min(thd_i, 50.0)  # Very non-linear load
    
    return round(thd_v, 2), round(thd_i, 2)


def get_power_quality_assessment(thd_v: float, thd_i: float) -> str:
    """
    Returns a qualitative assessment of power quality based on THD.
    """
    if thd_v <= 3.0 and thd_i <= 8.0:
        return "Excellent"
    elif thd_v <= 5.0 and thd_i <= 15.0:
        return "Good"
    elif thd_v <= 8.0 and thd_i <= 25.0:
        return "Acceptable"
    elif thd_v <= 12.0 and thd_i <= 40.0:
        return "Poor"
    else:
        return "Critical"


def calculate_harmonic_spectrum(thd_percent: float, fundamental_amplitude: float = 1.0) -> Dict[int, float]:
    """
    Generates a simplified harmonic spectrum (up to 13th harmonic) given a THD value.
    
    This is a simplified model. In reality, harmonic spectra depend heavily on 
    the specific load characteristics.
    
    Returns:
        Dict mapping harmonic order (3, 5, 7, 11, 13) to amplitude (as fraction of fundamental)
    """
    if thd_percent <= 0:
        return {}
    
    # Typical harmonic distribution for power electronic loads
    # (EV chargers, inverters are 6-pulse rectifiers producing 5th, 7th, 11th, 13th)
    harmonic_ratios = {
        3: 0.1,   # Triplen (neutral overloading)
        5: 0.4,   # Dominant in 6-pulse
        7: 0.25,  # Second largest in 6-pulse
        11: 0.15, # Decreasing 
        13: 0.10  # Smallest significant
    }
    
    # Convert THD to individual harmonic amplitudes
    # THD = sqrt(sum(Ih^2)) / I1, so we scale harmonics
    total_ratio = sum(harmonic_ratios.values())
    
    spectrum = {}
    for order, ratio in harmonic_ratios.items():
        # Individual harmonic amplitude (simplified)
        h_amplitude = fundamental_amplitude * (thd_percent / 100.0) * (ratio / total_ratio)
        spectrum[order] = round(h_amplitude, 4)
    
    return spectrum
