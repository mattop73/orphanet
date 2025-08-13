#!/usr/bin/env python3
"""
Test script to verify Supabase integration works correctly
"""

import requests
import json
import time
import sys
import os

def test_supabase_integration(base_url="http://localhost:8000"):
    """Test Supabase integration for both computation modes"""
    
    print(f"🧪 Testing Supabase integration at {base_url}")
    
    # Test symptoms endpoint first
    print(f"\n🔍 Testing symptoms endpoint...")
    try:
        response = requests.get(f"{base_url}/symptoms?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Symptoms endpoint working: {len(data['symptoms'])} symptoms")
            print(f"   Method: {data.get('method', 'unknown')}")
            print(f"   Sample symptoms: {data['symptoms'][:3]}")
        else:
            print(f"   ❌ Symptoms endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Symptoms endpoint error: {e}")
        return False
    
    # Test health endpoint
    print(f"\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health: {data.get('status', 'unknown')}")
            print(f"   Data loaded: {data.get('data_loaded', 'unknown')}")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health endpoint error: {e}")
    
    # Test symptoms for diagnosis
    test_symptoms = ["Seizure", "Intellectual disability"]
    
    # Test both computation modes
    modes = ["fast", "true"]
    results = {}
    
    for mode in modes:
        print(f"\n🔍 Testing {mode.upper()} mode with Supabase...")
        
        try:
            start_time = time.time()
            
            request_data = {
                "present_symptoms": test_symptoms,
                "absent_symptoms": [],
                "top_n": 5,
                "computation_mode": mode
            }
            
            # Set longer timeout for true mode
            timeout = 60 if mode == "true" else 30
            
            response = requests.post(
                f"{base_url}/diagnose",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            
            actual_time = (time.time() - start_time) * 1000
            
            print(f"   Status: {response.status_code}")
            print(f"   Actual time: {actual_time:.0f}ms")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['success', 'results', 'computation_mode', 'processing_time_ms']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ❌ FAIL - Missing fields: {missing_fields}")
                    results[mode] = "FAIL"
                    continue
                
                # Verify computation mode
                if data['computation_mode'] != mode:
                    print(f"   ❌ FAIL - Wrong mode returned: {data['computation_mode']} (expected {mode})")
                    results[mode] = "FAIL"
                    continue
                
                print(f"   Results: {len(data['results'])} diseases")
                print(f"   Diseases evaluated: {data['total_diseases_evaluated']}")
                print(f"   Server processing time: {data['processing_time_ms']:.0f}ms")
                print(f"   Computation mode: {data['computation_mode']}")
                
                if len(data['results']) > 0:
                    top_result = data['results'][0]
                    print(f"   Top result: {top_result['disorder_name']}")
                    print(f"   Probability: {top_result['probability']:.6f}")
                    print(f"   Matching symptoms: {top_result['matching_symptoms']}")
                    print(f"   Confidence: {top_result['confidence_score']:.3f}")
                
                print("   ✅ PASS")
                results[mode] = "PASS"
                
            else:
                error_text = response.text[:300]
                print(f"   ❌ FAIL - HTTP {response.status_code}: {error_text}")
                results[mode] = "FAIL"
                
        except requests.exceptions.Timeout:
            print(f"   ❌ FAIL - Request timeout (>{timeout}s)")
            results[mode] = "FAIL"
        except requests.exceptions.RequestException as e:
            print(f"   ❌ FAIL - Connection error: {e}")
            results[mode] = "FAIL"
        except Exception as e:
            print(f"   ❌ FAIL - Unexpected error: {e}")
            results[mode] = "FAIL"
    
    # Summary
    print(f"\n📊 Supabase Integration Test Summary:")
    passed = sum(1 for status in results.values() if status == "PASS")
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    for mode, status in results.items():
        if status == "PASS":
            print(f"   ✅ {mode.upper()} mode with Supabase")
        else:
            print(f"   ❌ {mode.upper()} mode failed")
    
    if passed == total:
        print("   🎉 All Supabase integration tests passed!")
        return True
    else:
        print("   ⚠️  Some Supabase tests failed!")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check SUPABASE_URL and SUPABASE_KEY environment variables")
        print("   2. Verify Supabase tables exist (disorders, hpo_terms, hpo_associations)")
        print("   3. Check Supabase permissions and RLS policies")
        print("   4. Ensure disorder_symptoms_view exists for optimal performance")
        return False

def check_environment():
    """Check if required environment variables are set"""
    print("🔧 Checking environment variables...")
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"   ✅ {var}: {'*' * 20}...{os.getenv(var)[-10:]}")
    
    if missing_vars:
        print(f"   ❌ Missing environment variables: {missing_vars}")
        print("   💡 Make sure to set these in your Railway environment")
        return False
    
    print("   ✅ All required environment variables are set")
    return True

if __name__ == "__main__":
    print("🚀 Supabase Integration Test for Railway Deployment")
    print("=" * 60)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please set required variables.")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    success = test_supabase_integration(base_url)
    sys.exit(0 if success else 1)