#!/usr/bin/env python3
"""
Railway-Ready Bayesian Disease Diagnosis API with Supabase
Ultra-fast diagnosis using pre-computed probabilities in Supabase
"""

import os
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Import Supabase fast diagnosis
from supabase_fast_diagnosis import supabase_diagnosis, initialize_supabase_diagnosis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models
class DiagnosisRequest(BaseModel):
    """Request model for disease diagnosis"""
    present_symptoms: List[str] = Field(..., description="List of symptoms that are present")
    absent_symptoms: List[str] = Field(default=[], description="List of symptoms that are absent")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of top results to return")


class DiagnosisResult(BaseModel):
    """Individual diagnosis result"""
    disorder_name: str
    orpha_code: str
    probability: float
    matching_symptoms: List[str]
    total_symptoms: int
    confidence_score: float


class DiagnosisResponse(BaseModel):
    """Response model for diagnosis results"""
    success: bool
    results: List[DiagnosisResult]
    total_diseases_evaluated: int
    input_symptoms: List[str]
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    supabase_connected: bool
    total_symptoms: int
    total_diseases: int
    api_version: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Railway Bayesian Disease Diagnosis API...")
    
    # Initialize Supabase diagnosis
    if initialize_supabase_diagnosis():
        logger.info("✅ Supabase fast diagnosis system ready!")
    else:
        logger.warning("⚠️  Supabase system not ready - check configuration")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Railway API...")


# Initialize FastAPI app
app = FastAPI(
    title="Railway Bayesian Disease Diagnosis API",
    description="Ultra-fast disease diagnosis using Supabase and Bayesian inference",
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

# Mount static files
if os.path.exists("public"):
    app.mount("/static", StaticFiles(directory="public"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main diagnosis interface"""
    try:
        with open("index.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Railway Disease Diagnosis API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
                a { color: #007bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Railway Disease Diagnosis API</h1>
                <div class="status success">
                    ✅ API is running successfully on Railway!
                </div>
                <div class="status info">
                    🔗 <strong>API Documentation:</strong> <a href="/docs">/docs</a><br>
                    🔗 <strong>Health Check:</strong> <a href="/health">/health</a><br>
                    🔗 <strong>Symptoms:</strong> <a href="/symptoms?limit=10">/symptoms</a><br>
                    🔗 <strong>Diseases:</strong> <a href="/diseases?limit=10">/diseases</a>
                </div>
                <p>This API provides ultra-fast Bayesian disease diagnosis using Supabase pre-computed probabilities.</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>⚡ Ultra-fast diagnosis (milliseconds)</li>
                    <li>🏥 4,281+ rare diseases</li>
                    <li>🔬 8,595+ medical symptoms</li>
                    <li>📊 Bayesian probability calculations</li>
                    <li>☁️ Supabase-powered for scalability</li>
                </ul>
            </div>
        </body>
        </html>
        """)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        supabase_connected = supabase_diagnosis.test_connection()
        
        # Get counts
        symptoms = supabase_diagnosis.get_symptoms(limit=1)
        diseases = supabase_diagnosis.get_diseases(limit=1)
        
        return HealthResponse(
            status="healthy" if supabase_connected else "degraded",
            message="Railway API operational" if supabase_connected else "API running but Supabase issues",
            supabase_connected=supabase_connected,
            total_symptoms=len(symptoms) if symptoms else 0,
            total_diseases=len(diseases) if diseases else 0,
            api_version="2.0.0"
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            message=f"Error: {str(e)}",
            supabase_connected=False,
            total_symptoms=0,
            total_diseases=0,
            api_version="2.0.0"
        )


@app.get("/symptoms")
async def get_symptoms(
    search: Optional[str] = Query(None, description="Search term to filter symptoms"),
    limit: int = Query(50, ge=1, le=10000, description="Maximum number of symptoms to return")
):
    """Get list of available symptoms from Supabase"""
    try:
        symptoms = supabase_diagnosis.get_symptoms(search, limit)
        
        return {
            "symptoms": symptoms,
            "total_returned": len(symptoms),
            "search_term": search,
            "method": "supabase",
            "limit_used": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting symptoms: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get symptoms: {str(e)}")


@app.get("/diseases")
async def get_diseases(
    search: Optional[str] = Query(None, description="Search term to filter diseases"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of diseases to return")
):
    """Get list of available diseases from Supabase"""
    try:
        diseases = supabase_diagnosis.get_diseases(search, limit)
        
        return {
            "diseases": [d['disease_name'] for d in diseases],
            "diseases_with_info": diseases,
            "total_returned": len(diseases),
            "search_term": search,
            "method": "supabase",
            "limit_used": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting diseases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get diseases: {str(e)}")


@app.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose_disease(request: DiagnosisRequest):
    """
    Perform ultra-fast Bayesian disease diagnosis using Supabase pre-computed probabilities
    """
    try:
        logger.info(f"🚀 Railway diagnosis request: {len(request.present_symptoms)} present, {len(request.absent_symptoms)} absent symptoms")
        
        # Validate input
        if not request.present_symptoms:
            raise HTTPException(
                status_code=400,
                detail="At least one present symptom is required"
            )
        
        # Use Supabase ultra-fast diagnosis
        result = supabase_diagnosis.ultra_fast_diagnosis(
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
        
        logger.info(f"⚡ Railway diagnosis completed in {result['processing_time_ms']:.1f}ms")
        
        return DiagnosisResponse(
            success=True,
            results=api_results,
            total_diseases_evaluated=result['total_diseases_evaluated'],
            input_symptoms=request.present_symptoms,
            processing_time_ms=result['processing_time_ms']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Railway diagnosis error: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


@app.get("/info")
async def get_api_info():
    """Get API information and statistics"""
    try:
        # Get some basic stats
        sample_symptoms = supabase_diagnosis.get_symptoms(limit=5)
        sample_diseases = supabase_diagnosis.get_diseases(limit=3)
        
        return {
            "api_name": "Railway Bayesian Disease Diagnosis API",
            "version": "2.0.0",
            "description": "Ultra-fast disease diagnosis using Supabase and Bayesian inference",
            "features": [
                "Ultra-fast diagnosis (milliseconds)",
                "4,281+ rare diseases from Orphanet",
                "8,595+ medical symptoms (HPO terms)",
                "Bayesian probability calculations",
                "Supabase-powered for scalability",
                "Railway deployment ready"
            ],
            "endpoints": {
                "GET /": "Main interface",
                "GET /health": "Health check",
                "GET /symptoms": "Get symptoms list",
                "GET /diseases": "Get diseases list",
                "POST /diagnose": "Perform diagnosis",
                "GET /info": "API information",
                "GET /docs": "API documentation"
            },
            "sample_symptoms": sample_symptoms,
            "sample_diseases": [d['disease_name'] for d in sample_diseases],
            "powered_by": ["FastAPI", "Supabase", "Railway", "Orphanet", "HPO"],
            "supabase_connected": supabase_diagnosis.test_connection()
        }
        
    except Exception as e:
        logger.error(f"Error getting API info: {e}")
        return {
            "api_name": "Railway Bayesian Disease Diagnosis API",
            "version": "2.0.0",
            "error": str(e),
            "supabase_connected": False
        }


# Railway deployment entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Railway API on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )