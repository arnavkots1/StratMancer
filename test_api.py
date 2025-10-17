"""
Test script for StratMancer API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

headers = {
    "X-STRATMANCER-KEY": API_KEY,
    "Content-Type": "application/json"
}

print("=" * 70)
print("StratMancer API Test Suite")
print("=" * 70)

# Test 1: Health Check
print("\n1. Testing GET /healthz...")
try:
    response = requests.get(f"{BASE_URL}/healthz")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Health check OK")
        print(f"      Version: {data['version']}")
        print(f"      Models loaded: {data['models_loaded']}")
    else:
        print(f"   ❌ Health check failed")
except Exception as e:
    print(f"   ❌ Error: {e}")
    print("   Make sure the API is running: uvicorn backend.api.main:app --reload")
    exit(1)

# Test 2: Model Registry
print("\n2. Testing GET /models/registry...")
try:
    response = requests.get(f"{BASE_URL}/models/registry", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Model registry OK")
        print(f"      Feature map version: {data['feature_map_version']}")
        print(f"      Total champions: {data['total_champions']}")
        print(f"      Models available: {list(data['models'].keys())}")
    else:
        print(f"   ❌ Model registry failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Draft Prediction
print("\n3. Testing POST /predict-draft...")
try:
    payload = {
        "elo": "mid",
        "patch": "15.20",
        "blue": {
            "top": 266,    # Aatrox
            "jgl": 64,     # Lee Sin
            "mid": 103,    # Ahri
            "adc": 51,     # Caitlyn
            "sup": 12,     # Alistar
            "bans": [53, 89, 412]
        },
        "red": {
            "top": 24,     # Jax
            "jgl": 76,     # Nidalee
            "mid": 238,    # Zed
            "adc": 498,    # Xayah
            "sup": 267,    # Nami
            "bans": [421, 75, 268]
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/predict-draft",
        headers=headers,
        json=payload
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Prediction successful")
        print(f"      Blue win prob: {data['blue_win_prob']:.2%}")
        print(f"      Red win prob: {data['red_win_prob']:.2%}")
        print(f"      Confidence: {data['confidence']:.2%}")
        print(f"      Calibrated: {data['calibrated']}")
        print(f"      Model: {data['model_version']}")
        print(f"      Explanations:")
        for exp in data['explanations']:
            print(f"        - {exp}")
    else:
        print(f"   ❌ Prediction failed")
        print(f"      Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Team Optimizer (404 expected)
print("\n4. Testing GET /team-optimizer/player/<fake> (expect 404)...")
try:
    fake_puuid = "fake-player-puuid-12345"
    response = requests.get(
        f"{BASE_URL}/team-optimizer/player/{fake_puuid}",
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 404:
        data = response.json()
        print(f"   ✅ Correct 404 response")
        print(f"      Error: {data['detail']}")
    else:
        print(f"   ⚠ Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Invalid ELO (400 expected)
print("\n5. Testing POST /predict-draft with invalid ELO (expect 400)...")
try:
    invalid_payload = {
        "elo": "invalid",
        "patch": "15.20",
        "blue": {
            "top": 266, "jgl": 64, "mid": 103, "adc": 51, "sup": 12,
            "bans": []
        },
        "red": {
            "top": 24, "jgl": 76, "mid": 238, "adc": 498, "sup": 267,
            "bans": []
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/predict-draft",
        headers=headers,
        json=invalid_payload
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 422:  # Pydantic validation
        print(f"   ✅ Correct validation error")
    else:
        print(f"   ⚠ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Test caching (second identical request should be faster)
print("\n6. Testing cache performance...")
try:
    payload = {
        "elo": "mid",
        "patch": "15.20",
        "blue": {
            "top": 266, "jgl": 64, "mid": 103, "adc": 51, "sup": 12,
            "bans": [53]
        },
        "red": {
            "top": 24, "jgl": 76, "mid": 238, "adc": 498, "sup": 267,
            "bans": [421]
        }
    }
    
    # First request
    start = time.time()
    response1 = requests.post(f"{BASE_URL}/predict-draft", headers=headers, json=payload)
    time1 = (time.time() - start) * 1000
    
    # Second request (should be cached)
    time.sleep(0.1)
    start = time.time()
    response2 = requests.post(f"{BASE_URL}/predict-draft", headers=headers, json=payload)
    time2 = (time.time() - start) * 1000
    
    print(f"   First request: {time1:.1f}ms")
    print(f"   Second request: {time2:.1f}ms")
    
    if time2 < time1 / 2:
        print(f"   ✅ Cache working (2nd request {time1/time2:.1f}x faster)")
    else:
        print(f"   ⚠ Cache may not be working optimally")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("API Test Suite Complete!")
print("=" * 70)
print("\nTo start the API server:")
print("  uvicorn backend.api.main:app --reload")
print("\nTo view API docs:")
print("  http://localhost:8000/docs")
print("=" * 70)

