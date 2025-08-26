#!/usr/bin/env python3
"""
Enhanced KPI registration script with SQL validation and LLM-powered fixing
Registers KPIs from tb_tables_kpis.json into Metabase with comprehensive validation
"""

import os
import json
import time
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

class EnhancedMetabaseKPIRegistrar:
    def __init__(self):
        """Initialize the enhanced KPI registrar"""
        load_dotenv()
        
        # Metabase configuration
        self.metabase_url = os.getenv('METABASE_URL')
        self.metabase_username = os.getenv('METABASE_USERNAME')
        self.metabase_password = os.getenv('METABASE_PASSWORD')
        

        
        # Session management
        self.session_id = None
        self.headers = {}
        
        # Registration tracking
        self.registered_kpis = set()
        self.failed_kpis = []
        self.invalid_sqls = []
        
        # Validation results
        self.validation_results = {
            'total_processed': 0,
            'successfully_registered': 0,
            'validation_failed': 0,
            'creation_failed': 0
        }

    def authenticate_metabase(self) -> bool:
        """Authenticate with Metabase and get session ID"""
        print("🔐 Authenticating with Metabase...")
        
        try:
            auth_data = {
                "username": self.metabase_username,
                "password": self.metabase_password
            }
            
            auth_url = f"{self.metabase_url}/api/session"
            response = requests.post(auth_url, json=auth_data)
            
            if response.status_code == 200:
                auth_response = response.json()
                self.session_id = auth_response.get('id')
                
                if self.session_id:
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
                
                if isinstance(databases, dict):
                    if 'data' in databases:
                        databases = databases['data']
                    else:
                        databases = [databases]
                
                if databases and len(databases) > 0:
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

    def remove_existing_kpis(self, collection_name: str = "jae's validated analysis") -> bool:
        """Remove all existing KPIs from the specified collection"""
        print(f"🗑️  Removing existing KPIs from collection: '{collection_name}'")
        
        try:
            # Get the collection first
            collection_id = self.get_or_create_collection(collection_name)
            if not collection_id:
                print("❌ Cannot get collection for cleanup")
                return False
            
            # Get all cards in the collection
            collection_url = f"{self.metabase_url}/api/collection/{collection_id}/items"
            response = requests.get(collection_url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"❌ Failed to get collection items: {response.status_code}")
                return False
            
            items = response.json()
            cards_to_remove = [item for item in items if item.get('model') == 'card']
            
            if not cards_to_remove:
                print("✅ No existing KPIs to remove")
                return True
            
            print(f"🗑️  Found {len(cards_to_remove)} existing KPIs to remove...")
            
            removed_count = 0
            for card in cards_to_remove:
                card_id = card.get('id')
                card_name = card.get('name', 'Unknown')
                
                # Delete the card
                delete_url = f"{self.metabase_url}/api/card/{card_id}"
                delete_response = requests.delete(delete_url, headers=self.headers)
                
                if delete_response.status_code == 204:
                    print(f"    ✅ Removed: {card_name}")
                    removed_count += 1
                else:
                    print(f"    ❌ Failed to remove {card_name}: {delete_response.status_code}")
                
                time.sleep(0.2)  # Small delay between deletions
            
            print(f"✅ Successfully removed {removed_count}/{len(cards_to_remove)} existing KPIs")
            return True
            
        except Exception as e:
            print(f"❌ Error during KPI cleanup: {e}")
            return False

    def get_or_create_collection(self, collection_name: str) -> int:
        """Get or create collection for KPI questions"""
        print(f"📁 Getting or creating collection: '{collection_name}'...")
        
        try:
            collections_url = f"{self.metabase_url}/api/collection"
            response = requests.get(collections_url, headers=self.headers)
            
            if response.status_code == 200:
                collections = response.json()
                for collection in collections:
                    if collection.get('name') == collection_name:
                        collection_id = collection.get('id')
                        print(f"✅ Found existing collection: '{collection_name}' (ID: {collection_id})")
                        return collection_id
                
                print(f"📝 Creating new collection: '{collection_name}'...")
                create_data = {
                    "name": collection_name,
                    "description": f"Collection for validated KPI questions from tb_tables_kpis.json",
                    "color": "#84BB4C",
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

    def validate_sql_execution(self, database_id: int, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query to validate it works correctly"""
        try:
            # Execute the SQL query
            query_data = {
                "type": "native",
                "native": {"query": sql_query, "template-tags": {}},
                "database": database_id
            }
            
            response = requests.post(
                f"{self.metabase_url}/api/dataset",
                json=query_data,
                headers=self.headers,
                timeout=30
            )
            
            # Parse the response
            if response.status_code in [200, 202]:  # Both 200 and 202 are success codes
                result = response.json()
                
                # Check if the query executed successfully
                if result.get('status') == 'completed':
                    # Check if we got valid results
                    rows = result.get('data', {}).get('rows', [])
                    cols = result.get('data', {}).get('cols', [])
                    
                    # SQL is valid if we get results (even if 0 rows)
                    if rows is not None and cols is not None:
                        return {
                            'status': 'valid',
                            'message': f'SQL executed successfully with {len(rows)} rows',
                            'rows': rows,
                            'cols': cols,
                            'execution_time': result.get('running_time', 0)
                        }
                    else:
                        return {
                            'status': 'failed',
                            'message': 'SQL executed but returned invalid result structure',
                            'error': 'Invalid result structure'
                        }
                elif result.get('status') == 'failed':
                    # Query failed execution
                    error_info = result.get('error', 'Unknown error')
                    return {
                        'status': 'failed',
                        'message': f'SQL execution failed: {error_info}',
                        'error': error_info
                    }
                else:
                    # Check if we have data (successful execution)
                    if 'data' in result and 'rows' in result['data']:
                        rows = result['data']['rows']
                        cols = result['data'].get('cols', [])
                        return {
                            'status': 'valid',
                            'message': f'SQL executed successfully with {len(rows)} rows',
                            'rows': rows,
                            'cols': cols,
                            'execution_time': result.get('running_time', 0)
                        }
                    else:
                        return {
                            'status': 'failed',
                            'message': 'SQL execution returned unexpected response format',
                            'error': 'Unexpected response format'
                        }
            else:
                # HTTP error
                return {
                    'status': 'failed',
                    'message': f'HTTP error {response.status_code}: {response.text}',
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Exception during SQL execution: {str(e)}',
                'error': str(e)
            }





    

    def create_question(self, database_id: int, collection_id: int, kpi_data: Dict[str, Any], table_name: str, final_sql: str) -> bool:
        """Create a question in Metabase with the validated/fixed SQL"""
        kpi_name = kpi_data.get('kpi_name', 'Unknown KPI')
        description = kpi_data.get('description', '')
        business_value = kpi_data.get('business_value', '')
        
        full_description = f"Description: {description}"
        if business_value:
            full_description += f"\n\nBusiness Value: {business_value}"
        full_description += f"\n\nTable: {table_name}"
        
        question_data = {
            "name": kpi_name,
            "description": full_description,
            "collection_id": collection_id,
            "dataset_query": {
                "type": "native",
                "native": {
                    "query": final_sql,
                    "template-tags": {}
                },
                "database": database_id
            },
            "display": "table",
            "visualization_settings": {},
            "result_metadata": []
        }
        
        try:
            questions_url = f"{self.metabase_url}/api/card"
            response = requests.post(questions_url, json=question_data, headers=self.headers)
            
            if response.status_code == 200:
                question = response.json()
                question_id = question.get('id')
                print(f"    ✅ Created question: '{kpi_name}' (ID: {question_id})")
                return True
            else:
                print(f"    ❌ Failed to create question '{kpi_name}': {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"    ❌ Error creating question '{kpi_name}': {e}")
            return False

    def register_kpis_with_validation(self, json_file_path: str = "tb_tables_kpis_clean.json", test_mode: bool = False, test_limit: int = 10):
        """Main method to register KPIs with comprehensive validation and fixing"""
        print("🚀 Starting enhanced KPI registration with SQL validation...")
        if test_mode:
            print(f"🧪 TEST MODE: Processing only {test_limit} KPIs for testing")
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
        collection_name = "jae's validated SQL"
        if test_mode:
            collection_name = "jae's test SQL"
        
        # Remove existing KPIs first
        if not self.remove_existing_kpis(collection_name):
            print("⚠️  Warning: Failed to remove existing KPIs, but continuing...")
        
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
        
        # Collect all KPIs for processing
        all_kpis = []
        for table_name, table_data in data.items():
            kpis = table_data.get('kpis', [])
            for kpi in kpis:
                all_kpis.append({
                    'table_name': table_name,
                    'table_data': table_data,
                    'kpi': kpi
                })
        
        # Limit to test cases if in test mode
        if test_mode:
            import random
            all_kpis = random.sample(all_kpis, min(test_limit, len(all_kpis)))
            print(f"🧪 Selected {len(all_kpis)} random KPIs for testing")
        
        print(f"📊 Total KPIs to process: {len(all_kpis)}")
        
        # Process each KPI
        for i, kpi_info in enumerate(all_kpis, 1):
            table_name = kpi_info['table_name']
            table_data = kpi_info['table_data']
            kpi = kpi_info['kpi']
            
            print(f"\n📊 Processing KPI {i}/{len(all_kpis)} from table: {table_name}")
            print(f"⏱️  Progress: {i}/{len(all_kpis)} ({i/len(all_kpis)*100:.1f}%)")
            print("-" * 60)
            
            kpi_name = kpi.get('kpi_name', f'KPI_{i}')
            sql_query = kpi.get('sql_query', '')
            
            print(f"  🔄 Processing KPI: {kpi_name}")
            
            # Skip if already registered
            if kpi_name in self.registered_kpis:
                print(f"    ⏭️  KPI '{kpi_name}' already registered, skipping...")
                continue
            
            # Validate SQL only (no fixing attempts)
            validation_result = self.validate_sql_execution(database_id, sql_query)
            
            if validation_result['status'] == 'valid':
                # SQL is valid, create the question
                if self.create_question(database_id, collection_id, kpi, table_name, sql_query):
                    self.registered_kpis.add(kpi_name)
                    self.validation_results['successfully_registered'] += 1
                    print(f"    ✅ Successfully registered: {kpi_name}")
                else:
                    self.failed_kpis.append({
                        'kpi_name': kpi_name,
                        'table_name': table_name,
                        'sql_query': sql_query,
                        'error': 'Failed to create question in Metabase'
                    })
                    print(f"    ❌ Failed to create question: {kpi_name}")
            else:
                # SQL validation failed, record it for later analysis
                self.invalid_sqls.append({
                    'kpi_name': kpi_name,
                    'table_name': table_name,
                    'sql_query': sql_query,
                    'error': validation_result.get('message', 'Unknown validation error'),
                    'validation_details': validation_result
                })
                self.validation_results['validation_failed'] += 1
                print(f"    ⚠️  SQL validation failed: {kpi_name} - {validation_result.get('message', 'Unknown error')}")
            
            self.validation_results['total_processed'] += 1
            
            # Add delay between KPIs
            time.sleep(0.5)
        
        # Final summary
        self.print_final_summary(collection_id, collection_name)
        self.save_detailed_results()

    def print_final_summary(self, collection_id: int, collection_name: str):
        """Print comprehensive final summary"""
        print("\n" + "=" * 80)
        print("🎯 ENHANCED KPI REGISTRATION COMPLETE!")
        print("=" * 80)
        print(f"📊 VALIDATION SUMMARY:")
        print(f"  • Total KPIs processed: {self.validation_results['total_processed']}")
        print(f"  • Successfully registered: {self.validation_results['successfully_registered']}")
        print(f"  • SQL validation failed: {self.validation_results['validation_failed']}")
        print(f"  • Question creation failed: {self.validation_results['creation_failed']}")
        print(f"  • Success rate: {(self.validation_results['successfully_registered']/self.validation_results['total_processed'])*100:.1f}%" if self.validation_results['total_processed'] > 0 else "0%")
        
        print(f"\n📁 COLLECTION DETAILS:")
        print(f"  • Collection: '{collection_name}' (ID: {collection_id})")
        print(f"  • URL: {self.metabase_url}/collection/{collection_id}")
        
        if self.invalid_sqls:
            print(f"\n⚠️  INVALID SQLs (saved for analysis):")
            print(f"  • Total invalid SQLs: {len(self.invalid_sqls)}")
            print(f"  • Saved to: invalid_sqls_for_analysis.json")
            for invalid in self.invalid_sqls[:5]:  # Show first 5
                print(f"  • {invalid['kpi_name']} (Table: {invalid['table_name']}) - {invalid['error']}")
        
        if self.failed_kpis:
            print(f"\n❌ CREATION FAILED KPIs:")
            for failed in self.failed_kpis[:5]:  # Show first 5
                print(f"  • {failed['kpi_name']} (Table: {failed['table_name']}) - {failed['error']}")

    def save_detailed_results(self):
        """Save detailed results to files"""
        # Save validation results
        validation_file = 'enhanced_kpi_validation_results.json'
        try:
            with open(validation_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'validation_summary': self.validation_results,
                    'failed_kpis': self.failed_kpis,
                    'registered_kpis': list(self.registered_kpis)
                }, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Detailed validation results saved to: {validation_file}")
        except Exception as e:
            print(f"❌ Failed to save validation results: {e}")
        
        # Save invalid SQLs to separate file for analysis
        if self.invalid_sqls:
            invalid_sqls_file = 'invalid_sqls_for_analysis.json'
            try:
                with open(invalid_sqls_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'summary': {
                            'total_invalid_sqls': len(self.invalid_sqls),
                            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'description': 'SQLs that failed validation and were not registered'
                        },
                        'invalid_sqls': self.invalid_sqls
                    }, f, indent=2, ensure_ascii=False)
                print(f"💾 Invalid SQLs saved to: {invalid_sqls_file}")
            except Exception as e:
                print(f"❌ Failed to save invalid SQLs: {e}")

def main():
    """Main function to run the enhanced KPI registration"""
    import sys
    
    # Check if test mode is requested
    test_mode = '--test' in sys.argv
    test_limit = 50  # Default test limit for 50 SQLs
    
    # Parse test limit if provided
    if '--test' in sys.argv:
        try:
            limit_index = sys.argv.index('--test') + 1
            if limit_index < len(sys.argv) and sys.argv[limit_index].isdigit():
                test_limit = int(sys.argv[limit_index])
        except (ValueError, IndexError):
            pass
    
    if test_mode:
        print(f"🧪 Running in TEST MODE with {test_limit} KPIs")
        print("Usage: python register_kpis_enhanced.py --test [number]")
        print("Example: python register_kpis_enhanced.py --test 50")
        print()
    
    registrar = EnhancedMetabaseKPIRegistrar()
    registrar.register_kpis_with_validation(test_mode=test_mode, test_limit=test_limit)

if __name__ == "__main__":
    main() 