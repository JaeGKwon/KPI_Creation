#!/usr/bin/env python3
"""
Regenerate KPIs for selected TB tables with improved SQL validation
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metabase_kpi_extractor_fixed import MetabaseKPIExtractor

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize the extractor
    extractor = MetabaseKPIExtractor()
    
    # Test authentication
    if not extractor.authenticate_metabase():
        print("❌ Authentication failed. Please check your credentials.")
        return
    
    print("✅ Authentication successful!")
    
    # Get database list
    databases = extractor.get_database_list()
    if not databases:
        print("❌ Failed to get database list")
        return
    
    print(f"✅ Found {len(databases)} databases")
    
    # Define the important TB tables to process
    important_tb_tables = [
        "tb_market_order",      # Core business table
        "tb_user",              # User management
        "tb_product",           # Product catalog
        "tb_inventory",         # Inventory management
        "tb_supplier",          # Supplier information
        "tb_customer",          # Customer data
        "tb_transaction",       # Financial transactions
        "tb_order_item",        # Order details
        "tb_payment",           # Payment processing
        "tb_shipping",          # Shipping/logistics
        "tb_category",          # Product categorization
        "tb_review",            # Customer reviews
        "tb_notification",      # System notifications
        "tb_audit_log",         # System audit trail
        "tb_configuration"      # System configuration
    ]
    
    print(f"🎯 Processing {len(important_tb_tables)} important TB tables...")
    
    all_results = {}
    
    for i, table_name in enumerate(important_tb_tables, 1):
        print(f"\n{'='*60}")
        print(f"📊 Processing Table {i}/{len(important_tb_tables)}: {table_name}")
        print(f"{'='*60}")
        
        try:
            # Search for the table
            table_info = extractor.search_tables_by_name([table_name])
            
            if not table_info:
                print(f"❌ Table {table_name} not found")
                continue
            
            # Get the first (and should be only) result
            table_basic = table_info[0]
            table_id = table_basic.get('id')
            
            print(f"✅ Found table: {table_name} (ID: {table_id})")
            print(f"📋 Table description: {table_basic.get('description', 'No description')}")
            
            # Get complete table metadata including fields and related tables
            print(f"🔍 Fetching complete table metadata...")
            table_data = extractor.get_table_metadata(table_id)
            
            if not table_data:
                print(f"❌ Failed to get metadata for {table_name}")
                continue
            
            print(f"📊 Fields found: {len(table_data.get('fields', []))}")
            print(f"🔗 Related tables: {len(table_data.get('related_tables', []))}")
            
            # Generate KPIs with improved validation
            print(f"🤖 Generating KPIs with improved SQL validation...")
            kpis = extractor.generate_kpis_for_table(table_name, table_data)
            
            if kpis:
                print(f"✅ Generated {len(kpis)} KPIs")
                
                # Store results
                all_results[table_name] = {
                    "table_info": table_data.get("table_info", {}),
                    "fields": table_data.get("fields", []),
                    "related_tables": table_data.get("related_tables", []),
                    "kpis": kpis
                }
                
                # Show sample KPI
                if kpis:
                    sample_kpi = kpis[0]
                    print(f"📊 Sample KPI: {sample_kpi['kpi_name']}")
                    print(f"   Description: {sample_kpi['description']}")
                    print(f"   SQL: {sample_kpi['sql_query'][:100]}...")
            else:
                print(f"❌ Failed to generate KPIs for {table_name}")
                
        except Exception as e:
            print(f"❌ Error processing {table_name}: {str(e)}")
            continue
    
    # Save all results
    if all_results:
        output_file = "tb_tables_kpis_improved.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            print(f"\n✅ All results saved to {output_file}")
            
            # Summary
            total_tables = len(all_results)
            total_kpis = sum(len(data.get('kpis', [])) for data in all_results.values())
            print(f"\n📊 SUMMARY:")
            print(f"   Tables processed: {total_tables}")
            print(f"   Total KPIs generated: {total_kpis}")
            print(f"   Average KPIs per table: {total_kpis/total_tables:.1f}")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    else:
        print("❌ No results to save")

if __name__ == "__main__":
    main() 