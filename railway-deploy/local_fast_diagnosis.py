#!/usr/bin/env python3
"""
Local Fast Diagnosis - Pre-compute probabilities in memory for ultra-fast diagnosis
No external database required - uses local caching and optimization
"""

import os
import pandas as pd
import numpy as np
import pickle
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalFastDiagnosis:
    """Local fast diagnosis with pre-computed probabilities"""
    
    def __init__(self):
        """Initialize the fast diagnosis system"""
        self.disease_data = None
        self.symptom_disease_matrix = {}  # Pre-computed probabilities
        self.disease_symptoms_map = {}    # Disease -> symptoms mapping
        self.symptom_diseases_map = {}    # Symptom -> diseases mapping
        self.symptoms_list = []
        self.diseases_list = []
        self.is_ready = False
    
    def load_and_precompute(self, csv_path: str) -> bool:
        """Load CSV data and pre-compute all probabilities"""
        try:
            logger.info(f"Loading and pre-computing from {csv_path}")
            start_time = time.time()
            
            # Load CSV data
            self.disease_data = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(self.disease_data)} records")
            
            # Clean the data
            self.disease_data = self.disease_data.dropna(subset=['orpha_code', 'disorder_name', 'hpo_term'])
            
            # Add frequency mapping
            frequency_mapping = {
                'Very frequent (99-80%)': 0.9,
                'Frequent (79-30%)': 0.55,
                'Occasional (29-5%)': 0.17,
                'Very rare (<5%)': 0.025,
                'Excluded (0%)': 0.0
            }
            
            self.disease_data['frequency_numeric'] = self.disease_data['hpo_frequency'].map(
                lambda x: frequency_mapping.get(str(x).strip(), 0.5) if pd.notna(x) else 0.5
            )
            
            # Extract unique lists
            self.symptoms_list = sorted(self.disease_data['hpo_term'].unique().tolist())
            self.diseases_list = sorted(self.disease_data['disorder_name'].unique().tolist())
            
            logger.info(f"Found {len(self.diseases_list)} diseases and {len(self.symptoms_list)} symptoms")
            
            # Pre-compute disease -> symptoms mapping
            logger.info("Pre-computing disease-symptom mappings...")
            for disease in self.diseases_list:
                disease_data = self.disease_data[self.disease_data['disorder_name'] == disease]
                self.disease_symptoms_map[disease] = {
                    'symptoms': {},
                    'orpha_code': str(disease_data.iloc[0]['orpha_code']),
                    'total_symptoms': len(disease_data)
                }
                
                for _, row in disease_data.iterrows():
                    symptom = row['hpo_term']
                    frequency = row['frequency_numeric']
                    self.disease_symptoms_map[disease]['symptoms'][symptom] = frequency
            
            # Pre-compute symptom -> diseases mapping
            logger.info("Pre-computing symptom-disease mappings...")
            for symptom in self.symptoms_list:
                symptom_data = self.disease_data[self.disease_data['hpo_term'] == symptom]
                self.symptom_diseases_map[symptom] = {}
                
                for _, row in symptom_data.iterrows():
                    disease = row['disorder_name']
                    frequency = row['frequency_numeric']
                    self.symptom_diseases_map[symptom][disease] = {
                        'frequency': frequency,
                        'orpha_code': str(row['orpha_code'])
                    }
            
            # Pre-compute probability matrix for common combinations
            logger.info("Pre-computing probability combinations...")
            self._precompute_probability_matrix()
            
            # Cache to disk for faster future loading
            self._save_cache()
            
            end_time = time.time()
            logger.info(f"Pre-computation completed in {end_time - start_time:.2f} seconds")
            
            self.is_ready = True
            return True
            
        except Exception as e:
            logger.error(f"Error in load_and_precompute: {e}")
            return False
    
    def _precompute_probability_matrix(self):
        """Pre-compute probability combinations for faster lookup"""
        logger.info("Building probability matrix...")
        
        # For each symptom, pre-compute probabilities for all associated diseases
        for symptom in self.symptoms_list:
            if symptom not in self.symptom_disease_matrix:
                self.symptom_disease_matrix[symptom] = {}
            
            # Get all diseases that have this symptom
            if symptom in self.symptom_diseases_map:
                for disease, info in self.symptom_diseases_map[symptom].items():
                    # Calculate base probability
                    base_prob = info['frequency']
                    
                    # Store pre-computed result
                    self.symptom_disease_matrix[symptom][disease] = {
                        'probability': base_prob,
                        'orpha_code': info['orpha_code'],
                        'confidence': min(1.0, base_prob * 1.2)
                    }
        
        logger.info(f"Pre-computed matrix for {len(self.symptom_disease_matrix)} symptoms")
    
    def _save_cache(self):
        """Save pre-computed data to disk cache"""
        try:
            cache_data = {
                'disease_symptoms_map': self.disease_symptoms_map,
                'symptom_diseases_map': self.symptom_diseases_map,
                'symptom_disease_matrix': self.symptom_disease_matrix,
                'symptoms_list': self.symptoms_list,
                'diseases_list': self.diseases_list
            }
            
            with open('diagnosis_cache.pkl', 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info("Cached pre-computed data to diagnosis_cache.pkl")
            
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def load_from_cache(self) -> bool:
        """Load pre-computed data from disk cache"""
        try:
            if not os.path.exists('diagnosis_cache.pkl'):
                return False
            
            logger.info("Loading from cache...")
            with open('diagnosis_cache.pkl', 'rb') as f:
                cache_data = pickle.load(f)
            
            self.disease_symptoms_map = cache_data['disease_symptoms_map']
            self.symptom_diseases_map = cache_data['symptom_diseases_map']
            self.symptom_disease_matrix = cache_data['symptom_disease_matrix']
            self.symptoms_list = cache_data['symptoms_list']
            self.diseases_list = cache_data['diseases_list']
            
            self.is_ready = True
            logger.info(f"Loaded cache: {len(self.diseases_list)} diseases, {len(self.symptoms_list)} symptoms")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return False
    
    def ultra_fast_diagnosis(
        self,
        present_symptoms: List[str],
        absent_symptoms: List[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Ultra-fast diagnosis using pre-computed probabilities"""
        
        if not self.is_ready:
            raise Exception("System not ready - run load_and_precompute first")
        
        if absent_symptoms is None:
            absent_symptoms = []
        
        start_time = time.time()
        
        # Use pre-computed probability matrix for instant lookup
        disease_scores = defaultdict(lambda: {
            'probability': 0.0,
            'matching_symptoms': [],
            'orpha_code': '',
            'confidence': 0.0,
            'total_symptoms': 0
        })
        
        # Process present symptoms using pre-computed matrix
        for symptom in present_symptoms:
            if symptom in self.symptom_disease_matrix:
                for disease, prob_info in self.symptom_disease_matrix[symptom].items():
                    disease_scores[disease]['probability'] += prob_info['probability']
                    disease_scores[disease]['matching_symptoms'].append(symptom)
                    disease_scores[disease]['orpha_code'] = prob_info['orpha_code']
                    disease_scores[disease]['confidence'] += prob_info['confidence']
        
        # Add total symptoms count
        for disease in disease_scores.keys():
            if disease in self.disease_symptoms_map:
                disease_scores[disease]['total_symptoms'] = self.disease_symptoms_map[disease]['total_symptoms']
        
        # Apply absent symptom penalties
        for symptom in absent_symptoms:
            if symptom in self.symptom_disease_matrix:
                for disease, prob_info in self.symptom_disease_matrix[symptom].items():
                    if disease in disease_scores:
                        # Reduce probability for absent symptoms
                        penalty = prob_info['probability'] * 0.3
                        disease_scores[disease]['probability'] *= (1 - penalty)
        
        # Calculate final confidence scores
        for disease, scores in disease_scores.items():
            matching_count = len(set(scores['matching_symptoms']))
            total_present = len(present_symptoms)
            scores['confidence_score'] = matching_count / max(total_present, 1)
            scores['matching_symptoms'] = list(set(scores['matching_symptoms']))
        
        # Sort results
        sorted_diseases = sorted(
            disease_scores.items(),
            key=lambda x: (x[1]['probability'], x[1]['confidence_score']),
            reverse=True
        )
        
        # Format results
        results = []
        for disease, scores in sorted_diseases[:top_n]:
            results.append({
                'disorder_name': disease,
                'orpha_code': scores['orpha_code'],
                'probability': min(scores['probability'], 1.0),
                'matching_symptoms': scores['matching_symptoms'],
                'total_symptoms': scores['total_symptoms'],
                'confidence_score': scores['confidence_score']
            })
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'success': True,
            'results': results,
            'total_diseases_evaluated': len(disease_scores),
            'processing_time_ms': processing_time,
            'method': 'local_precomputed'
        }
    
    def get_symptoms(self, search: str = None, limit: int = 50) -> List[str]:
        """Get symptoms with optional search filter"""
        if not self.is_ready:
            return []
        
        if search:
            search_lower = search.lower()
            filtered = [s for s in self.symptoms_list if search_lower in s.lower()]
            return filtered[:limit]
        
        return self.symptoms_list[:limit]


# Global instance
fast_diagnosis = LocalFastDiagnosis()


def initialize_fast_diagnosis(force_rebuild: bool = False) -> bool:
    """Initialize the fast diagnosis system"""
    global fast_diagnosis
    
    # Try to load from cache first
    if not force_rebuild and fast_diagnosis.load_from_cache():
        logger.info("Fast diagnosis ready from cache!")
        return True
    
    # Otherwise, build from CSV
    csv_path = "file/clinical_signs_and_symptoms_in_rare_diseases.csv"
    if os.path.exists(csv_path):
        return fast_diagnosis.load_and_precompute(csv_path)
    else:
        logger.error(f"CSV file not found: {csv_path}")
        return False


def test_performance():
    """Test the performance of the fast diagnosis system"""
    if not fast_diagnosis.is_ready:
        logger.error("Fast diagnosis not ready")
        return
    
    test_cases = [
        ["Seizure"],
        ["Seizure", "Intellectual disability"],
        ["Seizure", "Intellectual disability", "Macrocephaly"],
        ["Seizure", "Intellectual disability", "Macrocephaly", "Spasticity"]
    ]
    
    print("\n🧪 Performance Test Results:")
    print("=" * 50)
    
    for i, symptoms in enumerate(test_cases, 1):
        print(f"\nTest {i}: {len(symptoms)} symptom(s)")
        print(f"Symptoms: {', '.join(symptoms)}")
        
        start_time = time.time()
        result = fast_diagnosis.ultra_fast_diagnosis(symptoms, top_n=5)
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        
        print(f"⏱️  Time: {duration_ms:.1f}ms")
        print(f"📊 Diseases evaluated: {result['total_diseases_evaluated']}")
        
        if result['results']:
            top_result = result['results'][0]
            print(f"🏆 Top result: {top_result['disorder_name']} ({top_result['probability']:.4f})")
        
        if duration_ms < 10:
            print("🚀 Excellent performance!")
        elif duration_ms < 50:
            print("✅ Good performance")
        else:
            print("⚠️  Could be faster")


if __name__ == "__main__":
    print("🚀 Local Fast Diagnosis Setup")
    print("=" * 40)
    
    # Initialize
    if initialize_fast_diagnosis():
        print("✅ Fast diagnosis system ready!")
        
        # Test performance
        test_performance()
        
        print(f"\n📊 System loaded:")
        print(f"  • {len(fast_diagnosis.diseases_list)} diseases")
        print(f"  • {len(fast_diagnosis.symptoms_list)} symptoms")
        print(f"  • Pre-computed probability matrix")
        print(f"  • Cached to disk for future use")
        
    else:
        print("❌ Failed to initialize fast diagnosis system")