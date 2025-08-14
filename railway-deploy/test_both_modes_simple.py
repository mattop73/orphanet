#!/usr/bin/env python3
"""
Simple test to verify both computation modes work
"""

import requests
import json
import sys

def test_mode(base_url, mode, symptoms):
    """Test a specific computation mode"""
    print(f"Testing {mode.upper()} mode...")
    
    try:
        request_data = {
            "present_symptoms": symptoms,
            "absent_symptoms": [],
            "top_n": 10,
            "computation_mode": mode
        }
        
        response = requests.post(
            f"{base_url}/diagnose",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60 if mode == "fast" else 150
        )
        
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get('results', []))
            print(f"   ✅ {mode.upper()} mode: {result_count} results")
            print(f"   Mode: {data.get('computation_mode')}")
            print(f"   Time: {data.get('processing_time_ms', 0):.0f}ms")
            return True
        else:
            print(f"   ❌ {mode.upper()} mode failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ {mode.upper()} mode error: {e}")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("🧪 Quick Mode Test")
    print("=" * 30)
    
    # Simple symptoms for testing
    test_symptoms = ["Fever", "Atonic seizure"]
    
    print(f"Testing with symptoms: {test_symptoms}")
    print()
    
    fast_works = test_mode(base_url, "fast", test_symptoms)
    true_works = test_mode(base_url, "true", test_symptoms)
    
    print()
    print("Results:")
    print(f"FAST mode: {'✅ WORKS' if fast_works else '❌ FAILED'}")
    print(f"TRUE mode: {'✅ WORKS' if true_works else '❌ FAILED'}")
    
    if fast_works and true_works:
        print("\n🎉 Both modes working!")
    else:
        print("\n❌ Some modes failed")
    
    sys.exit(0 if (fast_works and true_works) else 1)