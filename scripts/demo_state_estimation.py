#!/usr/bin/env python3
"""
State Estimation - Demonstration Script

Shows how to use StateEstimator for power system state estimation and validation.
Run with: python scripts/demo_state_estimation.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smart_meter_simulator.adapters import (
    PandapowerAdapter,
    TopologyBuilder,
    StateEstimator,
    MeasurementValidator,
    EstimationAlgorithm
)
from smart_meter_simulator.core.meter import SmartMeter
from smart_meter_simulator.models.reading import EnergyReading
from smart_meter_simulator.config import MeterType

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False
    print("❌ pandapower not installed. Install with: pip install pandapower>=2.14.0")
    sys.exit(1)


def create_test_scenario():
    """
    Create a test network with meters and measurements.
    
    Returns:
        Tuple of (network, adapter)
    """
    print("Setting up test scenario...")
    
    # Create adapter with topology builder
    adapter = PandapowerAdapter(sigma_factor=3)
    
    # Build simple radial network
    net = adapter.topology_builder.build_radial_network(
        num_buses=5,
        voltage_kv=0.4,
        line_length_km=0.1,
        add_grid=True
    )
    
    # Create test meters
    test_meters = [
        {
            "meter_id": "METER_001",
            "bus": 1,
            "type": MeterType.GRID_CONSUMER,
            "energy_consumed": 2.0,
            "energy_generated": 0.0,
            "voltage": 230.0,
        },
        {
            "meter_id": "METER_002",
            "bus": 2,
            "type": MeterType.SOLAR_PROSUMER,
            "energy_consumed": 0.5,
            "energy_generated": 3.5,
            "voltage": 235.0,
        },
        {
            "meter_id": "METER_003",
            "bus": 3,
            "type": MeterType.GRID_CONSUMER,
            "energy_consumed": 5.0,
            "energy_generated": 0.0,
            "voltage": 228.0,
        },
        {
            "meter_id": "METER_004",
            "bus": 4,
            "type": MeterType.HYBRID_PROSUMER,
            "energy_consumed": 1.0,
            "energy_generated": 2.0,
            "voltage": 232.0,
        },
    ]
    
    timestamp = datetime.now(timezone.utc)
    
    # Add meters to network
    for meter_config in test_meters:
        # Create meter
        meter = SmartMeter(config={
            "meter_id": meter_config["meter_id"],
            "meter_type": meter_config["type"],
            "has_solar": meter_config["energy_generated"] > 0,
            "has_battery": meter_config["type"] == MeterType.HYBRID_PROSUMER,
        })
        
        # Create reading
        net_energy = meter_config["energy_generated"] - meter_config["energy_consumed"]
        reading = EnergyReading(
            meter_id=meter_config["meter_id"],
            timestamp=timestamp,
            energy_consumed=meter_config["energy_consumed"],
            energy_generated=meter_config["energy_generated"],
            surplus_energy=max(0, net_energy),
            deficit_energy=max(0, -net_energy),
            voltage=meter_config["voltage"],
            current=10.0,
            power_factor=0.95,
            frequency=50.0,
            temperature=20.0,
            location="Test Location",
            meter_type=meter_config["type"].value,
            user_type="Test User",
            battery_level=0.0,
            weather_condition="Sunny"
        )
        
        # Add to network
        adapter.add_meter_to_network(net, meter, reading, meter_config["bus"])
    
    # Transfer measurements from builder to network
    measurement_df = adapter.get_measurement_table()
    net.measurement = measurement_df
    
    # Run power flow to initialize network state
    try:
        pp.runpp(net, algorithm='nr', calculate_voltage_angles=True)
        print(f"✓ Power flow converged")
    except Exception as e:
        print(f"⚠️  Power flow did not converge: {e}")
    
    print(f"✓ Created network with {len(net.bus)} buses, {len(net.load)} loads, {len(net.sgen)} generators")
    print(f"✓ Added {len(net.measurement)} measurements")
    
    return net, adapter


def demo_basic_estimation():
    """Demonstrate basic state estimation."""
    print("\n" + "="*60)
    print("Demo 1: Basic State Estimation")
    print("="*60)
    
    net, adapter = create_test_scenario()
    
    # Create state estimator
    estimator = StateEstimator(
        algorithm=EstimationAlgorithm.WLS,
        tolerance=1e-6,
        max_iterations=10
    )
    
    print("\nRunning state estimation...")
    results = estimator.run_estimation(net, init="flat")
    
    print(f"\nEstimation Results:")
    print(f"  Converged: {'✅ Yes' if results.converged else '❌ No'}")
    print(f"  Iterations: {results.iterations}")
    print(f"  Mean Absolute Error: {results.mean_absolute_error:.6f}" if results.mean_absolute_error else "  MAE: N/A")
    print(f"  Max Residual: {results.max_residual:.6f}" if results.max_residual else "  Max Residual: N/A")
    
    # Display estimated voltages
    print("\nEstimated Bus Voltages:")
    print(results.estimated_voltages.to_string())
    
    # Display residuals
    if len(results.residuals) > 0:
        print("\nMeasurement Residuals (top 5):")
        print(results.residuals.head().to_string(index=False))
    
    return estimator, net


def demo_ansi_validation():
    """Demonstrate ANSI C12.20 accuracy validation."""
    print("\n" + "="*60)
    print("Demo 2: ANSI C12.20 Accuracy Validation")
    print("="*60)
    
    net, adapter = create_test_scenario()
    
    # Run state estimation first
    estimator = StateEstimator()
    results = estimator.run_estimation(net)
    
    if not results.converged:
        print("❌ State estimation did not converge")
        return
    
    print("\nValidating against ANSI C12.20 standard (±2%)...")
    
    # Validate accuracy
    metrics = estimator.validate_ansi_c12_20(
        net,
        tolerance_percent=2.0  # ±2% for residential meters
    )
    
    print(f"\nAccuracy Metrics ({len(metrics)} measurements):")
    print(f"{'Measurement':<20} {'Error %':<12} {'Within Tol':<12} {'Status'}")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for metric in metrics[:10]:  # Show first 10
        status = "✅ PASS" if metric.within_tolerance else "❌ FAIL"
        if metric.within_tolerance:
            passed += 1
        else:
            failed += 1
        
        print(f"{metric.measurement_name:<20} {metric.error_percent:>10.4f}% "
              f"{'✅ Yes' if metric.within_tolerance else '❌ No':>10}  {status}")
    
    if len(metrics) > 10:
        print(f"... ({len(metrics) - 10} more measurements)")
    
    print(f"\nSummary:")
    print(f"  Total Measurements: {len(metrics)}")
    print(f"  Passed (±2%): {passed} ({passed/len(metrics)*100:.1f}%)")
    print(f"  Failed: {failed} ({failed/len(metrics)*100:.1f}%)")
    
    return metrics


def demo_measurement_validation():
    """Demonstrate measurement validation and outlier detection."""
    print("\n" + "="*60)
    print("Demo 3: Measurement Validation & Outlier Detection")
    print("="*60)
    
    net, adapter = create_test_scenario()
    
    # Create validator
    validator = MeasurementValidator()
    
    # Validate range
    print("\nRange Validation:")
    range_results = validator.validate_range(net.measurement)
    
    valid_count = sum(1 for r in range_results.values() if r.value == "valid")
    outlier_count = sum(1 for r in range_results.values() if r.value == "outlier")
    
    print(f"  Valid measurements: {valid_count}")
    print(f"  Outliers detected: {outlier_count}")
    
    if outlier_count > 0:
        print("\n  Outliers:")
        for name, result in range_results.items():
            if result.value == "outlier":
                meas = net.measurement[net.measurement['name'] == name].iloc[0]
                print(f"    - {name}: {meas['value']} {meas['meas_type']}")
    
    # Z-score outlier detection
    print("\nStatistical Outlier Detection (Z-score):")
    zscore_results = validator.detect_outliers_zscore(net.measurement, threshold=3.0)
    
    outliers = [name for name, result in zscore_results.items() if result.value == "outlier"]
    print(f"  Outliers detected: {len(outliers)}")
    
    if outliers:
        print("  Outlier measurements:")
        for name in outliers:
            print(f"    - {name}")
    
    # Consistency checks
    print("\nConsistency Checks:")
    consistency = validator.validate_consistency(net)
    
    for check, result in consistency.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check.replace('_', ' ').title()}: {result}")
    
    return validator


def demo_bad_data_detection():
    """Demonstrate bad data detection and removal."""
    print("\n" + "="*60)
    print("Demo 4: Bad Data Detection & Removal")
    print("="*60)
    
    net, adapter = create_test_scenario()
    
    # Add some bad data (intentionally corrupted measurement)
    print("\nAdding corrupted measurement...")
    bad_meas_idx = 5
    if bad_meas_idx < len(net.measurement):
        original_value = net.measurement.loc[bad_meas_idx, 'value']
        net.measurement.loc[bad_meas_idx, 'value'] = original_value * 10  # 10x corruption
        print(f"  Corrupted {net.measurement.loc[bad_meas_idx, 'name']}: "
              f"{original_value} → {net.measurement.loc[bad_meas_idx, 'value']}")
    
    # Create estimator
    estimator = StateEstimator()
    
    # Run estimation with bad data
    print("\nRunning estimation with bad data...")
    results_bad = estimator.run_estimation(net)
    
    print(f"  Converged: {'✅ Yes' if results_bad.converged else '❌ No'}")
    print(f"  MAE with bad data: {results_bad.mean_absolute_error:.6f}" if results_bad.mean_absolute_error else "  MAE: N/A")
    
    # Detect bad data
    print("\nDetecting bad data...")
    bad_data = estimator.detect_bad_data(net, chi2_prob_false=0.05)
    
    print(f"  Bad measurements detected: {len(bad_data)}")
    if bad_data:
        for name in bad_data:
            print(f"    - {name}")
    
    # Remove bad data
    if bad_data:
        print("\nRemoving bad data and re-estimating...")
        net_clean, removed = estimator.remove_bad_data(net, chi2_prob_false=0.05)
        
        print(f"  Removed {len(removed)} measurements")
        
        # Re-run estimation
        results_clean = estimator.run_estimation(net_clean)
        
        print(f"  Converged: {'✅ Yes' if results_clean.converged else '❌ No'}")
        print(f"  MAE after cleaning: {results_clean.mean_absolute_error:.6f}" if results_clean.mean_absolute_error else "  MAE: N/A")
        
        if results_bad.mean_absolute_error and results_clean.mean_absolute_error:
            improvement = (1 - results_clean.mean_absolute_error / results_bad.mean_absolute_error) * 100
            print(f"  Improvement: {improvement:.1f}%")


def main():
    """Run all state estimation demonstrations."""
    print("="*60)
    print("State Estimation - Demonstration")
    print("="*60)
    print("\nThis script demonstrates state estimation, validation,")
    print("and ANSI C12.20 accuracy checking.")
    
    demos = [
        ("Basic State Estimation", demo_basic_estimation),
        ("ANSI C12.20 Validation", demo_ansi_validation),
        ("Measurement Validation", demo_measurement_validation),
        ("Bad Data Detection", demo_bad_data_detection),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ All demonstrations complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Add state estimation to production pipeline")
    print("  2. Implement real-time bad data detection")
    print("  3. Create ANSI C12.20 compliance reports")


if __name__ == "__main__":
    main()
