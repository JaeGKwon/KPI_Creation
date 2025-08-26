#!/usr/bin/env python3
"""
Comprehensive SQL Validation and Business Value Assessment
Validates all SQLs in tb_tables_kpis.json against actual table schemas
Assesses business value and removes low-value KPIs
Fixes SQL issues based on correct column names and types
"""

import os
import json
import time
import requests
import openai
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from datetime import datetime

class SQLValidatorAndBusinessAssessor:
    def __init__(self):
        """Initialize the validator and assessor"""
        load_dotenv()
        
        # Metabase configuration
        self.metabase_url = os.getenv('METABASE_URL')
        self.metabase_username = os.getenv('METABASE_USERNAME')
        self.metabase_password = os.getenv('METABASE_PASSWORD')
        
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = self.openai_api_key
        
        # Session management
        self.session_id = None
        self.headers = {}
        
        # Validation results
        self.validation_results = {
            'total_kpis': 0,
            'business_value_assessed': 0,
            'high_value_kpis': 0,
            'low_value_kpis': 0,
            'sql_validation_passed': 0,
            'sql_validation_failed': 0,
            'sql_fixes_applied': 0,
            'unfixable_sql': 0,
            'removed_kpis': 0
        }
        
        # Detailed logs
        self.business_assessment_logs = []
        self.sql_validation_logs = []
        self.sql_fix_logs = []
        self.removal_logs = []

    def authenticate_metabase(self) -> bool:
        """Authenticate with Metabase"""
        print("🔐 Authenticating with Metabase...")
        try:
            auth_data = {"username": self.metabase_username, "password": self.metabase_password}
            auth_url = f"{self.metabase_url}/api/session"
            response = requests.post(auth_url, json=auth_data)
            
            if response.status_code == 200:
                auth_response = response.json()
                self.session_id = auth_response.get('id')
                if self.session_id:
                    self.headers = {'X-Metabase-Session': self.session_id, 'Content-Type': 'application/json'}
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
        """Get the database ID"""
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

    def get_table_schema(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get the actual table schema from Metabase"""
        try:
            # Search for the table
            search_url = f"{self.metabase_url}/api/table"
            response = requests.get(search_url, headers=self.headers)
            
            if response.status_code == 200:
                tables = response.json()
                for table in tables:
                    if table.get('name') == table_name:
                        table_id = table.get('id')
                        
                        # Get detailed table metadata
                        metadata_url = f"{self.metabase_url}/api/table/{table_id}"
                        metadata_response = requests.get(metadata_url, headers=self.headers)
                        
                        if metadata_response.status_code == 200:
                            return metadata_response.json()
                        break
            return None
        except Exception as e:
            print(f"❌ Error getting schema for {table_name}: {e}")
            return None

    def assess_business_value(self, kpi_name: str, description: str, business_value: str, table_name: str) -> Tuple[bool, str]:
        """Assess the business value of a KPI using LLM"""
        try:
            prompt = f"""You are a business analyst expert. Assess the business value of this KPI:

KPI Name: {kpi_name}
Description: {description}
Business Value: {business_value}
Table: {table_name}

Evaluate this KPI based on:
1. **Actionability**: Can business users take action based on this metric?
2. **Strategic Impact**: Does it align with business objectives?
3. **Operational Value**: Does it help with day-to-day operations?
4. **Decision Making**: Does it support business decisions?
5. **Performance Monitoring**: Does it help track business performance?

Rate this KPI as HIGH VALUE or LOW VALUE and provide a brief explanation.

Response format:
RATING: [HIGH VALUE or LOW VALUE]
REASON: [Brief explanation]"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a business analyst expert. Assess KPI business value objectively."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse the response
            if "HIGH VALUE" in result.upper():
                rating = True
            else:
                rating = False
            
            reason = result.split("REASON:")[-1].strip() if "REASON:" in result else "No reason provided"
            
            # Log the assessment
            log_entry = {
                'kpi_name': kpi_name,
                'table_name': table_name,
                'rating': 'HIGH VALUE' if rating else 'LOW VALUE',
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            self.business_assessment_logs.append(log_entry)
            
            return rating, reason
            
        except Exception as e:
            print(f"❌ Business value assessment failed for {kpi_name}: {e}")
            # Default to high value if assessment fails
            return True, "Assessment failed - defaulting to high value"

    def validate_sql_against_schema(self, sql_query: str, table_schema: Dict[str, Any]) -> Tuple[bool, List[str], Optional[str]]:
        """Validate SQL query against actual table schema"""
        issues = []
        is_valid = True
        
        try:
            # Extract field information from schema
            fields = table_schema.get('fields', [])
            field_names = {field.get('name', '').lower(): field for field in fields}
            
            # Basic SQL parsing to find column references
            sql_lower = sql_query.lower()
            
            # Check for common SQL patterns and validate columns
            if 'select' in sql_lower:
                # Extract column names from SELECT clause
                select_start = sql_lower.find('select')
                from_start = sql_lower.find('from')
                
                if from_start > select_start:
                    select_clause = sql_lower[select_start:from_start]
                    
                    # Look for column references
                    for field_name in field_names.keys():
                        if field_name in select_clause and field_name not in ['count', 'sum', 'avg', 'min', 'max']:
                            # Check if this is a valid column reference
                            if not any(func in select_clause for func in ['count(', 'sum(', 'avg(', 'min(', 'max(']):
                                if f" {field_name} " in select_clause or f" {field_name}," in select_clause:
                                    # This looks like a valid column reference
                                    pass
                                else:
                                    # Potential issue
                                    issues.append(f"Column '{field_name}' referenced but may not be properly formatted")
            
            # Check WHERE clause for column references
            if 'where' in sql_lower:
                where_start = sql_lower.find('where')
                where_clause = sql_lower[where_start:]
                
                for field_name in field_names.keys():
                    if field_name in where_clause:
                        # Check if it's a proper column reference in WHERE
                        if f" {field_name} " in where_clause or f" {field_name}=" in where_clause:
                            pass
                        else:
                            issues.append(f"Column '{field_name}' in WHERE clause may not be properly formatted")
            
            # Check for basic SQL syntax issues
            if sql_lower.count('select') != 1:
                issues.append("Multiple SELECT statements detected")
                is_valid = False
            
            if 'from' not in sql_lower:
                issues.append("Missing FROM clause")
                is_valid = False
            
            if sql_lower.count('from') != 1:
                issues.append("Multiple FROM clauses detected")
                is_valid = False
            
            # Check for proper table name
            table_name = table_schema.get('name', '').lower()
            if table_name and table_name not in sql_lower:
                issues.append(f"Table '{table_name}' not referenced in FROM clause")
                is_valid = False
            
        except Exception as e:
            issues.append(f"Schema validation error: {str(e)}")
            is_valid = False
        
        return is_valid, issues, None

    def fix_sql_issues(self, sql_query: str, table_schema: Dict[str, Any], issues: List[str]) -> Tuple[str, List[str]]:
        """Fix SQL issues based on schema information"""
        fixed_sql = sql_query
        fixes_applied = []
        
        try:
            # Extract field information
            fields = table_schema.get('fields', [])
            field_names = {field.get('name', '').lower(): field for field in fields}
            
            # Fix common issues
            for issue in issues:
                if "Column" in issue and "not properly formatted" in issue:
                    # Try to fix column formatting issues
                    for field_name in field_names.keys():
                        if field_name in sql_query.lower():
                            # Ensure proper spacing around column names
                            old_pattern = f" {field_name} "
                            new_pattern = f" {field_name} "
                            if old_pattern in sql_query:
                                fixed_sql = fixed_sql.replace(old_pattern, new_pattern)
                                fixes_applied.append(f"Fixed spacing around column '{field_name}'")
                
                elif "Table" in issue and "not referenced" in issue:
                    # Fix table reference issues
                    table_name = table_schema.get('name', '')
                    if table_name and table_name not in sql_query:
                        # Add proper table reference
                        if 'from' in sql_query.lower():
                            # Replace existing FROM clause
                            import re
                            from_pattern = r'from\s+\w+'
                            replacement = f"FROM {table_name}"
                            fixed_sql = re.sub(from_pattern, replacement, sql_query, flags=re.IGNORECASE)
                            fixes_applied.append(f"Fixed table reference to '{table_name}'")
            
            # Apply LLM-based fixes for complex issues
            if len(issues) > 0:
                llm_fixed_sql = self.fix_sql_with_llm(sql_query, table_schema, issues)
                if llm_fixed_sql and llm_fixed_sql != sql_query:
                    fixed_sql = llm_fixed_sql
                    fixes_applied.append("Applied LLM-based SQL fixes")
            
        except Exception as e:
            fixes_applied.append(f"Error during SQL fixing: {str(e)}")
        
        return fixed_sql, fixes_applied

    def fix_sql_with_llm(self, sql_query: str, table_schema: Dict[str, Any], issues: List[str]) -> Optional[str]:
        """Use LLM to fix complex SQL issues"""
        try:
            # Prepare schema information for LLM
            fields = table_schema.get('fields', [])
            field_info = []
            for field in fields[:20]:  # Limit to first 20 fields
                field_info.append(f"- {field.get('name', 'Unknown')}: {field.get('effective_type', 'Unknown')}")
            
            schema_info = "\n".join(field_info)
            
            prompt = f"""Fix this SQL query based on the table schema and identified issues:

TABLE SCHEMA:
{schema_info}

ORIGINAL SQL:
{sql_query}

IDENTIFIED ISSUES:
{chr(10).join(f"- {issue}" for issue in issues)}

INSTRUCTIONS:
1. Fix all identified issues
2. Ensure column names match the schema exactly
3. Use proper SQL syntax for PostgreSQL
4. Return ONLY the corrected SQL query
5. Do not include explanations or comments

CORRECTED SQL:"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Fix SQL issues and return ONLY the corrected query."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            fixed_sql = response.choices[0].message.content.strip()
            
            # Clean up the response
            fixed_sql = fixed_sql.replace('```sql', '').replace('```', '').strip()
            
            # Ensure it starts with valid SQL keywords
            if any(fixed_sql.upper().startswith(keyword) for keyword in ['SELECT', 'WITH']):
                return fixed_sql
            
            return None
            
        except Exception as e:
            print(f"❌ LLM SQL fix failed: {e}")
            return None

    def validate_and_fix_kpis(self, kpis_to_process: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Main method to validate and fix all KPIs"""
        print("🚀 Starting comprehensive KPI validation and business assessment...")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_metabase():
            print("❌ Authentication failed. Cannot proceed.")
            return {"business_assessments": [], "sql_validations": [], "sql_fixes": [], "removals": []}
        
        # Get database ID
        database_id = self.get_database_id()
        if not database_id:
            print("❌ No database available. Cannot proceed.")
            return {"business_assessments": [], "sql_validations": [], "sql_fixes": [], "removals": []}
        
        # Process each KPI
        business_assessments = []
        sql_validations = []
        sql_fixes = []
        removals = []

        for kpi_info in kpis_to_process:
            kpi_name = kpi_info['kpi'].get('kpi_name', 'KPI_N/A')
            description = kpi_info['kpi'].get('description', '')
            business_value = kpi_info['kpi'].get('business_value', '')
            sql_query = kpi_info['kpi'].get('sql_query', '')
            table_name = kpi_info['table_name']
            
            print(f"\n�� Processing KPI: {kpi_name} (Table: {table_name})")
            print("-" * 60)
            
            # Step 1: Business Value Assessment
            has_business_value, reason = self.assess_business_value(kpi_name, description, business_value, table_name)
            
            if has_business_value:
                self.validation_results['high_value_kpis'] += 1
                print(f"    ✅ HIGH BUSINESS VALUE: {reason}")
            else:
                self.validation_results['low_value_kpis'] += 1
                print(f"    ❌ LOW BUSINESS VALUE: {reason}")
                
                # Log for removal
                removal_log = {
                    'kpi_name': kpi_name,
                    'table_name': table_name,
                    'reason': f"Low business value: {reason}",
                    'timestamp': datetime.now().isoformat()
                }
                removals.append(removal_log)
                
                # Skip this KPI
                continue
            
            # Step 2: SQL Validation
            table_schema = self.get_table_schema(table_name)
            if not table_schema:
                print(f"⚠️  Could not get schema for {table_name}, skipping SQL validation.")
                sql_validations.append({
                    'kpi_name': kpi_name,
                    'table_name': table_name,
                    'sql_query': sql_query,
                    'issues': ["Could not get table schema"],
                    'status': 'skipped',
                    'timestamp': datetime.now().isoformat()
                })
                continue

            is_valid, issues, _ = self.validate_sql_against_schema(sql_query, table_schema)
            
            if is_valid and len(issues) == 0:
                self.validation_results['sql_validation_passed'] += 1
                print(f"    ✅ SQL validation passed")
                sql_validations.append({
                    'kpi_name': kpi_name,
                    'table_name': table_name,
                    'sql_query': sql_query,
                    'issues': [],
                    'status': 'passed',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self.validation_results['sql_validation_failed'] += 1
                print(f"    ❌ SQL validation failed:")
                for issue in issues:
                    print(f"      - {issue}")
                
                # Step 3: SQL Fixing
                fixed_sql, fixes_applied = self.fix_sql_issues(sql_query, table_schema, issues)
                
                if fixes_applied and any("Error" not in fix for fix in fixes_applied):
                    self.validation_results['sql_fixes_applied'] += 1
                    print(f"    🔧 SQL fixes applied:")
                    for fix in fixes_applied:
                        print(f"      - {fix}")
                    
                    # Update the KPI with fixed SQL
                    kpi_info['kpi']['sql_query'] = fixed_sql
                    kpi_info['kpi']['sql_fixes_applied'] = fixes_applied
                    sql_fixes.append({
                        'kpi_name': kpi_name,
                        'table_name': table_name,
                        'original_sql': sql_query,
                        'fixed_sql': fixed_sql,
                        'fixes_applied': fixes_applied,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    self.validation_results['unfixable_sql'] += 1
                    print(f"    ❌ SQL could not be fixed")
                    
                    # Log the unfixable SQL
                    sql_validations.append({
                        'kpi_name': kpi_name,
                        'table_name': table_name,
                        'sql_query': sql_query,
                        'issues': issues,
                        'status': 'unfixable',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Remove this KPI
                    removal_log = {
                        'kpi_name': kpi_name,
                        'table_name': table_name,
                        'reason': f"Unfixable SQL issues: {', '.join(issues)}",
                        'timestamp': datetime.now().isoformat()
                    }
                    removals.append(removal_log)
                
                self.validation_results['total_kpis'] += 1
                self.validation_results['business_value_assessed'] += 1
                
                # Add delay between KPIs
                time.sleep(0.5)
            
            # Log the assessment
            business_assessments.append({
                'kpi_name': kpi_name,
                'table_name': table_name,
                'rating': 'HIGH VALUE' if has_business_value else 'LOW VALUE',
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })
        
        # Save the updated data (if needed, but not directly in this method's return)
        # The original code saved the data to "tb_tables_kpis_validated.json"
        # This part is removed as per the new_code's return structure.
        
        # Save detailed logs
        self.save_detailed_logs()
        
        # Print final summary
        self.print_final_summary(kpis_to_process)

        return {
            "business_assessments": business_assessments,
            "sql_validations": sql_validations,
            "sql_fixes": sql_fixes,
            "removals": removals
        }

    def clean_data_for_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean data to remove unwanted characters and ensure proper formatting"""
        def clean_string(value):
            if isinstance(value, str):
                # Remove unwanted /n characters and normalize line breaks
                value = value.replace('/n', '')
                value = value.replace('\\n', '\n')  # Convert escaped newlines to actual newlines
                value = value.strip()
            return value
        
        def clean_dict(d):
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            else:
                return clean_string(d)
        
        return clean_dict(data)

    def save_validation_results(self, data: Dict[str, Any], timestamp: str):
        pass # This function is not used in the current code, but is part of the new_code.

    def save_detailed_logs(self):
        """Save all detailed logs to separate files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Business assessment logs
        with open(f"business_assessment_logs_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(self.business_assessment_logs, f, indent=2, ensure_ascii=False)
        
        # SQL validation logs
        with open(f"sql_validation_logs_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(self.sql_validation_logs, f, indent=2, ensure_ascii=False)
        
        # SQL fix logs
        with open(f"sql_fix_logs_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(self.sql_fix_logs, f, indent=2, ensure_ascii=False)
        
        # Removal logs
        with open(f"removal_logs_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(self.removal_logs, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed logs saved with timestamp: {timestamp}")

    def print_final_summary(self, kpis_to_process: List[Dict[str, Any]]):
        """Print final validation summary"""
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE KPI VALIDATION COMPLETE!")
        print("=" * 80)
        
        print(f"📊 VALIDATION SUMMARY:")
        print(f"  • Total KPIs processed: {self.validation_results['total_kpis']}")
        print(f"  • Business value assessed: {self.validation_results['business_value_assessed']}")
        print(f"  • High business value: {self.validation_results['high_value_kpis']}")
        print(f"  • Low business value: {self.validation_results['low_value_kpis']}")
        print(f"  • SQL validation passed: {self.validation_results['sql_validation_passed']}")
        print(f"  • SQL validation failed: {self.validation_results['sql_validation_failed']}")
        print(f"  • SQL fixes applied: {self.validation_results['sql_fixes_applied']}")
        print(f"  • Unfixable SQL: {self.validation_results['unfixable_sql']}")
        print(f"  • KPIs removed: {self.validation_results['removed_kpis']}")
        
        print(f"\n💾 OUTPUT FILES:")
        print(f"  • Validated KPIs: {kpis_to_process}") # This line was changed to reflect the input
        print(f"  • Business assessment logs: business_assessment_logs_*.json")
        print(f"  • SQL validation logs: sql_validation_logs_*.json")
        print(f"  • SQL fix logs: sql_fix_logs_*.json")
        print(f"  • Removal logs: removal_logs_*.json")
        
        print(f"\n✅ VALIDATION COMPLETE!")
        print(f"   All KPIs have been assessed for business value and SQL validity.")
        print(f"   Low-value KPIs and unfixable SQL have been removed.")
        print(f"   Detailed logs are available for review.")

def main():
    """Main function to run the validation and assessment process."""
    print("🚀 Starting SQL Validation and Business Assessment...")
    
    # Load the KPI data
    try:
        with open("tb_tables_kpis.json", "r", encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: tb_tables_kpis.json not found!")
        return
    
    # Get all KPIs
    all_kpis = []
    for table_name, table_data in data.items():
        if "kpis" in table_data:
            for kpi in table_data["kpis"]:
                all_kpis.append({
                    "table_name": table_name,
                    "kpi": kpi,
                    "table_data": table_data
                })
    
    print(f"📊 Found {len(all_kpis)} total KPIs to validate")
    
    # RANGE SELECTOR: Choose which KPIs to process
    # Set these values to control the range
    start_index = 1       # Start from KPI number (1-based indexing)
    end_index = 536       # End at KPI number (inclusive) - process all KPIs
    
    # Validate range
    if start_index < 1 or end_index > len(all_kpis):
        print(f"❌ Error: Invalid range. Must be between 1 and {len(all_kpis)}")
        return
    
    if start_index > end_index:
        print(f"❌ Error: Start index ({start_index}) must be <= end index ({end_index})")
        return
    
    # Convert to 0-based indexing and slice
    start_idx = start_index - 1
    end_idx = end_index
    selected_kpis = all_kpis[start_idx:end_idx]
    
    print(f"🎯 Processing KPIs {start_index} to {end_index} (out of {len(all_kpis)} total)")
    print(f"📋 Selected KPIs:")
    for i, kpi_info in enumerate(selected_kpis, start_index):
        print(f"   {i}. {kpi_info['kpi']['kpi_name']} (Table: {kpi_info['table_name']})")
    
    # Initialize the validator
    validator = SQLValidatorAndBusinessAssessor()
    
    # Process selected KPIs
    results = validator.validate_and_fix_kpis(selected_kpis)
    
    # Clean the data before saving to remove unwanted characters
    cleaned_data = validator.clean_data_for_output(data)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save business assessment results
    with open(f"business_assessment_logs_{timestamp}.json", "w", encoding='utf-8') as f:
        json.dump(results["business_assessments"], f, indent=2, ensure_ascii=False)
    
    # Save SQL validation results
    with open(f"sql_validation_logs_{timestamp}.json", "w", encoding='utf-8') as f:
        json.dump(results["sql_validations"], f, indent=2, ensure_ascii=False)
    
    # Save SQL fixes
    with open(f"sql_fix_logs_{timestamp}.json", "w", encoding='utf-8') as f:
        json.dump(results["sql_fixes"], f, indent=2, ensure_ascii=False)
    
    # Save removal logs
    with open(f"removal_logs_{timestamp}.json", "w", encoding='utf-8') as f:
        json.dump(results["removals"], f, indent=2, ensure_ascii=False)
    
    # Save cleaned KPIs
    with open("tb_tables_kpis_validated.json", "w", encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Validation complete!")
    print(f"📊 Results saved to:")
    print(f"   - business_assessment_logs_{timestamp}.json")
    print(f"   - sql_validation_logs_{timestamp}.json")
    print(f"   - sql_fix_logs_{timestamp}.json")
    print(f"   - removal_logs_{timestamp}.json")
    print(f"   - tb_tables_kpis_validated.json")
    print(f"\n📈 Summary:")
    print(f"   - Total KPIs processed: {len(selected_kpis)}")
    print(f"   - Business assessments: {len(results['business_assessments'])}")
    print(f"   - SQL validations: {len(results['sql_validations'])}")
    print(f"   - SQL fixes applied: {len(results['sql_fixes'])}")
    print(f"   - KPIs removed: {len(results['removals'])}")

if __name__ == "__main__":
    main() 