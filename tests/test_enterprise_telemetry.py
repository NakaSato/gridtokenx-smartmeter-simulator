import pytest
from datetime import datetime, timezone
from src.smart_meter_simulator.models.reading import EnergyReading

def test_energy_reading_enterprise_payload():
    """Verify that the submission payload contains Phase 24 metrics."""
    reading = EnergyReading(
        meter_id="METER_TEST_001",
        timestamp=datetime.now(timezone.utc),
        energy_generated=10.5,
        energy_consumed=2.0,
        surplus_energy=8.5,
        deficit_energy=0.0,
        interval_seconds=900,
        location="Zone_1",
        meter_type="solar",
        user_type="residential",
        wallet_address="5H8...xyz",
        nodal_price=0.742,
        carbon_intensity=342.5
    )
    
    payload = reading.to_submission_payload()
    
    # Check core enterprise fields
    assert "nodal_price" in payload
    assert "carbon_intensity" in payload
    
    # Check values and rounding
    assert payload["nodal_price"] == 0.742
    assert payload["carbon_intensity"] == 342.5
    assert payload["kwh"] == 8.5
    assert payload["meter_serial"] == "METER_TEST_001"

    print("\n✅ Enterprise Telemetry Payload Verified")

if __name__ == "__main__":
    test_energy_reading_enterprise_payload()
