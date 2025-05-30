#!/usr/bin/env python3
"""
Test Google API Key directly
"""
import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from dotenv import load_dotenv
import google.genai as genai

# Load environment variables from the correct path
env_path = os.path.join(backend_path, '.env')
print(f"📁 Loading .env from: {env_path}")
load_dotenv(env_path)

# Get API key
api_key = os.getenv('GOOGLE_API_KEY')
print(f"🔑 API Key loaded: {'✅ Yes' if api_key else '❌ No'}")
if api_key:
    print(f"🔑 Key prefix: {api_key[:20]}...")
    print(f"🔑 Key length: {len(api_key)} characters")
else:
    print("❌ No API key found in environment")
    # Try reading directly from file
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('GOOGLE_API_KEY='):
                    direct_key = line.split('=', 1)[1].strip()
                    print(f"📄 Found key in file: {direct_key[:20]}...")
                    api_key = direct_key
                    break
    except Exception as e:
        print(f"❌ Could not read .env file: {e}")

# Test the API
if api_key:
    try:
        print("\n🧪 Testing Google GenAI Client...")
        client = genai.Client(api_key=api_key)
        
        # Try a simple generation
        print("🤖 Testing simple text generation...")
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',  # Using a stable model
            contents="Hello, this is a test. Reply with 'API key working!'"
        )
        
        # Extract text from response
        text = ""
        if hasattr(response, 'text'):
            text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    text += part.text
        
        print(f"✅ Response: {text}")
        print("\n🎉 API Key is properly configured and working!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check if it's an authentication error
        if "403" in str(e) or "API key not valid" in str(e):
            print("\n⚠️  This appears to be an authentication issue.")
            print("Please check that:")
            print("1. Your API key is valid")
            print("2. The Gemini API is enabled in your Google Cloud project")
            print("3. The API key has the necessary permissions")
else:
    print("\n❌ Cannot test API without a key")
