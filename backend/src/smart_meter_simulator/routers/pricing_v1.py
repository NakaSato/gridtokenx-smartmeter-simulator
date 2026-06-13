"""Thai electricity tariff / billing endpoints.

Exposes the MEA/PEA retail tariff model (``pricing.thai_tariff``) over REST:
list the rate tables and quote an itemised bill for a given kWh.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from smart_meter_simulator.pricing import (
    TARIFFS,
    Bill,
    TariffClass,
    TieredRate,
    TOURate,
    compute_bill,
)

router = APIRouter(prefix="/pricing", tags=["Pricing"])


def _config():
    from smart_meter_simulator.config.settings import get_config

    return get_config()


def _bill_to_dict(bill: Bill) -> dict[str, Any]:
    data = asdict(bill)
    data["tariff"] = bill.tariff.value
    data["currency"] = "THB"
    data["average_rate_per_kwh"] = bill.average_rate_per_kwh
    return data


def _rate_to_dict(tariff: TariffClass, rate: Any) -> dict[str, Any]:
    if isinstance(rate, TOURate):
        return {
            "tariff": tariff.value,
            "structure": "tou",
            "peak_rate": rate.peak,
            "off_peak_rate": rate.off_peak,
            "service_charge": rate.service_charge,
        }
    assert isinstance(rate, TieredRate)
    return {
        "tariff": tariff.value,
        "structure": "tiered",
        "tiers": [
            {"up_to_kwh": tier.up_to_kwh, "rate": tier.rate} for tier in rate.tiers
        ],
        "service_charge": rate.service_charge,
    }


class QuoteInput(BaseModel):
    """Bill-quote request. TOU tariffs use peak/off_peak; tiered tariffs use kwh."""

    tariff: TariffClass = TariffClass.RESIDENTIAL_AUTO
    kwh: Optional[float] = Field(None, ge=0)
    peak_kwh: Optional[float] = Field(None, ge=0)
    off_peak_kwh: Optional[float] = Field(None, ge=0)
    months: int = Field(1, ge=1)
    # Net-billing solar export: surplus PV bought back at export_per_kwh, netted
    # off the import bill into net_total.
    export_kwh: Optional[float] = Field(None, ge=0)
    # Optional overrides; default to the configured Ft / VAT / export rate.
    ft_per_kwh: Optional[float] = Field(None, ge=0)
    vat_rate: Optional[float] = Field(None, ge=0, le=1)
    export_per_kwh: Optional[float] = Field(None, ge=0)


@router.get("/tariffs")
async def list_tariffs():
    """List the modelled tariff classes with their rate tables and current Ft/VAT."""
    config = _config()
    return {
        "currency": "THB",
        "ft_per_kwh": config.tariff_ft_per_kwh,
        "vat_rate": config.tariff_vat_rate,
        "note": (
            "Energy-charge rates are the MEA Nov-2018 base schedule (฿/kWh). Ft is "
            "the ERC fuel-adjustment surcharge, revised ~quarterly and config-driven."
        ),
        "tariffs": [_rate_to_dict(tariff, rate) for tariff, rate in TARIFFS.items()],
    }


@router.post("/quote")
async def quote_bill(data: QuoteInput):
    """Compute an itemised bill for the supplied energy under the chosen tariff."""
    config = _config()
    try:
        bill = compute_bill(
            data.tariff,
            kwh=data.kwh,
            peak_kwh=data.peak_kwh,
            off_peak_kwh=data.off_peak_kwh,
            ft_per_kwh=(
                data.ft_per_kwh
                if data.ft_per_kwh is not None
                else config.tariff_ft_per_kwh
            ),
            vat_rate=(
                data.vat_rate if data.vat_rate is not None else config.tariff_vat_rate
            ),
            months=data.months,
            export_kwh=data.export_kwh or 0.0,
            export_per_kwh=(
                data.export_per_kwh
                if data.export_per_kwh is not None
                else config.tariff_export_per_kwh
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _bill_to_dict(bill)
