#!/usr/bin/env python3
"""
Railway Deployment Entry Point for Bayesian Disease Diagnosis API
"""

import os
import sys
import uvicorn

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function for Railway deployment"""
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Railway: Starting Bayesian Disease Diagnosis API...")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🌐 Starting server on port {port}")
    
    # Import the FastAPI app
    from main import app
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()