#!/usr/bin/env python3
"""
Ultra-Fast Bayesian Disease Diagnosis API using Supabase
Pre-computed probabilities for instant diagnosis
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from collections import defaultdict
import time

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, ConfigDict
import uvicorn
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global Supabase client
supabase_client: Optional[Client] = None
symptoms_cache: List[str] = []


class DiagnosisRequest(BaseModel):
    """Request model for diagnosis endpoint"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "present_symptoms": ["Seizure", "Intellectual disability"],
                "absent_symptoms": ["Fever"],
                "top_n": 10
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
    method: str = Field(..., description="Diagnosis method used")


class SystemInfo(BaseModel):
    """System information model"""
    total_diseases: int
    total_symptoms: int
    total_associations: int
    api_version: str
    status: str
    method: str


async def initialize_supabase():
    """Initialize Supabase connection and cache symptoms"""
    global supabase_client, symptoms_cache
    
    try:
        # Supabase configuration
        SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ecrcdeztnbciybqkwkpf.supabase.co')
        SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjcmNkZXp0bmJjaXlicWt3a3BmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NDIwOTQsImV4cCI6MjA3MDUxODA5NH0.TPT6CdwI3lgBeh-V_X-a8_H4m3YFK0lLg31eWM0woho')
        
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Connected to Supabase")
        
        # Cache all symptoms for fast search
        logger.info("Loading symptoms cache...")
        result = supabase_client.table('fast_symptoms').select('term').execute()
        
        if result.data:
            symptoms_cache = [row['term'] for row in result.data]
            logger.info(f"Cached {len(symptoms_cache)} symptoms")
        else:
            logger.warning("No symptoms found in fast_symptoms table")
            # Fallback to CSV loading if needed
            await fallback_csv_loading()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
        # Fallback to CSV loading
        return await fallback_csv_loading()


async def fallback_csv_loading():
    """Fallback to CSV loading if Supabase tables don't exist"""
    global symptoms_cache
    
    try:
        logger.info("Falling back to CSV data loading...")
        import pandas as pd
        
        csv_file = "file/clinical_signs_and_symptoms_in_rare_diseases.csv"
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            df = df.dropna(subset=['hpo_term'])
            symptoms_cache = sorted(df['hpo_term'].unique().tolist())
            logger.info(f"Loaded {len(symptoms_cache)} symptoms from CSV")
            return True
        else:
            logger.error("CSV file not found")
            return False
            
    except Exception as e:
        logger.error(f"Fallback CSV loading failed: {e}")
        return False


async def fast_diagnosis(
    present_symptoms: List[str],
    absent_symptoms: List[str] = None,
    top_n: int = 10
) -> Dict[str, Any]:
    """Ultra-fast diagnosis using pre-computed Supabase probabilities"""
    global supabase_client
    
    if absent_symptoms is None:
        absent_symptoms = []
    
    start_time = time.time()
    
    try:
        # Step 1: Get pre-computed probabilities for present symptoms
        logger.info(f"Fast diagnosis for symptoms: {present_symptoms}")
        
        disease_scores = defaultdict(lambda: {
            'probability': 0.0,
            'matching_symptoms': [],
            'total_symptoms': 0,
            'orpha_code': '',
            'confidence': 0.0
        })
        
        # Query pre-computed probabilities for each present symptom
        for symptom in present_symptoms:
            result = supabase_client.table('symptom_disease_probs').select(
                'disorder_name, orpha_code, probability, confidence'
            ).eq('symptom_term', symptom).order('probability', desc=True).execute()
            
            if result.data:
                for row in result.data:
                    disease = row['disorder_name']
                    disease_scores[disease]['probability'] += row['probability']
                    disease_scores[disease]['matching_symptoms'].append(symptom)
                    disease_scores[disease]['orpha_code'] = row['orpha_code']
                    disease_scores[disease]['confidence'] += row['confidence']
        
        # Step 2: Get total symptoms for each disease
        for disease in disease_scores.keys():
            try:
                result = supabase_client.table('fast_disorders').select(
                    'total_symptoms'
                ).eq('name', disease).execute()
                
                if result.data:
                    disease_scores[disease]['total_symptoms'] = result.data[0]['total_symptoms']
            except:
                disease_scores[disease]['total_symptoms'] = len(disease_scores[disease]['matching_symptoms'])
        
        # Step 3: Apply absent symptom penalties (if any)
        if absent_symptoms:
            for symptom in absent_symptoms:
                result = supabase_client.table('symptom_disease_probs').select(
                    'disorder_name, probability'
                ).eq('symptom_term', symptom).execute()
                
                if result.data:
                    for row in result.data:
                        disease = row['disorder_name']
                        if disease in disease_scores:
                            # Reduce probability if absent symptom is frequent in disease
                            penalty = row['probability'] * 0.5
                            disease_scores[disease]['probability'] *= (1 - penalty)
        
        # Step 4: Calculate final confidence scores
        for disease, scores in disease_scores.items():
            matching_count = len(scores['matching_symptoms'])
            total_present = len(present_symptoms)
            scores['confidence_score'] = matching_count / max(total_present, 1)
        
        # Step 5: Sort and format results
        sorted_diseases = sorted(
            disease_scores.items(),
            key=lambda x: (x[1]['probability'], x[1]['confidence_score']),
            reverse=True
        )
        
        results = []
        for disease, scores in sorted_diseases[:top_n]:
            results.append(DiagnosisResult(
                disorder_name=disease,
                orpha_code=scores['orpha_code'],
                probability=min(scores['probability'], 1.0),
                matching_symptoms=list(set(scores['matching_symptoms'])),
                total_symptoms=scores['total_symptoms'],
                confidence_score=scores['confidence_score']
            ))
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"Fast diagnosis completed in {processing_time:.2f}ms")
        
        return {
            'success': True,
            'results': results,
            'total_diseases_evaluated': len(disease_scores),
            'processing_time_ms': processing_time,
            'method': 'supabase_precomputed'
        }
        
    except Exception as e:
        logger.error(f"Fast diagnosis failed: {e}")
        # Fallback to slower method if needed
        raise HTTPException(status_code=500, detail=f"Fast diagnosis failed: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Ultra-Fast Bayesian Disease Diagnosis API...")
    success = await initialize_supabase()
    if success:
        logger.info("Supabase connection and caching completed")
    else:
        logger.error("Failed to initialize properly")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ultra-Fast Bayesian Disease Diagnosis API...")


