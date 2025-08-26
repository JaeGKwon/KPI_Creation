#!/usr/bin/env python3
"""
Test Step 2: Table Metadata Extraction
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metabase_kpi_extractor import MetabaseKPIExtractor

def test_metadata_extraction():
    """Test table metadata extraction"""
    print("="*50)
    print("TESTING STEP 2: TABLE METADATA EXTRACTION")
    print("="*50)
    
    try:
        # Initialize the extractor
        extractor = MetabaseKPIExtractor()
        
        # First authenticate
        if not extractor.authenticate_metabase():
            print("❌ Authentication failed! Cannot proceed with metadata test.")
            return False
        
        # Test getting database list
        print("\n1. Testing database list retrieval...")
        databases = extractor.get_database_list()
        if databases:
            print(f"✅ Found {len(databases)} databases")
            print(f"Database structure: {type(databases)}")
            print(f"First database: {databases[0] if databases else 'None'}")
            for db in databases:  # Show all databases
                if isinstance(db, dict):
                    print(f"   - {db.get('name', 'Unknown')} (ID: {db.get('id', 'Unknown')})")
                else:
                    print(f"   - {db}")
        else:
            print("❌ No databases found")
            return False
        
        # Test table search
        print("\n2. Testing table search...")
        
        # Test the new table search method
        test_table_names = ["ACCOUNTS", "USERS", "ORDERS", "PRODUCTS", "CUSTOMERS"]
        print(f"Searching for tables: {test_table_names}")
        
        matching_tables = extractor.search_tables_by_name(test_table_names)
        
        if matching_tables:
            print(f"✅ Found {len(matching_tables)} matching tables")
            for table in matching_tables:
                print(f"   - {table.get('name', 'Unknown')} (ID: {table.get('id', 'Unknown')})")
            
            # Test metadata extraction for first table
            first_table = matching_tables[0]
            table_id = first_table.get('id')
            table_name = first_table.get('name')
            
            print(f"\n3. Testing metadata extraction for table: {table_name}")
            metadata = extractor.get_table_metadata(table_id)
            
            if metadata:
                print("✅ Metadata extraction successful!")
                print(f"   - Table fields: {len(metadata.get('fields', []))}")
                print(f"   - Related tables: {len(metadata.get('related_tables', []))}")
                
                # Save sample metadata for inspection
                with open(f"sample_metadata_{table_name}.json", 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f"   - Sample metadata saved to: sample_metadata_{table_name}.json")
                
                return True
            else:
                print("❌ Metadata extraction failed")
                return False
        else:
            print("❌ No matching tables found")
            return False
            
    except Exception as e:
        print(f"❌ Error during metadata test: {e}")
        return False

if __name__ == "__main__":
    success = test_metadata_extraction()
    if success:
        print("\n🎉 Step 2 test passed!")
    else:
        print("\n💥 Step 2 test failed!")
        print("Please check your environment variables and Metabase connection.") 