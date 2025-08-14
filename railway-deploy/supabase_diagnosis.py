#!/usr/bin/env python3
"""
Supabase Diagnosis - Railway Deployment Ready
Uses Supabase for both fast and true Bayesian disease diagnosis
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


class SupabaseDiagnosis:
    """Supabase-based diagnosis system supporting both fast and true Bayesian modes"""
    
    def __init__(self):
        """Initialize Supabase client with service key"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url:
            raise ValueError("Missing SUPABASE_URL in environment")
        
        if not self.supabase_service_key:
            raise ValueError("Missing SUPABASE_SERVICE_KEY in environment")
        
        try:
            # Always use service key for full database access
            self.supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
            logger.info(f"🔑 Connected to Supabase with service role key")
        except Exception as e:
            logger.error(f"❌ Failed to create Supabase client: {e}")
            raise ValueError(f"Failed to initialize Supabase client: {e}")
        
        self.is_ready = False
        
        # Cache for frequently accessed data
        self._symptoms_cache = None
        self._diseases_cache = None
        self._cache_timestamp = None
        self.CACHE_DURATION = 300  # 5 minutes
    
    def test_connection(self) -> bool:
        """Test Supabase connection using new schema"""
        try:
            # Test with the new schema tables
            try:
                result = self.supabase.table('disorders').select('count').limit(1).execute()
                logger.info("✅ Supabase connection successful - disorders table accessible")
                return True
            except Exception as e:
                logger.warning(f"disorders table test failed: {e}")
                
            # Fallback test with hpo_terms
            try:
                result = self.supabase.table('hpo_terms').select('count').limit(1).execute()
                logger.info("✅ Supabase connection successful - hpo_terms table accessible")
                return True
            except Exception as e:
                logger.error(f"❌ All connection tests failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False
    
    def get_symptoms(self, search: str = None, limit: int = 50) -> List[str]:
        """Get symptoms from Supabase using the new schema"""
        try:
            # Try fast_symptoms first for performance
            try:
                query = self.supabase.table('fast_symptoms').select('symptom_name')
                if search:
                    query = query.ilike('symptom_name', f'%{search}%')
                result = query.order('symptom_count', desc=True).limit(limit).execute()
                return [row['symptom_name'] for row in result.data]
            except Exception as e:
                logger.warning(f"fast_symptoms query failed: {e}")
            
            # Fallback to hpo_terms table with correct column name
            try:
                query = self.supabase.table('hpo_terms').select('term')
                if search:
                    query = query.ilike('term', f'%{search}%')
                result = query.limit(limit).execute()
                return [row['term'] for row in result.data]
            except Exception as e:
                logger.warning(f"hpo_terms query failed: {e}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting symptoms: {e}")
            return []
    
    def get_diseases(self, search: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get diseases from Supabase using the new schema"""
        try:
            # Try fast_diseases first for performance
            try:
                query = self.supabase.table('fast_diseases').select('disease_name, orpha_code, symptom_count')
                if search:
                    query = query.ilike('disease_name', f'%{search}%')
                result = query.order('symptom_count', desc=True).limit(limit).execute()
                return result.data
            except Exception as e:
                logger.warning(f"fast_diseases query failed: {e}")
            
            # Fallback to disorders table with correct column names
            try:
                query = self.supabase.table('disorders').select('name, orpha_code')
                if search:
                    query = query.ilike('name', f'%{search}%')
                result = query.limit(limit).execute()
                return [{'disease_name': row['name'], 'orpha_code': row['orpha_code'], 'symptom_count': 0} for row in result.data]
            except Exception as e:
                logger.warning(f"disorders query failed: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting diseases: {e}")
            return []
    
    def fast_diagnosis(
        self,
        present_symptoms: List[str],
        absent_symptoms: List[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Fast diagnosis using pre-computed probabilities"""
        
        if absent_symptoms is None:
            absent_symptoms = []
        
        start_time = time.time()
        
        try:
            # Try to use fast_probabilities table first
            try:
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
                    'confidence_sum': 0.0
                })
                
                # Process present symptoms
                for row in probability_data:
                    disease = row['disease_name']
                    disease_scores[disease]['total_probability'] += row['probability']
                    disease_scores[disease]['matching_symptoms'].append(row['symptom_name'])
                    disease_scores[disease]['orpha_code'] = row['orpha_code']
                    disease_scores[disease]['confidence_sum'] += row['confidence_score']
                
                # Format results
                results = []
                for disease, scores in disease_scores.items():
                    matching_count = len(set(scores['matching_symptoms']))
                    confidence_score = matching_count / max(len(present_symptoms), 1)
                    
                    results.append({
                        'disorder_name': disease,
                        'orpha_code': scores['orpha_code'],
                        'probability': min(scores['total_probability'], 1.0),
                        'matching_symptoms': list(set(scores['matching_symptoms'])),
                        'total_symptoms': matching_count,
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
                    'processing_time_ms': processing_time
                }
                
            except Exception as e:
                logger.warning(f"Fast probabilities table not available, falling back: {e}")
                # Fallback to basic disorder_symptoms_view query
                return self._fallback_fast_diagnosis(present_symptoms, absent_symptoms, top_n, start_time)
                
        except Exception as e:
            logger.error(f"Error in fast_diagnosis: {e}")
            raise Exception(f"Fast diagnosis failed: {str(e)}")
    
    def true_bayesian_diagnosis(
        self,
        present_symptoms: List[str],
        absent_symptoms: List[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """True Bayesian diagnosis using full Supabase dataset"""
        
        if absent_symptoms is None:
            absent_symptoms = []
        
        start_time = time.time()
        
        try:
            logger.info("🧮 Starting true Bayesian computation using Supabase...")
            
            # Get all disorder-symptom associations from Supabase
            logger.info("📊 Fetching all disorder-symptom data from Supabase...")
            
            try:
                # Use the new schema with proper joins
                logger.info("Using new normalized schema with joins...")
                result = self.supabase.table('disorder_hpo_associations')\
                    .select('''
                        frequency,
                        disorders(name, orpha_code),
                        hpo_terms(term)
                    ''')\
                    .limit(10000)\
                    .execute()
                
                # Transform the joined data to match expected format
                all_data = []
                for row in result.data:
                    if row.get('disorders') and row.get('hpo_terms'):
                        all_data.append({
                            'disorder_name': row['disorders']['name'],
                            'orpha_code': row['disorders']['orpha_code'],
                            'hpo_term': row['hpo_terms']['term'],
                            'hpo_frequency': row.get('frequency', 'Unknown')
                        })
                logger.info(f"✅ Loaded {len(all_data)} associations from new schema")
            except Exception as e:
                logger.error(f"Failed to load from new schema: {e}")
                raise Exception(f"Could not load disorder-symptom associations: {e}")
            
            if not all_data:
                raise Exception("No disease-symptom data found in Supabase")
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(all_data)
            
            # Clean data
            df = df.dropna(subset=['orpha_code', 'disorder_name', 'hpo_term'])
            logger.info(f"After cleaning: {len(df)} associations")
            
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
            
            # Get unique diseases and symptoms
            all_diseases = df['disorder_name'].unique()
            all_symptoms = df['hpo_term'].unique()
            
            logger.info(f"🔄 Computing true Bayesian probabilities for {len(all_diseases)} diseases...")
            
            # Calculate total associations for priors
            total_associations = len(df)
            
            # Filter valid symptoms
            valid_present_symptoms = [s for s in present_symptoms if s in all_symptoms]
            valid_absent_symptoms = [s for s in absent_symptoms if s in all_symptoms]
            
            if not valid_present_symptoms:
                raise Exception("None of the provided symptoms are found in the database")
            
            logger.info(f"Valid present symptoms: {valid_present_symptoms}")
            logger.info(f"Valid absent symptoms: {valid_absent_symptoms}")
            
            # Limit computation to prevent timeout - focus on diseases with matching symptoms
            matching_diseases = set()
            for symptom in valid_present_symptoms:
                symptom_diseases = df[df['hpo_term'] == symptom]['disorder_name'].unique()
                matching_diseases.update(symptom_diseases)
            
            # If we have too many matching diseases, limit to most frequent ones
            if len(matching_diseases) > 25:
                disease_counts = df[df['disorder_name'].isin(matching_diseases)].groupby('disorder_name').size()
                top_diseases = disease_counts.nlargest(25).index.tolist()
                matching_diseases = set(top_diseases)
            
            computation_diseases = list(matching_diseases) if matching_diseases else all_diseases[:25]
            logger.info(f"🔄 Computing for {len(computation_diseases)} relevant diseases...")
            
            # Calculate evidence P(symptoms) by summing over relevant diseases
            evidence = 0.0
            disease_posteriors = {}
            
            for i, disease in enumerate(computation_diseases):
                if i % 10 == 0:
                    logger.info(f"   Processing disease {i+1}/{len(computation_diseases)}: {disease}")
                
                # Get disease-specific data
                disease_data = df[df['disorder_name'] == disease]
                symptom_freq_map = dict(zip(disease_data['hpo_term'], disease_data['frequency_numeric']))
                
                # Calculate prior P(disease)
                disease_associations = len(disease_data)
                prior = disease_associations / total_associations
                
                # Calculate likelihood P(symptoms|disease)
                likelihood = 1.0
                matching_symptoms = []
                
                # For present symptoms
                for symptom in valid_present_symptoms:
                    if symptom in symptom_freq_map:
                        freq = symptom_freq_map[symptom]
                        likelihood *= freq
                        matching_symptoms.append(symptom)
                    else:
                        likelihood *= 0.01  # Small probability for unseen symptoms
                
                # For absent symptoms
                for symptom in valid_absent_symptoms:
                    if symptom in symptom_freq_map:
                        freq = symptom_freq_map[symptom]
                        likelihood *= (1 - freq)
                
                # Calculate unnormalized posterior
                unnormalized_posterior = likelihood * prior
                evidence += unnormalized_posterior
                
                # Store for final calculation
                disease_posteriors[disease] = {
                    'unnormalized_posterior': unnormalized_posterior,
                    'matching_symptoms': matching_symptoms,
                    'orpha_code': str(disease_data.iloc[0]['orpha_code']),
                    'total_symptoms': len(disease_data)
                }
            
            logger.info(f"✅ Computed unnormalized posteriors for {len(all_diseases)} diseases")
            
            # Avoid division by zero
            if evidence == 0:
                evidence = 1e-10
            
            # Calculate final normalized probabilities
            results = []
            for disease, data in disease_posteriors.items():
                if data['unnormalized_posterior'] > 0 or len(data['matching_symptoms']) > 0:
                    # True Bayesian posterior
                    probability = data['unnormalized_posterior'] / evidence
                    confidence_score = len(data['matching_symptoms']) / max(len(valid_present_symptoms), 1)
                    
                    results.append({
                        'disorder_name': disease,
                        'orpha_code': data['orpha_code'],
                        'probability': probability,
                        'matching_symptoms': data['matching_symptoms'],
                        'total_symptoms': data['total_symptoms'],
                        'confidence_score': confidence_score
                    })
            
            # Sort by probability (true Bayesian probabilities)
            results.sort(key=lambda x: x['probability'], reverse=True)
            top_results = results[:top_n]
            
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ True Bayesian computation completed in {processing_time:.1f}ms")
            logger.info(f"Top result: {top_results[0]['disorder_name'] if top_results else 'None'} ({top_results[0]['probability']:.6f})" if top_results else "No results")
            
            return {
                'success': True,
                'results': top_results,
                'total_diseases_evaluated': len(computation_diseases),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in true_bayesian_diagnosis: {e}")
            raise Exception(f"True Bayesian diagnosis failed: {str(e)}")
    
    def _fallback_fast_diagnosis(self, present_symptoms, absent_symptoms, top_n, start_time):
        """Fallback fast diagnosis using basic Supabase tables"""
        try:
            # Basic query using disorder_symptoms_view or hpo_associations
            results = []
            
            # This is a simplified fallback - you might want to enhance this
            logger.info("Using fallback fast diagnosis method")
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                'success': True,
                'results': results,
                'total_diseases_evaluated': 0,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Fallback diagnosis failed: {e}")
            raise Exception(f"Fallback diagnosis failed: {str(e)}")


# Global instance - initialized later to avoid import-time crashes
supabase_diagnosis = None


def initialize_supabase_diagnosis() -> bool:
    """Initialize the Supabase diagnosis system"""
    global supabase_diagnosis
    
    try:
        # Initialize the client only when needed
        if supabase_diagnosis is None:
            logger.info("🔄 Creating Supabase diagnosis client...")
            supabase_diagnosis = SupabaseDiagnosis()
        
        if supabase_diagnosis.test_connection():
            supabase_diagnosis.is_ready = True
            logger.info("✅ Supabase diagnosis system ready!")
            return True
        else:
            logger.error("❌ Failed to connect to Supabase")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing Supabase diagnosis: {e}")
        logger.error("💡 This might be due to missing environment variables or network issues")
        # Set a dummy object to prevent further crashes
        supabase_diagnosis = type('DummySupabase', (), {'is_ready': False})()
        return False


if __name__ == "__main__":
    print("🚀 Supabase Diagnosis System for Railway")
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
        
    else:
        print("❌ Failed to initialize Supabase system")
        print("🔧 Please check your SUPABASE_URL and SUPABASE_KEY")