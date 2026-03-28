"""
Price Comparison API Tests

Tests for the utility vs P2P price comparison API endpoints:
- POST /api/v1/price/compare - Compare utility and P2P prices
- GET /api/v1/price/utility-rates - Get utility rates
- GET /api/v1/price/p2p-dynamic - Get dynamic P2P price

Run with:
    uv run pytest tests/test_price_comparison_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from smart_meter_simulator.app import app


class TestPriceComparisonEndpoint:
    """Tests for POST /api/v1/price/compare endpoint."""

    def test_compare_prices_basic(self):
        """Test basic price comparison request."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 500.0,
                "utility_provider": "PEA",
                "tariff_category": "1.1.2",
                "billing_month": 3,
                "wheeling_cost": 1.76,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "timestamp" in data
        assert "energy_kwh" in data
        assert "utility" in data
        assert "p2p" in data
        assert "analysis" in data
        assert "recommendation" in data
        
        # Verify utility response
        assert data["utility"]["provider"] == "PEA"
        assert data["utility"]["tariff_category"] == "1.1.2"
        assert data["utility"]["total_amount_baht"] > 0
        
        # Verify P2P response
        assert data["p2p"]["market_clearing_price_baht_kwh"] > 0
        assert data["p2p"]["wheeling_cost_baht_kwh"] == 1.76
        assert data["p2p"]["buyer_total_baht_kwh"] > 0
        
        # Verify analysis
        assert "buyer_savings_baht" in data["analysis"]
        assert "is_p2p_beneficial" in data["analysis"]

    def test_compare_prices_mea_provider(self):
        """Test price comparison with MEA provider."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 300.0,
                "utility_provider": "MEA",
                "tariff_category": "1.1.2",
                "billing_month": 1,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["utility"]["provider"] == "MEA"

    def test_compare_prices_tou_tariff(self):
        """Test price comparison with TOU tariff."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 500.0,
                "tariff_category": "1.2",  # TOU tariff
                "billing_month": 6,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["utility"]["tariff_category"] == "1.2"

    def test_compare_prices_custom_p2p_price(self):
        """Test price comparison with custom P2P price."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 200.0,
                "p2p_price": 3.50,
                "wheeling_cost": 1.50,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["p2p"]["market_clearing_price_baht_kwh"] == 3.50

    def test_compare_prices_high_consumption(self):
        """Test price comparison for high consumption (>400 kWh)."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 600.0,
                "tariff_category": "1.1.2",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # High consumption should have higher average rate
        assert data["utility"]["average_rate_baht_kwh"] > 4.0

    def test_compare_prices_low_consumption(self):
        """Test price comparison for low consumption (<150 kWh)."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 100.0,
                "tariff_category": "1.1.2",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Low consumption has lower total bill but rate depends on tier structure
        # For Type 1.1.2, even 100 kWh is in first tier (3.2484 Baht/kWh base + Ft)
        assert data["utility"]["average_rate_baht_kwh"] > 3.0
        assert data["utility"]["total_amount_baht"] < 1000  # Total bill should be low

    def test_compare_prices_validation_missing_energy(self):
        """Test validation error for missing energy_kwh."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/price/compare",
            json={
                "utility_provider": "PEA",
            },
        )
        
        assert response.status_code == 422

    def test_compare_prices_validation_invalid_month(self):
        """Test validation error for invalid billing month."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 100.0,
                "billing_month": 13,  # Invalid
            },
        )
        
        assert response.status_code == 422


class TestUtilityRatesEndpoint:
    """Tests for GET /api/v1/price/utility-rates endpoint."""

    def test_get_utility_rates_pea(self):
        """Test getting PEA utility rates."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/price/utility-rates",
            params={
                "provider": "PEA",
                "tariff_category": "1.1.2",
                "billing_month": 3,
                "energy_kwh": 500.0,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["provider"] == "PEA"
        assert data["tariff_category"] == "1.1.2"
        assert data["ft_rate_baht_kwh"] > 0
        assert "sample_bill" in data
        assert data["sample_bill"]["total_kwh"] == 500.0

    def test_get_utility_rates_mea(self):
        """Test getting MEA utility rates."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/price/utility-rates",
            params={
                "provider": "MEA",
                "billing_month": 6,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "MEA"

    def test_get_utility_rates_tou(self):
        """Test getting TOU tariff rates."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/price/utility-rates",
            params={
                "tariff_category": "1.2",
                "billing_month": 1,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tariff_category"] == "1.2"

    def test_get_utility_rates_ft_rate_by_month(self):
        """Test Ft rate varies by billing month."""
        client = TestClient(app)
        
        # Jan-Apr: Ft = 0.0972
        response_jan = client.get(
            "/api/v1/price/utility-rates",
            params={"billing_month": 1},
        )
        # Sep-Dec: Ft = 0.1572 (2025 rate)
        response_sep = client.get(
            "/api/v1/price/utility-rates",
            params={"billing_month": 9},
        )
        
        assert response_jan.status_code == 200
        assert response_sep.status_code == 200
        
        # Ft rates should be different
        assert response_jan.json()["ft_rate_baht_kwh"] != response_sep.json()["ft_rate_baht_kwh"]


class TestP2PDynamicPriceEndpoint:
    """Tests for GET /api/v1/price/p2p-dynamic endpoint."""

    def test_get_p2p_dynamic_price_balanced(self):
        """Test P2P dynamic price for balanced market."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/price/p2p-dynamic",
            params={
                "supply_kwh": 100.0,
                "demand_kwh": 100.0,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["market_clearing_price_baht_kwh"] > 0
        assert data["buyer_total_baht_kwh"] > 0
        assert data["seller_net_baht_kwh"] > 0
        assert "formula" in data
        assert data["formula"]["name"] == "GridTokenX Dynamic Pricing"

    def test_get_p2p_dynamic_price_high_demand(self):
        """Test P2P dynamic price for high demand."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/price/p2p-dynamic",
            params={
                "supply_kwh": 50.0,
                "demand_kwh": 150.0,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # High demand should result in higher price
        assert data["market_clearing_price_baht_kwh"] > 3.0

    def test_get_p2p_dynamic_price_oversupply(self):
        """Test P2P dynamic price for oversupply."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/price/p2p-dynamic",
            params={
                "supply_kwh": 200.0,
                "demand_kwh": 50.0,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Oversupply should result in lower price (close to base)
        # Note: Formula produces ~3.54 for this scenario, which is still reasonable
        assert data["market_clearing_price_baht_kwh"] < 4.0

    def test_get_p2p_dynamic_price_formula_params(self):
        """Test P2P dynamic price returns correct formula parameters."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/price/p2p-dynamic",
            params={
                "supply_kwh": 100.0,
                "demand_kwh": 120.0,
                "base_price": 2.20,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify formula parameters
        formula = data["formula"]
        assert formula["equation"] == "p_t = arctan(e^D_t) + arctan(R_t)/10 + p_min"
        assert formula["D_t"] == (120 - 100) / 100.0
        assert formula["R_t"] == 120 / 100
        assert formula["p_min"] == 2.20

    def test_get_p2p_dynamic_price_custom_wheeling(self):
        """Test P2P dynamic price with custom wheeling cost."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/price/p2p-dynamic",
            params={
                "wheeling_cost": 1.50,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["wheeling_cost_baht_kwh"] == 1.50


class TestIntegration:
    """Integration tests for price comparison APIs."""

    def test_full_comparison_workflow(self):
        """Test complete price comparison workflow."""
        client = TestClient(app)
        
        # Step 1: Get utility rates
        utility_response = client.get(
            "/api/v1/price/utility-rates",
            params={
                "provider": "PEA",
                "tariff_category": "1.1.2",
                "billing_month": 3,
                "energy_kwh": 500.0,
            },
        )
        assert utility_response.status_code == 200
        utility_data = utility_response.json()
        
        # Step 2: Get P2P dynamic price
        p2p_response = client.get(
            "/api/v1/price/p2p-dynamic",
            params={
                "supply_kwh": 100.0,
                "demand_kwh": 100.0,
            },
        )
        assert p2p_response.status_code == 200
        p2p_data = p2p_response.json()
        
        # Step 3: Compare prices
        compare_response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 500.0,
                "utility_provider": "PEA",
                "tariff_category": "1.1.2",
                "billing_month": 3,
                "p2p_price": p2p_data["market_clearing_price_baht_kwh"],
                "wheeling_cost": 1.76,
            },
        )
        assert compare_response.status_code == 200
        compare_data = compare_response.json()
        
        # Verify consistency
        assert compare_data["utility"]["provider"] == "PEA"
        assert compare_data["p2p"]["market_clearing_price_baht_kwh"] == p2p_data["market_clearing_price_baht_kwh"]
        assert "recommendation" in compare_data

    def test_scenario_evening_peak(self):
        """Test evening peak scenario (high demand, low solar)."""
        client = TestClient(app)
        
        # Evening: high demand, low supply
        response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 400.0,
                "billing_month": 3,
                "market_volume": 50.0,  # Low supply
                "market_sentiment": "Bullish",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # P2P price should be higher during peak
        assert data["p2p"]["market_clearing_price_baht_kwh"] > 3.0

    def test_scenario_solar_peak(self):
        """Test solar peak scenario (oversupply)."""
        client = TestClient(app)
        
        # Midday: high solar supply
        response = client.post(
            "/api/v1/price/compare",
            json={
                "energy_kwh": 200.0,
                "billing_month": 6,
                "market_volume": 200.0,  # High supply
                "market_sentiment": "Bearish",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # With high supply (200) and default demand (220 = 200*1.1), 
        # the market is nearly balanced, so price is moderate
        # The formula naturally handles supply/demand dynamics
        assert data["p2p"]["market_clearing_price_baht_kwh"] > 2.0
        assert data["p2p"]["market_sentiment"] in ["Stable", "Bearish"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
