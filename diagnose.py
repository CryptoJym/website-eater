#!/usr/bin/env python3
"""
Diagnose Website Eater extraction issues
"""
import requests
import json

# Test URL
test_url = "https://example.com"

# API endpoint
api_url = "http://localhost:5001/api/process"

print("🔍 Diagnosing Website Eater...")
print("=" * 60)

# Test 1: Check if server is responding
try:
    response = requests.get("http://localhost:5001", timeout=5)
    print("✅ Server is responding on port 5001")
except Exception as e:
    print(f"❌ Server not responding: {e}")
    exit(1)

# Test 2: Try a simple extraction without AI analysis
print("\n📝 Test 1: Basic extraction (no AI)")
try:
    response = requests.post(api_url, json={
        "url": test_url,
        "options": {
            "deep_analysis": False,
            "extract_images": False,
            "extract_metadata": False
        }
    }, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Check the raw scraping function
print("\n📝 Test 2: Testing raw web scraping...")
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    from app_working import extract_content_from_url
    
    scraped = extract_content_from_url(test_url)
    print(f"Scraping successful: {scraped['success']}")
    print(f"Title: {scraped['title']}")
    print(f"Content length: {len(scraped['content'])} chars")
    print(f"Content preview: {scraped['content'][:200]}...")
    
except Exception as e:
    print(f"❌ Scraping error: {e}")

# Test 4: Check Gemini API directly
print("\n📝 Test 3: Testing Gemini API...")
try:
    from dotenv import load_dotenv
    import google.genai as genai
    
    load_dotenv('backend/.env')
    api_key = os.getenv('GOOGLE_API_KEY')
    model_name = os.getenv('GEMINI_MODEL')
    
    print(f"API Key: {api_key[:20]}...")
    print(f"Model: {model_name}")
    
    client = genai.Client(api_key=api_key)
    
    # Simple test
    response = client.models.generate_content(
        model=model_name,
        contents="Say 'Hello, working!' if you receive this"
    )
    
    text = ""
    if hasattr(response, 'text'):
        text = response.text
    elif hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                text += part.text
    
    print(f"Gemini response: {text}")
    
except Exception as e:
    print(f"❌ Gemini API error: {e}")
    import traceback
    traceback.print_exc()
