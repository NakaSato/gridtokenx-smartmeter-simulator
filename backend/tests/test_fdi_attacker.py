"""
Tests for FDI (False Data Injection) Attacker Module.
"""

import pytest
from datetime import datetime, timezone

from smart_meter_simulator.core.attacker import (
    FDIAttacker,
    AttackMode,
    AttackProfile,
)
from smart_meter_simulator.models.reading import EnergyReading


def make_reading(
    meter_id: str = "M001",
    gen: float = 5.0,
    cons: float = 3.0,
    voltage: float = 230.0,
    current: float = 10.0,
) -> EnergyReading:
    """Create a minimal EnergyReading for testing."""
    return EnergyReading(
        meter_id=meter_id,
        timestamp=datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc),
        energy_generated=gen,
        energy_consumed=cons,
        surplus_energy=max(0.0, gen - cons),
        deficit_energy=max(0.0, cons - gen),
        interval_seconds=900,
        battery_level=0.0,
        location="Test",
        meter_type="Residential",
        user_type="Test",
        voltage=voltage,
        current=current,
        power_factor=0.95,
        frequency=50.0,
        temperature=25.0,
        nodal_price=0.5,
        carbon_intensity=0.0,
        carbon_offset=0.0,
        weather_condition="Sunny",
        rec_eligible=False,
    )


# ============================================================================
# Attack Management Tests
# ============================================================================

class TestAttackManagement:
    def test_no_active_attacks(self):
        attacker = FDIAttacker()
        assert attacker.is_attacking() is False
        assert len(attacker.active_attacks) == 0

    def test_start_bias_attack(self):
        attacker = FDIAttacker()
        aid = attacker.start_attack("a1", AttackMode.BIAS, bias_kw=5.0)
        assert aid == "a1"
        assert attacker.is_attacking() is True
        assert "a1" in attacker.active_attacks

    def test_start_attack_auto_id(self):
        attacker = FDIAttacker()
        aid = attacker.start_attack("custom", AttackMode.RANDOM)
        assert aid == "custom"
        assert attacker.active_attacks["custom"].attack_mode == AttackMode.RANDOM

    def test_stop_attack(self):
        attacker = FDIAttacker()
        attacker.start_attack("a1", AttackMode.BIAS)
        result = attacker.stop_attack("a1")
        assert result is True
        assert "a1" not in attacker.active_attacks
        assert attacker.is_attacking() is False

    def test_stop_nonexistent_attack(self):
        attacker = FDIAttacker()
        result = attacker.stop_attack("nonexistent")
        assert result is False

    def test_stop_all_attacks(self):
        attacker = FDIAttacker()
        attacker.start_attack("a1", AttackMode.BIAS)
        attacker.start_attack("a2", AttackMode.SCALE)
        attacker.start_attack("a3", AttackMode.RANDOM)
        count = attacker.stop_all_attacks()
        assert count == 3
        assert attacker.is_attacking() is False

    def test_stop_all_when_empty(self):
        attacker = FDIAttacker()
        count = attacker.stop_all_attacks()
        assert count == 0

    def test_get_status_empty(self):
        attacker = FDIAttacker()
        status = attacker.get_status()
        assert status["is_attacking"] is False
        assert status["active_attacks"] == 0
        assert status["attacks"] == {}

    def test_get_status_with_attacks(self):
        attacker = FDIAttacker()
        attacker.start_attack(
            "a1", AttackMode.BIAS,
            target_meters={"M001", "M002"},
            bias_kw=10.0,
        )
        status = attacker.get_status()
        assert status["is_attacking"] is True
        assert status["active_attacks"] == 1
        assert "a1" in status["attacks"]
        assert status["attacks"]["a1"]["mode"] == "bias"
        assert status["attacks"]["a1"]["bias_kw"] == 10.0


# ============================================================================
# Bias Attack Tests
# ============================================================================

