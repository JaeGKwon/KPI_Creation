#!/usr/bin/env python3
"""
Focused test script for randomly selected SQL queries from tb_tables_kpis.json
Tests SQL execution via Metabase API to diagnose UI vs API differences
"""

import os
import json
import time
import random
import requests
from dotenv import load_dotenv
from typing import Dict, Any

class RandomSQLTester:
    def __init__(self):
        """Initialize the SQL tester"""
        load_dotenv()
        
        # Metabase configuration
        self.metabase_url = os.getenv('METABASE_URL')
        self.metabase_username = os.getenv('METABASE_USERNAME')
        self.metabase_password = os.getenv('METABASE_PASSWORD')
        
        # Session management
        self.session_id = None
        self.headers = {}
        
        # Test results
        self.test_results = []

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

    def collect_all_sqls(self) -> list:
        """Collect all SQL queries from the JSON file"""
        print("📋 Collecting all SQL queries from JSON file...")
        
        try:
            with open('tb_tables_kpis.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_sqls = []
            
            for table_name, table_data in data.items():
                kpis = table_data.get('kpis', [])
                for kpi in kpis:
                    kpi_name = kpi.get('kpi_name', 'Unknown KPI')
                    sql_query = kpi.get('sql_query', '')
                    if sql_query:
                        all_sqls.append({
                            'table_name': table_name,
                            'kpi_name': kpi_name,
                            'sql_query': sql_query
                        })
            
            print(f"✅ Collected {len(all_sqls)} SQL queries from {len(data)} tables")
            return all_sqls
            
        except Exception as e:
            print(f"❌ Error collecting SQLs: {e}")
            return []

    def test_sql_execution_detailed(self, database_id: int, sql_query: str, kpi_name: str, table_name: str) -> Dict[str, Any]:
        """Test SQL execution with detailed error analysis"""
        print(f"  🔍 Testing SQL for: {kpi_name}")
        print(f"     Table: {table_name}")
        print(f"     SQL: {sql_query[:100]}...")
        
        try:
            # Create test query data
            test_data = {
                "type": "native",
                "native": {
                    "query": sql_query,
                    "template-tags": {}
                },
                "database": database_id
            }
            
            # Test with dataset endpoint
            query_url = f"{self.metabase_url}/api/dataset"
            response = requests.post(query_url, json=test_data, headers=self.headers)
            
            print(f"     Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and 'rows' in result['data']:
                    rows = result['data']['rows']
                    row_count = len(rows)
                    
                    print(f"     ✅ SUCCESS: {row_count} rows returned")
                    return {
                        'status': 'success',
                        'row_count': row_count,
                        'message': f'Returned {row_count} rows'
                    }
                else:
                    print(f"     ⚠️  PARTIAL: No data structure in response")
                    print(f"     Response: {result}")
                    return {
                        'status': 'partial',
                        'message': 'No data structure in response',
                        'response': result
                    }
            else:
                error_text = response.text
                print(f"     ❌ FAILED: {response.status_code}")
                print(f"     Error: {error_text}")
                
                # Try to parse error details
                try:
                    error_json = response.json()
                    return {
                        'status': 'failed',
                        'error_code': response.status_code,
                        'error_message': error_text,
                        'error_details': error_json
                    }
                except:
                    return {
                        'status': 'failed',
                        'error_code': response.status_code,
                        'error_message': error_text
                    }
                
        except Exception as e:
            print(f"     ❌ EXCEPTION: {str(e)}")
            return {
                'status': 'exception',
                'error_message': str(e)
            }

    def test_random_sqls(self, limit: int = 10):
        """Test randomly selected SQL queries from the JSON file"""
        print("🚀 Starting random SQL testing...")
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
        
        # Collect all SQLs
        all_sqls = self.collect_all_sqls()
        if not all_sqls:
            print("❌ No SQL queries found in JSON file")
            return
        
        # Randomly select SQLs
        selected_sqls = random.sample(all_sqls, min(limit, len(all_sqls)))
        
        print(f"\n🎲 Randomly selected {len(selected_sqls)} SQL queries for testing")
        print("=" * 60)
        
        # Test each selected SQL
        success_count = 0
        partial_count = 0
        failure_count = 0
        
        for i, sql_info in enumerate(selected_sqls, 1):
            table_name = sql_info['table_name']
            kpi_name = sql_info['kpi_name']
            sql_query = sql_info['sql_query']
            
            print(f"\n🔄 Testing SQL {i}/{len(selected_sqls)}: {kpi_name}")
            print("-" * 50)
            
            # Test the SQL
            result = self.test_sql_execution_detailed(database_id, sql_query, kpi_name, table_name)
            
            # Store result
            test_result = {
                'table_name': table_name,
                'kpi_name': kpi_name,
                'sql_query': sql_query,
                'test_result': result
            }
            self.test_results.append(test_result)
            
            # Count results
            if result['status'] == 'success':
                success_count += 1
            elif result['status'] == 'partial':
                partial_count += 1
            else:
                failure_count += 1
            
            # Add delay between tests
            time.sleep(1)
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎯 RANDOM SQL TESTING COMPLETE!")
        print("=" * 80)
        print(f"📊 SUMMARY:")
        print(f"  • Total SQLs tested: {len(selected_sqls)}")
        print(f"  • Successful executions: {success_count}")
        print(f"  • Partial executions: {partial_count}")
        print(f"  • Failed executions: {failure_count}")
        print(f"  • Success rate: {(success_count/len(selected_sqls))*100:.1f}%" if len(selected_sqls) > 0 else "0%")
        
        # Save detailed results
        self.save_test_results()
        
        # Show sample of failed queries for analysis
        if failure_count > 0:
            print(f"\n🔍 SAMPLE FAILED QUERIES FOR ANALYSIS:")
            failed_results = [r for r in self.test_results if r['test_result']['status'] == 'failed']
            for i, result in enumerate(failed_results[:3], 1):  # Show first 3 failures
                print(f"\n  {i}. {result['kpi_name']} (Table: {result['table_name']})")
                print(f"     Error: {result['test_result'].get('error_message', 'Unknown error')}")
                print(f"     SQL: {result['sql_query'][:100]}...")

    def save_test_results(self):
        """Save detailed test results to file"""
        output_file = 'random_sql_test_results.json'
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Detailed test results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Failed to save test results: {e}")

def main():
    """Main function to run the random SQL testing"""
    
    tester = RandomSQLTester()
    tester.test_random_sqls(limit=10)  # Test only 10 random SQLs

if __name__ == "__main__":
    main() 