#!/usr/bin/env python3
"""
Setup Supabase Tables for Railway Deployment
This script will help you create the necessary tables in your Supabase database
"""

import os
import sys
from supabase_fast_diagnosis import supabase_diagnosis, setup_and_populate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_sql_commands():
    """Print the SQL commands you need to run in Supabase SQL Editor"""
    
    sql_commands = """
-- =================================================================
-- SQL Commands to Run in Supabase SQL Editor
-- =================================================================

-- 1. Fast Symptoms Table (for quick symptom lookup)
CREATE TABLE IF NOT EXISTS fast_symptoms (
    id SERIAL PRIMARY KEY,
    symptom_name TEXT UNIQUE NOT NULL,
    symptom_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Fast Diseases Table (for quick disease lookup)  
CREATE TABLE IF NOT EXISTS fast_diseases (
    id SERIAL PRIMARY KEY,
    disease_name TEXT UNIQUE NOT NULL,
    orpha_code TEXT,
    symptom_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Pre-computed Probabilities Table (the core optimization)
CREATE TABLE IF NOT EXISTS fast_probabilities (
    id SERIAL PRIMARY KEY,
    symptom_name TEXT NOT NULL,
    disease_name TEXT NOT NULL,
    orpha_code TEXT,
    probability FLOAT NOT NULL,
    frequency FLOAT NOT NULL,
    confidence_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symptom_name, disease_name)
);

-- 4. Indexes for ultra-fast queries
CREATE INDEX IF NOT EXISTS idx_fast_probabilities_symptom ON fast_probabilities(symptom_name);
CREATE INDEX IF NOT EXISTS idx_fast_probabilities_disease ON fast_probabilities(disease_name);
CREATE INDEX IF NOT EXISTS idx_fast_probabilities_probability ON fast_probabilities(probability DESC);
CREATE INDEX IF NOT EXISTS idx_fast_symptoms_name ON fast_symptoms(symptom_name);
CREATE INDEX IF NOT EXISTS idx_fast_diseases_name ON fast_diseases(disease_name);

-- =================================================================
-- After running the above SQL, come back and run this Python script
-- =================================================================
"""
    
    print("🗄️  SUPABASE TABLE SETUP")
    print("=" * 60)
    print("📋 Please run these SQL commands in your Supabase SQL Editor:")
    print("   1. Go to https://supabase.com/dashboard")
    print("   2. Select your project")
    print("   3. Go to SQL Editor")
    print("   4. Create a new query and paste the following SQL:")
    print()
    print(sql_commands)
    print()
    print("✅ After running the SQL commands, run this script again to populate data")


def check_tables_exist():
    """Check if the required tables exist"""
    try:
        # Try to query each table
        tables_to_check = ['fast_symptoms', 'fast_diseases', 'fast_probabilities']
        
        for table in tables_to_check:
            try:
                result = supabase_diagnosis.supabase.table(table).select('count').limit(1).execute()
                logger.info(f"✅ Table '{table}' exists")
            except Exception as e:
                logger.error(f"❌ Table '{table}' missing or inaccessible: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return False


def populate_tables():
    """Populate the Supabase tables with CSV data"""
    try:
        logger.info("🚀 Starting table population...")
        
        # Check if CSV file exists
        csv_path = "file/clinical_signs_and_symptoms_in_rare_diseases.csv"
        if not os.path.exists(csv_path):
            logger.error(f"❌ CSV file not found: {csv_path}")
            return False
        
        # Populate from CSV
        success = supabase_diagnosis.populate_from_csv(csv_path)
        
        if success:
            logger.info("✅ Tables populated successfully!")
            return True
        else:
            logger.error("❌ Failed to populate tables")
            return False
            
    except Exception as e:
        logger.error(f"Error populating tables: {e}")
        return False


def test_system():
    """Test the Supabase fast diagnosis system"""
    try:
        logger.info("🧪 Testing Supabase system...")
        
        # Test connection
        if not supabase_diagnosis.test_connection():
            logger.error("❌ Connection test failed")
            return False
        
        # Test getting symptoms
        symptoms = supabase_diagnosis.get_symptoms(limit=5)
        logger.info(f"📋 Sample symptoms: {symptoms}")
        
        # Test getting diseases
        diseases = supabase_diagnosis.get_diseases(limit=3)
        logger.info(f"🏥 Sample diseases: {[d['disease_name'] for d in diseases]}")
        
        # Test diagnosis
        if symptoms:
            test_symptoms = symptoms[:2]  # Use first 2 symptoms
            logger.info(f"🔬 Testing diagnosis with: {test_symptoms}")
            
            result = supabase_diagnosis.ultra_fast_diagnosis(test_symptoms, top_n=3)
            logger.info(f"⚡ Diagnosis completed in {result['processing_time_ms']:.1f}ms")
            logger.info(f"🏆 Top result: {result['results'][0]['disorder_name'] if result['results'] else 'None'}")
        
        logger.info("✅ All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Supabase Setup for Railway Deployment")
    print("=" * 50)
    
    # Check connection first
    if not supabase_diagnosis.test_connection():
        print("❌ Cannot connect to Supabase!")
        print("🔧 Please check your SUPABASE_URL and SUPABASE_ANON_KEY in config.env")
        return
    
    print("✅ Supabase connection established!")
    
    # Check if tables exist
    if not check_tables_exist():
        print("\n📋 Tables need to be created first!")
        print_sql_commands()
        print("\n🔄 Run this script again after creating the tables")
        return
    
    print("✅ All required tables exist!")
    
    # Check if tables are already populated
    try:
        symptoms_count = len(supabase_diagnosis.get_symptoms(limit=1))
        if symptoms_count > 0:
            print("📊 Tables appear to be already populated")
            
            response = input("\n❓ Do you want to re-populate the tables? (y/N): ").strip().lower()
            if response != 'y':
                print("⏭️  Skipping population, testing system...")
                if test_system():
                    print("\n🎉 Supabase system is ready for Railway deployment!")
                return
    except:
        pass
    
    # Populate tables
    print("\n📊 Populating tables with CSV data...")
    if populate_tables():
        print("\n🧪 Testing the complete system...")
        if test_system():
            print("\n🎉 SUCCESS! Supabase system is ready for Railway deployment!")
            print("\n📝 Next steps:")
            print("   1. Deploy main_railway.py to Railway")
            print("   2. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
            print("   3. Your API will be ultra-fast with pre-computed probabilities!")
        else:
            print("\n⚠️  Tables populated but testing failed - check logs")
    else:
        print("\n❌ Failed to populate tables - check logs and try again")


if __name__ == "__main__":
    main()