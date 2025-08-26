#!/usr/bin/env python3
"""
Metabase KPI Extractor with improved SQL validation
"""

import os
import json
import time
import requests
import openai
from typing import List, Dict, Any
from dotenv import load_dotenv

class MetabaseKPIExtractor:
    def __init__(self):
        """Initialize the Metabase KPI Extractor"""
        load_dotenv()
        
        # Metabase configuration
        self.metabase_url = os.getenv('METABASE_URL')
        self.metabase_username = os.getenv('METABASE_USERNAME')
        self.metabase_password = os.getenv('METABASE_PASSWORD')
        
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Initialize OpenAI client
        if self.openai_api_key:
            try:
                # For openai==0.28.1
                openai.api_key = self.openai_api_key
                self.openai_client = openai
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            self.openai_client = None
        
        # Session management
        self.session_id = None
        self.headers = {}
        
        if not all([self.metabase_url, self.metabase_username, self.metabase_password]):
            print("Warning: Missing Metabase credentials")
        
        if not self.openai_api_key:
            print("Warning: Missing OpenAI API key")

    def authenticate_metabase(self) -> bool:
        """Authenticate with Metabase and get session ID"""
        print("Authenticating with Metabase...")
        
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
                    print(f"Successfully authenticated. Session ID: {self.session_id}")
                    return True
                else:
                    print("Authentication failed: No session ID received")
                    return False
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def get_database_list(self) -> List[Dict[str, Any]]:
        """Get list of databases from Metabase"""
        print("Fetching database list...")
        
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
                
                print(f"Found {len(databases)} databases")
                return databases
            else:
                print(f"Failed to get databases: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting databases: {e}")
            return []

    def search_tables_by_name(self, table_names: List[str]) -> List[Dict[str, Any]]:
        """Search for tables by name across all databases"""
        print(f"Searching for tables: {table_names}")
        
        try:
            # Get all tables from the /api/table endpoint
            tables_url = f"{self.metabase_url}/api/table"
            tables_response = requests.get(tables_url, headers=self.headers)
            
            if tables_response.status_code != 200:
                print(f"Failed to get tables: {tables_response.status_code}")
                return []
            
            all_tables = tables_response.json()
            matching_tables = []
            
            # Filter tables by name
            for table in all_tables:
                table_name = table.get('name', '')
                if any(name.lower() in table_name.lower() for name in table_names):
                    matching_tables.append(table)
            
            print(f"Found {len(matching_tables)} matching tables out of {len(all_tables)} total tables")
            return matching_tables
            
        except Exception as e:
            print(f"Error searching tables: {e}")
            return []

    def get_table_metadata(self, table_id: int) -> Dict[str, Any]:
        """Get comprehensive metadata for a specific table"""
        print(f"Fetching metadata for table ID: {table_id}")
        
        try:
            # Get table information
            table_url = f"{self.metabase_url}/api/table/{table_id}"
            table_response = requests.get(table_url, headers=self.headers)
            
            if table_response.status_code != 200:
                print(f"Failed to get table info: {table_response.status_code}")
                return {}
            
            table_info = table_response.json()
            
            # Get table fields
            fields_url = f"{self.metabase_url}/api/table/{table_id}/query_metadata"
            fields_response = requests.get(fields_url, headers=self.headers)
            
            fields = []
            if fields_response.status_code == 200:
                fields_data = fields_response.json()
                fields = fields_data.get('fields', [])
            
            # Get related tables (simplified - could be enhanced)
            related_tables = []
            
            # Compile metadata
            metadata = {
                "table_info": table_info,
                "fields": fields,
                "related_tables": related_tables
            }
            
            print(f"Successfully fetched metadata for table: {table_info.get('name', 'Unknown')}")
            return metadata
            
        except Exception as e:
            print(f"Error getting table metadata: {e}")
            return {}

    def generate_kpis_for_table(self, table_name, table_metadata):
        """Generate KPIs for a specific table using OpenAI"""
        print(f"Generating KPIs for table: {table_name}")
        
        # Get related tables information
        related_tables = table_metadata.get("related_tables", [])
        
        # SIMPLIFIED: Extract only essential table information
        table_info = table_metadata.get("table_info", {})
        simplified_table_info = {
            "name": table_info.get("name", table_name),
            "description": table_info.get("description", "No description"),
            "schema": table_info.get("schema", "Unknown"),
            "entity_type": table_info.get("entity_type", "Unknown")
        }
        
        # ENHANCED: Extract detailed field information (name, type, description, FK relationships, semantic type)
        fields = table_metadata.get("fields", [])
        simplified_fields = []
        field_details = []
        
        # Select only the most important fields (first 20 to reduce tokens)
        important_fields = fields[:20] if len(fields) > 20 else fields
        
        for field in important_fields:
            field_name = field.get('name', '')
            field_type = field.get('effective_type', 'Unknown')
            field_description = field.get('description', '')
            semantic_type = field.get('semantic_type', '')
            
            if field_name:
                # Basic field info for prompt
                simplified_fields.append(f"{field_name} ({field_type})")
                
                # Detailed field info with relationships (for output)
                field_info = {
                    'name': field_name,
                    'type': field_type,
                    'description': field_description or 'No description',
                    'semantic_type': semantic_type
                }
                
                # Add foreign key information if available
                if field.get('fk_target_field_id'):
                    target_info = field.get('target', {})
                    if target_info:
                        field_info['foreign_key'] = {
                            'target_table': target_info.get('table_id', 'Unknown'),
                            'target_field': target_info.get('name', 'Unknown'),
                            'relationship': f"FK to {target_info.get('name', 'Unknown')}"
                        }
                
                field_details.append(field_info)
        
        # Add count of total fields for context
        if len(fields) > 20:
            simplified_fields.append(f"... and {len(fields) - 20} more fields")
        
        # SIMPLIFIED: Extract only essential related table information
        simplified_related = []
        for rt in related_tables:
            rt_name = rt.get('name', 'Unknown')
            simplified_related.append(rt_name)
        
        # Create a comprehensive prompt for KPI generation
        prompt = f"""You are the super guru of data Analytics and SQL expert. You are given table information and need to generate AT LEAST 15-20 useful KPIs with proper SQL statements.

Table Information for "{table_name}":
{json.dumps(simplified_table_info, indent=2)}

Field Information (with relationships):
{json.dumps(field_details, indent=2)}

Related Tables: {', '.join(simplified_related)}

CRITICAL SQL VALIDATION RULES - ALWAYS FOLLOW THESE:
1. NULL HANDLING: Always check for NULL values before date operations or calculations
2. DATA VALIDATION: Validate data exists and is in correct format before using
3. BUSINESS LOGIC: Consider that not all records complete the full business process
4. DATE LOGIC: Ensure date operations make sense (e.g., purchase_date > quotation_date)
5. SAFE CALCULATIONS: Use CASE statements for conditional logic and safe calculations
6. CONVERSION RATES: For conversion KPIs, handle both numerator and denominator properly
7. TIME WINDOWS: Use reasonable timeframes for business processes
8. STATUS FIELDS: Use status fields when available for more accurate business state
9. MULTI-TABLE JOINS: Use JOINs when foreign key relationships exist for richer insights
10. RELATIONSHIP AWARENESS: Leverage table relationships for comprehensive business metrics

EXAMPLES OF GOOD SQL:
- Use CASE WHEN field IS NOT NULL THEN calculation ELSE NULL END
- Check date validity: WHERE date_field IS NOT NULL AND date_field > '1900-01-01'
- Handle conversions: COUNT(CASE WHEN status = 'completed' THEN 1 END) / COUNT(*)
- Safe date differences: CASE WHEN end_date > start_date THEN DATEDIFF(end_date, start_date) ELSE NULL END
- Multi-table joins: JOIN related_table ON main_table.fk_field = related_table.pk_field
- Relationship metrics: Use JOINs to combine user data with order data for user behavior analysis

IMPORTANT: You MUST respond with ONLY a valid JSON array. Do not include any other text, explanations, or formatting.

Respond with this exact JSON structure:
[
  {{
    "kpi_name": "KPI Name",
    "description": "What this KPI measures",
    "business_value": "Why this KPI is important",
    "sql_query": "Validated, safe SQL that handles NULLs and edge cases (use JOINs when beneficial)",
    "output_format": "What the result represents",
    "table_name": "{table_name}"
  }}
]

Focus on:
- Operational KPIs, conversion rates, efficiency metrics
- Business performance indicators
- Multi-table insights using JOINs when relationships exist
- User behavior analysis combining multiple tables
- Financial metrics across related business processes
- Process efficiency using workflow tables

Generate AT LEAST 15-20 KPIs in the JSON array format above."""

        # Generate KPIs using OpenAI
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data analytics expert specializing in creating meaningful KPIs and robust SQL queries. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            # Extract the response content
            kpi_content = response.choices[0].message.content
            
            # Parse the KPIs from the response
            kpis = self.parse_kpis_from_response(kpi_content, table_name)
            
            # Return both KPIs and field details for saving
            return {
                'kpis': kpis,
                'field_details': field_details,
                'total_fields': len(fields),
                'fields_used': len(important_fields),
                'foreign_keys': len([f for f in fields if f.get('fk_target_field_id')])
            }
            
        except Exception as e:
            print(f"Error generating KPIs for {table_name}: {str(e)}")
            return {
                'kpis': [],
                'field_details': [],
                'total_fields': 0,
                'fields_used': 0,
                'foreign_keys': 0
            }

    def parse_kpis_from_response(self, response_content, table_name):
        """Parse KPIs from LLM response and validate them"""
        try:
            # Find JSON array in the response
            start_idx = response_content.find('[')
            end_idx = response_content.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                print("No JSON array found in LLM response")
                print(f"Response content: {response_content[:200]}...")
                return []
            
            json_content = response_content[start_idx:end_idx]
            kpis = json.loads(json_content)
            
            # Validate and clean each KPI
            validated_kpis = []
            for kpi in kpis:
                if isinstance(kpi, dict):
                    # Ensure required fields exist
                    validated_kpi = {
                        'kpi_name': kpi.get('kpi_name', 'Unnamed KPI'),
                        'description': kpi.get('description', 'No description provided'),
                        'business_value': kpi.get('business_value', 'Business value not specified'),
                        'sql_query': kpi.get('sql_query', 'SELECT 1'),
                        'output_format': kpi.get('output_format', 'Not specified'),
                        'table_name': table_name
                    }
                    
                    # Validate SQL query for common issues
                    sql_query = validated_kpi['sql_query'].strip()
                    if sql_query and not sql_query.startswith('SELECT'):
                        print(f"Warning: Invalid SQL query for KPI '{validated_kpi['kpi_name']}': {sql_query}")
                    
                    validated_kpis.append(validated_kpi)
            
            print(f"Successfully generated {len(validated_kpis)} validated KPIs")
            return validated_kpis
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from LLM response: {e}")
            print(f"Raw response: {response_content}")
            return []
        except Exception as e:
            print(f"Error parsing KPIs: {str(e)}")
            return []

def main():
    """Main function to run the KPI extraction process"""
    print("Metabase KPI Extractor - Main function")
    print("Use the regenerate_kpis_improved.py script instead")

if __name__ == "__main__":
    main() 