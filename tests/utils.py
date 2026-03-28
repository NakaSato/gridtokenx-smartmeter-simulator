"""
Test Utilities Module

Shared utility functions and helpers for test suites.

This module provides:
- Test data generators
- Assertion helpers
- Mock builders
- Test constants
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandapower as pp


# ============================================================================
# Test Constants
# ============================================================================

DEFAULT_TEST_SEED = 42
DEFAULT_VOLTAGE_PU = 1.0
DEFAULT_FREQUENCY_HZ = 50.0
TOLERANCE_VOLTAGE = 0.01
TOLERANCE_POWER = 0.001
TOLERANCE_ANGLE = 0.1


# ============================================================================
# Data Generators
# ============================================================================


def generate_meter_id(prefix: str = "METER", index: int = 0) -> str:
    """
    Generate a unique meter ID.

    Args:
        prefix: ID prefix
        index: Numeric suffix

    Returns:
        str: Generated meter ID
    """
    return f"{prefix}_{index:04d}"


def generate_random_reading(
    meter_id: str,
    timestamp: Optional[datetime] = None,
    gen_min: float = 0.0,
    gen_max: float = 10.0,
    cons_min: float = 0.0,
    cons_max: float = 5.0,
    noise_factor: float = 0.05,
) -> Dict[str, Any]:
    """
    Generate a random energy reading for testing.

    Args:
        meter_id: Meter identifier
        timestamp: Reading timestamp (default: now)
        gen_min: Minimum generation (kW)
        gen_max: Maximum generation (kW)
        cons_min: Minimum consumption (kW)
        cons_max: Maximum consumption (kW)
        noise_factor: Noise standard deviation factor

    Returns:
        dict: Energy reading dictionary
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    gen = random.uniform(gen_min, gen_max)
    cons = random.uniform(cons_min, cons_max)

    # Add noise
    gen_noisy = gen * (1 + random.gauss(0, noise_factor))
    cons_noisy = cons * (1 + random.gauss(0, noise_factor))

    return {
        "meter_id": meter_id,
        "timestamp": timestamp.isoformat(),
        "energy_generated_kwh": max(0, gen_noisy),
        "energy_consumed_kwh": max(0, cons_noisy),
        "net_energy_kwh": max(0, gen_noisy - cons_noisy),
        "voltage_v": 240.0 * (1 + random.gauss(0, 0.02)),
        "frequency_hz": 50.0 + random.gauss(0, 0.05),
    }


