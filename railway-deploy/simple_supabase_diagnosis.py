#!/usr/bin/env python3
"""
Simple Supabase Diagnosis - Fallback version for Railway deployment
Uses basic HTTP requests to Supabase REST API to avoid client library issues
"""

import os
import requests
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleSupabaseDiagnosis:
    """Simple HTTP-based Supabase diagnosis system"""
    
    def __init__(self):
        """Initialize with direct HTTP client using service key"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url:
            raise ValueError("Missing SUPABASE_URL in environment")
        
        if not self.supabase_key:
            raise ValueError("Missing SUPABASE_SERVICE_KEY in environment")
        
        # Clean URL
        self.supabase_url = self.supabase_url.rstrip('/')
        self.rest_url = f"{self.supabase_url}/rest/v1"
        
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
        
        self.is_ready = False
        logger.info(f"🔧 Simple Supabase client initialized for {self.supabase_url}")
    
    def test_connection(self) -> bool:
        """Test connection using simple HTTP request"""
        try:
            # Try to access disorders table
            response = requests.get(
                f"{self.rest_url}/disorders?select=count&limit=1",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Simple Supabase connection successful")
                return True
            else:
                logger.error(f"❌ Connection failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def get_symptoms(self, search: str = None, limit: int = 50) -> List[str]:
        """Get symptoms using HTTP request"""
        try:
            url = f"{self.rest_url}/hpo_terms?select=hpo_term"
            
            if search:
                url += f"&hpo_term=ilike.*{search}*"
            
            url += f"&limit={limit}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return [row['hpo_term'] for row in data]
            else:
                logger.error(f"Failed to get symptoms: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting symptoms: {e}")
            return []
    
    def fast_diagnosis(
        self,
        present_symptoms: List[str],
        absent_symptoms: List[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Fast diagnosis using simple HTTP queries"""
        
        if absent_symptoms is None:
            absent_symptoms = []
        
        start_time = time.time()
        
        try:
            # Simple approach: get disorder-symptom associations for present symptoms
            results = []
            
            if present_symptoms:
                # Build query for disorder_symptoms_view or join
                symptom_list = "','".join(present_symptoms)
                
                try:
                    # Try optimized view first
                    url = f"{self.rest_url}/disorder_symptoms_view?hpo_term=in.(''{symptom_list}'')"
                    response = requests.get(url, headers=self.headers, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Got {len(data)} associations from disorder_symptoms_view")
                    else:
                        # Fallback to basic query
                        logger.info("Falling back to basic disorder query")
                        data = []
                
                except Exception as e:
                    logger.warning(f"View query failed, using fallback: {e}")
                    data = []
                
                # Process the data
                if data:
                    # Group by disorder and calculate simple scores
                    disorder_scores = {}
                    
                    for row in data:
                        disorder_name = row.get('disorder_name', '')
                        orpha_code = row.get('orpha_code', '')
                        symptom = row.get('hpo_term', '')
                        frequency = row.get('hpo_frequency', 'Unknown')
                        
                        if disorder_name not in disorder_scores:
                            disorder_scores[disorder_name] = {
                                'orpha_code': orpha_code,
                                'matching_symptoms': [],
                                'total_score': 0.0
                            }
                        
                        disorder_scores[disorder_name]['matching_symptoms'].append(symptom)
                        
                        # Simple frequency scoring
                        freq_score = 0.5  # default
                        if 'Very frequent' in frequency:
                            freq_score = 0.9
                        elif 'Frequent' in frequency:
                            freq_score = 0.7
                        elif 'Occasional' in frequency:
                            freq_score = 0.3
                        elif 'Very rare' in frequency:
                            freq_score = 0.1
                        
                        disorder_scores[disorder_name]['total_score'] += freq_score
                    
                    # Convert to results format
                    for disorder_name, scores in disorder_scores.items():
                        matching_count = len(scores['matching_symptoms'])
                        confidence_score = matching_count / max(len(present_symptoms), 1)
                        probability = min(scores['total_score'] / max(len(present_symptoms), 1), 1.0)
                        
                        results.append({
                            'disorder_name': disorder_name,
                            'orpha_code': scores['orpha_code'],
                            'probability': probability,
                            'matching_symptoms': scores['matching_symptoms'],
                            'total_symptoms': matching_count,
                            'confidence_score': confidence_score
                        })
                    
                    # Sort by probability
                    results.sort(key=lambda x: (x['probability'], x['confidence_score']), reverse=True)
                    results = results[:top_n]
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                'success': True,
                'results': results,
                'total_diseases_evaluated': len(results),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in fast_diagnosis: {e}")
            raise Exception(f"Fast diagnosis failed: {str(e)}")
    
    def true_bayesian_diagnosis(
        self,
        present_symptoms: List[str],
        absent_symptoms: List[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """True Bayesian diagnosis using HTTP requests"""
        
        if absent_symptoms is None:
            absent_symptoms = []
        
        start_time = time.time()
        
        try:
            logger.info("🧮 Starting true Bayesian computation using HTTP requests...")
            
            # Get all disorder-symptom data
            logger.info("📊 Fetching all disorder-symptom data...")
            
            try:
                # Try to get all data from view
                response = requests.get(
                    f"{self.rest_url}/disorder_symptoms_view?select=disorder_name,orpha_code,hpo_term,hpo_frequency",
                    headers=self.headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    all_data = response.json()
                    logger.info(f"✅ Loaded {len(all_data)} associations from view")
                else:
                    logger.error(f"Failed to load data: {response.status_code}")
                    raise Exception("Failed to load disorder-symptom data")
                
            except Exception as e:
                logger.error(f"Error loading data: {e}")
                raise Exception(f"Failed to load data: {str(e)}")
            
            if not all_data:
                raise Exception("No disorder-symptom data available")
            
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
            
            # Filter valid symptoms
            valid_present_symptoms = [s for s in present_symptoms if s in all_symptoms]
            valid_absent_symptoms = [s for s in absent_symptoms if s in all_symptoms]
            
            if not valid_present_symptoms:
                raise Exception("None of the provided symptoms are found in the database")
            
            logger.info(f"Valid present symptoms: {valid_present_symptoms}")
            
            # Calculate total associations for priors
            total_associations = len(df)
            
            # Calculate evidence P(symptoms) by summing over all diseases
            evidence = 0.0
            disease_posteriors = {}
            
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
            
            for i, disease in enumerate(computation_diseases):
                if i % 25 == 0:
                    logger.info(f"   Processing disease {i+1}/{len(computation_diseases)}")
                
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
                        likelihood *= 0.01
                
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
            
            # Avoid division by zero
            if evidence == 0:
                evidence = 1e-10
            
            # Calculate final normalized probabilities
            results = []
            for disease, data in disease_posteriors.items():
                if data['unnormalized_posterior'] > 0 or len(data['matching_symptoms']) > 0:
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
            
            # Sort by probability
            results.sort(key=lambda x: x['probability'], reverse=True)
            top_results = results[:top_n]
            
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ True Bayesian computation completed in {processing_time:.1f}ms")
            
            return {
                'success': True,
                'results': top_results,
                'total_diseases_evaluated': len(computation_diseases),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in true_bayesian_diagnosis: {e}")
            raise Exception(f"True Bayesian diagnosis failed: {str(e)}")


# Global instance - initialized later
simple_supabase_diagnosis = None


def initialize_simple_supabase_diagnosis() -> bool:
    """Initialize the simple Supabase diagnosis system"""
    global simple_supabase_diagnosis
    
    try:
        if simple_supabase_diagnosis is None:
            logger.info("🔄 Creating simple Supabase diagnosis client...")
            simple_supabase_diagnosis = SimpleSupabaseDiagnosis()
        
        if simple_supabase_diagnosis.test_connection():
            simple_supabase_diagnosis.is_ready = True
            logger.info("✅ Simple Supabase diagnosis system ready!")
            return True
        else:
            logger.error("❌ Failed to connect to Supabase")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing simple Supabase diagnosis: {e}")
        # Set a dummy object to prevent crashes
        simple_supabase_diagnosis = type('DummySupabase', (), {'is_ready': False})()
        return False


if __name__ == "__main__":
    print("🚀 Simple Supabase Diagnosis System for Railway")
    print("=" * 50)
    
    # Initialize and test
    if initialize_simple_supabase_diagnosis():
        print("✅ Simple Supabase connection established!")
        
        # Test basic functionality
        symptoms = simple_supabase_diagnosis.get_symptoms(limit=5)
        print(f"📋 Sample symptoms: {symptoms}")
        
        print("\n🎯 System ready for Railway deployment!")
        
    else:
        print("❌ Failed to initialize simple Supabase system")
        print("🔧 Please check your SUPABASE_URL and SUPABASE_KEY")