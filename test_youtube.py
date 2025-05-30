#!/usr/bin/env python3
"""
Test URL digestion with Gemini
"""
import requests
import json

# Test with a YouTube URL
test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

print("🔗 Testing Gemini URL Digestion")
print("=" * 60)
print(f"URL: {test_url}")
print("\n📡 Sending request to digest YouTube video...")

try:
    response = requests.post("http://localhost:5003/api/digest", 
        json={
            "url": test_url,
            "options": {
                "extract_metadata": True,
                "deep_analysis": True
            }
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            print("\n✅ Success! URL digested by Gemini")
            print(f"\n📹 Title: {data.get('title', 'N/A')}")
            print(f"📊 Content Type: {data.get('content_type', 'N/A')}")
            print(f"🔗 URL Accessed: {'Yes' if data.get('url_accessed') else 'No'}")
            print(f"\n📝 Analysis Preview:")
            print("-" * 60)
            analysis = data.get('analysis', '')
            if analysis:
                print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
            print("-" * 60)
        else:
            print(f"\n❌ Error: {data.get('error', 'Unknown error')}")
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    print("Make sure the server is running at http://localhost:5003")
