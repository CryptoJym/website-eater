#!/usr/bin/env python3
"""
Test Google API Key directly
"""
import os
import sys
sys.path.append('backend')

from dotenv import load_dotenv

# Try different import methods
try:
    import google.genai as genai
    print("✅ Import method 1: import google.genai as genai")
except ImportError:
    try:
        import genai
        print("✅ Import method 2: import genai")
    except ImportError:
        from google import genai
        print("✅ Import method 3: from google import genai")

# Load environment variables
load_dotenv('backend/.env')

# Get API key
api_key = os.getenv('GOOGLE_API_KEY')
print(f"\n🔑 API Key loaded: {'✅ Yes' if api_key else '❌ No'}")
print(f"🔑 Key prefix: {api_key[:20]}..." if api_key else "No key found")

# Test the API
try:
    print("\n🧪 Testing Google GenAI Client...")
    client = genai.Client(api_key=api_key)
    
    # Try a simple generation
    print("\n🤖 Testing simple text generation...")
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',  # Using a stable model
        contents="Hello, this is a test. Reply with 'API key working!'"
    )
    
    if hasattr(response, 'text'):
        print(f"✅ Response: {response.text}")
    else:
        print(f"✅ Response: {response.candidates[0].content.parts[0].text}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
