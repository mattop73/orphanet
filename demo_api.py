#!/usr/bin/env python3
"""
Demo script showing how to use the Bayesian Disease Diagnosis API
"""

import requests
import json
import time

# API configuration
API_BASE = "http://localhost:8000"

def test_api():
    """Test the API with sample data"""
    print("🧬 Bayesian Disease Diagnosis API Demo")
    print("=" * 50)
    
    # Test health check
    print("1. Testing API health...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print("❌ API health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure it's running on localhost:8000")
        print("   Run: python3 start_interface.py")
        return
    
    # Get system info
    print("\n2. Getting system information...")
    response = requests.get(f"{API_BASE}/info")
    if response.status_code == 200:
        info = response.json()
        print(f"   📊 Total diseases: {info['total_diseases']}")
        print(f"   🔬 Total symptoms: {info['total_symptoms']}")
        print(f"   🔗 Total associations: {info['total_associations']}")
    
    # Search for symptoms
    print("\n3. Searching for symptoms...")
    response = requests.get(f"{API_BASE}/symptoms?search=seizure&limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {len(data['symptoms'])} symptoms containing 'seizure':")
        for symptom in data['symptoms'][:3]:
            print(f"   • {symptom}")
    
    # Perform diagnosis
    print("\n4. Performing sample diagnosis...")
    diagnosis_request = {
        "present_symptoms": [
            "Seizure",
            "Intellectual disability",
            "Macrocephaly"
        ],
        "absent_symptoms": [
            "Fever"
        ],
        "top_n": 5
    }
    
    print(f"   Present symptoms: {', '.join(diagnosis_request['present_symptoms'])}")
    print(f"   Absent symptoms: {', '.join(diagnosis_request['absent_symptoms'])}")
    
    start_time = time.time()
    response = requests.post(
        f"{API_BASE}/diagnose",
        json=diagnosis_request,
        headers={"Content-Type": "application/json"}
    )
    end_time = time.time()
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n   ✅ Diagnosis completed in {(end_time - start_time) * 1000:.1f}ms")
        print(f"   🔍 Evaluated {result['total_diseases_evaluated']} diseases")
        print(f"   🎯 Found {len(result['results'])} potential matches")
        
        print("\n   🏆 Top 3 Results:")
        for i, disease in enumerate(result['results'][:3], 1):
            print(f"   {i}. {disease['disorder_name']}")
            print(f"      • Orpha Code: {disease['orpha_code']}")
            print(f"      • Probability: {disease['probability']:.4f} ({disease['probability']*100:.2f}%)")
            print(f"      • Confidence: {disease['confidence_score']:.2f}")
            print(f"      • Matching symptoms: {len(disease['matching_symptoms'])}/{disease['total_symptoms']}")
            print(f"      • Matches: {', '.join(disease['matching_symptoms'][:3])}")
            if len(disease['matching_symptoms']) > 3:
                print(f"        + {len(disease['matching_symptoms']) - 3} more...")
            print()
    else:
        print(f"   ❌ Diagnosis failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print("=" * 50)
    print("🌐 Open the web interface at: http://localhost:8000")
    print("📖 API documentation at: http://localhost:8000/docs")
    print("\n💡 To start the web interface:")
    print("   python3 start_interface.py")

if __name__ == "__main__":
    test_api()