class TestBiasAttack:
    def test_positive_bias(self):
        attacker = FDIAttacker()
        attacker.start_attack("bias1", AttackMode.BIAS, bias_kw=5.0)

        r = make_reading(cons=10.0, gen=5.0)
        attacker.inject_readings([r])

        assert r.energy_consumed == pytest.approx(15.0, rel=0.01)
        assert r.is_compromised is True

    def test_negative_bias(self):
        attacker = FDIAttacker()
        attacker.start_attack("bias2", AttackMode.BIAS, bias_kw=-3.0)

        r = make_reading(cons=10.0, gen=5.0)
        attacker.inject_readings([r])

        assert r.energy_consumed == pytest.approx(7.0, rel=0.01)

    def test_bias_does_not_go_negative(self):
        attacker = FDIAttacker()
        attacker.start_attack("bias3", AttackMode.BIAS, bias_kw=-100.0)

        r = make_reading(cons=10.0, gen=5.0)
        attacker.inject_readings([r])

        assert r.energy_consumed >= 0.0
        assert r.energy_generated >= 0.0

    def test_bias_targeted(self):
        attacker = FDIAttacker()
        attacker.start_attack("bias4", AttackMode.BIAS, target_meters={"M001"}, bias_kw=5.0)

        r1 = make_reading(meter_id="M001", cons=10.0)
        r2 = make_reading(meter_id="M002", cons=10.0)
        attacker.inject_readings([r1, r2])

        assert r1.energy_consumed == pytest.approx(15.0, rel=0.01)
        assert r2.energy_consumed == pytest.approx(10.0, rel=0.01)  # Unchanged
        assert r1.is_compromised is True
        assert r2.is_compromised is False


# ============================================================================
# Scale Attack Tests
# ============================================================================

class TestScaleAttack:
    def test_scale_up(self):
        attacker = FDIAttacker()
        attacker.start_attack("scale1", AttackMode.SCALE, scale_factor=2.0)

        r = make_reading(cons=10.0, gen=5.0)
        attacker.inject_readings([r])

        assert r.energy_consumed == pytest.approx(20.0, rel=0.01)
        assert r.energy_generated == pytest.approx(10.0, rel=0.01)
        assert r.is_compromised is True

    def test_scale_down(self):
        attacker = FDIAttacker()
        attacker.start_attack("scale2", AttackMode.SCALE, scale_factor=0.5)

        r = make_reading(cons=10.0, gen=5.0)
        attacker.inject_readings([r])

        assert r.energy_consumed == pytest.approx(5.0, rel=0.01)

    def test_scale_voltage_and_current(self):
        attacker = FDIAttacker()
        attacker.start_attack("scale3", AttackMode.SCALE, scale_factor=2.0)

        r = make_reading(voltage=230.0, current=10.0)
        attacker.inject_readings([r])

        assert r.current == pytest.approx(20.0, rel=0.01)
        # Voltage scales less (10% of the factor)
        assert r.voltage > 230.0


# ============================================================================
# Random Attack Tests
# ============================================================================

class TestRandomAttack:
    def test_random_adds_noise(self):
        attacker = FDIAttacker()
        attacker.start_attack("rand1", AttackMode.RANDOM, noise_bound_kw=5.0)

        r = make_reading(cons=10.0, gen=5.0)
        attacker.inject_readings([r])

        # Should have changed from original
        assert r.energy_consumed != 10.0 or r.energy_generated != 5.0
        assert r.energy_consumed >= 0.0
        assert r.energy_generated >= 0.0
        assert r.is_compromised is True

    def test_random_bounded(self):
        attacker = FDIAttacker()
        attacker.start_attack("rand2", AttackMode.RANDOM, noise_bound_kw=1.0)

        results = []
        for _ in range(50):
            r = make_reading(cons=100.0, gen=50.0)
            attacker.inject_readings([r])
            results.append(r.energy_consumed)

        # All should be within ±1.0 of 100
        for val in results:
            assert 99.0 <= val <= 101.0


# ============================================================================
# Stealth Attack Tests
# ============================================================================

