#!/usr/bin/env python3
"""
Process TB_ tables to generate KPIs
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metabase_kpi_extractor import MetabaseKPIExtractor

def get_tb_tables(extractor):
    """Get all tables starting with 'TB_'"""
    try:
        print("🔍 Finding tables starting with 'TB_'...")
        
        # Get tables directly from the /api/table endpoint
        tables_url = f"{extractor.metabase_url}/api/table"
        tables_response = requests.get(tables_url, headers=extractor.headers)
        if tables_response.status_code != 200:
            print(f"Failed to get tables: {tables_response.status_code}")
            return []
        
        all_tables = tables_response.json()
        tb_tables = []
        
        for table in all_tables:
            table_name = table.get('name', '')
            if table_name.upper().startswith('TB_'):
                tb_tables.append(table)
        
        print(f"✅ Found {len(tb_tables)} tables starting with 'TB_'")
        return tb_tables
        
    except Exception as e:
        print(f"Failed to get TB_ tables: {e}")
        return []

def process_tb_table(extractor, table, index, total):
    """Process a single TB_ table"""
    table_name = table.get('name', 'Unknown')
    table_id = table.get('id')
    
    print(f"\n{'='*60}")
    print(f"📊 PROCESSING TABLE {index}/{total}: {table_name}")
    print(f"{'='*60}")
    
    # Get table metadata
    print(f"🔍 Fetching metadata for table: {table_name}")
    metadata = extractor.get_table_metadata(table_id)
    if not metadata:
        print(f"❌ Failed to get metadata for table: {table_name}")
        return None
    
    # Show table information that will be fed to the prompt
    print(f"\n📋 TABLE INFORMATION FOR PROMPT:")
    print(f"   Table Name: {table_name}")
    print(f"   Description: {metadata.get('table_info', {}).get('description', 'N/A')}")
    print(f"   Fields Count: {len(metadata.get('fields', []))}")
    print(f"   Related Tables: {len(metadata.get('related_tables', []))}")
    
    # Show sample fields
    fields = metadata.get('fields', [])
    if fields:
        print(f"   Sample Fields: {', '.join([f.get('name', '') for f in fields[:8]])}")
        if len(fields) > 8:
            print(f"   ... and {len(fields) - 8} more fields")
    
    # Generate KPIs
    print(f"\n🤖 Generating KPIs with LLM...")
    kpis = extractor.generate_kpis_with_llm(metadata)
    
    if kpis:
        print(f"✅ Successfully generated {len(kpis)} KPIs!")
        
        # Display KPIs
        for i, kpi in enumerate(kpis, 1):
            print(f"\n   📊 KPI {i}:")
            print(f"      Name: {kpi.get('kpi_name', 'N/A')}")
            print(f"      Description: {kpi.get('description', 'N/A')}")
            print(f"      Business Value: {kpi.get('business_value', 'N/A')}")
            print(f"      SQL Query: {kpi.get('sql_query', 'N/A')}")
            print(f"      Output Format: {kpi.get('output_format', 'N/A')}")
        
        return {
            "table_name": table_name,
            "table_id": table_id,
            "metadata": metadata,
            "kpis": kpis
        }
    else:
        print("❌ No KPIs generated")
        return None

def main():
    """Main function to process TB_ tables"""
    print("🚀 TB_ TABLES KPI EXTRACTION")
    print("="*60)
    
    # Initialize the extractor
    extractor = MetabaseKPIExtractor()
    
    # Authenticate
    if not extractor.authenticate_metabase():
        print("❌ Authentication failed. Exiting.")
        return
    
    # Get TB_ tables
    tb_tables = get_tb_tables(extractor)
    if not tb_tables:
        print("❌ No TB_ tables found. Exiting.")
        return
    
    # Show all TB_ tables found
    print(f"\n📋 ALL TB_ TABLES FOUND:")
    for i, table in enumerate(tb_tables, 1):
        table_name = table.get('name', 'Unknown')
        table_id = table.get('id')
        print(f"   {i}. {table_name} (ID: {table_id})")
    
            # Process the 15 most important TB_ tables
        important_table_names = [
            "tb_user", "tb_payment", "tb_market_order", "tb_partner", "tb_market_product",
            "tb_user_activity_log", "tb_user_statistics", "tb_partner_statistics", 
            "tb_market_cart", "tb_payment_method", "tb_rfq", "tb_quotation", 
            "tb_subscribe_plan", "tb_point", "tb_notification"
        ]
        
        # Find these specific tables
        important_tables = []
        for table_name in important_table_names:
            for table in tb_tables:
                if table.get('name') == table_name:
                    important_tables.append(table)
                    break
        
        if len(important_tables) < 15:
            print(f"⚠️  Warning: Only found {len(important_tables)} out of 15 important tables")
            # Fill remaining slots with other TB_ tables
            remaining_slots = 15 - len(important_tables)
            for table in tb_tables:
                if table not in important_tables and len(important_tables) < 15:
                    important_tables.append(table)
        
        tables_to_process = important_tables
        print(f"\n🎯 PROCESSING {len(tables_to_process)} IMPORTANT TB_ TABLES:")
    
    all_results = {}
    
    for i, table in enumerate(tables_to_process, 1):
        result = process_tb_table(extractor, table, i, len(tables_to_process))
        if result:
            all_results[table.get('name')] = result
        
        # Add delay between tables
        if i < len(tables_to_process):
            print(f"\n⏳ Waiting 3 seconds before next table...")
            import time
            time.sleep(3)
    
    # Save results
    if all_results:
        output_file = "tb_tables_kpis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 PROCESSING COMPLETE!")
        print(f"📊 Tables processed: {len(all_results)}")
        
        total_kpis = sum(len(table_data.get('kpis', [])) for table_data in all_results.values())
        print(f"📈 Total KPIs generated: {total_kpis}")
        
        for table_name, table_data in all_results.items():
            kpi_count = len(table_data.get('kpis', []))
            print(f"   - {table_name}: {kpi_count} KPIs")
        
        print(f"\n💾 Results saved to: {output_file}")
    else:
        print("❌ No results generated")

if __name__ == "__main__":
    main() 