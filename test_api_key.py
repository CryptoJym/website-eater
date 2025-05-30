#!/usr/bin/env python3
"""
Simple test to verify Gemini API key works
"""
import os
import sys
sys.path.append('backend')

from dotenv import load_dotenv
load_dotenv('backend/.env')

try:
    import google.genai as genai
    
    # Get API key
    api_key = os.getenv('GOOGLE_API_KEY')
    print(f"🔑 Testing API Key: {api_key[:20]}...")
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    
    # Test with a simple prompt
    print("📝 Testing Gemini with simple prompt...")
    response = client.models.generate_content(
        model='gemini-2.5-pro-preview-03-25',
        contents='Say "Hello, API is working!" if you can read this.'
    )
    
    # Extract response
    result = ""
    if hasattr(response, 'text'):
        result = response.text
    elif hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                result += part.text
    
    print(f"✅ Response: {result}")
    print("\n🎉 SUCCESS! Your API key is working!")
    
    # Now test URL digestion
    print("\n🔗 Testing URL digestion capability...")
    url_response = client.models.generate_content(
        model='gemini-2.5-pro-preview-03-25',
        contents=f'What is the main topic of this webpage: https://www.google.com'
    )
    
    # Extract response
    url_result = ""
    if hasattr(url_response, 'text'):
        url_result = url_response.text
    elif hasattr(url_response, 'candidates') and url_response.candidates:
        for part in url_response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                url_result += part.text
    
    if len(url_result) > 50:
        print("✅ URL digestion is working!")
    else:
        print("⚠️  URL digestion may need to be enabled")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    
    error_msg = str(e)
    if '403' in error_msg or 'not enabled' in error_msg.lower():
        print("\n📍 The Generative Language API needs to be enabled!")
        print("   Run: ./enable_api.sh")
    elif '429' in error_msg or 'quota' in error_msg.lower():
        print("\n⚠️  API quota exceeded - wait a bit or check billing")
    elif 'api key not valid' in error_msg.lower():
        print("\n❌ Invalid API key - create a new one")
    else:
        print("\n🔍 Check that:")
        print("   1. The API is enabled in your project")
        print("   2. The API key has no restrictions")
        print("   3. Billing is enabled on your project")
