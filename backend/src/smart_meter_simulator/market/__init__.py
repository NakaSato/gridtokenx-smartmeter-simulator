"""
Transactive Energy Market module for GridTokenX Smart Meter Simulator.

Implements a Thai-grid-adapted version of TESP's DSO+T (Distribution System
Operator + Transactive) market patterns:

- :class:`ThaiRetailMarket` — Double-auction clearing engine with Thai tariff structure
- :class:`TransactiveAgent` — Per-meter agent that generates bids/offers
- :class:`TOUEngine` — Thai time-of-use tariff engine (PEA/MEA rates)
- :class:`MarketHandler` — Orchestrates market clearing within the simulation tick

References:
    - TESP DSO+T Study: https://tesp.readthedocs.io/en/latest/
    - PEA Tariff Structure: Thailand Provincial Electricity Authority
"""

from .retail_market import ThaiRetailMarket, MarketResult, Bid, Offer
from .curves import SupplyCurve, DemandCurve
from .tou_engine import TOUEngine
from .market_agent import TransactiveAgent
from .market_handler import MarketHandler

__all__ = [
    "ThaiRetailMarket",
    "MarketResult",
    "Bid",
    "Offer",
    "SupplyCurve",
    "DemandCurve",
    "TOUEngine",
    "TransactiveAgent",
    "MarketHandler",
]
