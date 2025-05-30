#!/usr/bin/env python3
"""
Test the working Website Eater
"""
import requests
import json

# Test URL
test_url = "https://example.com"

# API endpoint
api_url = "http://localhost:5001/api/process"

# Options
options = {
    "deep_analysis": True,
    "extract_images": False,
    "extract_metadata": True
}

print("🧪 Testing Website Eater with Gemini AI Analysis")
print("=" * 50)
print(f"URL: {test_url}")
print(f"Options: {json.dumps(options, indent=2)}")
print("=" * 50)
print("\n📡 Sending request to extract and analyze content...")

try:
    response = requests.post(api_url, json={
        "url": test_url,
        "options": options
    }, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            print("\n✅ Success! Content extracted and analyzed")
            print(f"\n📄 Title: {data['title']}")
            print(f"📊 Content Type: {data['content_type']}")
            print(f"📏 Content Length: {data['content_length']:,} characters")
            print(f"🆔 Memory ID: {data['memory_id']}")
            print(f"📍 Routes: {', '.join([r['destination'] for r in data['routes']])}")
            
            if data.get('analysis_preview'):
                print(f"\n🤖 AI Analysis Preview:")
                print("-" * 50)
                print(data['analysis_preview'])
                print("-" * 50)
        else:
            print(f"\n❌ Error: {data['error']}")
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    print("\nMake sure the Website Eater server is running at http://localhost:5001")
