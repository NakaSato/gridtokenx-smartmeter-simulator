"""Per-meter carbon accounting and avoided-emissions (offset) model.

Mirrors ``pricing.thai_tariff``: a pure, framework-free computation over a
meter's accumulated grid import / export, parameterised by emission factors.

The model is *consequential*: exported rooftop-PV surplus displaces marginal
grid generation, so each exported kWh avoids ``grid_intensity`` kg CO2e but
carries the PV's own life-cycle footprint ``solar_intensity`` — the **net**
offset per exported kWh is ``grid_intensity - solar_intensity``. Self-consumed
PV is already netted out of grid import (the meter only sees the residual
deficit), so it needs no separate term here.

Emission factors are config-driven (``CARBON_*``); the defaults are documented
public figures:

- ``grid_intensity`` 0.4999 kg CO2e/kWh — Thailand grid average electricity
  emission factor (TGO / Thailand Greenhouse Gas Management Organization).
- ``solar_intensity`` 0.041 kg CO2e/kWh — IPCC AR5 median life-cycle intensity
  for rooftop solar PV.
- ``kg_per_tree_year`` 21.77 kg CO2/year — US EPA estimate of CO2 sequestered
  by one urban tree seedling grown for 10 years (for the tangible
  "trees-equivalent" display only).
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_GRID_INTENSITY_KGCO2_PER_KWH = 0.4999
DEFAULT_SOLAR_INTENSITY_KGCO2_PER_KWH = 0.041
DEFAULT_KG_PER_TREE_YEAR = 21.77


@dataclass
class CarbonOffset:
    """Carbon footprint of a meter's grid exchange and the offset from export."""

    import_kwh: float
    export_kwh: float
    grid_intensity_kgco2_per_kwh: float
    solar_intensity_kgco2_per_kwh: float
    # Emissions caused by importing grid energy.
    grid_emissions_kg: float
    # Avoided grid emissions from exported surplus, before deducting the PV
    # life-cycle footprint (export_kwh * grid_intensity).
    gross_offset_kg: float
    # Net offset: avoided grid emissions less the exported PV's own footprint.
    offset_kg: float
    # grid_emissions_kg - offset_kg. Negative = net carbon-negative meter.
    net_emissions_kg: float
    # Net offset expressed as equivalent tree-years of sequestration.
    trees_equivalent: float


def compute_offset(
    *,
    import_kwh: float,
    export_kwh: float,
    grid_intensity: float = DEFAULT_GRID_INTENSITY_KGCO2_PER_KWH,
    solar_intensity: float = DEFAULT_SOLAR_INTENSITY_KGCO2_PER_KWH,
    kg_per_tree_year: float = DEFAULT_KG_PER_TREE_YEAR,
) -> CarbonOffset:
    """Compute a meter's carbon footprint and avoided emissions.

    ``import_kwh`` / ``export_kwh`` are lifetime accumulators (kWh). Emission
    factors are kg CO2e/kWh. Raises ``ValueError`` on negative energy / factors
    or a non-positive ``kg_per_tree_year``.
    """
    if import_kwh < 0 or export_kwh < 0:
        raise ValueError("import_kwh and export_kwh must be non-negative")
    if grid_intensity < 0 or solar_intensity < 0:
        raise ValueError("emission factors must be non-negative")
    if kg_per_tree_year <= 0:
        raise ValueError("kg_per_tree_year must be positive")

    grid_emissions = import_kwh * grid_intensity
    gross_offset = export_kwh * grid_intensity
    # Net of the exported PV's own life-cycle footprint; clamp so a (degenerate)
    # solar_intensity > grid_intensity can't turn an export into an emission.
    net_offset = export_kwh * max(0.0, grid_intensity - solar_intensity)
    net_emissions = grid_emissions - net_offset

    return CarbonOffset(
        import_kwh=round(import_kwh, 4),
        export_kwh=round(export_kwh, 4),
        grid_intensity_kgco2_per_kwh=grid_intensity,
        solar_intensity_kgco2_per_kwh=solar_intensity,
        grid_emissions_kg=round(grid_emissions, 4),
        gross_offset_kg=round(gross_offset, 4),
        offset_kg=round(net_offset, 4),
        net_emissions_kg=round(net_emissions, 4),
        trees_equivalent=round(net_offset / kg_per_tree_year, 2),
    )
