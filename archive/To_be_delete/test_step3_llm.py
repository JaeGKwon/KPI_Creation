#!/usr/bin/env python3
"""
Test Step 3: LLM KPI Generation
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metabase_kpi_extractor import MetabaseKPIExtractor

def test_llm_kpi_generation():
    """Test LLM KPI generation"""
    print("="*50)
    print("TESTING STEP 3: LLM KPI GENERATION")
    print("="*50)
    
    try:
        # Initialize the extractor
        extractor = MetabaseKPIExtractor()
        
        # Check if OpenAI is configured
        if not extractor.openai_client:
            print("❌ OpenAI client not available. Please set OPENAI_API_KEY in your environment.")
            return False
        
        # First authenticate with Metabase
        if not extractor.authenticate_metabase():
            print("❌ Authentication failed! Cannot proceed with LLM test.")
            return False
        
        # Get sample metadata (either from existing file or create mock data)
        sample_metadata_file = None
        
        # Look for existing metadata files
        for filename in os.listdir('.'):
            if filename.startswith('sample_metadata_') and filename.endswith('.json'):
                sample_metadata_file = filename
                break
        
        if sample_metadata_file:
            print(f"📁 Using existing metadata file: {sample_metadata_file}")
            with open(sample_metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            print("📝 Creating mock metadata for testing...")
            # Create mock metadata for testing
            metadata = {
                "table_info": {
                    "name": "orders",
                    "id": 1,
                    "description": "Customer orders table"
                },
                "fields": [
                    {"name": "id", "base_type": "type/Integer", "description": "Order ID"},
                    {"name": "customer_id", "base_type": "type/Integer", "description": "Customer ID"},
                    {"name": "order_date", "base_type": "type/Date", "description": "Order date"},
                    {"name": "total_amount", "base_type": "type/Decimal", "description": "Order total"},
                    {"name": "status", "base_type": "type/Text", "description": "Order status"}
                ],
                "related_tables": [
                    {
                        "name": "customers",
                        "id": 2,
                        "description": "Customer information",
                        "fields": [
                            {"name": "id", "base_type": "type/Integer", "description": "Customer ID"},
                            {"name": "name", "base_type": "type/Text", "description": "Customer name"},
                            {"name": "email", "base_type": "type/Text", "description": "Customer email"}
                        ]
                    }
                ]
            }
        
        # Test KPI generation
        print("\n🤖 Testing KPI generation with LLM...")
        kpis = extractor.generate_kpis_with_llm(metadata)
        
        if kpis:
            print(f"✅ Successfully generated {len(kpis)} KPIs!")
            
            # Display KPIs
            for i, kpi in enumerate(kpis, 1):
                print(f"\n📊 KPI {i}:")
                print(f"   Name: {kpi.get('kpi_name', 'N/A')}")
                print(f"   Description: {kpi.get('description', 'N/A')}")
                print(f"   Business Value: {kpi.get('business_value', 'N/A')}")
                print(f"   SQL Query: {kpi.get('sql_query', 'N/A')}")
                print(f"   Output Format: {kpi.get('output_format', 'N/A')}")
            
            # Save KPIs to file
            output_file = "test_kpis.json"
            with open(output_file, 'w') as f:
                json.dump(kpis, f, indent=2)
            print(f"\n💾 KPIs saved to: {output_file}")
            
            return True
        else:
            print("❌ No KPIs generated")
            return False
            
    except Exception as e:
        print(f"❌ Error during LLM test: {e}")
        return False

if __name__ == "__main__":
    success = test_llm_kpi_generation()
    if success:
        print("\n🎉 Step 3 test passed!")
    else:
        print("\n💥 Step 3 test failed!")
        print("Please check your OpenAI API key and configuration.") 