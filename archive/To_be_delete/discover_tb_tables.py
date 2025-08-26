#!/usr/bin/env python3
"""
Script to discover all available TB tables in Metabase
"""

import os
import sys
import json
from metabase_kpi_extractor import MetabaseKPIExtractor

def discover_all_tb_tables():
    """Discover all TB tables available in the system"""
    
    print("🔍 Discovering all available TB tables in Metabase...")
    
    # Initialize extractor
    extractor = MetabaseKPIExtractor()
    
    # Authenticate
    if not extractor.authenticate_metabase():
        print("❌ Authentication failed")
        return
    
    # Get all tables
    all_tables = extractor.search_tables_by_name("TB_")
    
    if not all_tables:
        print("❌ No TB tables found")
        return
    
    print(f"\n📊 Found {len(all_tables)} TB tables:")
    print("=" * 80)
    
    # Load existing processed tables
    processed_tables = set()
    try:
        with open('tb_tables_kpis.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            processed_tables = set(data.keys())
    except FileNotFoundError:
        print("⚠️  No existing tb_tables_kpis.json found")
    
    # Categorize tables
    processed = []
    not_processed = []
    
    for table in all_tables:
        table_name = table.get('name', 'Unknown')
        table_id = table.get('id', 'Unknown')
        description = table.get('description', 'No description')
        
        if table_name in processed_tables:
            processed.append({
                'name': table_name,
                'id': table_id,
                'description': description
            })
        else:
            not_processed.append({
                'name': table_name,
                'id': table_id,
                'description': description
            })
    
    # Display processed tables
    print(f"\n✅ ALREADY PROCESSED ({len(processed)} tables):")
    print("-" * 80)
    for table in processed:
        print(f"  • {table['name']} (ID: {table['id']})")
        print(f"    Description: {table['description']}")
        print()
    
    # Display not processed tables
    print(f"\n❌ NOT PROCESSED ({len(not_processed)} tables):")
    print("-" * 80)
    for table in not_processed:
        print(f"  • {table['name']} (ID: {table['id']})")
        print(f"    Description: {table['description']}")
        print()
    
    # Summary
    print("=" * 80)
    print(f"📈 SUMMARY:")
    print(f"  • Total TB tables found: {len(all_tables)}")
    print(f"  • Already processed: {len(processed)}")
    print(f"  • Not processed: {len(not_processed)}")
    print(f"  • Processing completion: {len(processed)/len(all_tables)*100:.1f}%")
    
    # Save detailed discovery results
    discovery_results = {
        'total_tables': len(all_tables),
        'processed_tables': processed,
        'not_processed_tables': not_processed,
        'all_tables': all_tables
    }
    
    with open('tb_tables_discovery.json', 'w', encoding='utf-8') as f:
        json.dump(discovery_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Discovery results saved to: tb_tables_discovery.json")
    
    return not_processed

if __name__ == "__main__":
    discover_all_tb_tables() 