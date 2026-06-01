import pytest
from datetime import datetime
from smart_meter_simulator.core.transactive import TransactiveController
from smart_meter_simulator.devices.ami import SmartMeter


def test_transactive_controller_price_history():
    """Verify that the TransactiveController records prices and computes correct averages."""
    controller = TransactiveController(history_limit=5)