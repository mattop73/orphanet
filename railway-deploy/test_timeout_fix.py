#!/usr/bin/env python3
"""
Test script to verify the timeout fix for True Bayesian mode
"""

import requests
import json
import time
import sys

def test_timeout_fix(base_url="http://localhost:8000"):
    """Test that True Bayesian mode works without timing out"""
    
    print(f"🧪 Testing timeout fix at {base_url}")
    
    # Test with the same symptoms that were causing timeout
    test_symptoms = ["Fever", "Abdominal aortic aneurysm"]
    
    print(f"\n🔍 Testing TRUE mode with symptoms: {test_symptoms}")
    print("⏱️  This should complete within 2 minutes...")
    
    try:
        start_time = time.time()
        
        request_data = {
            "present_symptoms": test_symptoms,
            "absent_symptoms": [],
            "top_n": 20,
            "computation_mode": "true"
        }
        
        print(f"   📤 Sending request with 2-minute timeout...")
        
        response = requests.post(
            f"{base_url}/diagnose",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=150  # 2.5 minute timeout to match frontend
        )
        
        actual_time = (time.time() - start_time) * 1000
        
        print(f"   ⏱️  Total request time: {actual_time:.0f}ms ({actual_time/1000:.1f}s)")
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response
            if data.get('computation_mode') == 'true':
                print(f"   ✅ Correct computation mode: {data['computation_mode']}")
            else:
                print(f"   ❌ Wrong mode: {data.get('computation_mode')}")
                return False
            
            result_count = len(data.get('results', []))
            print(f"   ✅ Results: {result_count} diseases found")
            print(f"   ✅ Server processing time: {data.get('processing_time_ms', 0):.0f}ms")
            print(f"   ✅ Diseases evaluated: {data.get('total_diseases_evaluated', 0)}")
            
            if result_count > 0:
                top_result = data['results'][0]
                print(f"   🏆 Top result: {top_result['disorder_name']}")
                print(f"   📈 Probability: {top_result['probability']:.6f}")
            
            # Check if it completed in reasonable time
            if actual_time < 120000:  # Less than 2 minutes
                print(f"   ✅ Completed within timeout limit")
                return True
            else:
                print(f"   ⚠️  Took longer than expected but didn't timeout")
                return True
                
        else:
            error_text = response.text[:500]
            print(f"   ❌ FAIL - HTTP {response.status_code}")
            print(f"   Error: {error_text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ FAIL - Still timing out after 2.5 minutes")
        print("   💡 The backend computation is taking too long")
        return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ FAIL - Connection error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ FAIL - Unexpected error: {e}")
        return False

def test_fast_mode_still_works(base_url):
    """Verify fast mode still works quickly"""
    print(f"\n🚀 Testing FAST mode for comparison...")
    
    try:
        start_time = time.time()
        
        request_data = {
            "present_symptoms": ["Fever", "Abdominal aortic aneurysm"],
            "absent_symptoms": [],
            "top_n": 20,
            "computation_mode": "fast"
        }
        
        response = requests.post(
            f"{base_url}/diagnose",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        actual_time = (time.time() - start_time) * 1000
        
        print(f"   ⏱️  Fast mode time: {actual_time:.0f}ms")
        
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get('results', []))
            print(f"   ✅ Fast mode: {result_count} results in {actual_time:.0f}ms")
            return True
        else:
            print(f"   ❌ Fast mode failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Fast mode error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print("🔧 Timeout Fix Test")
    print("=" * 50)
    
    # Test both modes
    true_works = test_timeout_fix(base_url)
    fast_works = test_fast_mode_still_works(base_url)
    
    print(f"\n📊 Results:")
    print(f"   True Bayesian mode: {'✅ WORKS' if true_works else '❌ FAILED'}")
    print(f"   Fast mode: {'✅ WORKS' if fast_works else '❌ FAILED'}")
    
    if true_works and fast_works:
        print("\n🎉 Both modes working! Timeout issue fixed.")
        print("\n💡 Improvements made:")
        print("   - Increased timeout to 2 minutes for True mode")
        print("   - Optimized computation to focus on relevant diseases")
        print("   - Better error messages with mode-specific timeouts")
        print("   - Loading indicators show expected processing time")
    else:
        print("\n⚠️  Some issues remain - check the logs above")
    
    sys.exit(0 if (true_works and fast_works) else 1)