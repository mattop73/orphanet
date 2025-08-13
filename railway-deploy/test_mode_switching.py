#!/usr/bin/env python3
"""
Test script to verify mode switching works correctly
"""

import requests
import json
import sys

def test_mode_switching(base_url="http://localhost:8000"):
    """Test both computation modes to verify they work correctly"""
    
    print(f"🧪 Testing mode switching at {base_url}")
    
    # Test symptoms
    test_symptoms = ["Fever", "Abdominal aortic aneurysm"]
    
    # Test both modes
    modes = [
        {"mode": "fast", "description": "FAST mode (should use pre-computed/optimized)"},
        {"mode": "true", "description": "TRUE mode (should use full Bayesian computation)"}
    ]
    
    results = {}
    
    for mode_config in modes:
        mode = mode_config["mode"]
        description = mode_config["description"]
        
        print(f"\n🔍 Testing {description}...")
        
        try:
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
                timeout=60
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify computation mode matches request
                if data.get('computation_mode') != mode:
                    print(f"   ❌ FAIL - Wrong mode returned: {data.get('computation_mode')} (expected {mode})")
                    results[mode] = "FAIL"
                    continue
                
                print(f"   ✅ Computation mode: {data['computation_mode']}")
                print(f"   Results: {len(data['results'])} diseases")
                print(f"   Processing time: {data['processing_time_ms']:.0f}ms")
                print(f"   Diseases evaluated: {data['total_diseases_evaluated']}")
                
                if len(data['results']) > 0:
                    top_result = data['results'][0]
                    print(f"   Top result: {top_result['disorder_name']}")
                    print(f"   Probability: {top_result['probability']:.6f}")
                
                # Check expected processing time ranges
                processing_time = data['processing_time_ms']
                if mode == "fast" and processing_time > 2000:
                    print(f"   ⚠️  WARNING - Fast mode took {processing_time:.0f}ms (expected < 2000ms)")
                elif mode == "true" and processing_time < 500:
                    print(f"   ⚠️  WARNING - True mode took only {processing_time:.0f}ms (expected > 500ms)")
                
                print("   ✅ PASS")
                results[mode] = "PASS"
                
            else:
                error_text = response.text[:300]
                print(f"   ❌ FAIL - HTTP {response.status_code}: {error_text}")
                results[mode] = "FAIL"
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ FAIL - Connection error: {e}")
            results[mode] = "FAIL"
        except Exception as e:
            print(f"   ❌ FAIL - Unexpected error: {e}")
            results[mode] = "FAIL"
    
    # Summary
    print(f"\n📊 Mode Switching Test Summary:")
    passed = sum(1 for status in results.values() if status == "PASS")
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    for mode, status in results.items():
        if status == "PASS":
            print(f"   ✅ {mode.upper()} mode working correctly")
        else:
            print(f"   ❌ {mode.upper()} mode failed")
    
    if passed == total:
        print("   🎉 All modes working correctly!")
        print("\n💡 Expected behavior:")
        print("   - FAST mode: Quick results using pre-computed probabilities")
        print("   - TRUE mode: Slower but more accurate full Bayesian computation")
        return True
    else:
        print("   ⚠️  Some modes failed!")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    success = test_mode_switching(base_url)
    sys.exit(0 if success else 1)