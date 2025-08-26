#!/usr/bin/env python3
"""
Regenerate KPIs for selected TB tables with ENHANCED field information
This includes foreign key relationships and enables multi-table joins for richer KPIs
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metabase_kpi_extractor import MetabaseKPIExtractor

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
    
    # Define the important TB tables to process (focusing on tables with relationships)
    important_tb_tables = [
        "tb_market_order",           # Core business table with user relationships
        "tb_user",                   # User management (referenced by orders)
        "tb_payment",                # Payment processing with order relationships
        "tb_market_order_detail",    # Order line items (related to orders)
        "tb_market_order_log",       # Order lifecycle (related to orders)
        "tb_payment_market",         # Market payments (related to orders)
        "tb_user_activity_log",      # User behavior (related to users)
        "tb_user_monthly_statistics" # User trends (related to users)
    ]
    
    print(f"🎯 Processing {len(important_tb_tables)} important TB tables with ENHANCED field information...")
    print("📊 This approach includes foreign key relationships and enables multi-table joins")
    
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
            
            # Count foreign key relationships
            fk_count = 0
            for field in table_data.get('fields', []):
                if field.get('fk_target_field_id'):
                    fk_count += 1
            
            print(f"🔗 Foreign key relationships: {fk_count}")
            print(f"🔗 Related tables: {len(table_data.get('related_tables', []))}")
            
            # Generate KPIs with enhanced field information and multi-table capabilities
            print(f"🤖 Generating KPIs with ENHANCED field info and multi-table join capabilities...")
            result = extractor.generate_kpis_for_table(table_name, table_data)
            
            if result and result.get('kpis'):
                kpis = result.get('kpis', [])
                field_details = result.get('field_details', [])
                total_fields = result.get('total_fields', 0)
                fields_used = result.get('fields_used', 0)
                foreign_keys = result.get('foreign_keys', 0)
                
                print(f"✅ Generated {len(kpis)} KPIs")
                
                # Count KPIs with JOINs
                join_kpis = 0
                for kpi in kpis:
                    if 'JOIN' in kpi.get('sql_query', '').upper():
                        join_kpis += 1
                
                print(f"🔗 KPIs with multi-table JOINs: {join_kpis}")
                
                # Store results with field information
                all_results[table_name] = {
                    "table_info": {
                        "name": table_name,
                        "description": table_basic.get('description', 'No description'),
                        "total_fields": total_fields,
                        "fields_used": fields_used,
                        "foreign_keys": foreign_keys,
                        "related_tables": len(table_data.get('related_tables', []))
                    },
                    "field_details": field_details,
                    "kpis": kpis,
                    "join_analysis": {
                        "total_kpis": len(kpis),
                        "kpis_with_joins": join_kpis,
                        "join_percentage": round((join_kpis / len(kpis)) * 100, 1) if kpis else 0
                    }
                }
                
                # Show sample KPI
                if kpis:
                    sample_kpi = kpis[0]
                    print(f"📊 Sample KPI: {sample_kpi['kpi_name']}")
                    print(f"   Description: {sample_kpi['description']}")
                    sql_preview = sample_kpi['sql_query'][:100] + "..." if len(sample_kpi['sql_query']) > 100 else sample_kpi['sql_query']
                    print(f"   SQL: {sql_preview}")
                    
                    # Show if it uses JOINs
                    if 'JOIN' in sample_kpi.get('sql_query', '').upper():
                        print(f"   🔗 Uses multi-table JOINs")
                
                # Show field information summary
                print(f"📋 Field details: {len(field_details)} fields with enhanced metadata")
            else:
                print(f"❌ Failed to generate KPIs for {table_name}")
                
        except Exception as e:
            print(f"❌ Error processing {table_name}: {str(e)}")
            continue
    
    # Save all results
    if all_results:
        output_file = "tb_tables_kpis_enhanced.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            print(f"\n✅ All results saved to {output_file}")
            
            # Summary
            total_tables = len(all_results)
            total_kpis = sum(len(data.get('kpis', [])) for data in all_results.values())
            total_joins = sum(data.get('join_analysis', {}).get('kpis_with_joins', 0) for data in all_results.values())
            
            print(f"\n📊 SUMMARY:")
            print(f"   Tables processed: {total_tables}")
            print(f"   Total KPIs generated: {total_kpis}")
            print(f"   Average KPIs per table: {total_kpis/total_tables:.1f}")
            print(f"   KPIs with multi-table JOINs: {total_joins}")
            print(f"   JOIN percentage: {(total_joins/total_kpis)*100:.1f}%" if total_kpis > 0 else "0%")
            print(f"   Metadata approach: ENHANCED (with relationships and JOINs)")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    else:
        print("❌ No results to save")

if __name__ == "__main__":
    main() 