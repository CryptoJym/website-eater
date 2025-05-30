#!/usr/bin/env python3
"""
Test if API key is using paid tier or free tier
"""
import os
import sys
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from dotenv import load_dotenv
import google.genai as genai

# Load environment
env_path = os.path.join(backend_path, '.env')
load_dotenv(env_path)

api_key = os.getenv('GOOGLE_API_KEY')
print(f"🔑 Testing API Key: {api_key[:20]}...")
print("=" * 60)

# Initialize client
client = genai.Client(api_key=api_key)

# Test with a longer prompt to check quota
test_prompt = """
Please write a detailed 500-word essay about the importance of artificial intelligence
in modern society, covering its impacts on healthcare, education, transportation,
and the economy. Include specific examples and recent developments.
""" * 5  # Repeat to make it longer

print("📝 Sending test request (using more tokens)...")
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash-preview-05-20',
        contents=test_prompt
    )
    
    print("✅ Success! Response received.")
    
    # Check response length
    text = ""
    if hasattr(response, 'text'):
        text = response.text
    elif hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                text += part.text
    
    print(f"📊 Response length: {len(text)} characters")
    print(f"📊 First 100 chars: {text[:100]}...")
    
    print("\n✅ Your API key appears to be working!")
    print("   If you're still hitting quotas, you may be on the free tier.")
    
except Exception as e:
    error_str = str(e)
    print(f"\n❌ Error: {error_str}")
    
    if "429" in error_str or "quota" in error_str.lower():
        print("\n⚠️  QUOTA ERROR DETECTED!")
        print("   Your API key is likely still on the FREE TIER.")
        print("   Even with billing enabled, you need a key from Google Cloud Console.")
        print("\n   Follow the steps in GOOGLE_CLOUD_SETUP.md to create a paid tier key.")
    elif "403" in error_str:
        print("\n⚠️  PERMISSION ERROR!")
        print("   The Generative Language API might not be enabled in your project.")
    else:
        print("\n⚠️  Unknown error - check your API key and project setup.")

print("\n" + "=" * 60)
print("💡 Quick Check:")
print("   - Keys from ai.google.dev = FREE TIER (limited quota)")
print("   - Keys from console.cloud.google.com = PAID TIER (high quota)")
print("   - You need to create a NEW key in Cloud Console after enabling billing")
