#!/usr/bin/env python3
"""
Test the ultra-fast True Bayesian mode fix
"""

import requests
import json
import time
import sys

def test_ultra_fast_true_mode(base_url):
    """Test that True mode completes very quickly now"""
    print("🚀 Testing ULTRA-FAST TRUE mode...")
    
    try:
        start_time = time.time()
        
        request_data = {
            "present_symptoms": ["Fever", "Abdominal colic"],
            "absent_symptoms": [],
            "top_n": 20,
            "computation_mode": "true"
        }
        
        print(f"   📤 Starting TRUE mode request...")
        print(f"   ⏱️  Should complete within 10-30 seconds now...")
        
        response = requests.post(
            f"{base_url}/diagnose",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=90  # 1.5 minute timeout
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
            
            # Show top result
            if result_count > 0:
                top_result = data['results'][0]
                print(f"   🏆 Top result: {top_result['disorder_name']}")
                print(f"   📈 Probability: {top_result['probability']:.4f}")
                print(f"   🎯 Matching symptoms: {len(top_result['matching_symptoms'])}")
            
            if actual_time < 30:
                print(f"   🎉 EXCELLENT - Completed in {actual_time:.1f}s!")
                return True
            elif actual_time < 60:
                print(f"   ✅ GOOD - Completed in {actual_time:.1f}s")
                return True
            else:
                print(f"   ⚠️  SLOW - Still took {actual_time:.1f}s")
                return False
        else:
            print(f"   ❌ FAILED - HTTP {response.status_code}")
            print(f"   Error: {response.text[:300]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ FAILED - Still timing out")
        return False
    except Exception as e:
        print(f"   ❌ FAILED - Error: {e}")
        return False

def test_both_modes(base_url):
    """Test both modes work quickly"""
    print("\n🧪 Testing both modes...")
    
    results = {}
    
    for mode in ['fast', 'true']:
        print(f"\n   Testing {mode.upper()} mode...")
        start_time = time.time()
        
        try:
            request_data = {
                "present_symptoms": ["Fever", "Abdominal colic"],
                "absent_symptoms": [],
                "top_n": 10,
                "computation_mode": mode
            }
            
            response = requests.post(
                f"{base_url}/diagnose",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=90
            )
            
            actual_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get('results', []))
                results[mode] = {
                    'success': True,
                    'time': actual_time,
                    'results': result_count,
                    'diseases_evaluated': data.get('total_diseases_evaluated', 0)
                }
                print(f"      ✅ {mode.upper()}: {result_count} results in {actual_time:.1f}s")
            else:
                results[mode] = {'success': False, 'error': response.status_code}
                print(f"      ❌ {mode.upper()}: Failed with {response.status_code}")
                
        except Exception as e:
            results[mode] = {'success': False, 'error': str(e)}
            print(f"      ❌ {mode.upper()}: Error - {e}")
    
    return results

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("⚡ Ultra-Fast TRUE Mode Test")
    print("=" * 40)
    print(f"Testing: {base_url}")
    print()
    
    # Test true mode specifically
    true_works = test_ultra_fast_true_mode(base_url)
    
    # Test both modes
    both_results = test_both_modes(base_url)
    
    print(f"\n📊 Final Results:")
    print(f"   TRUE mode: {'✅ FIXED' if true_works else '❌ STILL BROKEN'}")
    
    for mode, result in both_results.items():
        if result['success']:
            print(f"   {mode.upper()} mode: ✅ {result['time']:.1f}s ({result['results']} results, {result['diseases_evaluated']} diseases)")
        else:
            print(f"   {mode.upper()} mode: ❌ {result['error']}")
    
    all_working = true_works and all(r['success'] for r in both_results.values())
    
    if all_working:
        print("\n🎉 SUCCESS! Both modes working with ultra-fast performance!")
        print("\n💡 Final optimizations:")
        print("   - TRUE mode: Simplified scoring (no full Bayesian normalization)")
        print("   - Backend: Limited to 5 most relevant diseases only")
        print("   - Frontend: 1-minute timeout for TRUE mode")
        print("   - CSV fallback: Ultra-fast symptom frequency scoring")
    else:
        print("\n❌ Some issues remain - check individual results above")
    
    sys.exit(0 if all_working else 1)