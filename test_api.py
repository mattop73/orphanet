#!/usr/bin/env python3
"""
Quick API test script
"""

import requests
import json

def test_api():
    """Test the API endpoints"""
    print("🧪 Testing Bayesian Disease Diagnosis API")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Test health
    try:
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Data loaded: {data.get('data_loaded', 'unknown')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Connection failed: {e}")
        print("   Make sure to run: python3 start_selector.py")
        return
    
    # Test symptoms endpoint
    try:
        print("\n2. Testing symptoms endpoint...")
        response = requests.get(f"{base_url}/symptoms?limit=5", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            symptoms = data.get('symptoms', [])
            print(f"   Total available: {data.get('total_available', 0)}")
            print(f"   First 3 symptoms: {symptoms[:3]}")
        else:
            print(f"   Error: {response.text}")
            print(f"   Headers: {response.headers}")
            
    except Exception as e:
        print(f"   Request failed: {e}")
    
    # Test diagnosis endpoint
    try:
        print("\n3. Testing diagnosis endpoint...")
        test_data = {
            "present_symptoms": ["Seizure"],
            "top_n": 3
        }
        
        response = requests.post(
            f"{base_url}/diagnose",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Results found: {len(data.get('results', []))}")
            if data.get('results'):
                first_result = data['results'][0]
                print(f"   Top result: {first_result['disorder_name']}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Request failed: {e}")
    
    print("\n✅ API test completed!")
    print(f"🌐 Web interface: {base_url}/selector")

if __name__ == "__main__":
    test_api()