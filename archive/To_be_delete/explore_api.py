#!/usr/bin/env python3
"""
Explore Metabase API to find correct endpoints
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def explore_api():
    """Explore available API endpoints"""
    print("🔍 EXPLORING METABASE API")
    print("="*50)
    
    metabase_url = os.getenv('METABASE_URL')
    username = os.getenv('METABASE_USERNAME')
    password = os.getenv('METABASE_PASSWORD')
    
    if not all([metabase_url, username, password]):
        print("❌ Missing environment variables")
        return
    
    # Authenticate
    print("Authenticating...")
    auth_url = f"{metabase_url}/api/session"
    auth_data = {"username": username, "password": password}
    
    try:
        response = requests.post(auth_url, json=auth_data)
        response.raise_for_status()
        session_id = response.json().get('id')
        
        if not session_id:
            print("❌ Authentication failed")
            return
        
        headers = {'X-Metabase-Session': session_id, 'Content-Type': 'application/json'}
        print(f"✅ Authenticated. Session ID: {session_id}")
        
        # Test different API endpoints
        endpoints_to_test = [
            "/api/database",
            "/api/database/2",
            "/api/database/2/tables",
            "/api/database/2/schemas",
            "/api/table",
            "/api/collection",
            "/api/card",
            "/api/dataset",
            "/api/health"
        ]
        
        print("\n🔍 Testing API endpoints:")
        for endpoint in endpoints_to_test:
            try:
                url = f"{metabase_url}{endpoint}"
                response = requests.get(url, headers=headers, timeout=10)
                print(f"{endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"  ✅ List with {len(data)} items")
                        if data and isinstance(data[0], dict):
                            print(f"  📋 Sample keys: {list(data[0].keys())[:5]}")
                    elif isinstance(data, dict):
                        print(f"  ✅ Dict with keys: {list(data.keys())[:5]}")
                    else:
                        print(f"  ✅ {type(data)}")
                elif response.status_code == 404:
                    print(f"  ❌ Not found")
                else:
                    print(f"  ⚠️  Status: {response.status_code}")
                    
            except Exception as e:
                print(f"{endpoint}: ❌ Error - {e}")
        
        # Try to find tables using different approaches
        print("\n🔍 Looking for tables...")
        
        # Method 1: Direct table endpoint
        try:
            url = f"{metabase_url}/api/table"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                tables = response.json()
                print(f"✅ /api/table returned {len(tables) if isinstance(tables, list) else 'data'}")
                if isinstance(tables, list) and tables:
                    print(f"   First table: {tables[0].get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ /api/table failed: {e}")
        
        # Method 2: Database schemas
        try:
            url = f"{metabase_url}/api/database/2/schemas"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                schemas = response.json()
                print(f"✅ /api/database/2/schemas returned: {schemas}")
        except Exception as e:
            print(f"❌ /api/database/2/schemas failed: {e}")
        
        # Method 3: Search for tables in database details
        try:
            url = f"{metabase_url}/api/database/2"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                db_info = response.json()
                print(f"✅ Database info: {db_info.get('name', 'Unknown')}")
                print(f"   Tables count: {db_info.get('tables', 'Not found')}")
        except Exception as e:
            print(f"❌ Database info failed: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    explore_api() 