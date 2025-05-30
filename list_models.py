#!/usr/bin/env python3
"""
List available Gemini models
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
client = genai.Client(api_key=api_key)

print("🤖 Available Gemini Models:")
print("=" * 60)
try:
    for model in client.models.list():
        print(f"  - {model.name}")
        if hasattr(model, 'description'):
            print(f"    Description: {model.description}")
        if hasattr(model, 'display_name'):
            print(f"    Display Name: {model.display_name}")
        print()
except Exception as e:
    print(f"Error: {e}")
