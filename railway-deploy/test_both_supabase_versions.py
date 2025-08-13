#!/usr/bin/env python3
"""
Test both Supabase client versions to see which one works
"""

import os
import sys

def test_full_supabase():
    """Test the full Supabase client"""
    print("🧪 Testing full Supabase client...")
    try:
        from supabase_diagnosis import initialize_supabase_diagnosis
        success = initialize_supabase_diagnosis()
        if success:
            print("   ✅ Full Supabase client works!")
            return True
        else:
            print("   ❌ Full Supabase client failed to connect")
            return False
    except Exception as e:
        print(f"   ❌ Full Supabase client error: {e}")
        return False

def test_simple_supabase():
    """Test the simple Supabase client"""
    print("🧪 Testing simple Supabase client...")
    try:
        from simple_supabase_diagnosis import initialize_simple_supabase_diagnosis
        success = initialize_simple_supabase_diagnosis()
        if success:
            print("   ✅ Simple Supabase client works!")
            return True
        else:
            print("   ❌ Simple Supabase client failed to connect")
            return False
    except Exception as e:
        print(f"   ❌ Simple Supabase client error: {e}")
        return False

def check_environment():
    """Check environment variables"""
    print("🔧 Checking environment variables...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url:
        print("   ❌ Missing SUPABASE_URL")
        return False
    
    if not supabase_key:
        print("   ❌ Missing SUPABASE_KEY")
        return False
    
    print(f"   ✅ SUPABASE_URL: {supabase_url}")
    print(f"   ✅ SUPABASE_KEY: {'*' * 20}...{supabase_key[-10:]}")
    return True

if __name__ == "__main__":
    print("🚀 Testing Supabase Client Versions")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment variables missing")
        sys.exit(1)
    
    # Test both versions
    full_works = test_full_supabase()
    simple_works = test_simple_supabase()
    
    print(f"\n📊 Results:")
    print(f"   Full client: {'✅ WORKS' if full_works else '❌ FAILED'}")
    print(f"   Simple client: {'✅ WORKS' if simple_works else '❌ FAILED'}")
    
    if full_works or simple_works:
        print("\n🎉 At least one Supabase client is working!")
        if simple_works and not full_works:
            print("💡 Using simple HTTP-based client as fallback")
    else:
        print("\n❌ Neither Supabase client is working")
        print("🔧 Please check your Supabase credentials and database setup")
        sys.exit(1)