"""
FDI (False Data Injection) Attacker Module
Simulates cyber-physical attacks on smart meter readings for security testing.

Supports four attack modes:
- bias: Add constant offset to target meters
- scale: Multiply readings by scale factor
- random: Inject random noise within bounds
- stealth: Craft correlated attacks that bypass chi-squared detection
"""

import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

import numpy as np

from ..models.reading import EnergyReading
from .constants import (
    BAD_DATA_COMPROMISED_THRESHOLD,
    BAD_DATA_NORM_RESIDUAL_THRESHOLD,
)

logger = logging.getLogger(__name__)


class AttackMode(str, Enum):
    BIAS = "bias"
    SCALE = "scale"
    RANDOM = "random"
    STEALTH = "stealth"


@dataclass
class AttackProfile:
    """Configuration for an active FDI attack."""
    attack_mode: AttackMode
    target_meters: Set[str]           # Empty = all meters
    bias_kw: float                    # For bias mode: constant offset
    scale_factor: float               # For scale mode: multiplier
    noise_bound_kw: float             # For random mode: ± bound
    stealth_residual_target: float    # For stealth: target normalized residual
    active: bool = True


class FDIAttacker:
    """
    False Data Injection attack simulator.

    Injects crafted errors into meter readings to test
    the resilience of state estimation and bad data detection.
    """

    def __init__(self):
        self.active_attacks: Dict[str, AttackProfile] = {}
        self.attack_counter = 0
        self._rng = np.random.default_rng(seed=42)

    # ========================================================================
    # Attack Management
    # ========================================================================

    def start_attack(
        self,
        attack_id: str,
        attack_mode: AttackMode,
        target_meters: Optional[Set[str]] = None,
        bias_kw: float = 0.0,
        scale_factor: float = 1.0,
        noise_bound_kw: float = 5.0,
        stealth_residual_target: float = 0.5,
    ) -> str:
        """
        Start an FDI attack on specified meters.

        Args:
            attack_id: Unique identifier for this attack
            attack_mode: Type of attack (bias/scale/random/stealth)
            target_meters: Set of meter IDs to target (None = all)
            bias_kw: Constant bias to add (kW) — for bias mode
            scale_factor: Multiplier for readings — for scale mode
            noise_bound_kw: Random noise bounds (±kW) — for random mode
            stealth_residual_target: Target normalized residual — for stealth
        """
        profile = AttackProfile(
            attack_mode=attack_mode,
            target_meters=target_meters or set(),
            bias_kw=bias_kw,
            scale_factor=scale_factor,
            noise_bound_kw=noise_bound_kw,
            stealth_residual_target=stealth_residual_target,
            active=True,
        )
        self.active_attacks[attack_id] = profile
        target_info = list(profile.target_meters) if profile.target_meters else ["ALL"]
        logger.warning(
            f"FDI attack '{attack_id}' started: mode={attack_mode.value}, "
            f"targets={target_info}"
        )
        return attack_id

    def stop_attack(self, attack_id: str) -> bool:
        """Stop and remove an active attack."""
        if attack_id in self.active_attacks:
            del self.active_attacks[attack_id]
            logger.info(f"FDI attack '{attack_id}' stopped")
            return True
        return False

    def stop_all_attacks(self) -> int:
        """Stop all active attacks. Returns count of stopped attacks."""
        count = len(self.active_attacks)
        self.active_attacks.clear()
        logger.info(f"All FDI attacks stopped ({count} removed)")
        return count

    def is_attacking(self) -> bool:
        """Check if any attack is active."""
        return any(a.active for a in self.active_attacks.values())

    def get_status(self) -> Dict:
        """Get summary of all active attacks."""
        attacks = {}
        for aid, profile in self.active_attacks.items():
            attacks[aid] = {
                "mode": profile.attack_mode.value,
                "targets": list(profile.target_meters) if profile.target_meters else ["ALL"],
                "bias_kw": profile.bias_kw,
                "scale_factor": profile.scale_factor,
                "noise_bound_kw": profile.noise_bound_kw,
                "active": profile.active,
            }
        return {
            "is_attacking": self.is_attacking(),
            "active_attacks": len(self.active_attacks),
            "attacks": attacks,
        }

    # ========================================================================
    # Attack Injection
    # ========================================================================

    def inject_readings(
        self,
        readings: List[EnergyReading],
    ) -> List[EnergyReading]:
        """
        Apply all active attacks to a batch of readings.
        Modifies readings in-place and returns them.
        """
        if not self.is_attacking():
            return readings

        for reading in readings:
            self._apply_attacks_to_reading(reading)

        return readings

    def _apply_attacks_to_reading(self, reading: EnergyReading) -> None:
        """Apply all active attack profiles to a single reading."""
        for attack_id, profile in self.active_attacks.items():
            if not profile.active:
                continue
            if profile.target_meters and reading.meter_id not in profile.target_meters:
                continue

            if profile.attack_mode == AttackMode.BIAS:
                self._apply_bias(reading, profile)
            elif profile.attack_mode == AttackMode.SCALE:
                self._apply_scale(reading, profile)
            elif profile.attack_mode == AttackMode.RANDOM:
                self._apply_random(reading, profile)
            elif profile.attack_mode == AttackMode.STEALTH:
                self._apply_stealth(reading, profile)

            reading.is_compromised = True

    def _apply_bias(self, reading: EnergyReading, profile: AttackProfile) -> None:
        """Add constant bias to energy values."""
        bias = profile.bias_kw
        reading.energy_consumed = max(0.0, reading.energy_consumed + bias)
        # If bias is negative, consumption drops; if positive, it inflates
        reading.energy_generated = max(0.0, reading.energy_generated - bias * 0.1)
        reading.deficit_energy = max(0.0, reading.energy_consumed - reading.energy_generated)
        reading.surplus_energy = max(0.0, reading.energy_generated - reading.energy_consumed)

    def _apply_scale(self, reading: EnergyReading, profile: AttackProfile) -> None:
        """Multiply readings by a scale factor."""
        factor = profile.scale_factor
        reading.energy_consumed *= factor
        reading.energy_generated *= factor
        reading.deficit_energy = max(0.0, reading.energy_consumed - reading.energy_generated)
        reading.surplus_energy = max(0.0, reading.energy_generated - reading.energy_consumed)
        # Also scale electrical parameters
        if reading.voltage is not None:
            reading.voltage *= (1.0 + (factor - 1.0) * 0.1)  # Voltage scales less
        if reading.current is not None:
            reading.current *= factor

    def _apply_random(self, reading: EnergyReading, profile: AttackProfile) -> None:
        """Add random noise within bounds."""
        bound = profile.noise_bound_kw
        noise_cons = self._rng.uniform(-bound, bound)
        noise_gen = self._rng.uniform(-bound * 0.2, bound * 0.2)  # Generation noise smaller
        reading.energy_consumed = max(0.0, reading.energy_consumed + noise_cons)
        reading.energy_generated = max(0.0, reading.energy_generated + noise_gen)
        reading.deficit_energy = max(0.0, reading.energy_consumed - reading.energy_generated)
        reading.surplus_energy = max(0.0, reading.energy_generated - reading.energy_consumed)

    def _apply_stealth(self, reading: EnergyReading, profile: AttackProfile) -> None:
        """
        Craft stealthy attack that stays below detection thresholds.

        Strategy: inject error that keeps normalized residual below
        BAD_DATA_NORM_RESIDUAL_THRESHOLD (3.0) but still biases state estimation.
        Uses the relationship between measurement std_dev and accuracy class
        to craft errors that appear statistically plausible.
        """
        target_residual = profile.stealth_residual_target
        # Error magnitude chosen to stay below chi-squared threshold
        # Typical std_dev ~ 1-3% of reading for CLASS_1_0
        std_dev_fraction = 0.02  # 2% of reading as baseline std_dev
        error = target_residual * reading.energy_consumed * std_dev_fraction

        # Add small random component to avoid deterministic pattern
        jitter = self._rng.uniform(-0.1, 0.1) * error
        error += jitter

        # Apply error asymmetrically: bias consumption more than generation
        reading.energy_consumed = max(0.0, reading.energy_consumed + error)
        reading.energy_generated = max(0.0, reading.energy_generated + error * 0.3)
        reading.deficit_energy = max(0.0, reading.energy_consumed - reading.energy_generated)
        reading.surplus_energy = max(0.0, reading.energy_generated - reading.energy_consumed)

        # Mark with elevated but sub-threshold residual for tracking
        reading.norm_residual = target_residual + self._rng.uniform(0, 0.5)
