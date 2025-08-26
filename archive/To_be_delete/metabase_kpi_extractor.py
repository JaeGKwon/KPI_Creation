#!/usr/bin/env python3
"""
Metabase KPI Extractor
Extracts table metadata from Metabase API and generates KPIs using LLM
"""

import os
import json
import requests
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class MetabaseKPIExtractor:
    def __init__(self):
        """Initialize the Metabase KPI Extractor"""
        self.metabase_url = os.getenv('METABASE_URL')
        self.metabase_username = os.getenv('METABASE_USERNAME')
        self.metabase_password = os.getenv('METABASE_PASSWORD')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Initialize OpenAI client
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            try:
                # Use the older API style for openai==0.28.1
                self.openai_client = openai
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            self.openai_client = None
            
        # Metabase session
        self.session_id = None
        self.headers = {}
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required environment variables are set"""
        required_vars = {
            'METABASE_URL': self.metabase_url,
            'METABASE_USERNAME': self.metabase_username,
            'METABASE_PASSWORD': self.metabase_password,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        if not self.openai_api_key:
            print("Warning: OpenAI API key not found. LLM functionality will be disabled.")
    
    def authenticate_metabase(self) -> bool:
        """Authenticate with Metabase and get session ID"""
        try:
            print("Authenticating with Metabase...")
            
            auth_url = f"{self.metabase_url}/api/session"
            auth_data = {
                "username": self.metabase_username,
                "password": self.metabase_password
            }
            
            response = requests.post(auth_url, json=auth_data)
            response.raise_for_status()
            
            auth_response = response.json()
            self.session_id = auth_response.get('id')
            
            if self.session_id:
                self.headers = {
                    'X-Metabase-Session': self.session_id,
                    'Content-Type': 'application/json'
                }
                print(f"Successfully authenticated. Session ID: {self.session_id}")
                return True
            else:
                print("Failed to get session ID from authentication response")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {e}")
            return False
    
    def get_database_list(self) -> List[Dict[str, Any]]:
        """Get list of all databases from Metabase"""
        try:
            print("Fetching database list...")
            url = f"{self.metabase_url}/api/database"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            databases = response.json()
            # Handle both list and dict responses
            if isinstance(databases, dict):
                if 'data' in databases:
                    databases = databases['data']
                else:
                    # Convert dict to list if it's a single database
                    databases = [databases]
            
            print(f"Found {len(databases)} databases")
            return databases
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch database list: {e}")
            return []
    
    def get_table_metadata(self, table_id: int) -> Dict[str, Any]:
        """Get detailed metadata for a specific table"""
        try:
            print(f"Fetching metadata for table ID: {table_id}")
            
            # Get table information
            table_url = f"{self.metabase_url}/api/table/{table_id}"
            table_response = requests.get(table_url, headers=self.headers)
            table_response.raise_for_status()
            table_data = table_response.json()
            
            # Get table fields/columns
            fields_url = f"{self.metabase_url}/api/table/{table_id}/query_metadata"
            fields_response = requests.get(fields_url, headers=self.headers)
            fields_response.raise_for_status()
            fields_data = fields_response.json()
            
            # Optimize table info - keep only essential properties
            optimized_table_info = {
                "name": table_data.get("name"),
                "description": table_data.get("description"),
                "schema": table_data.get("schema"),
                "entity_type": table_data.get("entity_type")
            }
            
            # Optimize fields - keep only essential properties
            optimized_fields = []
            for field in fields_data.get("fields", []):
                optimized_field = {
                    "name": field.get("name"),
                    "type": field.get("effective_type", field.get("database_type")),
                    "semantic_type": field.get("semantic_type"),
                    "description": field.get("description"),
                    "position": field.get("position")
                }
                optimized_fields.append(optimized_field)
            
            # Combine optimized table and fields data
            metadata = {
                "table_info": optimized_table_info,
                "fields": optimized_fields,
                "related_tables": []
            }
            
            # Get related tables (foreign key relationships) - also optimized
            if "fks" in table_data:
                for fk in table_data["fks"]:
                    related_table_id = fk.get("destination_table_id")
                    if related_table_id:
                        try:
                            related_table_url = f"{self.metabase_url}/api/table/{related_table_id}"
                            related_response = requests.get(related_table_url, headers=self.headers)
                            if related_response.status_code == 200:
                                related_table = related_response.json()
                                
                                # Get fields for related table
                                related_fields_url = f"{self.metabase_url}/api/table/{related_table_id}/query_metadata"
                                related_fields_response = requests.get(related_fields_url, headers=self.headers)
                                if related_fields_response.status_code == 200:
                                    related_fields = related_fields_response.json()
                                    
                                    # Optimize related table fields too
                                    optimized_related_fields = []
                                    for field in related_fields.get("fields", []):
                                        optimized_related_field = {
                                            "name": field.get("name"),
                                            "type": field.get("effective_type", field.get("database_type")),
                                            "semantic_type": field.get("semantic_type"),
                                            "description": field.get("description"),
                                            "position": field.get("position")
                                        }
                                        optimized_related_fields.append(optimized_related_field)
                                    
                                    related_table["fields"] = optimized_related_fields
                                
                                # Optimize related table info
                                optimized_related_table = {
                                    "name": related_table.get("name"),
                                    "description": related_table.get("description"),
                                    "schema": related_table.get("schema"),
                                    "entity_type": related_table.get("entity_type")
                                }
                                
                                metadata["related_tables"].append(optimized_related_table)
                        except Exception as e:
                            print(f"Failed to fetch related table {related_table_id}: {e}")
            
            print(f"Successfully fetched metadata for table: {table_data.get('name', 'Unknown')}")
            return metadata
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch table metadata: {e}")
            return {}
    
    def search_tables_by_name(self, table_names: List[str]) -> List[Dict[str, Any]]:
        """Search for tables by name and return their metadata"""
        try:
            print(f"Searching for tables: {table_names}")
            
            # Get tables directly from the /api/table endpoint
            tables_url = f"{self.metabase_url}/api/table"
            tables_response = requests.get(tables_url, headers=self.headers)
            if tables_response.status_code != 200:
                print(f"Failed to get tables: {tables_response.status_code}")
                return []
            
            all_tables = tables_response.json()
            matching_tables = []
            
            for table in all_tables:
                table_name = table.get('name', '').lower()
                if any(search_name.lower() in table_name for search_name in table_names):
                    print(f"Found matching table: {table['name']} (ID: {table['id']})")
                    matching_tables.append(table)
            
            print(f"Found {len(matching_tables)} matching tables out of {len(all_tables)} total tables")
            return matching_tables
            
        except Exception as e:
            print(f"Failed to search tables: {e}")
            return []
    
    def generate_kpis_with_llm(self, table_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate KPIs using OpenAI API"""
        if not self.openai_client:
            print("OpenAI client not available. Skipping KPI generation.")
            return []
        
        try:
            print("Generating KPIs with LLM...")
            
            # Prepare the prompt
            table_name = table_metadata.get("table_info", {}).get("name", "Unknown")
            related_tables = table_metadata.get("related_tables", [])
            
            # Create a comprehensive prompt for KPI generation
            prompt = f"""You are the super guru of data Analytics and SQL expert. You are given table information and need to generate AT LEAST 15-20 useful KPIs with proper SQL statements.

Table Information for "{table_name}":
{json.dumps(table_metadata.get("table_info", {}), indent=2)}

Fields: {', '.join([f"{f['name']} ({f['type']})" for f in table_metadata.get("fields", [])])}

Related Tables: {', '.join([f"{rt['name']} (ID: {rt['id']})" for rt in related_tables])}

CRITICAL SQL VALIDATION RULES - ALWAYS FOLLOW THESE:
1. NULL HANDLING: Always check for NULL values before date operations or calculations
2. DATA VALIDATION: Validate data exists and is in correct format before using
3. BUSINESS LOGIC: Consider that not all records complete the full business process
4. DATE LOGIC: Ensure date operations make sense (e.g., purchase_date > quotation_date)
5. SAFE CALCULATIONS: Use CASE statements for conditional logic and safe calculations
6. CONVERSION RATES: For conversion KPIs, handle both numerator and denominator properly
7. TIME WINDOWS: Use reasonable timeframes for business processes
8. STATUS FIELDS: Use status fields when available for more accurate business state

EXAMPLES OF GOOD SQL:
- Use CASE WHEN field IS NOT NULL THEN calculation ELSE NULL END
- Check date validity: WHERE date_field IS NOT NULL AND date_field > '1900-01-01'
- Handle conversions: COUNT(CASE WHEN status = 'completed' THEN 1 END) / COUNT(*)
- Safe date differences: CASE WHEN end_date > start_date THEN DATEDIFF(end_date, start_date) ELSE NULL END

Please provide the list of the KPIs and SQL statement to get those KPIs. Each KPI should include:
- kpi_name: Clear, descriptive name
- description: What this KPI measures
- business_value: Why this KPI is important
- sql_query: Validated, safe SQL that handles NULLs and edge cases
- output_format: What the result represents
- table_name: The table this KPI is based on

Focus on operational KPIs, conversion rates, efficiency metrics, and business performance indicators."""

            # Generate KPIs using OpenAI
            try:
                response = self.openai_client.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a data analytics expert specializing in creating meaningful KPIs and robust SQL queries."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.3
                )
                
                # Extract the response content
                kpi_content = response.choices[0].message.content
                
                # Parse the KPIs from the response
                kpis = self.parse_kpis_from_response(kpi_content, table_name)
                
                return kpis
                
            except Exception as e:
                print(f"Error generating KPIs for {table_name}: {str(e)}")
                return []
                
        except Exception as e:
            print(f"Failed to generate KPIs with LLM: {e}")
            return []
    
    def process_table_list(self, table_names: List[str]) -> Dict[str, Any]:
        """Process a list of table names and generate KPIs for each"""
        print(f"Starting to process {len(table_names)} table names...")
        
        # Step 1: Authenticate with Metabase
        if not self.authenticate_metabase():
            print("Authentication failed. Exiting.")
            return {}
        
        # Step 2: Search for tables by name
        matching_tables = self.search_tables_by_name(table_names)
        if not matching_tables:
            print("No matching tables found. Exiting.")
            return {}
        
        # Step 3: Extract metadata for each table
        all_results = {}
        
        for table in matching_tables:
            table_name = table.get('name', 'Unknown')
            table_id = table.get('id')
            
            print(f"\n{'='*50}")
            print(f"Processing table: {table_name}")
            print(f"{'='*50}")
            
            # Get table metadata
            metadata = self.get_table_metadata(table_id)
            if not metadata:
                print(f"Failed to get metadata for table: {table_name}")
                continue
            
            # Step 4: Generate KPIs with LLM
            kpis = self.generate_kpis_with_llm(metadata)
            
            # Step 5: Format results
            table_result = {
                "table_name": table_name,
                "table_id": table_id,
                "metadata": metadata,
                "kpis": kpis
            }
            
            all_results[table_name] = table_result
            
            # Add delay to avoid rate limiting
            time.sleep(2)
        
        return all_results
    
    def save_results(self, results: Dict[str, Any], filename: str = "kpi_results.json"):
        """Save results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {filename}")
        except Exception as e:
            print(f"Failed to save results: {e}")

    def generate_kpis_for_table(self, table_name, table_metadata):
        """Generate KPIs for a specific table using OpenAI"""
        print(f"Generating KPIs for table: {table_name}")
        
        # Get related tables information
        related_tables = table_metadata.get("related_tables", [])
        
        # Create a comprehensive prompt for KPI generation
        prompt = f"""You are the super guru of data Analytics and SQL expert. You are given table information and need to generate AT LEAST 15-20 useful KPIs with proper SQL statements.

