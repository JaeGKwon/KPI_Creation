#!/usr/bin/env python3
"""
Test Step 1: Metabase Authentication
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metabase_kpi_extractor import MetabaseKPIExtractor

def test_authentication():
    """Test Metabase authentication"""
    print("="*50)
    print("TESTING STEP 1: METABASE AUTHENTICATION")
    print("="*50)
    
    try:
        # Initialize the extractor
        extractor = MetabaseKPIExtractor()
        
        # Test authentication
        auth_success = extractor.authenticate_metabase()
        
        if auth_success:
            print("✅ Authentication successful!")
            print(f"Session ID: {extractor.session_id}")
            print(f"Headers: {extractor.headers}")
            return True
        else:
            print("❌ Authentication failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during authentication test: {e}")
        return False

if __name__ == "__main__":
    success = test_authentication()
    if success:
        print("\n🎉 Step 1 test passed!")
    else:
        print("\n💥 Step 1 test failed!")
        print("Please check your environment variables and Metabase connection.") 