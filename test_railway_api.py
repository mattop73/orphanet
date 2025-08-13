#!/usr/bin/env python3
"""
Test Railway Deployment - Verify the deployed API works correctly
"""

import requests
import json
import time
from typing import Dict, Any


def test_railway_api(base_url: str = "http://localhost:8000") -> None:
    """Test all Railway API endpoints"""
    
    print("🧪 Testing Railway Disease Diagnosis API")
    print("=" * 50)
    print(f"🌐 Base URL: {base_url}")
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health: {health_data['status']}")
            print(f"   🔗 Supabase: {'✅' if health_data['supabase_connected'] else '❌'}")
            print(f"   📊 Symptoms: {health_data['total_symptoms']}")
            print(f"   🏥 Diseases: {health_data['total_diseases']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: Get Symptoms
    print("\n2️⃣ Testing Symptoms Endpoint...")
    try:
        response = requests.get(f"{base_url}/symptoms?limit=5", timeout=10)
        if response.status_code == 200:
            symptoms_data = response.json()
            symptoms = symptoms_data['symptoms']
            print(f"   ✅ Retrieved {len(symptoms)} symptoms")
            print(f"   📋 Examples: {symptoms[:3]}")
            print(f"   🔍 Method: {symptoms_data.get('method', 'unknown')}")
        else:
            print(f"   ❌ Symptoms failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Symptoms error: {e}")
    
    # Test 3: Get Diseases
    print("\n3️⃣ Testing Diseases Endpoint...")
    try:
        response = requests.get(f"{base_url}/diseases?limit=3", timeout=10)
        if response.status_code == 200:
            diseases_data = response.json()
            diseases = diseases_data['diseases']
            print(f"   ✅ Retrieved {len(diseases)} diseases")
            print(f"   🏥 Examples: {diseases[:2]}")
        else:
            print(f"   ❌ Diseases failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Diseases error: {e}")
    
    # Test 4: Ultra-Fast Diagnosis
    print("\n4️⃣ Testing Ultra-Fast Diagnosis...")
    try:
        diagnosis_data = {
            "present_symptoms": ["Seizure", "Intellectual disability"],
            "absent_symptoms": [],
            "top_n": 3
        }
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/diagnose", 
            json=diagnosis_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Diagnosis completed!")
            print(f"   ⏱️  Response time: {duration_ms:.1f}ms")
            print(f"   📊 Diseases evaluated: {result['total_diseases_evaluated']}")
            print(f"   🎯 Top results:")
            
            for i, disease in enumerate(result['results'][:3], 1):
                prob = disease['probability'] * 100
                conf = disease['confidence_score'] * 100
                print(f"      {i}. {disease['disorder_name']} ({prob:.1f}% prob, {conf:.1f}% conf)")
            
            # Performance assessment
            if duration_ms < 500:
                print(f"   🚀 Excellent performance!")
            elif duration_ms < 2000:
                print(f"   ✅ Good performance")
            else:
                print(f"   ⚠️  Could be faster")
                
        else:
            print(f"   ❌ Diagnosis failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Diagnosis error: {e}")
    
    # Test 5: API Info
    print("\n5️⃣ Testing API Info...")
    try:
        response = requests.get(f"{base_url}/info", timeout=10)
        if response.status_code == 200:
            info_data = response.json()
            print(f"   ✅ API: {info_data['api_name']}")
            print(f"   📦 Version: {info_data['version']}")
            print(f"   🔗 Supabase: {'✅' if info_data['supabase_connected'] else '❌'}")
            print(f"   🛠️  Features: {len(info_data['features'])} available")
        else:
            print(f"   ❌ API info failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API info error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Railway API Test Complete!")
    print("\n💡 To test your deployed API, replace the base_url with:")
    print("   https://your-app-name.railway.app")


if __name__ == "__main__":
    import sys
    
    # Allow custom URL for testing deployed version
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    test_railway_api(base_url)