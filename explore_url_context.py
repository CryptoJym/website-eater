#!/usr/bin/env python3
"""
Explore google-genai library to find URL Context feature
"""
import os
import sys
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

# Load environment
env_path = os.path.join(backend_path, '.env')
load_dotenv(env_path)

print("🔍 Exploring google-genai library for URL Context")
print("=" * 60)

# Check available types
print("\n📦 Available in google.genai.types:")
for item in dir(types):
    if not item.startswith('_'):
        print(f"  - {item}")

# Check Tool class
print("\n🔧 Checking Tool class:")
from google.genai.types import Tool
print(f"Tool class: {Tool}")
print(f"Tool fields: {Tool.__fields__ if hasattr(Tool, '__fields__') else 'No fields'}")

# Try different approaches
api_key = os.getenv('GOOGLE_API_KEY')
model_name = 'gemini-2.5-flash-preview-05-20'  # Using Flash for testing
client = genai.Client(api_key=api_key)

print("\n🧪 Testing URL handling approaches:")

# Test 1: Direct URL in prompt
test_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
print(f"\n1️⃣ Direct URL in prompt: {test_url}")
try:
    response = client.models.generate_content(
        model=model_name,
        contents=f"What is the main topic of this webpage: {test_url}"
    )
    
    text = ""
    if hasattr(response, 'text'):
        text = response.text
    elif hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                text += part.text
    
    print(f"Response: {text[:200]}...")
    
    # Check if URL was actually fetched
    if "python" in text.lower() and "programming" in text.lower():
        print("✅ Seems to have accessed the URL content!")
    else:
        print("❌ May not have accessed the actual URL")
        
except Exception as e:
    print(f"Error: {e}")

# Test 2: Check for grounding/retrieval metadata
print("\n2️⃣ Checking response metadata:")
try:
    response = client.models.generate_content(
        model=model_name,
        contents=f"Summarize: {test_url}"
    )
    
    # Check all response attributes
    print("Response attributes:")
    for attr in dir(response):
        if not attr.startswith('_'):
            print(f"  - {attr}")
    
    # Check for grounding metadata
    if hasattr(response, 'grounding_metadata'):
        print(f"Grounding metadata: {response.grounding_metadata}")
    
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        print(f"\nCandidate attributes:")
        for attr in dir(candidate):
            if not attr.startswith('_') and not callable(getattr(candidate, attr)):
                print(f"  - {attr}: {getattr(candidate, attr)}")
                
except Exception as e:
    print(f"Error: {e}")
