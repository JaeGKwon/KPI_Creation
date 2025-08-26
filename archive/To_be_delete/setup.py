#!/usr/bin/env python3
"""
Setup script for Metabase KPI Extractor
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with user input"""
    print("🔧 METABASE KPI EXTRACTOR SETUP")
    print("="*50)
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("Setup cancelled.")
            return False
    
    print("\nPlease provide the following information:")
    
    # Metabase configuration
    print("\n📊 METABASE CONFIGURATION")
    metabase_url = input("Metabase URL (e.g., http://localhost:3000): ").strip()
    if not metabase_url:
        metabase_url = "http://localhost:3000"
        print(f"Using default: {metabase_url}")
    
    metabase_username = input("Metabase Username: ").strip()
    if not metabase_username:
        print("❌ Username is required!")
        return False
    
    metabase_password = input("Metabase Password: ").strip()
    if not metabase_password:
        print("❌ Password is required!")
        return False
    
    # OpenAI configuration
    print("\n🤖 OPENAI CONFIGURATION")
    openai_api_key = input("OpenAI API Key: ").strip()
    if not openai_api_key:
        print("⚠️  OpenAI API key is optional but required for KPI generation")
        print("You can add it later by editing the .env file")
    
    # Create .env file
    env_content = f"""# Metabase Configuration
METABASE_URL={metabase_url}
METABASE_USERNAME={metabase_username}
METABASE_PASSWORD={metabase_password}

# OpenAI Configuration
OPENAI_API_KEY={openai_api_key}
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"\n✅ .env file created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 CHECKING DEPENDENCIES")
    print("="*30)
    
    required_packages = [
        'requests',
        'openai', 
        'dotenv',
        'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'dotenv':
                import dotenv
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All required packages are installed!")
        return True

def test_connection():
    """Test basic connection to Metabase"""
    print("\n🔗 TESTING CONNECTION")
    print("="*30)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        metabase_url = os.getenv('METABASE_URL')
        if not metabase_url:
            print("❌ METABASE_URL not found in .env file")
            return False
        
        import requests
        
        # Test basic connectivity
        print(f"Testing connection to: {metabase_url}")
        response = requests.get(f"{metabase_url}/api/health", timeout=10)
        
        if response.status_code == 200:
            print("✅ Metabase instance is accessible!")
            return True
        else:
            print(f"⚠️  Metabase responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Metabase instance")
        print("Check if the URL is correct and Metabase is running")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Welcome to Metabase KPI Extractor Setup!")
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies and run setup again.")
        return
    
    # Create .env file
    if not create_env_file():
        print("Setup failed. Please try again.")
        return
    
    # Test connection
    if not test_connection():
        print("\n⚠️  Connection test failed, but setup completed.")
        print("You can still proceed with testing individual components.")
    
    print("\n" + "="*50)
    print("🎉 SETUP COMPLETED!")
    print("="*50)
    print("\nNext steps:")
    print("1. Test authentication: python test_step1_auth.py")
    print("2. Test metadata extraction: python test_step2_auth.py")
    print("3. Test LLM integration: python test_step3_llm.py")
    print("4. Run full integration: python test_step4_integration.py")
    print("\nOr run the main script: python metabase_kpi_extractor.py")
    
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main() 