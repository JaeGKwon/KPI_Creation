#!/usr/bin/env python3
"""
Comprehensive SQL Validator and Fixer for KPI SQL queries
- Checks syntax and common issues using schema information
- Validates and tests SQL with database execution
- Uses LLM to fix SQL syntax errors
- Sets default duration to one month when not specified
- Separates problematic SQL into separate document
- Does NOT modify original tb_tables_kpis.json
"""

import os
import json
import time
import re
import requests
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

class SQLValidatorAndFixer:
    def __init__(self):
        """Initialize the SQL Validator and Fixer"""
        load_dotenv()
        
        # Metabase configuration
        self.metabase_url = os.getenv('METABASE_URL')
        self.metabase_username = os.getenv('METABASE_USERNAME')
        self.metabase_password = os.getenv('METABASE_PASSWORD')
        
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Session management
        self.session_id = None
        self.headers = {}
        
        # Schema information cache
        self.schema_cache = {}
        
        # Results tracking
        self.validation_results = {
            'valid_sql': [],
            'fixed_sql': [],
            'problematic_sql': [],
            'schema_issues': [],
            'execution_errors': []
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

    def analyze_schema_from_json(self, json_file_path: str = "tb_tables_kpis.json"):
        """Analyze schema information from the JSON file"""
        print("📋 Analyzing schema information from JSON...")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for table_name, table_data in data.items():
                fields = table_data.get('field_details', [])
                self.schema_cache[table_name] = {
                    'fields': {field['name']: field for field in fields},
                    'field_types': {field['name']: field.get('type', 'Unknown') for field in fields},
                    'field_descriptions': {field['name']: field.get('description', '') for field in fields}
                }
            
            print(f"✅ Analyzed schema for {len(self.schema_cache)} tables")
            
        except Exception as e:
            print(f"❌ Error analyzing schema: {e}")

    def check_sql_syntax_and_common_issues(self, sql_query: str, table_name: str) -> Dict[str, Any]:
        """Check SQL syntax and common issues using schema information"""
        issues = []
        warnings = []
        suggestions = []
        
        # Get table schema
        table_schema = self.schema_cache.get(table_name, {})
        fields = table_schema.get('fields', {})
        field_types = table_schema.get('field_types', {})
        
        # 1. Check for basic SQL syntax
        sql_upper = sql_query.upper()
        
        # Check for common SQL keywords
        if 'SELECT' not in sql_upper:
            issues.append("Missing SELECT statement")
        
        if 'FROM' not in sql_upper:
            issues.append("Missing FROM clause")
        
        # 2. Check for table/column existence
        for field_name in fields.keys():
            if field_name.lower() in sql_query.lower() and field_name not in sql_query:
                warnings.append(f"Column '{field_name}' referenced but may have case sensitivity issues")
        
        # 3. Check for NULL handling
        if 'AVG(' in sql_upper or 'SUM(' in sql_upper or 'COUNT(' in sql_upper:
            if 'IS NOT NULL' not in sql_upper and 'COALESCE' not in sql_upper:
                suggestions.append("Consider adding NULL checks for aggregate functions")
        
        # 4. Check for date operations
        if any(date_func in sql_upper for date_func in ['DATEDIFF', 'DATE_ADD', 'DATE_SUB', 'DATE_TRUNC']):
            if 'IS NOT NULL' not in sql_upper:
                suggestions.append("Consider adding NULL checks for date operations")
        
        # 5. Check for type conversions
        if 'CAST(' in sql_upper or 'CONVERT(' in sql_upper:
            suggestions.append("Verify type conversions are appropriate for the data")
        
        # 6. Check for duration/time window issues
        if 'INTERVAL' in sql_upper or 'MONTH' in sql_upper or 'WEEK' in sql_upper:
            if '1 MONTH' not in sql_query and '30 DAY' not in sql_query:
                suggestions.append("Duration not specified - consider adding time window")
        
        # 7. Check for JOIN syntax
        if 'JOIN' in sql_upper:
            if 'ON' not in sql_upper:
                issues.append("JOIN statement missing ON clause")
        
        return {
            'has_issues': len(issues) > 0,
            'has_warnings': len(warnings) > 0,
            'issues': issues,
            'warnings': warnings,
            'suggestions': suggestions
        }

    def fix_sql_with_llm(self, sql_query: str, table_name: str, error_message: str) -> Optional[str]:
        """Use LLM to fix SQL syntax errors"""
        if not self.openai_api_key:
            print("⚠️  OpenAI API key not available - cannot use LLM fixing")
            return None
        
        try:
            # Get table schema for context
            table_schema = self.schema_cache.get(table_name, {})
            fields = table_schema.get('fields', {})
            
            # Create prompt for LLM
            prompt = f"""You are a SQL expert. Fix the following SQL query that has an error.

Table: {table_name}
Available fields: {list(fields.keys())}
Field types: {table_schema.get('field_types', {})}

Original SQL with error:
{sql_query}

Error message:
{error_message}

Please fix the SQL query. Common fixes include:
1. Adding NULL checks for date operations and aggregates
2. Setting default duration to 1 month when time window is missing
3. Fixing JOIN syntax and ON clauses
4. Adding proper type conversions
5. Fixing table/column name references

Return ONLY the corrected SQL query, no explanations:"""

            # Call OpenAI API
            import openai
            openai.api_key = self.openai_api_key
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a SQL expert who fixes SQL syntax errors."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            fixed_sql = response.choices[0].message.content.strip()
            
            # Clean up the response
            if fixed_sql.startswith('```sql'):
                fixed_sql = fixed_sql[7:]
            if fixed_sql.endswith('```'):
                fixed_sql = fixed_sql[:-3]
            
            return fixed_sql.strip()
            
        except Exception as e:
            print(f"❌ Error using LLM to fix SQL: {e}")
            return None

    def test_sql_execution(self, database_id: int, sql_query: str) -> Tuple[bool, str]:
        """Test if a SQL query executes successfully"""
        try:
            test_data = {
                "type": "native",
                "native": {
                    "query": sql_query,
                    "template-tags": {}
                },
                "database": database_id
            }
            
            query_url = f"{self.metabase_url}/api/dataset"
            response = requests.post(query_url, json=test_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and 'rows' in result['data']:
                    rows = result['data']['rows']
                    row_count = len(rows)
                    
                    if row_count > 0:
                        return True, f"✅ SQL executed successfully - returned {row_count} rows"
                    else:
                        return False, f"⚠️  SQL executed but returned 0 rows"
                else:
                    return False, f"❌ SQL execution failed - no data returned"
            else:
                error_text = response.text[:200] if response.text else "Unknown error"
                return False, f"❌ SQL execution failed: {response.status_code} - {error_text}"
                
        except Exception as e:
            return False, f"❌ SQL execution error: {str(e)}"

    def add_default_duration(self, sql_query: str) -> str:
        """Add default duration (1 month) when time window is not specified"""
        sql_upper = sql_query.upper()
        
        # Check if duration is already specified
        if any(time_unit in sql_upper for time_unit in ['INTERVAL', 'MONTH', 'WEEK', 'DAY']):
            return sql_query
        
        # Check if WHERE clause exists
        if 'WHERE' in sql_upper:
            # Add date filter to existing WHERE clause
            modified_sql = re.sub(
                r'WHERE\s+(.+)',
                r'WHERE \1 AND create_date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)',
                sql_query,
                flags=re.IGNORECASE
            )
        else:
            # Add WHERE clause with date filter
            modified_sql = sql_query + " WHERE create_date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)"
        
        return modified_sql

    def validate_and_fix_all_sql(self, json_file_path: str = "tb_tables_kpis.json"):
        """Validate and fix all SQL queries from the JSON file"""
        print("🚀 Starting comprehensive SQL validation and fixing...")
        print("=" * 80)
        
        # Authenticate with Metabase
        if not self.authenticate_metabase():
            print("❌ Authentication failed. Cannot proceed.")
            return
        
        # Get database ID
        database_id = self.get_database_id()
        if not database_id:
            print("❌ No database available. Cannot proceed.")
            return
        
        # Analyze schema from JSON
        self.analyze_schema_from_json(json_file_path)
        
        # Load JSON data
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded {json_file_path} with {len(data)} tables")
        except FileNotFoundError:
            print(f"❌ File {json_file_path} not found")
            return
        
        # Process each table
        total_kpis = 0
        valid_count = 0
        fixed_count = 0
        problematic_count = 0
        
        for table_name, table_data in data.items():
            print(f"\n📊 Processing table: {table_name}")
            print("-" * 60)
            
            kpis = table_data.get('kpis', [])
            if not kpis:
                print(f"⚠️  No KPIs found for {table_name}")
                continue
            
            print(f"📈 Found {len(kpis)} KPIs to validate")
            
            # Process each KPI
            for i, kpi in enumerate(kpis, 1):
                kpi_name = kpi.get('kpi_name', 'Unknown')
                sql_query = kpi.get('sql_query', '')
                
                print(f"  🔄 Validating KPI {i}/{len(kpis)}: {kpi_name}")
                
                total_kpis += 1
                
                # Step 1: Check syntax and common issues
                syntax_check = self.check_sql_syntax_and_common_issues(sql_query, table_name)
                
                # Step 2: Add default duration if needed
                modified_sql = self.add_default_duration(sql_query)
                
                # Step 3: Test SQL execution
                execution_success, execution_result = self.test_sql_execution(database_id, modified_sql)
                
                if execution_success:
                    if modified_sql != sql_query:
                        print(f"    ✅ SQL fixed and validated: {execution_result}")
                        self.validation_results['fixed_sql'].append({
                            'table': table_name,
                            'kpi_name': kpi_name,
                            'original_sql': sql_query,
                            'fixed_sql': modified_sql,
                            'fix_type': 'default_duration_added'
                        })
                        fixed_count += 1
                    else:
                        print(f"    ✅ SQL valid: {execution_result}")
                        self.validation_results['valid_sql'].append({
                            'table': table_name,
                            'kpi_name': kpi_name,
                            'sql': sql_query
                        })
                        valid_count += 1
                else:
                    print(f"    ❌ SQL execution failed: {execution_result}")
                    
                    # Step 4: Try to fix with LLM
                    fixed_sql = self.fix_sql_with_llm(modified_sql, table_name, execution_result)
                    
                    if fixed_sql:
                        # Test the fixed SQL
                        fixed_execution_success, fixed_execution_result = self.test_sql_execution(database_id, fixed_sql)
                        
                        if fixed_execution_success:
                            print(f"    ✅ SQL fixed by LLM: {fixed_execution_result}")
                            self.validation_results['fixed_sql'].append({
                                'table': table_name,
                                'kpi_name': kpi_name,
                                'original_sql': sql_query,
                                'fixed_sql': fixed_sql,
                                'fix_type': 'llm_fixed'
                            })
                            fixed_count += 1
                        else:
                            print(f"    ❌ LLM fix failed: {fixed_execution_result}")
                            self.validation_results['problematic_sql'].append({
                                'table': table_name,
                                'kpi_name': kpi_name,
                                'original_sql': sql_query,
                                'error': execution_result,
                                'llm_fix_attempted': True,
                                'llm_fix_failed': True
                            })
                            problematic_count += 1
                    else:
                        print(f"    ❌ Could not fix SQL with LLM")
                        self.validation_results['problematic_sql'].append({
                            'table': table_name,
                            'kpi_name': kpi_name,
                            'original_sql': sql_query,
                            'error': execution_result,
                            'llm_fix_attempted': False
                        })
                        problematic_count += 1
                
                # Add delay between requests
                time.sleep(0.5)
        
        # Generate comprehensive report
        self.generate_validation_report()
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎯 SQL VALIDATION AND FIXING COMPLETE!")
        print("=" * 80)
        print(f"📊 SUMMARY:")
        print(f"  • Total KPIs processed: {total_kpis}")
        print(f"  • Valid SQL: {valid_count}")
        print(f"  • Fixed SQL: {fixed_count}")
        print(f"  • Problematic SQL: {problematic_count}")
        print(f"  • Success rate: {((valid_count + fixed_count)/total_kpis)*100:.1f}%" if total_kpis > 0 else "0%")

    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("\n📋 Generating validation report...")
        
        # Create detailed report
        report = {
            'summary': {
                'total_processed': len(self.validation_results['valid_sql']) + 
                                 len(self.validation_results['fixed_sql']) + 
                                 len(self.validation_results['problematic_sql']),
                'valid_sql_count': len(self.validation_results['valid_sql']),
                'fixed_sql_count': len(self.validation_results['fixed_sql']),
                'problematic_sql_count': len(self.validation_results['problematic_sql'])
            },
            'valid_sql': self.validation_results['valid_sql'],
            'fixed_sql': self.validation_results['fixed_sql'],
            'problematic_sql': self.validation_results['problematic_sql']
        }
        
        # Save detailed report
        with open('sql_validation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Save problematic SQL separately
        if self.validation_results['problematic_sql']:
            with open('problematic_sql_queries.json', 'w', encoding='utf-8') as f:
                json.dump(self.validation_results['problematic_sql'], f, indent=2, ensure_ascii=False)
            print(f"💾 Problematic SQL saved to: problematic_sql_queries.json")
        
        print(f"💾 Validation report saved to: sql_validation_report.json")

def main():
    """Main function to run the SQL validation and fixing"""
    
    validator = SQLValidatorAndFixer()
    validator.validate_and_fix_all_sql()

if __name__ == "__main__":
    main() 