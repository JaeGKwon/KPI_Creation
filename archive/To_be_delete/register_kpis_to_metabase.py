#!/usr/bin/env python3
"""
Script to register SQLs from tb_tables_kpis.json into Metabase as questions
"""

import os
import json
import time
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

class MetabaseKPIRegistrar:
    def __init__(self):
        """Initialize the Metabase KPI Registrar"""
        load_dotenv()
        
        # Metabase configuration
        self.metabase_url = os.getenv('METABASE_URL')
        self.metabase_username = os.getenv('METABASE_USERNAME')
        self.metabase_password = os.getenv('METABASE_PASSWORD')
        
        # Session management
        self.session_id = None
        self.headers = {}
        
        if not all([self.metabase_url, self.metabase_username, self.metabase_password]):
            print("Warning: Missing Metabase credentials")
            print("Please check your .env file")

    def authenticate_metabase(self) -> bool:
        """Authenticate with Metabase and get session ID"""
        print("🔐 Authenticating with Metabase...")
        
        try:
            # Prepare authentication data
            auth_data = {
                "username": self.metabase_username,
                "password": self.metabase_password
            }
            
            # Make authentication request
            auth_url = f"{self.metabase_url}/api/session"
            response = requests.post(auth_url, json=auth_data)
            
            if response.status_code == 200:
                auth_response = response.json()
                self.session_id = auth_response.get('id')
                
                if self.session_id:
                    # Set headers for subsequent requests
                    self.headers = {
                        'X-Metabase-Session': self.session_id,
                        'Content-Type': 'application/json'
                    }
                    print(f"✅ Successfully authenticated. Session ID: {self.session_id}")
                    return True
                else:
                    print("❌ Authentication failed: No session ID received")
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_database_id(self) -> int:
        """Get the first available database ID"""
        print("🔍 Getting database ID...")
        
        try:
            databases_url = f"{self.metabase_url}/api/database"
            response = requests.get(databases_url, headers=self.headers)
            
            if response.status_code == 200:
                databases = response.json()
                
                # Handle different response formats
                if isinstance(databases, dict):
                    if 'data' in databases:
                        databases = databases['data']
                    else:
                        databases = [databases]
                
                if databases and len(databases) > 0:
                    # Get the first database
                    database = databases[0]
                    database_id = database.get('id')
                    database_name = database.get('name', 'Unknown')
                    
                    print(f"✅ Using database: {database_name} (ID: {database_id})")
                    return database_id
                else:
                    print("❌ No databases found")
                    return None
            else:
                print(f"❌ Failed to get databases: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting database ID: {e}")
            return None

    def get_or_create_collection(self, collection_name: str) -> int:
        """Get or create a collection with the specified name"""
        print(f"📁 Getting or creating collection: '{collection_name}'...")
        
        try:
            # First, try to find existing collection
            collections_url = f"{self.metabase_url}/api/collection"
            response = requests.get(collections_url, headers=self.headers)
            
            if response.status_code == 200:
                collections = response.json()
                
                # Search for collection by name
                for collection in collections:
                    if collection.get('name') == collection_name:
                        collection_id = collection.get('id')
                        print(f"✅ Found existing collection: '{collection_name}' (ID: {collection_id})")
                        return collection_id
                
                # Collection not found, create it
                print(f"📝 Creating new collection: '{collection_name}'...")
                create_data = {
                    "name": collection_name,
                    "description": f"Collection for KPI questions from tb_tables_kpis.json",
                    "color": "#84BB4C",  # Green color
                    "parent_id": None
                }
                
                create_response = requests.post(collections_url, json=create_data, headers=self.headers)
                
                if create_response.status_code == 200:
                    new_collection = create_response.json()
                    new_collection_id = new_collection.get('id')
                    print(f"✅ Successfully created collection: '{collection_name}' (ID: {new_collection_id})")
                    return new_collection_id
                else:
                    print(f"❌ Failed to create collection: {create_response.status_code} - {create_response.text}")
                    return None
            else:
                print(f"❌ Failed to get collections: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error with collection: {e}")
            return None

    def create_question(self, database_id: int, collection_id: int, kpi_data: Dict[str, Any], table_name: str) -> bool:
        """Create a question in Metabase for the given KPI"""
        
        kpi_name = kpi_data.get('kpi_name', 'Unknown KPI')
        description = kpi_data.get('description', '')
        business_value = kpi_data.get('business_value', '')
        sql_query = kpi_data.get('sql_query', '')
        
        # Combine description and business value
        full_description = f"Description: {description}"
        if business_value:
            full_description += f"\n\nBusiness Value: {business_value}"
        full_description += f"\n\nTable: {table_name}"
        
        # Create question data
        question_data = {
            "name": kpi_name,
            "description": full_description,
            "collection_id": collection_id,
            "dataset_query": {
                "type": "native",
                "native": {
                    "query": sql_query,
                    "template-tags": {}
                },
                "database": database_id
            },
            "display": "table",
            "visualization_settings": {},
            "result_metadata": []
        }
        
        try:
            # Create the question
            questions_url = f"{self.metabase_url}/api/card"
            response = requests.post(questions_url, json=question_data, headers=self.headers)
            
            if response.status_code == 200:
                question = response.json()
                question_id = question.get('id')
                print(f"✅ Created question: '{kpi_name}' (ID: {question_id})")
                return True
            else:
                print(f"❌ Failed to create question '{kpi_name}': {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating question '{kpi_name}': {e}")
            return False

    def register_kpis_from_json(self, json_file_path: str = "tb_tables_kpis.json"):
        """Register all KPIs from the JSON file into Metabase"""
        
        print("🚀 Starting KPI registration process...")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_metabase():
            print("❌ Authentication failed. Cannot proceed.")
            return
        
        # Get database ID
        database_id = self.get_database_id()
        if not database_id:
            print("❌ No database available. Cannot proceed.")
            return
        
        # Get or create collection
        collection_name = "jae's quick analysis"
        collection_id = self.get_or_create_collection(collection_name)
        if not collection_id:
            print("❌ Collection creation failed. Cannot proceed.")
            return
        
        # Load JSON data
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded {json_file_path} with {len(data)} tables")
        except FileNotFoundError:
            print(f"❌ File {json_file_path} not found")
            return
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {json_file_path}: {e}")
            return
        
        # Process each table
        total_kpis = 0
        successful_registrations = 0
        failed_registrations = 0
        
        for table_name, table_data in data.items():
            print(f"\n📊 Processing table: {table_name}")
            print("-" * 60)
            
            kpis = table_data.get('kpis', [])
            if not kpis:
                print(f"⚠️  No KPIs found for {table_name}")
                continue
            
            print(f"📈 Found {len(kpis)} KPIs to register")
            
            # Register each KPI
            for i, kpi in enumerate(kpis, 1):
                print(f"  🔄 Registering KPI {i}/{len(kpis)}: {kpi.get('kpi_name', 'Unknown')}")
                
                if self.create_question(database_id, collection_id, kpi, table_name):
                    successful_registrations += 1
                else:
                    failed_registrations += 1
                
                total_kpis += 1
                
                # Add small delay between requests
                time.sleep(0.5)
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎯 KPI REGISTRATION COMPLETE!")
        print("=" * 80)
        print(f"📊 SUMMARY:")
        print(f"  • Total KPIs processed: {total_kpis}")
        print(f"  • Successfully registered: {successful_registrations}")
        print(f"  • Failed registrations: {failed_registrations}")
        print(f"  • Success rate: {(successful_registrations/total_kpis)*100:.1f}%" if total_kpis > 0 else "0%")
        print(f"  • Collection: '{collection_name}' (ID: {collection_id})")
        print(f"  • Database ID: {database_id}")
        
        if successful_registrations > 0:
            print(f"\n✅ You can now find your KPI questions in the '{collection_name}' collection in Metabase!")
            print(f"   URL: {self.metabase_url}/collection/{collection_id}")

def main():
    """Main function to run the KPI registration"""
    
    registrar = MetabaseKPIRegistrar()
    registrar.register_kpis_from_json()

if __name__ == "__main__":
    main() 