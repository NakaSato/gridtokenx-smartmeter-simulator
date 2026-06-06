from dataclasses import dataclass
from pathlib import Path

from smart_meter_simulator.core.engine import SimulationEngine

REFERENCE_GLM_FILE = Path("src/smart_meter_simulator/data/grids/grid_bus_network.glm")


@dataclass
class _Reading:
    energy_generated: float
    energy_consumed: float


def _engine(meters: int = 5) -> SimulationEngine:
    engine = SimulationEngine(
        grid_topology=f"glm:{REFERENCE_GLM_FILE}", num_meters=meters
    )
    engine.grid.initialize_network(engine.meters)
    return engine


def test_surplus_raises_frequency_above_nominal():
    engine = _engine()
    cfg = engine.config
    engine._update_grid_frequency([_Reading(10.0, 4.0)])
    assert engine.grid_frequency_hz > cfg.freq_nominal_hz
    # Frequency is fed to every meter for next-tick droop.
    assert all(m.current_frequency == engine.grid_frequency_hz for m in engine.meters)


def test_deficit_pulls_frequency_below_nominal():
    engine = _engine()
    cfg = engine.config
    engine._update_grid_frequency([_Reading(2.0, 9.0)])
    assert engine.grid_frequency_hz < cfg.freq_nominal_hz


def test_balanced_holds_nominal():
    engine = _engine()
    cfg = engine.config
    engine._update_grid_frequency([_Reading(5.0, 5.0)])
    assert engine.grid_frequency_hz == cfg.freq_nominal_hz


def test_swing_is_clamped_to_full_swing():
    engine = _engine()
    cfg = engine.config
    # Pure export (load ~0) -> ratio saturates at +1, freq caps at nominal+full_swing.
    engine._update_grid_frequency([_Reading(100.0, 0.0)])
    assert engine.grid_frequency_hz == cfg.freq_nominal_hz + cfg.freq_full_swing_hz


def test_disabled_pins_nominal_and_skips_meters():
    engine = _engine()
    cfg = engine.config
    engine.config.freq_droop_enabled = False
    before = [m.current_frequency for m in engine.meters]
    engine._update_grid_frequency([_Reading(10.0, 1.0)])
    assert engine.grid_frequency_hz == cfg.freq_nominal_hz
    assert [m.current_frequency for m in engine.meters] == before
