#!/usr/bin/env python3
"""
Start the Simple Symptom Selector Interface
"""

import os
import sys
import time
import webbrowser
import signal
from threading import Timer

def open_browser():
    """Open the symptom selector in the default browser"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:8000/selector')
    print("🌐 Simple symptom selector opened in your browser")
    print("🔗 URL: http://localhost:8000/selector")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\n🛑 Shutting down server...')
    sys.exit(0)

def main():
    """Main function to start the server"""
    print("🔍 Starting Simple Symptom Selector...")
    print("=" * 50)
    
    # Check if required files exist
    if not os.path.exists("symptom_selector.html"):
        print("❌ Error: symptom_selector.html not found")
        return
    
    if not os.path.exists("file/clinical_signs_and_symptoms_in_rare_diseases.csv"):
        print("❌ Error: CSV data file not found")
        return
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start browser opener timer
    Timer(2.0, open_browser).start()
    
    print("📊 Loading symptom data...")
    print("🌐 Starting server on http://localhost:8000")
    print("🔍 Symptom selector: http://localhost:8000/selector")
    print("\n💡 How to use:")
    print("   1. Type part of a symptom name")
    print("   2. Click on suggestions to select")
    print("   3. Click 'Get Diagnosis' to analyze")
    print("\n🛑 Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()