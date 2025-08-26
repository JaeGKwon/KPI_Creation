#!/usr/bin/env python3
"""
Test Step 4: Full Integration and End-to-End Workflow
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metabase_kpi_extractor import MetabaseKPIExtractor

def test_full_integration():
    """Test the complete end-to-end workflow"""
    print("="*50)
    print("TESTING STEP 4: FULL INTEGRATION")
    print("="*50)
    
    try:
        # Initialize the extractor
        extractor = MetabaseKPIExtractor()
        
        # Define test table names
        test_table_names = ["users", "orders", "products", "customers"]
        
        print(f"🎯 Testing with table names: {test_table_names}")
        
        # Run the complete process
        print("\n🚀 Starting complete KPI extraction process...")
        results = extractor.process_table_list(test_table_names)
        
        if results:
            print(f"\n✅ Successfully processed {len(results)} tables!")
            
            # Display summary
            total_kpis = 0
            for table_name, table_data in results.items():
                kpi_count = len(table_data.get('kpis', []))
                total_kpis += kpi_count
                print(f"   📊 {table_name}: {kpi_count} KPIs")
            
            print(f"\n📈 Total KPIs generated: {total_kpis}")
            
            # Save results
            output_file = "integration_test_results.json"
            extractor.save_results(results, output_file)
            print(f"\n💾 Complete results saved to: {output_file}")
            
            # Show sample KPI from first table
            if results:
                first_table_name = list(results.keys())[0]
                first_table_data = results[first_table_name]
                first_kpis = first_table_data.get('kpis', [])
                
                if first_kpis:
                    print(f"\n🔍 Sample KPI from {first_table_name}:")
                    sample_kpi = first_kpis[0]
                    print(f"   Name: {sample_kpi.get('kpi_name', 'N/A')}")
                    print(f"   Description: {sample_kpi.get('description', 'N/A')}")
                    print(f"   SQL: {sample_kpi.get('sql_query', 'N/A')}")
            
            return True
        else:
            print("❌ No results generated from the complete process")
            return False
            
    except Exception as e:
        print(f"❌ Error during integration test: {e}")
        return False

def test_custom_table_list():
    """Test with custom table names"""
    print("\n" + "="*50)
    print("TESTING WITH CUSTOM TABLE LIST")
    print("="*50)
    
    try:
        # Get custom table names from user
        print("Enter table names separated by commas (or press Enter to use defaults):")
        user_input = input().strip()
        
        if user_input:
            custom_table_names = [name.strip() for name in user_input.split(',')]
        else:
            custom_table_names = ["users", "orders", "products", "customers"]
        
        print(f"🎯 Using table names: {custom_table_names}")
        
        # Initialize and run
        extractor = MetabaseKPIExtractor()
        results = extractor.process_table_list(custom_table_names)
        
        if results:
            print(f"\n✅ Successfully processed {len(results)} tables!")
            
            # Save custom results
            output_file = "custom_table_results.json"
            extractor.save_results(results, output_file)
            print(f"💾 Results saved to: {output_file}")
            
            return True
        else:
            print("❌ No results generated")
            return False
            
    except Exception as e:
        print(f"❌ Error during custom table test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 INTEGRATION TESTING SUITE")
    print("="*50)
    
    # Test 1: Full integration with default tables
    success1 = test_full_integration()
    
    if success1:
        print("\n🎉 Full integration test passed!")
        
        # Test 2: Custom table list (optional)
        print("\n" + "="*50)
        print("Would you like to test with custom table names? (y/n)")
        user_choice = input().strip().lower()
        
        if user_choice in ['y', 'yes']:
            success2 = test_custom_table_list()
            if success2:
                print("\n🎉 Custom table test passed!")
            else:
                print("\n💥 Custom table test failed!")
        else:
            print("Skipping custom table test.")
    else:
        print("\n💥 Full integration test failed!")
        print("Please check the logs above for errors.") 