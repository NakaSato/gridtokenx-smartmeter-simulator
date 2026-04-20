import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8082/api/v1"

def test_endpoint(method, path, payload=None, params=None):
    url = f"{BASE_URL}{path}"
    print(f"\n" + "="*80)
    print(f"Testing {method} {path}")
    print(f"URL: {url}")
    if params: print(f"Params: {json.dumps(params, indent=2)}")
    if payload: print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-"*80)
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=payload)
        
        print(f"Response Status: {response.status_code}")
        try:
            data = response.json()
            print("Response Body:")
            print(json.dumps(data, indent=2))
        except:
            print(f"Response Body: {response.text}")
            
        if response.status_code == 200:
            print(f"\n✅ Success")
            return True
        else:
            print(f"\n❌ Failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_all_tests():
    tests = [
        ("GET", "/forecast/24h", None, {"current_load_kw": 15000}),
        ("GET", "/forecast/dual-target", None, {"current_load_kw": 15000}),
        ("GET", "/forecast/constraints", None, {"current_load_kw": 15000}),
        ("GET", "/forecast/demographics", None, None),
        ("POST", "/forecast/scenario", {
            "temp_delta": 2.0,
            "tourist_surge_pct": 10.0,
            "current_load_kw": 15000
        }, None),
        ("POST", "/forecast/train", None, None),
    ]
    
    results = []
    for method, path, payload, params in tests:
        results.append(test_endpoint(method, path, payload, params))
    
    print("\n--- Test Summary ---")
    for i, (method, path, _, _) in enumerate(tests):
        status = "✅" if results[i] else "❌"
        print(f"{status} {method} {path}")

if __name__ == "__main__":
    run_all_tests()
