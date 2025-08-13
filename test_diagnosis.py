#!/usr/bin/env python3
"""
Test the optimized diagnosis function
"""

import requests
import json
import time

def test_diagnosis():
    """Test diagnosis with different symptom combinations"""
    print("🧪 Testing Optimized Diagnosis Performance")
    print("=" * 50)
    
    api_base = "http://localhost:8000"
    
    # Test cases with different complexity
    test_cases = [
        {
            "name": "Simple case (1 symptom)",
            "symptoms": ["Seizure"],
            "expected_time": "< 5 seconds"
        },
        {
            "name": "Common case (2 symptoms)", 
            "symptoms": ["Seizure", "Intellectual disability"],
            "expected_time": "< 10 seconds"
        },
        {
            "name": "Complex case (3 symptoms)",
            "symptoms": ["Seizure", "Intellectual disability", "Macrocephaly"],
            "expected_time": "< 15 seconds"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Symptoms: {', '.join(test_case['symptoms'])}")
        print(f"   Expected: {test_case['expected_time']}")
        
        try:
            # Prepare request
            request_data = {
                "present_symptoms": test_case["symptoms"],
                "absent_symptoms": [],
                "top_n": 5
            }
            
            # Time the request
            start_time = time.time()
            
            response = requests.post(
                f"{api_base}/diagnose",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"   ⏱️  Time taken: {duration:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: Found {len(data['results'])} results")
                print(f"   📊 Evaluated {data['total_diseases_evaluated']} diseases")
                
                if data['results']:
                    top_result = data['results'][0]
                    print(f"   🏆 Top result: {top_result['disorder_name']} ({top_result['probability']*100:.2f}%)")
                
                # Performance evaluation
                if duration < 5:
                    print("   🚀 Excellent performance!")
                elif duration < 15:
                    print("   ✅ Good performance")
                else:
                    print("   ⚠️  Slow performance - may need further optimization")
                    
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("   ❌ Timeout: Request took longer than 30 seconds")
        except requests.exceptions.ConnectionError:
            print("   ❌ Connection Error: Make sure API server is running")
            print("   Run: python3 start_interface.py")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("💡 Optimizations implemented:")
    print("   • Pre-filter diseases with matching symptoms")
    print("   • Efficient symptom frequency mapping")
    print("   • Improved Bayesian calculation")
    print("   • Better error handling and logging")
    print("   • 30-second timeout in frontend")

if __name__ == "__main__":
    test_diagnosis()