#!/usr/bin/env python3
"""
Start Ultra-Fast Diagnosis Interface with Supabase
"""

import os
import sys
import time
import webbrowser
import signal
from threading import Timer

def open_browser():
    """Open the ultra-fast interface in the default browser"""
    time.sleep(3)  # Wait a bit longer for Supabase connection
    webbrowser.open('http://localhost:8001')
    print("🌐 Ultra-fast interface opened in your browser")
    print("🔗 URL: http://localhost:8001")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\n🛑 Shutting down ultra-fast server...')
    sys.exit(0)

def main():
    """Main function to start the ultra-fast server"""
    print("⚡ Starting Ultra-Fast Bayesian Disease Diagnosis...")
    print("=" * 60)
    
    # Check if required files exist
    if not os.path.exists("main_fast.py"):
        print("❌ Error: main_fast.py not found")
        return
    
    if not os.path.exists("index.html"):
        print("❌ Error: index.html not found")
        return
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start browser opener timer
    Timer(3.0, open_browser).start()
    
    print("🚀 Initializing Supabase connection...")
    print("📊 Loading pre-computed probabilities...")
    print("🌐 Starting ultra-fast server on http://localhost:8001")
    print("📖 API documentation: http://localhost:8001/docs")
    print("\n💡 Ultra-Fast Features:")
    print("   ⚡ ~100ms diagnosis time (vs 5-10 seconds)")
    print("   🗄️  Pre-computed Supabase probabilities")
    print("   🔍 Instant symptom search from cached data")
    print("   📊 Optimized database queries with indexes")
    print("   🎯 Smart disease filtering and ranking")
    print("\n🔍 How to use:")
    print("   1. Type symptom names for instant suggestions")
    print("   2. Click to select symptoms (Present/Absent)")
    print("   3. Click 'Diagnose Disease' for ultra-fast results")
    print("   4. Get results in ~100ms with visual charts")
    print("\n⚠️  Note: Requires Supabase setup with pre-computed data")
    print("   Run 'python3 fast_diagnosis_setup.py' first if needed")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        import uvicorn
        uvicorn.run(
            "main_fast:app",
            host="0.0.0.0",
            port=8001,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Ultra-fast server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Run setup first: python3 fast_diagnosis_setup.py")
        print("   2. Check Supabase connection")
        print("   3. Verify requirements: pip install supabase")

if __name__ == "__main__":
    main()