def generate_time_series(
    start: datetime,
    periods: int,
    freq_minutes: int = 15,
    base_value: float = 1.0,
    amplitude: float = 0.3,
    noise: float = 0.05,
) -> List[Dict[str, Any]]:
    """
    Generate a time series with daily pattern.

    Args:
        start: Start timestamp
        periods: Number of periods
        freq_minutes: Frequency in minutes
        base_value: Base value
        amplitude: Daily variation amplitude
        noise: Noise standard deviation

    Returns:
        list: Time series data points
    """
    data = []
    for i in range(periods):
        ts = start + timedelta(minutes=i * freq_minutes)
        hour = ts.hour + ts.minute / 60.0

        # Daily pattern (solar-like)
        daily_factor = np.sin(np.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 0
        value = base_value * (1 + amplitude * max(0, daily_factor))
        value *= 1 + random.gauss(0, noise)

        data.append({"timestamp": ts, "value": max(0, value)})

    return data


# ============================================================================
# Pandapower Helpers
# ============================================================================


def create_simple_grid(
    num_buses: int = 3,
    voltage_kv: float = 11.0,
    add_measurements: bool = False,
    seed: int = DEFAULT_TEST_SEED,
) -> pp.pandapowerNet:
    """
    Create a simple radial pandapower network.

    Args:
        num_buses: Number of buses
        voltage_kv: Nominal voltage
        add_measurements: Add measurements for SE
        seed: Random seed for reproducibility

    Returns:
        pandapowerNet: Created network
    """
    random.seed(seed)
    np.random.seed(seed)

    net = pp.create_empty_network()

    # Create buses
    bus_indices = []
    for i in range(num_buses):
        name = f"Bus {i}" if i > 0 else "Substation"
        bus_idx = pp.create_bus(net, vn_kv=voltage_kv, name=name)
        bus_indices.append(bus_idx)

    # Add ext_grid at substation
    pp.create_ext_grid(net, bus=bus_indices[0])

    # Create lines (radial)
    for i in range(num_buses - 1):
        pp.create_line_from_parameters(
            net,
            from_bus=bus_indices[i],
            to_bus=bus_indices[i + 1],
            length_km=1.0,
            r_ohm_per_km=0.1,
            x_ohm_per_km=0.1,
            c_nf_per_km=0.0,
            max_i_ka=1.0,
            name=f"Line {i}-{i+1}",
        )

    # Add loads (except at substation)
    for i in range(1, num_buses):
        p_mw = random.uniform(0.02, 0.1)
        q_mvar = p_mw * 0.2  # Assume PF ~0.98
        pp.create_load(
            net,
            bus=bus_indices[i],
            p_mw=p_mw,
            q_mvar=q_mvar,
            name=f"Load {i}",
        )

    # Run power flow
    pp.runpp(net)

    # Add measurements if requested
    if add_measurements:
        _add_measurements_to_net(net)

    return net


def _add_measurements_to_net(net: pp.pandapowerNet) -> None:
    """
    Add measurements to a pandapower network for state estimation.

    Args:
        net: Pandapower network
    """
    # Voltage measurements at all buses
    for i in range(len(net.bus)):
        pp.create_measurement(
            net,
            "v",
            "bus",
            value=net.res_bus.vm_pu.iloc[i],
            std_dev=0.001,
            element=i,
            name=f"v{i}",
        )

    # Line flow measurements
    for i in range(len(net.line)):
        pp.create_measurement(
            net,
            "p",
            "line",
            value=net.res_line.p_from_mw.iloc[i],
            std_dev=0.01,
            element=i,
            side="from",
            name=f"p_line{i}",
        )
        pp.create_measurement(
            net,
            "q",
            "line",
            value=net.res_line.q_from_mvar.iloc[i],
            std_dev=0.01,
            element=i,
            side="from",
            name=f"q_line{i}",
        )


def inject_bad_data(
    net: pp.pandapowerNet,
    meas_type: str = "v",
    element_type: str = "bus",
    element_idx: int = 0,
    bad_value: float = 2.0,
    name_suffix: str = "_bad",
) -> str:
    """
    Inject bad data into a pandapower network.

    Args:
        net: Pandapower network
        meas_type: Measurement type (v, p, q, i)
        element_type: Element type (bus, line, load, sgen)
        element_idx: Element index
        bad_value: Bad measurement value
        name_suffix: Suffix for measurement name

    Returns:
        str: Name of the bad measurement
    """
    meas_name = f"{meas_type}_{element_type}{element_idx}{name_suffix}"
    pp.create_measurement(
        net,
        meas_type,
        element_type,
        value=bad_value,
        std_dev=0.001,
        element=element_idx,
        name=meas_name,
    )
    return meas_name


# ============================================================================
# Assertion Helpers
# ============================================================================


def assert_voltage_valid(
    voltage_pu: float,
    min_pu: float = 0.95,
    max_pu: float = 1.05,
    msg: Optional[str] = None,
) -> None:
    """
    Assert voltage is within valid range.

    Args:
        voltage_pu: Voltage in per-unit
        min_pu: Minimum valid voltage
        max_pu: Maximum valid voltage
        msg: Optional error message
    """
    assert min_pu <= voltage_pu <= max_pu, (
        msg or f"Voltage {voltage_pu} pu out of range [{min_pu}, {max_pu}]"
    )


def assert_power_balance(
    generation: float,
    consumption: float,
    loss: float,
    tolerance: float = TOLERANCE_POWER,
    msg: Optional[str] = None,
) -> None:
    """
    Assert power balance (gen = load + losses).

    Args:
        generation: Total generation (MW)
        consumption: Total consumption (MW)
        loss: Total losses (MW)
        tolerance: Balance tolerance
        msg: Optional error message
    """
    balance = generation - consumption - loss
    assert abs(balance) < tolerance, (
        msg or f"Power imbalance: {balance:.6f} MW (tol={tolerance})"
    )


def assert_convergence(
    converged: bool,
    iterations: int,
    max_iterations: int = 10,
    msg: Optional[str] = None,
) -> None:
    """
    Assert estimation/power flow converged.

    Args:
        converged: Convergence flag
        iterations: Number of iterations
        max_iterations: Maximum allowed iterations
        msg: Optional error message
    """
    assert converged, msg or "Failed to converge"
    assert iterations <= max_iterations, (
        msg or f"Too many iterations: {iterations} > {max_iterations}"
    )


# ============================================================================
# Mock Builders
# ============================================================================


def build_mock_meter(
    meter_id: str = "M1",
    meter_type: str = "Residential",
    has_battery: bool = False,
    has_solar: bool = False,
    battery_capacity: float = 10.0,
    **kwargs,
) -> Dict[str, Any]:
    """
    Build a mock meter configuration dictionary.

    Args:
        meter_id: Meter identifier
        meter_type: Meter type
        has_battery: Include battery
        has_solar: Include solar
        battery_capacity: Battery capacity (kWh)
        **kwargs: Additional config fields

    Returns:
        dict: Meter configuration
    """
    config = {
        "meter_id": meter_id,
        "meter_type": meter_type,
        "has_battery": has_battery,
        "has_solar": has_solar,
        "battery_capacity": battery_capacity if has_battery else 0.0,
        "location": kwargs.get("location", "Zone_1"),
        "phase": kwargs.get("phase", "A"),
    }
    config.update(kwargs)
    return config


def build_mock_tariff(
    import_rate: float = 0.28,
    export_rate: float = 0.15,
    ft_rate: float = 0.0972,
    **kwargs,
) -> Dict[str, Any]:
    """
    Build a mock tariff dictionary.

    Args:
        import_rate: Import rate (Baht/kWh)
        export_rate: Export rate (Baht/kWh)
        ft_rate: Ft rate (Baht/kWh)
        **kwargs: Additional tariff fields

    Returns:
        dict: Tariff configuration
    """
    tariff = {
        "import_rate": import_rate,
        "export_rate": export_rate,
        "ft_rate": ft_rate,
    }
    tariff.update(kwargs)
    return tariff
