#!/usr/bin/env python3
"""
Test Google's URL Context Tool - The CORRECT Way
"""
import os
import sys
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from dotenv import load_dotenv
import google.genai as genai
from google.genai.types import Tool, UrlContext, GenerateContentConfig

# Load environment
env_path = os.path.join(backend_path, '.env')
load_dotenv(env_path)

api_key = os.getenv('GOOGLE_API_KEY')
model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro-exp-03-25')

print("🔍 Testing Google's URL Context Tool")
print("=" * 60)

# Initialize client
client = genai.Client(api_key=api_key)

# Test URLs including YouTube
test_urls = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # YouTube video
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://blog.google/technology/ai/"
]

for url in test_urls:
    print(f"\n📍 Testing URL: {url}")
    print("-" * 60)
    
    try:
        # Method 1: Direct URL in prompt (simplest)
        print("Method 1: URL in prompt")
        response = client.models.generate_content(
            model=model_name,
            contents=f"Summarize the content at this URL: {url}"
        )
        
        text = ""
        if hasattr(response, 'text'):
            text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    text += part.text
        
        print(f"Response: {text[:300]}...")
        
        # Method 2: Using URL Context tool explicitly
        print("\nMethod 2: URL Context Tool")
        try:
            # Create URL Context tool
            tools = [Tool(url_context=UrlContext())]
            
            response2 = client.models.generate_content(
                model=model_name,
                contents=f"Extract and analyze content from: {url}",
                config=GenerateContentConfig(
                    tools=tools,
                    response_modalities=["TEXT"],
                )
            )
            
            text2 = ""
            if hasattr(response2, 'text'):
                text2 = response2.text
            elif hasattr(response2, 'candidates') and response2.candidates:
                for part in response2.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        text2 += part.text
            
            print(f"Response: {text2[:300]}...")
            
        except Exception as e:
            print(f"URL Context tool error: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        if "quota" in str(e).lower():
            print("⚠️ Quota exceeded - this counts against your daily limit")
