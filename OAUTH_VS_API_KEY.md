# 🎯 Visual Guide: OAuth vs API Key

## ❌ What You Shared (OAuth Client):
```json
{
  "web": {
    "client_id": "856573319084-kkssb...apps.googleusercontent.com",
    "client_secret": "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"
  }
}
```
**Used for:** Letting users log in with Google

## ✅ What You Need (API Key):
```
AIzaSyD3f4V6wk9_XYZ... (just a string)
```
**Used for:** Accessing Gemini API

## 📍 Where to Get It:

### Step 1: Create API Key
Go to: https://console.cloud.google.com/apis/credentials?project=utlyze
- Click "+ CREATE CREDENTIALS"
- Choose "API key" (NOT "OAuth client ID")
- Copy the key

### Step 2: Enable Gemini API
Go to: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com?project=utlyze
- Click "ENABLE"

### Step 3: Update Your App
Run: `python3 update_api_key.py`
- Paste your new key
- Restart the server

## 🎉 Then You Can:
- Digest YouTube videos
- Analyze GitHub repos  
- Process any URL
- No more quota limits!
