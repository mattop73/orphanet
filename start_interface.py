#!/usr/bin/env python3
"""
Start the Bayesian Disease Diagnosis API with Web Interface
"""

import os
import sys
import time
import webbrowser
import subprocess
import signal
from threading import Timer

def open_browser():
    """Open the web interface in the default browser"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:8000')
    print("🌐 Web interface opened in your default browser")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\n🛑 Shutting down server...')
    sys.exit(0)

def main():
    """Main function to start the server and open browser"""
    print("🚀 Starting Bayesian Disease Diagnosis API with Enhanced Interface...")
    print("=" * 70)
    
    # Check if required files exist
    if not os.path.exists("index.html"):
        print("❌ Error: index.html not found in current directory")
        return
    
    if not os.path.exists("file/clinical_signs_and_symptoms_in_rare_diseases.csv"):
        print("❌ Error: CSV data file not found")
        print("   Please ensure 'file/clinical_signs_and_symptoms_in_rare_diseases.csv' exists")
        return
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start browser opener timer
    Timer(2.0, open_browser).start()
    
    print("📊 Loading disease data...")
    print("🌐 Starting web server on http://localhost:8000")
    print("📖 API documentation available at http://localhost:8000/docs")
    print("\n💡 Enhanced Features:")
    print("   • Smart symptom search with auto-suggestions")
    print("   • One-click symptom selection from 8,595 symptoms")
    print("   • Present and absent symptom categorization")
    print("   • Bayesian disease diagnosis with probabilities")
    print("   • Visual charts and probability rankings")
    print("   • Confidence scores and matching details")
    print("\n🔍 How to use:")
    print("   1. Type part of symptom name (e.g., 'seiz', 'intel', 'macro')")
    print("   2. Click suggestions to add symptoms instantly")
    print("   3. Toggle between 'Present' and 'Absent' symptoms")
    print("   4. Click 'Diagnose Disease' to see results with charts")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 70)
    
    try:
        # Start the FastAPI server
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("💡 Make sure you have installed the requirements:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main()