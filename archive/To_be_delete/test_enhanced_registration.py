#!/usr/bin/env python3
"""
Test script for enhanced KPI registration
Tests the registration of 50 SQLs with validation and LLM fixing
"""

import subprocess
import sys
import os

def main():
    """Test the enhanced KPI registration with 50 SQLs"""
    print("🧪 TESTING ENHANCED KPI REGISTRATION")
    print("=" * 60)
    print("📋 Test Configuration:")
    print("  • Target: 50 SQLs from tb_tables_kpis_clean.json")
    print("  • Mode: Test mode (will create 'jae's test analysis' collection)")
    print("  • Features: SQL validation + LLM fixing (up to 3 attempts)")
    print("  • Cleanup: Will remove existing KPIs before starting")
    print("=" * 60)
    
    # Check if the enhanced script exists
    if not os.path.exists("register_kpis_enhanced.py"):
        print("❌ Error: register_kpis_enhanced.py not found!")
        return
    
    # Check if the clean JSON file exists
    if not os.path.exists("tb_tables_kpis_clean.json"):
        print("❌ Error: tb_tables_kpis_clean.json not found!")
        return
    
    print("✅ All required files found")
    print("\n🚀 Starting enhanced KPI registration test...")
    print("   This will:")
    print("   1. Remove existing KPIs from test collection")
    print("   2. Validate each SQL by running it")
    print("   3. Use LLM to fix failed SQLs (up to 3 attempts)")
    print("   4. Register only valid/fixed SQLs")
    print("   5. Provide detailed results and statistics")
    
    input("\n⏸️  Press Enter to continue with the test...")
    
    try:
        # Run the enhanced registration script in test mode with 50 SQLs
        cmd = [sys.executable, "register_kpis_enhanced.py", "--test", "50"]
        
        print(f"\n🔧 Executing: {' '.join(cmd)}")
        print("=" * 60)
        
        # Run the command and capture output
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("✅ Test completed successfully!")
        else:
            print(f"❌ Test failed with return code: {result.returncode}")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during test execution: {e}")

if __name__ == "__main__":
    main() 