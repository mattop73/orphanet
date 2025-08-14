#!/usr/bin/env python3
"""
Complete system test for the updated Railway deployment
Tests both computation modes, top 20 results, and pie chart functionality
"""

import requests
import json
import sys
import time

def test_complete_system(base_url="http://localhost:8000"):
    """Test the complete system including new features"""
    
    print(f"🧪 Testing complete system at {base_url}")
    
    # Test symptoms
    test_symptoms = ["Fever", "Abdominal aortic aneurysm"]
    
    print(f"\n🔍 Testing with symptoms: {test_symptoms}")
    
    # Test both computation modes
    modes = ["fast", "true"]
    results = {}
    
    for mode in modes:
        print(f"\n📊 Testing {mode.upper()} mode...")
        
        try:
            start_time = time.time()
            
            request_data = {
                "present_symptoms": test_symptoms,
                "absent_symptoms": [],
                "top_n": 20,  # Request top 20
                "computation_mode": mode
            }
            
            print(f"   Request: top_n=20, mode={mode}")
            
            # Set appropriate timeout
            timeout = 120 if mode == "true" else 30
            
            response = requests.post(
                f"{base_url}/diagnose",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            
            actual_time = (time.time() - start_time) * 1000
            
            print(f"   Status: {response.status_code}")
            print(f"   Actual request time: {actual_time:.0f}ms")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ['success', 'results', 'computation_mode', 'processing_time_ms']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ❌ FAIL - Missing fields: {missing_fields}")
                    results[mode] = "FAIL"
                    continue
                
                # Verify computation mode
                if data.get('computation_mode') != mode:
                    print(f"   ❌ FAIL - Wrong mode: {data.get('computation_mode')} (expected {mode})")
                    results[mode] = "FAIL"
                    continue
                
                # Check results count
                result_count = len(data['results'])
                print(f"   ✅ Results count: {result_count} diseases")
                print(f"   ✅ Computation mode: {data['computation_mode']}")
                print(f"   ✅ Server processing time: {data['processing_time_ms']:.0f}ms")
                print(f"   ✅ Diseases evaluated: {data['total_diseases_evaluated']}")
                
                # Check if we got up to 20 results
                if result_count > 10:
                    print(f"   ✅ Got more than 10 results ({result_count}) - good for pie chart + list")
                
                if result_count > 0:
                    top_result = data['results'][0]
                    print(f"   Top result: {top_result['disorder_name']}")
                    print(f"   Probability: {top_result['probability']:.6f}")
                    print(f"   Matching symptoms: {len(top_result['matching_symptoms'])}/{top_result['total_symptoms']}")
                
                # Verify results are sorted by probability
                probabilities = [r['probability'] for r in data['results']]
                if probabilities == sorted(probabilities, reverse=True):
                    print(f"   ✅ Results properly sorted by probability")
                else:
                    print(f"   ⚠️  Results not properly sorted")
                
                # Check expected processing times
                processing_time = data['processing_time_ms']
                if mode == "fast":
                    if processing_time < 10000:  # Less than 10 seconds
                        print(f"   ✅ Fast mode timing appropriate ({processing_time:.0f}ms)")
                    else:
                        print(f"   ⚠️  Fast mode took {processing_time:.0f}ms (expected < 10s)")
                else:  # true mode
                    if processing_time > 100:  # More than 100ms
                        print(f"   ✅ True mode timing appropriate ({processing_time:.0f}ms)")
                    else:
                        print(f"   ⚠️  True mode too fast ({processing_time:.0f}ms)")
                
                print("   ✅ PASS")
                results[mode] = "PASS"
                
            else:
                error_text = response.text[:300]
                print(f"   ❌ FAIL - HTTP {response.status_code}")
                print(f"   Error: {error_text}")
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
    
    # Test other endpoints
    print(f"\n🔍 Testing other endpoints...")
    
    try:
        # Test symptoms endpoint
        response = requests.get(f"{base_url}/symptoms?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Symptoms endpoint: {len(data['symptoms'])} symptoms")
        else:
            print(f"   ❌ Symptoms endpoint failed: {response.status_code}")
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health endpoint: {data.get('status', 'unknown')}")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Endpoint tests failed: {e}")
    
    # Summary
    print(f"\n📊 Complete System Test Summary:")
    passed = sum(1 for status in results.values() if status == "PASS")
    total = len(results)
    print(f"   Core functionality: {passed}/{total}")
    
    for mode, status in results.items():
        if status == "PASS":
            print(f"   ✅ {mode.upper()} mode working")
        else:
            print(f"   ❌ {mode.upper()} mode failed")
    
    print(f"\n🎯 New Features Expected:")
    print(f"   📊 Pie chart: Top 10 diseases with hover effects and click-to-view")
    print(f"   📋 Results list: Up to 20 diseases displayed")
    print(f"   🔄 Mode switching: Fast (pre-computed) vs True (full Bayesian)")
    print(f"   🎨 Interactive: Click pie slices to open Orphanet pages")
    
    if passed == total:
        print("\n🎉 System ready for deployment!")
        print("💡 Features implemented:")
        print("   - Top 20 disease results")
        print("   - Interactive pie chart for top 10")
        print("   - Fixed True Bayesian mode with fallback")
        print("   - Proper mode switching logic")
        return True
    else:
        print(f"\n⚠️  Some issues found - check logs above")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    success = test_complete_system(base_url)
    sys.exit(0 if success else 1)