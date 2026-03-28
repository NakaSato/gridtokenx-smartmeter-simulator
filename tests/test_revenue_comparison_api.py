"""
Revenue Comparison API Tests

Tests for revenue comparison between single-buyer and P2P blockchain models:
- POST /api/v1/revenue/compare - Compare revenue models
- GET /api/v1/revenue/optimize - Optimize revenue configuration

Run with:
    uv run pytest tests/test_revenue_comparison_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from smart_meter_simulator.app import app


class TestRevenueComparisonEndpoint:
    """Tests for POST /api/v1/revenue/compare endpoint."""

    def test_compare_revenue_basic(self):
        """Test basic revenue comparison."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 30,
                "billing_month": 3,
                "self_consumption_ratio": 0.3,
                "p2p_participation_rate": 0.8,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "timestamp" in data
        assert "simulation_days" in data
        assert "solar_capacity_kwp" in data
        assert "single_buyer" in data
        assert "p2p_blockchain" in data
        assert "comparison" in data
        assert "recommendations" in data
        
        # Verify single-buyer revenue
        assert data["single_buyer"]["export_revenue_baht"] > 0
        assert data["single_buyer"]["self_consumption_savings_baht"] > 0
        assert data["single_buyer"]["total_revenue_baht"] > 0
        assert data["single_buyer"]["model"] == "Single-Buyer (Utility Feed-in Tariff)"
        
        # Verify P2P revenue
        assert data["p2p_blockchain"]["p2p_export_revenue_baht"] > 0
        assert data["p2p_blockchain"]["p2p_wheeling_cost_baht"] > 0
        assert data["p2p_blockchain"]["total_revenue_baht"] > 0
        assert data["p2p_blockchain"]["model"] == "P2P Blockchain (Dynamic Pricing)"
        
        # Verify comparison
        assert "revenue_difference_baht" in data["comparison"]
        assert "revenue_increase_percent" in data["comparison"]
        assert "is_p2p_better" in data["comparison"]

    def test_compare_revenue_large_system(self):
        """Test revenue comparison for large solar system."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 10.0,
                "simulation_days": 30,
                "self_consumption_ratio": 0.4,
                "p2p_participation_rate": 1.0,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Large system should have higher revenue
        assert data["single_buyer"]["total_revenue_baht"] > 2000
        assert data["p2p_blockchain"]["total_revenue_baht"] > 2000

    def test_compare_revenue_with_battery(self):
        """Test revenue comparison with battery storage."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 5.0,
                "battery_capacity_kwh": 10.0,
                "simulation_days": 30,
                "self_consumption_ratio": 0.6,  # Higher with battery
                "p2p_participation_rate": 0.5,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Higher self-consumption should reduce export
        assert data["single_buyer"]["self_consumed_kwh"] > data["single_buyer"]["export_kwh"]

    def test_compare_revenue_low_p2p_participation(self):
        """Test revenue comparison with low P2P participation."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 30,
                "p2p_participation_rate": 0.2,  # Low participation
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Most export should go to utility
        assert data["p2p_blockchain"]["utility_export_kwh"] > data["p2p_blockchain"]["p2p_export_kwh"]

    def test_compare_revenue_high_p2p_participation(self):
        """Test revenue comparison with high P2P participation."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 30,
                "p2p_participation_rate": 1.0,  # 100% P2P
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All export should go to P2P
        assert data["p2p_blockchain"]["utility_export_kwh"] == 0

    def test_compare_revenue_long_simulation(self):
        """Test revenue comparison with longer simulation period."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 365,  # Full year
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Year-long revenue should be substantial
        assert data["single_buyer"]["total_revenue_baht"] > 10000
        assert data["p2p_blockchain"]["total_revenue_baht"] > 10000

    def test_compare_revenue_recommendations_present(self):
        """Test that recommendations are provided."""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 30,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have recommendations
        assert len(data["recommendations"]) > 0
        assert isinstance(data["recommendations"], list)

    def test_compare_revenue_validation(self):
        """Test validation for invalid parameters."""
        client = TestClient(app)
        
        # Invalid simulation days (> 365)
        response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 400,  # Invalid
            },
        )
        
        assert response.status_code == 422


class TestRevenueOptimizeEndpoint:
    """Tests for GET /api/v1/revenue/optimize endpoint."""

    def test_optimize_revenue_basic(self):
        """Test basic revenue optimization."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/revenue/optimize",
            params={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 30,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "optimal_revenue_baht" in data
        assert "optimal_configuration" in data
        assert "solar_capacity_kwp" in data
        assert "simulation_days" in data
        
        # Verify optimal configuration
        config = data["optimal_configuration"]
        assert "p2p_participation_rate" in config
        assert "self_consumption_ratio" in config
        assert "avg_p2p_price_baht_kwh" in config
        
        # Values should be valid
        assert 0 <= config["p2p_participation_rate"] <= 1.0
        assert 0.2 <= config["self_consumption_ratio"] <= 0.6
        assert data["optimal_revenue_baht"] > 0

    def test_optimize_revenue_large_system(self):
        """Test optimization for large system."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/revenue/optimize",
            params={
                "solar_capacity_kwp": 10.0,
                "simulation_days": 30,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Large system should have higher optimal revenue
        assert data["optimal_revenue_baht"] > 2000

    def test_optimize_revenue_different_periods(self):
        """Test optimization for different simulation periods."""
        client = TestClient(app)
        
        # 30 days
        response_30 = client.get(
            "/api/v1/revenue/optimize",
            params={"solar_capacity_kwp": 5.0, "simulation_days": 30},
        )
        
        # 90 days
        response_90 = client.get(
            "/api/v1/revenue/optimize",
            params={"solar_capacity_kwp": 5.0, "simulation_days": 90},
        )
        
        assert response_30.status_code == 200
        assert response_90.status_code == 200
        
        # 90 days should have higher revenue
        assert response_90.json()["optimal_revenue_baht"] > response_30.json()["optimal_revenue_baht"]


class TestRevenueIntegration:
    """Integration tests for revenue comparison APIs."""

    def test_compare_then_optimize(self):
        """Test comparing revenue then optimizing."""
        client = TestClient(app)
        
        # Step 1: Compare with default parameters
        compare_response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 30,
                "p2p_participation_rate": 0.5,
                "self_consumption_ratio": 0.3,
            },
        )
        assert compare_response.status_code == 200
        compare_data = compare_response.json()
        
        # Step 2: Get optimal configuration
        optimize_response = client.get(
            "/api/v1/revenue/optimize",
            params={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 30,
            },
        )
        assert optimize_response.status_code == 200
        optimize_data = optimize_response.json()
        
        # Step 3: Compare with optimal parameters
        optimal_config = optimize_data["optimal_configuration"]
        optimal_response = client.post(
            "/api/v1/revenue/compare",
            json={
                "solar_capacity_kwp": 5.0,
                "simulation_days": 30,
                "p2p_participation_rate": optimal_config["p2p_participation_rate"],
                "self_consumption_ratio": optimal_config["self_consumption_ratio"],
            },
        )
        assert optimal_response.status_code == 200
        optimal_data = optimal_response.json()
        
        # Optimal configuration should give equal or better revenue
        assert optimal_data["p2p_blockchain"]["total_revenue_baht"] >= compare_data["p2p_blockchain"]["total_revenue_baht"]

    def test_revenue_analysis_workflow(self):
        """Test complete revenue analysis workflow."""
        client = TestClient(app)
        
        # Test multiple scenarios
        scenarios = [
            {"solar_capacity_kwp": 3.0, "name": "Small residential"},
            {"solar_capacity_kwp": 5.0, "name": "Medium residential"},
            {"solar_capacity_kwp": 10.0, "name": "Large residential"},
            {"solar_capacity_kwp": 20.0, "name": "Commercial"},
        ]
        
        results = {}
        for scenario in scenarios:
            response = client.post(
                "/api/v1/revenue/compare",
                json={
                    "solar_capacity_kwp": scenario["solar_capacity_kwp"],
                    "simulation_days": 30,
                },
            )
            assert response.status_code == 200
            results[scenario["name"]] = response.json()
        
        # Verify all scenarios have valid results
        for name, data in results.items():
            assert data["single_buyer"]["total_revenue_baht"] > 0
            assert data["p2p_blockchain"]["total_revenue_baht"] > 0
            assert "comparison" in data
            
        # Larger systems should have higher revenue
        assert results["Commercial"]["single_buyer"]["total_revenue_baht"] > results["Small residential"]["single_buyer"]["total_revenue_baht"]

    def test_p2p_benefit_analysis(self):
        """Test P2P benefit analysis across different configurations."""
        client = TestClient(app)
        
        # Test with varying P2P participation rates
        p2p_rates = [0.0, 0.25, 0.5, 0.75, 1.0]
        benefits = []
        
        for rate in p2p_rates:
            response = client.post(
                "/api/v1/revenue/compare",
                json={
                    "solar_capacity_kwp": 5.0,
                    "simulation_days": 30,
                    "p2p_participation_rate": rate,
                },
            )
            assert response.status_code == 200
            data = response.json()
            
            benefits.append({
                "p2p_rate": rate,
                "revenue_increase_percent": data["comparison"]["revenue_increase_percent"],
                "is_p2p_better": data["comparison"]["is_p2p_better"],
            })
        
        # Verify P2P benefits are tracked
        for benefit in benefits:
            assert "revenue_increase_percent" in benefit
            assert "is_p2p_better" in benefit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
