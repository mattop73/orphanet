#!/usr/bin/env python3
"""
Bayesian Disease Diagnosis API
A FastAPI application for rare disease diagnosis using Bayesian inference
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
import uvicorn

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Supabase diagnosis with fallback
try:
    from supabase_diagnosis import supabase_diagnosis, initialize_supabase_diagnosis
    logger.info("✅ Using full Supabase client")
except Exception as e:
    logger.warning(f"⚠️ Full Supabase client failed, using simple version: {e}")
    from simple_supabase_diagnosis import simple_supabase_diagnosis as supabase_diagnosis, initialize_simple_supabase_diagnosis as initialize_supabase_diagnosis

# Global variable to store the loaded data
disease_data: Optional[pd.DataFrame] = None
symptoms_list: List[str] = []
diseases_list: List[str] = []


class DiagnosisRequest(BaseModel):
    """Request model for diagnosis endpoint"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "present_symptoms": ["Seizure", "Intellectual disability"],
                "absent_symptoms": ["Fever"],
                "top_n": 10,
                "computation_mode": "fast"
            }
        }
    )
    
    present_symptoms: List[str] = Field(
        ..., 
        description="List of symptoms that are present in the patient",
        min_length=1
    )
    absent_symptoms: List[str] = Field(
        default_factory=list,
        description="List of symptoms that are explicitly absent in the patient"
    )
    top_n: int = Field(
        default=10,
        description="Number of top diagnoses to return",
        ge=1,
        le=50
    )
    computation_mode: str = Field(
        default="fast",
        description="Computation mode: 'fast' (pre-computed) or 'true' (full Bayesian)",
        pattern="^(fast|true)$"
    )


class DiagnosisResult(BaseModel):
    """Response model for diagnosis results"""
    disorder_name: str = Field(..., description="Name of the rare disorder")
    orpha_code: str = Field(..., description="Orphanet disorder code")
    probability: float = Field(..., description="Calculated probability (0-1)")
    matching_symptoms: List[str] = Field(..., description="Symptoms that match the input")
    total_symptoms: int = Field(..., description="Total number of symptoms for this disorder")
    confidence_score: float = Field(..., description="Confidence score based on symptom coverage")


