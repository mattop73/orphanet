#!/usr/bin/env python3
"""
Test the timeout fixes for True Bayesian mode
"""

import requests
import json
import time
import sys

def test_true_mode_timeout_fix(base_url):
    """Test that True mode completes within reasonable time"""
    print("🧪 Testing TRUE mode timeout fix...")
    
    try:
        start_time = time.time()
        
        # Use simple symptoms to test
        request_data = {
            "present_symptoms": ["Fever", "Atonic seizure"],
            "absent_symptoms": [],
            "top_n": 20,
            "computation_mode": "true"
        }
        
        print(f"   📤 Starting TRUE mode request...")
        print(f"   ⏱️  Expecting completion within 60 seconds...")
        
        response = requests.post(
            f"{base_url}/diagnose",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout
        )
        
        actual_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get('results', []))
            diseases_evaluated = data.get('total_diseases_evaluated', 0)
            server_time = data.get('processing_time_ms', 0)
            
            print(f"   ✅ TRUE mode completed!")
            print(f"   ⏱️  Total time: {actual_time:.1f}s")
            print(f"   🖥️  Server processing: {server_time:.0f}ms")
            print(f"   📊 Results: {result_count} diseases")
            print(f"   🔢 Diseases evaluated: {diseases_evaluated}")
            print(f"   🎯 Mode: {data.get('computation_mode')}")
            
            if actual_time < 60:  # Should complete within 1 minute now
                print(f"   🎉 EXCELLENT - Completed in {actual_time:.1f}s (much faster!)")
                return True
            elif actual_time < 120:
                print(f"   ⚠️  ACCEPTABLE - Completed in {actual_time:.1f}s (could be faster)")
                return True
            else:
                print(f"   ❌ SLOW - Took {actual_time:.1f}s (still too long)")
                return False
        else:
            print(f"   ❌ FAILED - HTTP {response.status_code}")
            print(f"   Error: {response.text[:300]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ FAILED - Still timing out after 2 minutes")
        return False
    except Exception as e:
        print(f"   ❌ FAILED - Error: {e}")
        return False

def test_fast_mode_still_works(base_url):
    """Verify fast mode still works"""
    print("\n🚀 Testing FAST mode...")
    
    try:
        start_time = time.time()
        
        request_data = {
            "present_symptoms": ["Fever", "Atonic seizure"],
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
        
        actual_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get('results', []))
            print(f"   ✅ FAST mode: {result_count} results in {actual_time:.1f}s")
            return True
        else:
            print(f"   ❌ FAST mode failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ FAST mode error: {e}")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("🔧 Timeout Fix Verification")
    print("=" * 40)
    print(f"Testing: {base_url}")
    print()
    
    true_works = test_true_mode_timeout_fix(base_url)
    fast_works = test_fast_mode_still_works(base_url)
    
    print(f"\n📊 Results:")
    print(f"   TRUE mode: {'✅ FIXED' if true_works else '❌ STILL BROKEN'}")
    print(f"   FAST mode: {'✅ WORKS' if fast_works else '❌ BROKEN'}")
    
    if true_works and fast_works:
        print("\n🎉 SUCCESS! Both modes working with optimized timeouts!")
        print("\n💡 Optimizations applied:")
        print("   - Frontend timeout: 5 minutes for TRUE mode")
        print("   - Backend computation: Limited to 20-25 relevant diseases")
        print("   - Smart disease filtering: Only diseases with matching symptoms")
        print("   - Fixed JavaScript scope error for timeoutDuration")
    else:
        print("\n❌ Some issues remain")
    
    sys.exit(0 if (true_works and fast_works) else 1)