Table Information for "{table_name}":
{json.dumps(table_metadata.get("table_info", {}), indent=2)}

Fields: {', '.join([f"{f['name']} ({f['type']})" for f in table_metadata.get("fields", [])])}

Related Tables: {', '.join([f"{rt['name']} (ID: {rt['id']})" for rt in related_tables])}

CRITICAL SQL VALIDATION RULES - ALWAYS FOLLOW THESE:
1. NULL HANDLING: Always check for NULL values before date operations or calculations
2. DATA VALIDATION: Validate data exists and is in correct format before using
3. BUSINESS LOGIC: Consider that not all records complete the full business process
4. DATE LOGIC: Ensure date operations make sense (e.g., purchase_date > quotation_date)
5. SAFE CALCULATIONS: Use CASE statements for conditional logic and safe calculations
6. CONVERSION RATES: For conversion KPIs, handle both numerator and denominator properly
7. TIME WINDOWS: Use reasonable timeframes for business processes
8. STATUS FIELDS: Use status fields when available for more accurate business state

EXAMPLES OF GOOD SQL:
- Use CASE WHEN field IS NOT NULL THEN calculation ELSE NULL END
- Check date validity: WHERE date_field IS NOT NULL AND date_field > '1900-01-01'
- Handle conversions: COUNT(CASE WHEN status = 'completed' THEN 1 END) / COUNT(*)
- Safe date differences: CASE WHEN end_date > start_date THEN DATEDIFF(end_date, start_date) ELSE NULL END

