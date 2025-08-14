#!/usr/bin/env python3
"""
Test the new Supabase schema connection with service key
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')
load_dotenv('.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_schema_connection():
    """Test connection to new Supabase schema"""
    
    print("🔧 Testing New Supabase Schema Connection")
    print("=" * 50)
    
    # Check environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    print(f"📊 Environment Check:")
    print(f"   SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"   SUPABASE_SERVICE_KEY: {'✅ Set' if supabase_service_key else '❌ Missing'}")
    
    if not supabase_url or not supabase_service_key:
        print("\n❌ Missing required environment variables")
        return False
    
    # Test Supabase diagnosis connection
    try:
        print(f"\n🔌 Testing SupabaseDiagnosis connection...")
        from supabase_diagnosis import SupabaseDiagnosis
        
        diagnosis = SupabaseDiagnosis()
        
        if diagnosis.test_connection():
            print("   ✅ SupabaseDiagnosis connection successful!")
            
            # Test basic queries
            print(f"\n📋 Testing basic queries...")
            
            # Test symptoms
            try:
                symptoms = diagnosis.get_symptoms(limit=5)
                print(f"   ✅ Symptoms query: {len(symptoms)} results")
                if symptoms:
                    print(f"      First symptom: {symptoms[0]}")
            except Exception as e:
                print(f"   ❌ Symptoms query failed: {e}")
            
            # Test diseases
            try:
                diseases = diagnosis.get_diseases(limit=5)
                print(f"   ✅ Diseases query: {len(diseases)} results")
                if diseases:
                    print(f"      First disease: {diseases[0].get('disease_name', 'N/A')}")
            except Exception as e:
                print(f"   ❌ Diseases query failed: {e}")
            
            # Test fast diagnosis
            try:
                print(f"\n🚀 Testing fast diagnosis...")
                result = diagnosis.fast_diagnosis(["Fever"], [], 5)
                print(f"   ✅ Fast diagnosis: {len(result.get('results', []))} results")
                if result.get('results'):
                    top_result = result['results'][0]
                    print(f"      Top result: {top_result.get('disorder_name', 'N/A')}")
            except Exception as e:
                print(f"   ❌ Fast diagnosis failed: {e}")
            
            return True
        else:
            print("   ❌ SupabaseDiagnosis connection failed")
            return False
            
    except Exception as e:
        print(f"   ❌ SupabaseDiagnosis initialization failed: {e}")
        
        # Try simple version
        try:
            print(f"\n🔌 Testing SimpleSupabaseDiagnosis fallback...")
            from simple_supabase_diagnosis import SimpleSupabaseDiagnosis
            
            simple_diagnosis = SimpleSupabaseDiagnosis()
            
            if simple_diagnosis.test_connection():
                print("   ✅ SimpleSupabaseDiagnosis connection successful!")
                return True
            else:
                print("   ❌ SimpleSupabaseDiagnosis connection failed")
                return False
                
        except Exception as e2:
            print(f"   ❌ SimpleSupabaseDiagnosis also failed: {e2}")
            return False

def test_schema_tables():
    """Test specific schema tables"""
    
    print(f"\n📊 Testing Schema Tables...")
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        client = create_client(supabase_url, supabase_service_key)
        
        # Test each main table
        tables_to_test = [
            'disorders',
            'hpo_terms', 
            'disorder_hpo_associations',
            'fast_diseases',
            'fast_symptoms',
            'fast_probabilities'
        ]
        
        results = {}
        
        for table in tables_to_test:
            try:
                result = client.table(table).select('*').limit(1).execute()
                count_result = client.table(table).select('count').execute()
                
                record_count = len(count_result.data) if count_result.data else 0
                results[table] = {'success': True, 'count': record_count}
                print(f"   ✅ {table}: {record_count} records")
                
            except Exception as e:
                results[table] = {'success': False, 'error': str(e)}
                print(f"   ❌ {table}: {e}")
        
        # Test join query
        try:
            print(f"\n🔗 Testing join query...")
            result = client.table('disorder_hpo_associations')\
                .select('frequency, disorders(name, orpha_code), hpo_terms(term)')\
                .limit(5)\
                .execute()
            
            if result.data:
                print(f"   ✅ Join query successful: {len(result.data)} records")
                sample = result.data[0]
                if sample.get('disorders') and sample.get('hpo_terms'):
                    print(f"      Sample: {sample['disorders']['name']} - {sample['hpo_terms']['term']}")
                else:
                    print(f"      ⚠️ Join structure unexpected: {sample}")
            else:
                print(f"   ⚠️ Join query returned no data")
                
        except Exception as e:
            print(f"   ❌ Join query failed: {e}")
        
        return results
        
    except Exception as e:
        print(f"   ❌ Schema table testing failed: {e}")
        return {}

if __name__ == "__main__":
    
    # Test basic connection
    connection_works = test_schema_connection()
    
    # Test schema tables
    table_results = test_schema_tables()
    
    print(f"\n📊 Final Results:")
    print(f"   Connection: {'✅ SUCCESS' if connection_works else '❌ FAILED'}")
    
    if table_results:
        working_tables = sum(1 for r in table_results.values() if r['success'])
        total_tables = len(table_results)
        print(f"   Schema tables: {working_tables}/{total_tables} working")
        
        if working_tables == total_tables:
            print(f"\n🎉 All systems ready! New schema is fully functional.")
        else:
            print(f"\n⚠️ Some tables need attention:")
            for table, result in table_results.items():
                if not result['success']:
                    print(f"      ❌ {table}: {result['error']}")
    
    success = connection_works and (working_tables == total_tables if table_results else False)
    
    if success:
        print(f"\n💡 Next steps:")
        print(f"   1. Deploy the updated code to Railway")
        print(f"   2. Test both FAST and TRUE modes")
        print(f"   3. Verify symptom loading works")
    
    sys.exit(0 if success else 1)