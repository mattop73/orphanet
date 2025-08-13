#!/usr/bin/env python3
"""
Demo the Simple Symptom Selector
"""

import subprocess
import time
import webbrowser
import signal
import sys

def main():
    """Demo the symptom selector"""
    print("🔍 Simple Symptom Selector Demo")
    print("=" * 40)
    print()
    print("This will:")
    print("1. Start the API server")
    print("2. Open the symptom selector in your browser")
    print("3. Show you how to use it")
    print()
    print("🚀 Starting server...")
    
    try:
        # Start the server
        server = subprocess.Popen([
            'python3', 'main.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        print("✅ Server started!")
        print("🌐 Opening browser...")
        
        # Open browser
        webbrowser.open('http://localhost:8000/selector')
        
        print()
        print("🎯 How to use the Symptom Selector:")
        print("=" * 40)
        print("1. TYPE part of a symptom name:")
        print("   • 'seiz' → shows 'Seizure'")
        print("   • 'intel' → shows 'Intellectual disability'")
        print("   • 'pain' → shows all pain symptoms")
        print()
        print("2. CLICK on any suggestion to select it")
        print("   • Selected symptoms appear as green tags")
        print("   • Click × on tags to remove them")
        print()
        print("3. CLICK 'Get Diagnosis' to analyze symptoms")
        print("   • Shows disease probabilities")
        print("   • Lists matching symptoms")
        print("   • Displays confidence scores")
        print()
        print("📊 Example searches to try:")
        print("   • seizure")
        print("   • intellectual")
        print("   • muscle")
        print("   • fever")
        print("   • headache")
        print("   • weakness")
        print()
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 40)
        
        # Wait for user to stop
        try:
            server.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            server.terminate()
            server.wait()
            print("✅ Server stopped")
            
    except FileNotFoundError:
        print("❌ Error: main.py not found")
        print("   Make sure you're in the correct directory")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()