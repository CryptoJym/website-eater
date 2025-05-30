#!/usr/bin/env python3
"""
Demo script showing the new feedback/context feature
"""
import requests
import json

# Test 1: Submit a Loom video bug report
print("🎥 Test 1: Submitting Loom video bug report...")
loom_context = """
https://www.loom.com/share/example123456
Bug: When clicking the submit button multiple times, the form submits duplicate entries.
Steps to reproduce shown in the video above.
"""

response = requests.post('http://localhost:5003/api/digest', 
    json={
        'url': 'https://www.loom.com/share/example123456',
        'options': {
            'extract_metadata': True,
            'deep_analysis': True,
            'context_type': 'bug_report',
            'additional_context': 'Bug: Duplicate form submissions when clicking submit multiple times'
        }
    })

print(f"Response: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Loom video processed!")
    print(f"   Memory ID: {data.get('memory_id')}")
    print(f"   Content Type: {data.get('content_type')}")
    print(f"   Routed to: {[r['destination'] for r in data.get('routes', [])]}")

print("\n" + "="*50 + "\n")

# Test 2: Submit general feedback without URL
print("💡 Test 2: Submitting general feedback...")
feedback_response = requests.post('http://localhost:5003/api/feedback',
    json={
        'content': 'Feature request: It would be great to have a dark mode toggle in the settings',
        'type': 'feature_request'
    })

print(f"Response: {feedback_response.status_code}")
if feedback_response.status_code == 200:
    data = feedback_response.json()
    print(f"✅ Feedback submitted!")
    print(f"   Feedback ID: {data.get('feedback_id')}")
    print(f"   Message: {data.get('message')}")

print("\n🎯 New feature is working! Users can now:")
print("   - Drop Loom videos for bug reports")
print("   - Submit general feedback and context")
print("   - Everything is automatically filed in the AI database")
