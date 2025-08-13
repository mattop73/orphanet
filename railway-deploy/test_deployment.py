#!/usr/bin/env python3
"""
Test script to verify the Railway deployment works correctly
"""

import requests
import json
import sys
import time

def test_api_endpoints(base_url="http://localhost:8000"):
    """Test all API endpoints"""
    
    print(f"🧪 Testing API endpoints at {base_url}")
    
    tests = [
        {
            "name": "Health Check",
            "endpoint": "/health",
            "method": "GET"
        },
        {
            "name": "API Info",
            "endpoint": "/api",
            "method": "GET"
        },
        {
            "name": "System Info",
            "endpoint": "/info",
            "method": "GET"
        },
        {
            "name": "Symptoms List (sample)",
            "endpoint": "/symptoms?limit=5",
            "method": "GET"
        },
        {
            "name": "Diseases List (sample)",
            "endpoint": "/diseases?limit=5",
            "method": "GET"
        },
        {
            "name": "Main Interface",
            "endpoint": "/",
            "method": "GET"
        },
        {
            "name": "Symptom Selector",
            "endpoint": "/selector",
            "method": "GET"
        }
    ]
    
    results = []
    
    for test in tests:
        try:
            print(f"\n🔍 Testing {test['name']}...")
            
            if test['method'] == 'GET':
                response = requests.get(f"{base_url}{test['endpoint']}", timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                if 'json' in response.headers.get('content-type', '').lower():
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"   Response keys: {list(data.keys())}")
                    elif isinstance(data, list):
                        print(f"   Response length: {len(data)}")
                else:
                    print(f"   Content length: {len(response.content)} bytes")
                print("   ✅ PASS")
                results.append({"test": test['name'], "status": "PASS"})
            else:
                print(f"   ❌ FAIL - {response.text[:100]}")
                results.append({"test": test['name'], "status": "FAIL", "error": response.text[:100]})
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ FAIL - Connection error: {e}")
            results.append({"test": test['name'], "status": "FAIL", "error": str(e)})
        except Exception as e:
            print(f"   ❌ FAIL - Unexpected error: {e}")
            results.append({"test": test['name'], "status": "FAIL", "error": str(e)})
    
    # Test diagnosis endpoint
    try:
        print(f"\n🔍 Testing Diagnosis...")
        diagnosis_data = {
            "present_symptoms": ["Seizure", "Intellectual disability"],
            "absent_symptoms": [],
            "top_n": 5
        }
        
        response = requests.post(
            f"{base_url}/diagnose",
            json=diagnosis_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Results: {len(data.get('results', []))} diseases")
            print(f"   Processing time: {data.get('processing_time_ms', 'N/A')}ms")
            print("   ✅ PASS")
            results.append({"test": "Diagnosis", "status": "PASS"})
        else:
            print(f"   ❌ FAIL - {response.text[:200]}")
            results.append({"test": "Diagnosis", "status": "FAIL", "error": response.text[:200]})
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ FAIL - Connection error: {e}")
        results.append({"test": "Diagnosis", "status": "FAIL", "error": str(e)})
    except Exception as e:
        print(f"   ❌ FAIL - Unexpected error: {e}")
        results.append({"test": "Diagnosis", "status": "FAIL", "error": str(e)})
    
    # Summary
    print(f"\n📊 Test Summary:")
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("   🎉 All tests passed!")
        return True
    else:
        print("   ⚠️  Some tests failed!")
        for result in results:
            if result['status'] == 'FAIL':
                print(f"   - {result['test']}: {result.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    success = test_api_endpoints(base_url)
    sys.exit(0 if success else 1)