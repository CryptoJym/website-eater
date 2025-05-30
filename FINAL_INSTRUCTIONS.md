# 🚨 IMPORTANT: You Need a Different Type of Key!

## ❌ What You Keep Sharing:
1. **OAuth Client Secret** - For user login (JSON file)
2. **Service Account Key** - For server auth (JSON file with private key)

## ✅ What You Actually Need:
**API KEY** - A simple string like: `AIzaSyD3f4V6wk9_XYZ...`

## 🎯 Super Simple Steps:

### 1. Open This Link:
https://console.cloud.google.com/apis/credentials?project=utlyze

### 2. Click This Exact Option:
```
+ CREATE CREDENTIALS
    │
    ├─→ API key          ← CLICK THIS ONE! ✅
    ├─→ OAuth client ID  ← NOT this ❌
    └─→ Service account  ← NOT this ❌
```

### 3. Copy the Key That Appears:
It will look like: `AIzaSyD3f4V6wk9_XYZ123abc...`

### 4. Enable the API:
https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com?project=utlyze
Click "ENABLE"

## 🔧 Test Your Credential:
```bash
cd /Users/jamesbrady/website-eater
python3 check_credential_type.py
# Paste what you have - it will tell you if it's right!
```

## 📺 Visual Guide:
I opened a webpage with pictures: `GET_API_KEY_GUIDE.html`

## 💡 The Difference:
- **Service Account** = Complex JSON file with private keys (what you have)
- **API Key** = Simple string starting with AIza (what you need)

You're in the right place (Google Cloud Console), just selecting the wrong credential type!
