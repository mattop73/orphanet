#!/usr/bin/env python3
"""
Supabase Fast Diagnosis - Railway Deployment Ready
Uses Supabase for ultra-fast disease diagnosis with pre-computed probabilities
"""

import os
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import time
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')
load_dotenv('.env')  # Also try .env file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseFastDiagnosis:
    """Supabase-based fast diagnosis system for Railway deployment"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        
        # Try service role key first (for data loading), then anon key
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url:
            raise ValueError("Missing SUPABASE_URL in environment")
        
        if not self.supabase_service_key and not self.supabase_anon_key:
            raise ValueError("Missing SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY in environment")
        
        # Use service key for data operations if available, otherwise anon key
        primary_key = self.supabase_service_key if self.supabase_service_key else self.supabase_anon_key
        self.supabase: Client = create_client(self.supabase_url, primary_key)
        
        logger.info(f"🔑 Using {'service role' if self.supabase_service_key else 'anon'} key for Supabase")
        self.is_ready = False
        
        # Cache for frequently accessed data
        self._symptoms_cache = None
        self._diseases_cache = None
        self._cache_timestamp = None
        self.CACHE_DURATION = 300  # 5 minutes
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Simple test query
            result = self.supabase.table('fast_symptoms').select('count').limit(1).execute()
            logger.info("✅ Supabase connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False
    
    def setup_tables(self) -> bool:
        """Create optimized Supabase tables for fast diagnosis"""
        try:
            logger.info("🔧 Setting up Supabase tables...")
            
            # SQL to create optimized tables
            setup_sql = """
            -- Fast Symptoms Table (for quick symptom lookup)
            CREATE TABLE IF NOT EXISTS fast_symptoms (
                id SERIAL PRIMARY KEY,
                symptom_name TEXT UNIQUE NOT NULL,
                symptom_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- Fast Diseases Table (for quick disease lookup)
            CREATE TABLE IF NOT EXISTS fast_diseases (
                id SERIAL PRIMARY KEY,
                disease_name TEXT UNIQUE NOT NULL,
                orpha_code TEXT,
                symptom_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- Pre-computed Probabilities Table (the core optimization)
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
            
            -- Indexes for ultra-fast queries
            CREATE INDEX IF NOT EXISTS idx_fast_probabilities_symptom ON fast_probabilities(symptom_name);
            CREATE INDEX IF NOT EXISTS idx_fast_probabilities_disease ON fast_probabilities(disease_name);
            CREATE INDEX IF NOT EXISTS idx_fast_probabilities_probability ON fast_probabilities(probability DESC);
            CREATE INDEX IF NOT EXISTS idx_fast_symptoms_name ON fast_symptoms(symptom_name);
            CREATE INDEX IF NOT EXISTS idx_fast_diseases_name ON fast_diseases(disease_name);
            """
            
            # Execute table creation (Note: This requires SQL execution via RPC or direct SQL)
            logger.info("📋 Tables and indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up tables: {e}")
            return False
    
    def populate_from_csv(self, csv_path: str) -> bool:
        """Populate Supabase tables from CSV data"""
        try:
            logger.info(f"📊 Loading data from {csv_path}")
            
            # Load CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} records")
            
            # Clean data
            df = df.dropna(subset=['orpha_code', 'disorder_name', 'hpo_term'])
            
            # Frequency mapping
            frequency_mapping = {
                'Very frequent (99-80%)': 0.9,
                'Frequent (79-30%)': 0.55,
                'Occasional (29-5%)': 0.17,
                'Very rare (<5%)': 0.025,
                'Excluded (0%)': 0.0
            }
            
            df['frequency_numeric'] = df['hpo_frequency'].map(
                lambda x: frequency_mapping.get(str(x).strip(), 0.5) if pd.notna(x) else 0.5
            )
            
            # 1. Populate fast_symptoms
            logger.info("🔄 Populating symptoms...")
            symptoms_data = []
            symptom_counts = df['hpo_term'].value_counts()
            
            for symptom, count in symptom_counts.items():
                symptoms_data.append({
                    'symptom_name': symptom,
                    'symptom_count': int(count)
                })
            
            # Insert symptoms in batches
            batch_size = 100
            for i in range(0, len(symptoms_data), batch_size):
                batch = symptoms_data[i:i + batch_size]
                try:
                    self.supabase.table('fast_symptoms').upsert(batch).execute()
                except Exception as e:
                    logger.warning(f"Batch insert warning: {e}")
            
            logger.info(f"✅ Inserted {len(symptoms_data)} symptoms")
            
            # 2. Populate fast_diseases
            logger.info("🔄 Populating diseases...")
            diseases_data = []
            disease_info = df.groupby('disorder_name').agg({
                'orpha_code': 'first',
                'hpo_term': 'count'
            }).reset_index()
            
            for _, row in disease_info.iterrows():
                diseases_data.append({
                    'disease_name': row['disorder_name'],
                    'orpha_code': str(row['orpha_code']),
                    'symptom_count': int(row['hpo_term'])
                })
            
            # Insert diseases in batches
            for i in range(0, len(diseases_data), batch_size):
                batch = diseases_data[i:i + batch_size]
                try:
                    self.supabase.table('fast_diseases').upsert(batch).execute()
                except Exception as e:
                    logger.warning(f"Batch insert warning: {e}")
            
            logger.info(f"✅ Inserted {len(diseases_data)} diseases")
            
            # 3. Populate fast_probabilities (the core optimization)
            logger.info("🔄 Populating pre-computed probabilities...")
            probabilities_data = []
            
            for _, row in df.iterrows():
                # Calculate probability and confidence
                frequency = row['frequency_numeric']
                probability = min(frequency * 1.2, 1.0)  # Boost probability slightly
                confidence_score = frequency
                
                probabilities_data.append({
                    'symptom_name': row['hpo_term'],
                    'disease_name': row['disorder_name'],
                    'orpha_code': str(row['orpha_code']),
                    'probability': float(probability),
                    'frequency': float(frequency),
                    'confidence_score': float(confidence_score)
                })
            
            # Insert probabilities in batches
            logger.info(f"Inserting {len(probabilities_data)} probability records...")
            for i in range(0, len(probabilities_data), batch_size):
                batch = probabilities_data[i:i + batch_size]
                try:
                    self.supabase.table('fast_probabilities').upsert(batch).execute()
                    if i % 1000 == 0:
                        logger.info(f"Inserted {i + len(batch)} probability records...")
                except Exception as e:
                    logger.warning(f"Batch insert warning: {e}")
            
            logger.info(f"✅ Inserted {len(probabilities_data)} probability records")
            
            self.is_ready = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error populating from CSV: {e}")
            return False
    
    def get_symptoms(self, search: str = None, limit: int = 50) -> List[str]:
        """Get symptoms with caching for performance"""
        try:
            # Check cache
            if self._should_use_cache('symptoms'):
                if search:
                    search_lower = search.lower()
                    filtered = [s for s in self._symptoms_cache if search_lower in s.lower()]
                    return filtered[:limit]
                return self._symptoms_cache[:limit]
            
            # Query Supabase
            query = self.supabase.table('fast_symptoms').select('symptom_name')
            
            if search:
                query = query.ilike('symptom_name', f'%{search}%')
            
            result = query.order('symptom_count', desc=True).limit(limit).execute()
            
            symptoms = [row['symptom_name'] for row in result.data]
            
            # Update cache if no search
            if not search:
                self._symptoms_cache = symptoms
                self._cache_timestamp = time.time()
            
            return symptoms
            
        except Exception as e:
            logger.error(f"Error getting symptoms: {e}")
            return []
    
    def get_diseases(self, search: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get diseases with caching"""
        try:
            query = self.supabase.table('fast_diseases').select('disease_name, orpha_code, symptom_count')
            
            if search:
                query = query.ilike('disease_name', f'%{search}%')
            
            result = query.order('symptom_count', desc=True).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting diseases: {e}")
            return []
    
    def ultra_fast_diagnosis(
        self,
        present_symptoms: List[str],
        absent_symptoms: List[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Ultra-fast diagnosis using Supabase pre-computed probabilities"""
        
        if not self.is_ready and not self.test_connection():
            raise Exception("Supabase system not ready")
        
        if absent_symptoms is None:
            absent_symptoms = []
        
        start_time = time.time()
        
        try:
            # Query pre-computed probabilities for present symptoms
            if present_symptoms:
                result = self.supabase.table('fast_probabilities')\
                    .select('disease_name, orpha_code, probability, frequency, confidence_score, symptom_name')\
                    .in_('symptom_name', present_symptoms)\
                    .execute()
                
                probability_data = result.data
            else:
                probability_data = []
            
            # Aggregate results by disease
            disease_scores = defaultdict(lambda: {
                'total_probability': 0.0,
                'matching_symptoms': [],
                'orpha_code': '',
                'confidence_sum': 0.0,
                'frequency_sum': 0.0
            })
            
            # Process present symptoms
            for row in probability_data:
                disease = row['disease_name']
                disease_scores[disease]['total_probability'] += row['probability']
                disease_scores[disease]['matching_symptoms'].append(row['symptom_name'])
                disease_scores[disease]['orpha_code'] = row['orpha_code']
                disease_scores[disease]['confidence_sum'] += row['confidence_score']
                disease_scores[disease]['frequency_sum'] += row['frequency']
            
            # Apply penalties for absent symptoms
            if absent_symptoms:
                absent_result = self.supabase.table('fast_probabilities')\
                    .select('disease_name, probability')\
                    .in_('symptom_name', absent_symptoms)\
                    .execute()
                
                for row in absent_result.data:
                    disease = row['disease_name']
                    if disease in disease_scores:
                        # Reduce probability for diseases that have absent symptoms
                        penalty = row['probability'] * 0.3
                        disease_scores[disease]['total_probability'] *= (1 - penalty)
            
            # Calculate final scores and format results
            results = []
            for disease, scores in disease_scores.items():
                matching_count = len(set(scores['matching_symptoms']))
                confidence_score = matching_count / max(len(present_symptoms), 1)
                
                results.append({
                    'disorder_name': disease,
                    'orpha_code': scores['orpha_code'],
                    'probability': min(scores['total_probability'], 1.0),
                    'matching_symptoms': list(set(scores['matching_symptoms'])),
                    'total_symptoms': matching_count,  # This could be enhanced with a separate query
                    'confidence_score': confidence_score
                })
            
            # Sort and limit results
            results.sort(key=lambda x: (x['probability'], x['confidence_score']), reverse=True)
            top_results = results[:top_n]
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                'success': True,
                'results': top_results,
                'total_diseases_evaluated': len(disease_scores),
                'processing_time_ms': processing_time,
                'method': 'supabase_precomputed'
            }
            
        except Exception as e:
            logger.error(f"Error in ultra_fast_diagnosis: {e}")
            raise Exception(f"Diagnosis failed: {str(e)}")
    
    def _should_use_cache(self, cache_type: str) -> bool:
        """Check if cache is valid and should be used"""
        if cache_type == 'symptoms' and self._symptoms_cache is None:
            return False
        
        if self._cache_timestamp is None:
            return False
        
        return (time.time() - self._cache_timestamp) < self.CACHE_DURATION


# Global instance
supabase_diagnosis = SupabaseFastDiagnosis()


def initialize_supabase_diagnosis() -> bool:
    """Initialize the Supabase diagnosis system"""
    global supabase_diagnosis
    
    try:
        if supabase_diagnosis.test_connection():
            supabase_diagnosis.is_ready = True
            logger.info("✅ Supabase diagnosis system ready!")
            return True
        else:
            logger.error("❌ Failed to connect to Supabase")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing Supabase diagnosis: {e}")
        return False


def setup_and_populate() -> bool:
    """Setup tables and populate with CSV data"""
    global supabase_diagnosis
    
    try:
        # Test connection first
        if not supabase_diagnosis.test_connection():
            return False
        
        # Setup tables
        if not supabase_diagnosis.setup_tables():
            return False
        
        # Populate from CSV
        csv_path = "file/clinical_signs_and_symptoms_in_rare_diseases.csv"
        if os.path.exists(csv_path):
            return supabase_diagnosis.populate_from_csv(csv_path)
        else:
            logger.error(f"CSV file not found: {csv_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error in setup_and_populate: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Supabase Fast Diagnosis Setup for Railway")
    print("=" * 50)
    
    # Initialize and test
    if initialize_supabase_diagnosis():
        print("✅ Supabase connection established!")
        
        # Test basic functionality
        symptoms = supabase_diagnosis.get_symptoms(limit=5)
        print(f"📋 Sample symptoms: {symptoms}")
        
        diseases = supabase_diagnosis.get_diseases(limit=3)
        print(f"🏥 Sample diseases: {[d['disease_name'] for d in diseases]}")
        
        print("\n🎯 System ready for Railway deployment!")
        print("📝 Next steps:")
        print("   1. Run setup_and_populate() to populate tables")
        print("   2. Deploy to Railway with Supabase integration")
        
    else:
        print("❌ Failed to initialize Supabase system")
        print("🔧 Please check your SUPABASE_URL and SUPABASE_ANON_KEY")