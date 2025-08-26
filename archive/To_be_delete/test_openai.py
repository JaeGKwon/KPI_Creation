#!/usr/bin/env python3
"""
Test OpenAI API key
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai():
    """Test OpenAI API key"""
    print("🔑 TESTING OPENAI API KEY")
    print("="*40)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found in .env file")
        return False
    
    print(f"✅ API key found: {api_key[:20]}...")
    
    try:
        import openai
        print(f"✅ OpenAI package imported: {openai.__version__}")
        
        # Test client creation
        print("✅ OpenAI client created successfully")
        
        # Test a simple API call
        print("🧪 Testing API call...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello World'"}],
            max_tokens=10
        )
        
        content = response.choices[0].message.content
        print(f"✅ API call successful: {content}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_openai()
    if success:
        print("\n🎉 OpenAI test passed!")
    else:
        print("\n💥 OpenAI test failed!") 