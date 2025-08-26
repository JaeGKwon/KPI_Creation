#!/usr/bin/env python3
"""
Regenerate KPIs for selected TB tables with SIMPLIFIED metadata approach
This reduces token usage and costs while maintaining KPI quality
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
    
    # Define the important TB tables to process (focusing on core business tables)
    important_tb_tables = [
        "tb_market_order",      # Core business table - orders and revenue
        "tb_user",              # User management and analytics
        "tb_payment",           # Payment processing and financial metrics
        "tb_shipping",          # Shipping/logistics performance
        "tb_notification",      # System engagement metrics
        "tb_market_order_detail", # Order line items and product analytics
        "tb_market_order_log",   # Order lifecycle and process efficiency
        "tb_payment_market",     # Market-specific payment analytics
        "tb_user_activity_log",  # User behavior and engagement
        "tb_user_monthly_statistics" # User performance trends
    ]
    
    print(f"🎯 Processing {len(important_tb_tables)} important TB tables with SIMPLIFIED metadata...")
    print("📊 This approach reduces token usage and costs while maintaining KPI quality")
    
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
            
            total_fields = len(table_data.get('fields', []))
            print(f"📊 Total fields found: {total_fields}")
            print(f"🔗 Related tables: {len(table_data.get('related_tables', []))}")
            
            # Generate KPIs with simplified metadata (reduces token usage)
            print(f"🤖 Generating KPIs with SIMPLIFIED metadata and improved SQL validation...")
            kpis = extractor.generate_kpis_for_table(table_name, table_data)
            
            if kpis:
                print(f"✅ Generated {len(kpis)} KPIs")
                
                # Store results
                all_results[table_name] = {
                    "table_info": {
                        "name": table_name,
                        "description": table_basic.get('description', 'No description'),
                        "total_fields": total_fields,
                        "fields_used": min(20, total_fields)
                    },
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
        output_file = "tb_tables_kpis_simplified.json"
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
            print(f"   Metadata approach: SIMPLIFIED (reduced token usage)")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    else:
        print("❌ No results to save")

if __name__ == "__main__":
    main() 