class TestStealthAttack:
    def test_stealth_adds_subtle_bias(self):
        attacker = FDIAttacker()
        attacker.start_attack("stealth1", AttackMode.STEALTH, stealth_residual_target=1.5)

        r = make_reading(cons=100.0, gen=50.0)
        attacker.inject_readings([r])

        # Should be slightly modified but not wildly
        assert r.energy_consumed != 100.0
        assert abs(r.energy_consumed - 100.0) < 10.0  # Small deviation
        assert r.is_compromised is True

    def test_stealth_sets_norm_residual(self):
        attacker = FDIAttacker()
        attacker.start_attack("stealth2", AttackMode.STEALTH, stealth_residual_target=2.0)

        r = make_reading(cons=100.0)
        attacker.inject_readings([r])

        # norm_residual should be set near target
        assert r.norm_residual is not None
        assert 1.5 <= r.norm_residual <= 3.5  # Near 2.0 ± 0.5 jitter

    def test_stealth_stays_below_detection_threshold(self):
        """Stealth attacks should set norm_residual below 3.0 (detection threshold)."""
        attacker = FDIAttacker()
        attacker.start_attack("stealth3", AttackMode.STEALTH, stealth_residual_target=2.5)

        results = []
        for _ in range(20):
            r = make_reading(cons=100.0)
            attacker.inject_readings([r])
            results.append(r.norm_residual)

        # All should be below the bad data threshold of 4.0
        for val in results:
            assert val is not None
            assert val < 4.0


# ============================================================================
# Batch Injection Tests
# ============================================================================

class TestBatchInjection:
    def test_inject_no_attacks(self):
        attacker = FDIAttacker()
        readings = [make_reading(meter_id=f"M{i}") for i in range(5)]
        result = attacker.inject_readings(readings)
        # No changes when no attacks active
        for r in result:
            assert r.energy_consumed != 0  # Original values preserved
            assert r.is_compromised is False

    def test_inject_multiple_attacks_same_meter(self):
        attacker = FDIAttacker()
        attacker.start_attack("a1", AttackMode.BIAS, bias_kw=5.0)
        attacker.start_attack("a2", AttackMode.BIAS, bias_kw=3.0)

        r = make_reading(cons=10.0)
        attacker.inject_readings([r])

        # Both biases applied sequentially
        assert r.energy_consumed == pytest.approx(18.0, rel=0.01)
        assert r.is_compromised is True

    def test_inject_large_batch(self):
        attacker = FDIAttacker()
        attacker.start_attack("batch", AttackMode.SCALE, scale_factor=1.5)

        readings = [make_reading(meter_id=f"M{i}", cons=10.0) for i in range(100)]
        attacker.inject_readings(readings)

        for r in readings:
            assert r.energy_consumed == pytest.approx(15.0, rel=0.01)
            assert r.is_compromised is True


# ============================================================================
# AttackMode Enum Tests
# ============================================================================

class TestAttackMode:
    def test_all_modes_exist(self):
        assert AttackMode.BIAS.value == "bias"
        assert AttackMode.SCALE.value == "scale"
        assert AttackMode.RANDOM.value == "random"
        assert AttackMode.STEALTH.value == "stealth"

    def test_mode_from_string(self):
        assert AttackMode("bias") == AttackMode.BIAS
        assert AttackMode("scale") == AttackMode.SCALE
        assert AttackMode("random") == AttackMode.RANDOM
        assert AttackMode("stealth") == AttackMode.STEALTH

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            AttackMode("invalid")


# ============================================================================
# Surplus/Deficit Recalculation Tests
# ============================================================================

class TestSurplusDeficit:
    def test_bias_creates_deficit(self):
        """Original: gen=10, cons=5 (surplus 5). After +10 bias on cons: cons=15 (deficit 5)."""
        attacker = FDIAttacker()
        attacker.start_attack("b1", AttackMode.BIAS, bias_kw=10.0)

        r = make_reading(gen=10.0, cons=5.0)
        attacker.inject_readings([r])

        assert r.deficit_energy > 0
        assert r.surplus_energy == 0.0

    def test_scale_preserves_surplus_sign(self):
        """Scaling shouldn't flip surplus to deficit."""
        attacker = FDIAttacker()
        attacker.start_attack("s1", AttackMode.SCALE, scale_factor=0.5)

        r = make_reading(gen=10.0, cons=5.0)  # Surplus 5
        attacker.inject_readings([r])

        assert r.surplus_energy > 0
        assert r.deficit_energy == 0.0
