#!/usr/bin/env python3
"""
Check extraction details without AI
"""
import requests
import json

# Test extraction without AI to see raw results
response = requests.post("http://localhost:5001/api/process", json={
    "url": "https://www.google.com",
    "options": {
        "deep_analysis": False,  # Disable AI to see raw extraction
        "extract_images": False,
        "extract_metadata": False
    }
}, timeout=30)

data = response.json()
print("🔍 Extraction Results:")
print("=" * 60)
print(f"✅ Status: {data['status']}")
print(f"📄 Title: {data.get('title', 'N/A')}")
print(f"🔗 URL: {data.get('url', 'N/A')}")
print(f"📊 Content Type: {data.get('content_type', 'N/A')}")
print(f"📏 Content Length: {data.get('content_length', 0):,} characters")
print(f"🆔 Memory ID: {data.get('memory_id', 'N/A')}")
print(f"📍 Routes: {', '.join([r['destination'] for r in data.get('routes', [])])}")

if 'analysis_preview' in data:
    print(f"\n⚠️  AI Analysis Status:")
    if 'quota' in data['analysis_preview'].lower() or '429' in data['analysis_preview']:
        print("❌ AI analysis failed due to API quota limits")
        print("   The content WAS extracted successfully!")
        print("   Only the AI analysis step failed.")
    else:
        print(data['analysis_preview'][:200])
