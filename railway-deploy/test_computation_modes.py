#!/usr/bin/env python3
"""
Test script to verify both computation modes work correctly
"""

import requests
import json
import time
import sys

def test_computation_modes(base_url="http://localhost:8000"):
    """Test both fast and true computation modes"""
    
    print(f"🧪 Testing computation modes at {base_url}")
    
    # Test symptoms
    test_symptoms = ["Seizure", "Intellectual disability"]
    
    # Test both modes
    modes = [
        {"mode": "fast", "expected_time": 1000, "description": "Fast mode (pre-computed)"},
        {"mode": "true", "expected_time": 30000, "description": "True Bayesian mode (full computation)"}
    ]
    
    results = []
    
    for mode_config in modes:
        mode = mode_config["mode"]
        expected_time = mode_config["expected_time"]
        description = mode_config["description"]
        
        print(f"\n🔍 Testing {description}...")
        
        try:
            start_time = time.time()
            
            request_data = {
                "present_symptoms": test_symptoms,
                "absent_symptoms": [],
                "top_n": 5,
                "computation_mode": mode
            }
            
            print(f"   Request: {json.dumps(request_data, indent=2)}")
            
            response = requests.post(
                f"{base_url}/diagnose",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=60  # 60 second timeout
            )
            
            actual_time = (time.time() - start_time) * 1000  # Convert to ms
            
            print(f"   Status: {response.status_code}")
            print(f"   Actual time: {actual_time:.0f}ms")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ['success', 'results', 'computation_mode', 'processing_time_ms']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ❌ FAIL - Missing fields: {missing_fields}")
                    results.append({"mode": mode, "status": "FAIL", "error": f"Missing fields: {missing_fields}"})
                    continue
                
                # Verify computation mode matches request
                if data['computation_mode'] != mode:
                    print(f"   ❌ FAIL - Wrong computation mode returned: {data['computation_mode']} (expected {mode})")
                    results.append({"mode": mode, "status": "FAIL", "error": f"Wrong mode returned: {data['computation_mode']}"})
                    continue
                
                # Check results
                print(f"   Results: {len(data['results'])} diseases")
                print(f"   Diseases evaluated: {data['total_diseases_evaluated']}")
                print(f"   Server processing time: {data['processing_time_ms']:.0f}ms")
                print(f"   Computation mode: {data['computation_mode']}")
                
                if len(data['results']) > 0:
                    top_result = data['results'][0]
                    print(f"   Top result: {top_result['disorder_name']} ({top_result['probability']:.4f})")
                    print(f"   Matching symptoms: {top_result['matching_symptoms']}")
                
                # Time check (allow some tolerance)
                if mode == "fast" and data['processing_time_ms'] > 5000:
                    print(f"   ⚠️  WARNING - Fast mode took {data['processing_time_ms']:.0f}ms (expected < 5000ms)")
                elif mode == "true" and data['processing_time_ms'] < 1000:
                    print(f"   ⚠️  WARNING - True mode took only {data['processing_time_ms']:.0f}ms (expected > 1000ms)")
                
                print("   ✅ PASS")
                results.append({"mode": mode, "status": "PASS", "time": data['processing_time_ms']})
                
            else:
                error_text = response.text[:200]
                print(f"   ❌ FAIL - {error_text}")
                results.append({"mode": mode, "status": "FAIL", "error": error_text})
                
        except requests.exceptions.Timeout:
            print(f"   ❌ FAIL - Request timeout (>{60}s)")
            results.append({"mode": mode, "status": "FAIL", "error": "Timeout"})
        except requests.exceptions.RequestException as e:
            print(f"   ❌ FAIL - Connection error: {e}")
            results.append({"mode": mode, "status": "FAIL", "error": str(e)})
        except Exception as e:
            print(f"   ❌ FAIL - Unexpected error: {e}")
            results.append({"mode": mode, "status": "FAIL", "error": str(e)})
    
    # Summary
    print(f"\n📊 Test Summary:")
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    for result in results:
        if result['status'] == 'PASS':
            time_info = f" ({result['time']:.0f}ms)" if 'time' in result else ""
            print(f"   ✅ {result['mode'].upper()} mode{time_info}")
        else:
            print(f"   ❌ {result['mode'].upper()} mode: {result.get('error', 'Unknown error')}")
    
    if passed == total:
        print("   🎉 All computation modes working!")
        return True
    else:
        print("   ⚠️  Some modes failed!")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    success = test_computation_modes(base_url)
    sys.exit(0 if success else 1)