#!/usr/bin/env python3
"""
Validation script to check AI implementation without running the full app
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def validate_imports():
    """Validate that all AI modules can be imported"""
    print("Validating AI Implementation...")
    print("=" * 60)
    
    try:
        print("✓ Importing AIForecastingEngine...", end=" ")
        from smart_meter_simulator.ai.forecasting_engine import AIForecastingEngine
        print("OK")
        
        print("✓ Importing FeaturePipeline...", end=" ")
        from smart_meter_simulator.ai.feature_engineering import FeaturePipeline
        print("OK")
        
        print("✓ Importing AIService...", end=" ")
        from smart_meter_simulator.services.ai_service import AIService
        print("OK")
        
        print("✓ Importing EdgeForecastingEngine...", end=" ")
        from smart_meter_simulator.core.forecaster import EdgeForecastingEngine
        print("OK")
        
        print("✓ Importing EarlyWarningSystem...", end=" ")
        from smart_meter_simulator.core.ews import EarlyWarningSystem
        print("OK")
        
        print("\n" + "=" * 60)
        print("✓ ALL IMPORTS SUCCESSFUL")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ IMPORT FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_structure():
    """Validate file structure"""
    print("\nValidating File Structure...")
    print("=" * 60)
    
    base_path = Path(__file__).parent.parent
    
    files_to_check = [
        "src/smart_meter_simulator/ai/forecasting_engine.py",
        "src/smart_meter_simulator/ai/feature_engineering.py",
        "src/smart_meter_simulator/services/ai_service.py",
        "src/smart_meter_simulator/routers/forecast_v1.py",
        "src/smart_meter_simulator/core/forecaster.py",
        "src/smart_meter_simulator/core/ews.py",
        "src/smart_meter_simulator/app.py",
        "scripts/test_ai_implementation.py",
        "../docs/API_AI_FORECASTING.md",
        "../docs/AI_QUICKSTART.md",
        "../docs/AI_IMPLEMENTATION_SUMMARY.md",
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = base_path / file_path
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False
    
    print("=" * 60)
    if all_exist:
        print("✓ ALL FILES PRESENT")
    else:
        print("✗ SOME FILES MISSING")
    print("=" * 60)
    
    return all_exist

def check_api_endpoints():
    """Check that API endpoints are properly defined"""
    print("\nChecking API Endpoints...")
    print("=" * 60)
    
    try:
        # Read the forecast_v1.py file
        forecast_file = Path(__file__).parent.parent / "src/smart_meter_simulator/routers/forecast_v1.py"
        content = forecast_file.read_text()
        
        endpoints = [
            ("GET /forecast/dual-target", "@forecast_router.get(\"/dual-target\")"),
            ("GET /forecast/constraints", "@forecast_router.get(\"/constraints\")"),
            ("GET /forecast/demographics", "@forecast_router.get(\"/demographics\")"),
            ("GET /forecast/24h", "@forecast_router.get(\"/24h\")"),
            ("GET /forecast/mape", "@forecast_router.get(\"/mape\")"),
            ("POST /forecast/train", "@forecast_router.post(\"/train\")"),
            ("GET /optimize/schedule", "@optimize_router.get(\"/schedule\")"),
            ("GET /optimize/savings", "@optimize_router.get(\"/savings\")"),
            ("GET /ews/status", "@ews_router.get(\"/status\")"),
            ("POST /ews/simulate", "@ews_router.post(\"/simulate\")"),
            ("POST /ews/reset", "@ews_router.post(\"/reset\")"),
        ]
        
        all_found = True
        for endpoint_name, decorator in endpoints:
            found = decorator in content
            status = "✓" if found else "✗"
            print(f"{status} {endpoint_name}")
            if not found:
                all_found = False
        
        print("=" * 60)
        if all_found:
            print("✓ ALL ENDPOINTS DEFINED")
        else:
            print("✗ SOME ENDPOINTS MISSING")
        print("=" * 60)
        
        return all_found
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("AI IMPLEMENTATION VALIDATION")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run validations
    results.append(("File Structure", validate_structure()))
    results.append(("Module Imports", validate_imports()))
    results.append(("API Endpoints", check_api_endpoints()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ ALL VALIDATIONS PASSED")
        print("\nNext steps:")
        print("1. Start infrastructure: docker compose up -d")
        print("2. Start simulator: uv run uvicorn smart_meter_simulator.app:app --port 8082")
        print("3. Test API: curl http://localhost:8082/api/v1/forecast/dual-target")
        print("4. View docs: http://localhost:8082/docs")
        return 0
    else:
        print("\n✗ SOME VALIDATIONS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
