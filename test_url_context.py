#!/usr/bin/env python3
"""
Test URL Context feature directly
"""
import os
import sys
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from dotenv import load_dotenv
import google.genai as genai
from google.genai.types import Tool, GenerateContentConfig

# Load environment
env_path = os.path.join(backend_path, '.env')
load_dotenv(env_path)

api_key = os.getenv('GOOGLE_API_KEY')
model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')

print(f"🔑 Using API Key: {api_key[:20]}...")
print(f"🤖 Using Model: {model_name}")

# Initialize client
client = genai.Client(api_key=api_key)

# Test URL
test_url = "https://example.com"

print(f"\n🌐 Testing URL Context with: {test_url}")

try:
    # Note: URL Context might not be available in all models
    # Let's test with a simple prompt first
    response = client.models.generate_content(
        model=model_name,
        contents=f"Please analyze this website URL and tell me what it's about: {test_url}"
    )
    
    # Extract text
    text = ""
    if hasattr(response, 'text'):
        text = response.text
    elif hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                text += part.text
    
    print(f"\n✅ Basic generation works!")
    print(f"Response: {text[:200]}...")
    
    # Now try with URL Context tool (if available)
    print("\n🔧 Testing URL Context Tool...")
    try:
        tools = [Tool(url_context={})]
        response2 = client.models.generate_content(
            model=model_name,
            contents=f"Extract content from: {test_url}",
            config=GenerateContentConfig(
                tools=tools,
                response_modalities=["TEXT"],
            )
        )
        print("✅ URL Context tool appears to be available!")
    except Exception as e:
        print(f"⚠️  URL Context tool error: {e}")
        print("\nNote: URL Context might not be available for all models or API keys.")
        print("The application will need to be modified to use standard web scraping instead.")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