class DiagnosisResponse(BaseModel):
    """Complete response model for diagnosis endpoint"""
    success: bool = Field(..., description="Whether the diagnosis was successful")
    results: List[DiagnosisResult] = Field(..., description="List of diagnosis results")
    total_diseases_evaluated: int = Field(..., description="Total number of diseases evaluated")
    input_symptoms: List[str] = Field(..., description="Input symptoms that were processed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    computation_mode: str = Field(..., description="Computation mode used: 'fast' or 'true'")


class SystemInfo(BaseModel):
    """System information model"""
    total_diseases: int
    total_symptoms: int
    total_associations: int
    api_version: str
    status: str


def load_disease_data() -> bool:
    """Load disease data from CSV file"""
    global disease_data, symptoms_list, diseases_list
    
    csv_file = "clinical_signs_and_symptoms_in_rare_diseases.csv"
    
    try:
        logger.info(f"Loading disease data from {csv_file}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Directory contents: {os.listdir('.')}")
        
        # Try to load from current directory first, then from file/ directory
        if os.path.exists(csv_file):
            data_path = csv_file
            logger.info(f"Found CSV file in current directory: {data_path}")
        elif os.path.exists(f"file/{csv_file}"):
            data_path = f"file/{csv_file}"
            logger.info(f"Found CSV file in file/ directory: {data_path}")
        else:
            # Check if file/ directory exists
            if os.path.exists("file/"):
                logger.info(f"file/ directory contents: {os.listdir('file/')}")
            logger.error(f"CSV file not found: {csv_file}")
            logger.error("Available files in current directory:")
            for f in os.listdir('.'):
                if f.endswith('.csv'):
                    logger.error(f"  - {f}")
            return False
        
        # Load CSV data
        disease_data = pd.read_csv(data_path)
        logger.info(f"Loaded {len(disease_data)} records from CSV")
        
        # Clean the data
        disease_data = disease_data.dropna(subset=['orpha_code', 'disorder_name', 'hpo_term'])
        logger.info(f"After cleaning: {len(disease_data)} records")
        
        # Create frequency mapping
        frequency_mapping = {
            'Very frequent (99-80%)': 0.9,
            'Frequent (79-30%)': 0.55,
            'Occasional (29-5%)': 0.17,
            'Very rare (<5%)': 0.025,
            'Excluded (0%)': 0.0
        }
        
        # Add numeric frequency column
        disease_data['frequency_numeric'] = disease_data['hpo_frequency'].map(
            lambda x: frequency_mapping.get(str(x).strip(), 0.5) if pd.notna(x) else 0.5
        )
        
        # Extract unique symptoms and diseases
        symptoms_list = sorted(disease_data['hpo_term'].dropna().unique().tolist())
        diseases_list = sorted(disease_data['disorder_name'].dropna().unique().tolist())
        
        logger.info(f"Loaded {len(diseases_list)} unique diseases and {len(symptoms_list)} unique symptoms")
        return True
        
    except Exception as e:
        logger.error(f"Error loading disease data: {e}")
        return False


def calculate_true_bayesian_probability(
    disease_name: str,
    present_symptoms: List[str],
    absent_symptoms: List[str] = None,
    all_diseases_data: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Calculate true Bayesian probability using full dataset normalization
    This is more accurate but slower than the fast method
    """
    global disease_data
    
    if absent_symptoms is None:
        absent_symptoms = []
    
    if all_diseases_data is None:
        all_diseases_data = disease_data
    
    # Get disease-specific data
    disease_symptoms = all_diseases_data[all_diseases_data['disorder_name'] == disease_name]
    
    if disease_symptoms.empty:
        return {
            'probability': 0.0,
            'matching_symptoms': [],
            'total_symptoms': 0,
            'confidence_score': 0.0
        }
    
    # Calculate prior probability based on disease prevalence/frequency in dataset
    total_diseases = len(all_diseases_data['disorder_name'].unique())
    disease_associations = len(disease_symptoms)
    total_associations = len(all_diseases_data)
    
    # Prior: How common is this disease in our dataset
    prior = disease_associations / total_associations
    
    # Calculate likelihood P(symptoms|disease)
    symptom_freq_map = dict(zip(disease_symptoms['hpo_term'], disease_symptoms['frequency_numeric']))
    
    likelihood = 1.0
    matching_symptoms = []
    
    # For present symptoms: P(symptom present | disease)
    for symptom in present_symptoms:
        if symptom in symptom_freq_map:
            freq = symptom_freq_map[symptom]
            likelihood *= freq
            matching_symptoms.append(symptom)
        else:
            # Symptom not associated with this disease
            likelihood *= 0.01  # Very small probability for unseen symptoms
    
    # For absent symptoms: P(symptom absent | disease) = 1 - P(symptom present | disease)
    for symptom in absent_symptoms:
        if symptom in symptom_freq_map:
            freq = symptom_freq_map[symptom]
            likelihood *= (1 - freq)
    
    # Calculate evidence P(symptoms) by summing over all diseases
    evidence = 0.0
    for other_disease in all_diseases_data['disorder_name'].unique():
        other_disease_symptoms = all_diseases_data[all_diseases_data['disorder_name'] == other_disease]
        other_symptom_freq_map = dict(zip(other_disease_symptoms['hpo_term'], other_disease_symptoms['frequency_numeric']))
        
        # Prior for this other disease
        other_prior = len(other_disease_symptoms) / total_associations
        
        # Likelihood for this other disease
        other_likelihood = 1.0
        
        for symptom in present_symptoms:
            if symptom in other_symptom_freq_map:
                freq = other_symptom_freq_map[symptom]
                other_likelihood *= freq
            else:
                other_likelihood *= 0.01
        
        for symptom in absent_symptoms:
            if symptom in other_symptom_freq_map:
                freq = other_symptom_freq_map[symptom]
                other_likelihood *= (1 - freq)
        
        evidence += other_prior * other_likelihood
    
    # Avoid division by zero
    if evidence == 0:
        evidence = 1e-10
    
    # True Bayesian posterior: P(disease|symptoms) = P(symptoms|disease) * P(disease) / P(symptoms)
    posterior = (likelihood * prior) / evidence
    
    # Calculate confidence score
    total_disease_symptoms = len(disease_symptoms)
    confidence_score = len(matching_symptoms) / max(len(present_symptoms), 1)
    
    return {
        'probability': min(posterior, 1.0),  # Cap at 1.0
        'matching_symptoms': matching_symptoms,
        'total_symptoms': total_disease_symptoms,
        'confidence_score': confidence_score
    }


def calculate_bayesian_probability(
    disease_name: str,
    present_symptoms: List[str],
    absent_symptoms: List[str] = None
) -> Dict[str, Any]:
    """Calculate Bayesian probability for a specific disease given symptoms"""
    global disease_data
    
    if absent_symptoms is None:
        absent_symptoms = []
    
    # Get disease data (optimized with direct filtering)
    disease_symptoms = disease_data[disease_data['disorder_name'] == disease_name]
    
    if disease_symptoms.empty:
        return {
            'probability': 0.0,
            'matching_symptoms': [],
            'total_symptoms': 0,
            'confidence_score': 0.0
        }
    
    # Pre-calculate symptom frequency mapping for this disease
    symptom_freq_map = dict(zip(disease_symptoms['hpo_term'], disease_symptoms['frequency_numeric']))
    
    # Calculate likelihood more efficiently
    likelihood = 1.0
    matching_symptoms = []
    
    # For present symptoms
    for symptom in present_symptoms:
        if symptom in symptom_freq_map:
            freq = symptom_freq_map[symptom]
            likelihood *= freq
            matching_symptoms.append(symptom)
        else:
            # Symptom not associated with this disease
            likelihood *= 0.05  # Small probability for unseen symptoms
    
    # For absent symptoms (reduce likelihood if symptom is frequent in this disease)
    for symptom in absent_symptoms:
        if symptom in symptom_freq_map:
            freq = symptom_freq_map[symptom]
            # If symptom is frequent in disease but absent in patient, reduce likelihood
            likelihood *= (1 - freq)
    
    # Calculate posterior probability (simplified Bayes with normalization)
    # Use a more reasonable prior based on matching symptoms
    prior = max(0.001, len(matching_symptoms) / len(present_symptoms)) if present_symptoms else 0.001
    posterior = prior * likelihood
    
    # Calculate confidence score based on symptom coverage
    total_disease_symptoms = len(disease_symptoms)
    confidence_score = len(matching_symptoms) / max(len(present_symptoms), 1)
    
    return {
        'probability': min(posterior, 1.0),  # Cap at 1.0
        'matching_symptoms': matching_symptoms,
        'total_symptoms': total_disease_symptoms,
        'confidence_score': confidence_score
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Enhanced Bayesian Disease Diagnosis API...")
    
    # Try Supabase diagnosis first
    if initialize_supabase_diagnosis():
        logger.info("✅ Supabase diagnosis system ready!")
    else:
        # Fallback to regular CSV loading
        logger.info("Falling back to regular CSV loading...")
        success = load_disease_data()
        if not success:
            logger.error("Failed to load disease data")
        else:
            logger.info("Disease data loaded successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enhanced Bayesian Disease Diagnosis API...")


# Initialize FastAPI app
app = FastAPI(
    title="Bayesian Disease Diagnosis API",
    description="API for rare disease diagnosis using Bayesian inference on Orphanet data",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware - more restrictive for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now - can be restricted later
    allow_credentials=False,  # Set to False for wildcard origins
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface with enhanced symptom selection"""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>Bayesian Disease Diagnosis API</h1>
                <p>API is running! Visit <a href="/docs">/docs</a> for API documentation.</p>
                <p>Web interface not found. Please ensure index.html is in the same directory.</p>
                <p><a href="/selector">Try simple selector</a></p>
            </body>
        </html>
        """)

@app.get("/selector", response_class=HTMLResponse)
async def symptom_selector():
    """Serve the simple symptom selector interface"""
    try:
        with open("symptom_selector.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>Symptom Selector Not Found</h1>
                <p>Please ensure symptom_selector.html is in the same directory.</p>
                <p><a href="/full">Try full interface</a> | <a href="/docs">API docs</a></p>
            </body>
        </html>
        """)

@app.get("/full", response_class=HTMLResponse)
async def full_interface():
    """Serve the full complex interface"""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>Full Interface Not Found</h1>
                <p>Please ensure index.html is in the same directory.</p>
                <p><a href="/selector">Back to simple selector</a></p>
            </body>
        </html>
        """)

@app.get("/api", response_model=Dict[str, str])
async def api_info():
    """API information endpoint"""
    return {
        "message": "Bayesian Disease Diagnosis API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "selector": "/selector"
    }


@app.get("/health", response_model=Dict[str, Union[str, bool]])
async def health_check():
    """Health check endpoint"""
    global disease_data
    
    is_healthy = disease_data is not None and not disease_data.empty
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "data_loaded": is_healthy,
        "timestamp": pd.Timestamp.now().isoformat()
    }


@app.get("/info", response_model=SystemInfo)
async def system_info():
    """Get system information"""
    global disease_data, symptoms_list, diseases_list
    
    if disease_data is None:
        raise HTTPException(status_code=503, detail="Disease data not loaded")
    
    return SystemInfo(
        total_diseases=len(diseases_list),
        total_symptoms=len(symptoms_list),
        total_associations=len(disease_data),
        api_version="1.0.0",
        status="operational"
    )


@app.get("/symptoms")
async def get_symptoms(
    search: Optional[str] = Query(None, description="Search term to filter symptoms"),
    limit: int = Query(50, ge=1, le=10000, description="Maximum number of symptoms to return")
):
    """Get list of available symptoms"""
    global symptoms_list
    
    # Try Supabase diagnosis first
    if supabase_diagnosis and supabase_diagnosis.is_ready:
        supabase_symptoms = supabase_diagnosis.get_symptoms(search, limit)
        return {
            "symptoms": supabase_symptoms,
            "total_available": len(supabase_symptoms) if not search else "Unknown",
            "filtered_count": len(supabase_symptoms),
            "search_term": search,
            "method": "supabase"
        }
    
    # Fallback to regular method
    if not symptoms_list:
        raise HTTPException(status_code=503, detail="Disease data not loaded")
    
    filtered_symptoms = symptoms_list
    
    if search:
        search_lower = search.lower()
        filtered_symptoms = [
            symptom for symptom in symptoms_list
            if search_lower in symptom.lower()
        ]
    
    return {
        "symptoms": filtered_symptoms[:limit],
        "total_available": len(symptoms_list),
        "filtered_count": len(filtered_symptoms),
        "search_term": search,
        "method": "regular"
    }


@app.get("/diseases")
async def get_diseases(
    search: Optional[str] = Query(None, description="Search term to filter diseases"),
    limit: int = Query(50, ge=1, le=10000, description="Maximum number of diseases to return")
):
    """Get list of available diseases"""
    global diseases_list
    
    if not diseases_list:
        raise HTTPException(status_code=503, detail="Disease data not loaded")
    
    filtered_diseases = diseases_list
    
    if search:
        search_lower = search.lower()
        filtered_diseases = [
            disease for disease in diseases_list
            if search_lower in disease.lower()
        ]
    
    return {
        "diseases": filtered_diseases[:limit],
        "total_available": len(diseases_list),
        "filtered_count": len(filtered_diseases),
        "search_term": search
    }


@app.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose_disease(request: DiagnosisRequest):
    """
    Perform Bayesian disease diagnosis with choice between fast and true computation modes
    - fast: Uses pre-computed probabilities (faster, ~100ms)
    - true: Full Bayesian computation with proper normalization (slower, ~5-30s)
    """
    global disease_data, diseases_list, symptoms_list
    
    import time
    start_time = time.time()
    
    logger.info(f"🎯 Diagnosis request: mode={request.computation_mode}, symptoms={request.present_symptoms}")
    
    try:
        # True Bayesian mode - use Supabase full computation
        if request.computation_mode == "true":
            logger.info("🧮 Using TRUE Bayesian computation with Supabase (full normalization)")
            
            if not supabase_diagnosis or not supabase_diagnosis.is_ready:
                logger.error("Supabase diagnosis not ready, falling back to CSV method")
                # Fallback to CSV-based true Bayesian computation
                if disease_data is None or not diseases_list:
                    raise HTTPException(status_code=503, detail="Neither Supabase nor CSV data available")
                
                # Use CSV-based true Bayesian computation
            valid_present_symptoms = [
                symptom for symptom in request.present_symptoms
                    if symptom in symptoms_list
            ]
            
            if not valid_present_symptoms:
                raise HTTPException(
                    status_code=400,
                    detail="None of the provided symptoms are found in the database"
                )
            
                valid_absent_symptoms = [
                    symptom for symptom in request.absent_symptoms
                    if symptom in symptoms_list
                ]
                
                # Ultra-fast simplified Bayesian computation (CSV fallback)
                results = []
                # Limit to diseases that have at least one matching symptom for efficiency
                relevant_diseases = set()
                for symptom in valid_present_symptoms:
                    matching_diseases = disease_data[disease_data["hpo_term"] == symptom]["disorder_name"].unique()
                    relevant_diseases.update(matching_diseases)
                
                # Limit to top 5 most relevant diseases to prevent timeout
                relevant_diseases = list(relevant_diseases)[:5]
                logger.info(f"Computing for {len(relevant_diseases)} relevant diseases (CSV fallback - ultra fast)")
                
                # Fast scoring without full Bayesian normalization
                for i, disease in enumerate(relevant_diseases):
                    try:
                        # Get disease-specific data
                        disease_symptoms = disease_data[disease_data['disorder_name'] == disease]
                        
                        if disease_symptoms.empty:
                            continue
                        
                        # Create symptom frequency map
                        symptom_freq_map = dict(zip(disease_symptoms['hpo_term'], disease_symptoms['frequency_numeric']))
                        
                        # Calculate simple score based on matching symptoms
                        score = 0.0
                        matching_symptoms = []
                        
                        # Score present symptoms
                        for symptom in valid_present_symptoms:
                            if symptom in symptom_freq_map:
                                freq = symptom_freq_map[symptom]
                                score += freq  # Add frequency directly
                                matching_symptoms.append(symptom)
                        
                        # Penalize for absent symptoms that should be present
                        for symptom in valid_absent_symptoms:
                            if symptom in symptom_freq_map:
                                freq = symptom_freq_map[symptom]
                                score -= freq * 0.5  # Subtract half the frequency
                        
                        # Normalize by number of present symptoms to get average
                        if len(valid_present_symptoms) > 0:
                            normalized_score = score / len(valid_present_symptoms)
                        else:
                            normalized_score = 0.0
                        
                        # Only include if we have matches
                        if len(matching_symptoms) > 0:
                            disease_info = disease_symptoms.iloc[0]
                            
                            results.append(DiagnosisResult(
                                disorder_name=disease,
                                orpha_code=str(disease_info['orpha_code']),
                                probability=max(0.0, min(1.0, normalized_score)),  # Clamp to [0,1]
                                matching_symptoms=matching_symptoms,
                                total_symptoms=len(disease_symptoms),
                                confidence_score=len(matching_symptoms) / len(valid_present_symptoms) if valid_present_symptoms else 0.0
                            ))
                            
                    except Exception as e:
                        logger.warning(f"Error calculating for {disease}: {e}")
                        continue
                
                results.sort(key=lambda x: x.probability, reverse=True)
                top_results = results[:request.top_n]
                
                processing_time = (time.time() - start_time) * 1000
                
                return DiagnosisResponse(
                    success=True,
                    results=top_results,
                    total_diseases_evaluated=len(relevant_diseases),
                    input_symptoms=valid_present_symptoms,
                    processing_time_ms=processing_time,
                    computation_mode="true"
                )
            
            try:
                # Use Supabase true Bayesian diagnosis
                result = supabase_diagnosis.true_bayesian_diagnosis(
                    request.present_symptoms,
                    request.absent_symptoms,
                    request.top_n
                )
            except Exception as e:
                logger.error(f"Supabase true Bayesian failed: {e}")
                raise HTTPException(status_code=500, detail=f"True Bayesian computation failed: {str(e)}")
            
            # Convert to API format
            api_results = []
            for res in result['results']:
                api_results.append(DiagnosisResult(
                    disorder_name=res['disorder_name'],
                    orpha_code=res['orpha_code'],
                    probability=res['probability'],
                    matching_symptoms=res['matching_symptoms'],
                    total_symptoms=res['total_symptoms'],
                    confidence_score=res['confidence_score']
                ))
            
            processing_time = result['processing_time_ms']
            
            logger.info(f"🧮 True Bayesian computation completed in {processing_time:.1f}ms")
            
            return DiagnosisResponse(
                success=True,
                results=api_results,
                total_diseases_evaluated=result['total_diseases_evaluated'],
                input_symptoms=request.present_symptoms,
                processing_time_ms=processing_time,
                computation_mode="true"
            )
        
        # Fast mode - use Supabase fast/pre-computed diagnosis
        elif supabase_diagnosis and supabase_diagnosis.is_ready:
            logger.info(f"🚀 Using FAST mode (pre-computed/optimized) for symptoms: {request.present_symptoms}")
            
            # Use Supabase fast diagnosis (pre-computed probabilities)
            result = supabase_diagnosis.fast_diagnosis(
                request.present_symptoms,
                request.absent_symptoms,
                request.top_n
            )
            
            # Convert to API format
            api_results = []
            for res in result['results']:
                api_results.append(DiagnosisResult(
                    disorder_name=res['disorder_name'],
                    orpha_code=res['orpha_code'],
                    probability=res['probability'],
                    matching_symptoms=res['matching_symptoms'],
                    total_symptoms=res['total_symptoms'],
                    confidence_score=res['confidence_score']
                ))
            
            processing_time = result['processing_time_ms']
            
            logger.info(f"⚡ FAST mode (pre-computed) completed in {processing_time:.1f}ms")
            
            return DiagnosisResponse(
                success=True,
                results=api_results,
                total_diseases_evaluated=result['total_diseases_evaluated'],
                input_symptoms=request.present_symptoms,
                processing_time_ms=processing_time,
                computation_mode="fast"
            )
        
        # Fallback to regular diagnosis
        else:
            logger.info("Using regular diagnosis method")
            
            if disease_data is None or not diseases_list:
                raise HTTPException(status_code=503, detail="Disease data not loaded")
            
            # Validate symptoms exist in our dataset
            valid_present_symptoms = [
                symptom for symptom in request.present_symptoms
                if symptom in symptoms_list
            ]
            
            if not valid_present_symptoms:
                raise HTTPException(
                    status_code=400,
                    detail="None of the provided symptoms are found in the database"
                )
            
            valid_absent_symptoms = [
                symptom for symptom in request.absent_symptoms
                if symptom in symptoms_list
            ]
            
            # Pre-filter diseases that have at least one matching symptom for better performance
            logger.info(f"Filtering diseases with matching symptoms from {valid_present_symptoms}")
            
            # Get diseases that have at least one of the present symptoms
            relevant_diseases = set()
            for symptom in valid_present_symptoms:
                matching_diseases = disease_data[disease_data['hpo_term'] == symptom]['disorder_name'].unique()
                relevant_diseases.update(matching_diseases)
            
            # If no diseases match any symptoms, check all diseases (fallback)
            if not relevant_diseases:
                relevant_diseases = set(diseases_list[:100])  # Limit to top 100 for performance
                logger.warning("No diseases found with matching symptoms, checking top 100 diseases")
            else:
                logger.info(f"Found {len(relevant_diseases)} diseases with matching symptoms")
            
            # Calculate probabilities only for relevant diseases
            results = []
            
            for disease in relevant_diseases:
                try:
                    result = calculate_bayesian_probability(
                        disease,
                        valid_present_symptoms,
                        valid_absent_symptoms
                    )
                    
                    if result['probability'] > 0 or len(result['matching_symptoms']) > 0:
                        # Get orpha code for this disease
                        disease_info = disease_data[disease_data['disorder_name'] == disease].iloc[0]
                        
                        results.append(DiagnosisResult(
                            disorder_name=disease,
                            orpha_code=str(disease_info['orpha_code']),
                            probability=result['probability'],
                            matching_symptoms=result['matching_symptoms'],
                            total_symptoms=result['total_symptoms'],
                            confidence_score=result['confidence_score']
                        ))
                except Exception as e:
                    logger.warning(f"Error calculating probability for {disease}: {e}")
                    continue
            
            logger.info(f"Calculated probabilities for {len(results)} diseases")
            
            # Sort by probability and confidence score
            results.sort(key=lambda x: (x.probability, x.confidence_score), reverse=True)
            
            # Return top N results
            top_results = results[:request.top_n]
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return DiagnosisResponse(
                success=True,
                results=top_results,
                total_diseases_evaluated=len(results),
                input_symptoms=valid_present_symptoms,
                processing_time_ms=processing_time,
                computation_mode="fast"
            )
        
    except Exception as e:
        logger.error(f"Error in diagnosis: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    """Upload a new dataset CSV file"""
    global disease_data, symptoms_list, diseases_list
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Save uploaded file
        content = await file.read()
        with open("clinical_signs_and_symptoms_in_rare_diseases.csv", "wb") as f:
            f.write(content)
        
        # Reload data
        success = load_disease_data()
        
        if success:
            return {
                "success": True,
                "message": "Dataset uploaded and loaded successfully",
                "total_diseases": len(diseases_list),
                "total_symptoms": len(symptoms_list)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to load uploaded dataset")
            
    except Exception as e:
        logger.error(f"Error uploading data: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


if __name__ == "__main__":
    # Configuration from environment variables (Railway uses PORT)
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))  # Railway uses PORT
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"🚀 Railway: Starting Bayesian Disease Diagnosis API...")
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    logger.info(f"🌐 Starting server on {host}:{port}")
    
    uvicorn.run(
        app,  # Pass app directly instead of string
        host=host,
        port=port,
        log_level=log_level,
        reload=False
    )