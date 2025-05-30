#!/usr/bin/env python3
"""
Test the enhanced Website Eater with extraction-only mode
"""
import requests
import json

# Test URL
test_url = "https://www.wikipedia.org"

# API endpoint
api_url = "http://localhost:5002/api/process"

# Test with AI disabled to show pure extraction
print("🧪 Testing Website Eater - Pure Extraction Mode (No AI)")
print("=" * 60)

options = {
    "skip_ai": True,  # Skip AI to show extraction working
    "extract_images": False,
    "extract_metadata": True
}

print(f"URL: {test_url}")
print(f"Mode: Extraction Only (AI Disabled)")
print("=" * 60)
print("\n📡 Extracting content...")

try:
    response = requests.post(api_url, json={
        "url": test_url,
        "options": options
    }, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            print("\n✅ Extraction Successful!")
            print(f"\n📄 Title: {data['title']}")
            print(f"📊 Content Type: {data['content_type']}")
            print(f"📏 Content Length: {data['content_length']:,} characters")
            print(f"🆔 Memory ID: {data['memory_id']}")
            
            if data.get('meta_description'):
                print(f"\n📝 Meta Description:")
                print(f"   {data['meta_description'][:150]}...")
            
            if data.get('headers'):
                print(f"\n📑 Headers Found ({len(data['headers'])} total):")
                for i, header in enumerate(data['headers'][:5], 1):
                    print(f"   {i}. {header}")
            
            if data.get('raw_content_preview'):
                print(f"\n📖 Content Preview:")
                print("-" * 60)
                print(data['raw_content_preview'][:300] + "...")
                print("-" * 60)
                
            print(f"\n📍 Routed to: {', '.join([r['destination'] for r in data['routes']])}")
            print(f"\n🎯 AI Analysis: {'Available' if data.get('ai_available') else 'Skipped'}")
        else:
            print(f"\n❌ Error: {data['error']}")
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