Please provide the list of the KPIs and SQL statement to get those KPIs. Each KPI should include:
- kpi_name: Clear, descriptive name
- description: What this KPI measures
- business_value: Why this KPI is important
- sql_query: Validated, safe SQL that handles NULLs and edge cases
- output_format: What the result represents
- table_name: The table this KPI is based on

Focus on operational KPIs, conversion rates, efficiency metrics, and business performance indicators."""

        # Generate KPIs using OpenAI
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data analytics expert specializing in creating meaningful KPIs and robust SQL queries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            # Extract the response content
            kpi_content = response.choices[0].message.content
            
            # Debug: Print the response to see what we're getting
            print(f"DEBUG: LLM Response length: {len(kpi_content)}")
            print(f"DEBUG: First 500 chars: {kpi_content[:500]}")
            print(f"DEBUG: Last 500 chars: {kpi_content[-500:]}")
            
            # Parse the KPIs from the response
            kpis = self.parse_kpis_from_response(kpi_content, table_name)
            
            return kpis
            
        except Exception as e:
            print(f"Error generating KPIs for {table_name}: {str(e)}")
            return []

    def parse_kpis_from_response(self, response_content, table_name):
        """Parse KPIs from LLM response and validate them"""
        try:
            # Find JSON array in the response
            start_idx = response_content.find('[')
            end_idx = response_content.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                print("No JSON array found in LLM response")
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
    
    # Example table names to search for
    table_names = [
        "users",
        "orders", 
        "products",
        "customers"
    ]
    
    # Initialize the extractor
    extractor = MetabaseKPIExtractor()
    
    # Process the table list
    results = extractor.process_table_list(table_names)
    
    if results:
        # Save results
        extractor.save_results(results)
        
        # Print summary
        print("\n" + "="*60)
        print("KPI EXTRACTION COMPLETE")
        print("="*60)
        
        total_kpis = sum(len(table_data.get('kpis', [])) for table_data in results.values())
        print(f"Total tables processed: {len(results)}")
        print(f"Total KPIs generated: {total_kpis}")
        
        for table_name, table_data in results.items():
            kpi_count = len(table_data.get('kpis', []))
            print(f"- {table_name}: {kpi_count} KPIs")
    else:
        print("No results generated. Check the logs above for errors.")


if __name__ == "__main__":
    main() 