# Initialize FastAPI app
app = FastAPI(
    title="Ultra-Fast Bayesian Disease Diagnosis API",
    description="Lightning-fast rare disease diagnosis using pre-computed Supabase probabilities",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>Ultra-Fast Bayesian Disease Diagnosis API</h1>
                <p>⚡ Lightning-fast diagnosis using pre-computed Supabase probabilities</p>
                <p>📖 API Documentation: <a href="/docs">/docs</a></p>
                <p>🔍 Simple Selector: <a href="/selector">Try it</a></p>
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
                <p><a href="/">Back to main interface</a></p>
            </body>
        </html>
        """)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global supabase_client, symptoms_cache
    
    is_healthy = supabase_client is not None and len(symptoms_cache) > 0
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "supabase_connected": supabase_client is not None,
        "symptoms_cached": len(symptoms_cache),
        "method": "supabase_precomputed",
        "timestamp": time.time()
    }


@app.get("/info", response_model=SystemInfo)
async def system_info():
    """Get system information"""
    global supabase_client, symptoms_cache
    
    if supabase_client is None:
        raise HTTPException(status_code=503, detail="Supabase not connected")
    
    try:
        # Get counts from Supabase
        disorders_result = supabase_client.table('fast_disorders').select('count').execute()
        symptoms_result = supabase_client.table('fast_symptoms').select('count').execute()
        associations_result = supabase_client.table('symptom_disease_probs').select('count').execute()
        
        return SystemInfo(
            total_diseases=len(disorders_result.data) if disorders_result.data else 0,
            total_symptoms=len(symptoms_cache),
            total_associations=len(associations_result.data) if associations_result.data else 0,
            api_version="2.0.0",
            status="operational",
            method="supabase_precomputed"
        )
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return SystemInfo(
            total_diseases=0,
            total_symptoms=len(symptoms_cache),
            total_associations=0,
            api_version="2.0.0",
            status="degraded",
            method="supabase_precomputed"
        )


@app.get("/symptoms")
async def get_symptoms(
    search: Optional[str] = Query(None, description="Search term to filter symptoms"),
    limit: int = Query(50, ge=1, le=10000, description="Maximum number of symptoms to return")
):
    """Get list of available symptoms"""
    global symptoms_cache
    
    if not symptoms_cache:
        raise HTTPException(status_code=503, detail="Symptoms not loaded")
    
    filtered_symptoms = symptoms_cache
    
    if search:
        search_lower = search.lower()
        filtered_symptoms = [
            symptom for symptom in symptoms_cache
            if search_lower in symptom.lower()
        ]
    
    return {
        "symptoms": filtered_symptoms[:limit],
        "total_available": len(symptoms_cache),
        "filtered_count": len(filtered_symptoms),
        "search_term": search,
        "method": "cached"
    }


@app.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose_disease(request: DiagnosisRequest):
    """
    Perform ultra-fast Bayesian disease diagnosis using pre-computed probabilities
    """
    global symptoms_cache
    
    if not symptoms_cache:
        raise HTTPException(status_code=503, detail="System not ready")
    
    try:
        # Validate symptoms exist in our dataset
        valid_present_symptoms = [
            symptom for symptom in request.present_symptoms
            if symptom in symptoms_cache
        ]
        
        if not valid_present_symptoms:
            raise HTTPException(
                status_code=400,
                detail="None of the provided symptoms are found in the database"
            )
        
        valid_absent_symptoms = [
            symptom for symptom in request.absent_symptoms
            if symptom in symptoms_cache
        ]
        
        # Perform ultra-fast diagnosis
        result = await fast_diagnosis(
            valid_present_symptoms,
            valid_absent_symptoms,
            request.top_n
        )
        
        return DiagnosisResponse(
            success=result['success'],
            results=result['results'],
            total_diseases_evaluated=result['total_diseases_evaluated'],
            input_symptoms=valid_present_symptoms,
            processing_time_ms=result['processing_time_ms'],
            method=result['method']
        )
        
    except Exception as e:
        logger.error(f"Error in diagnosis: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8001"))  # Different port to avoid conflicts
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting ultra-fast server on {host}:{port}")
    
    uvicorn.run(
        "main_fast:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False
    )