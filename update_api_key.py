#!/usr/bin/env python3
"""
Update API key in Website Eater
"""
import os
import sys

print("🔑 Website Eater API Key Updater")
print("=" * 50)

# Get new API key from user
new_key = input("Paste your new API key here: ").strip()

if not new_key.startswith("AIza"):
    print("❌ That doesn't look like a valid API key.")
    print("   API keys start with 'AIza...'")
    sys.exit(1)

# Update the .env file
env_path = "backend/.env"
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update the API key line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('GOOGLE_API_KEY='):
            lines[i] = f'GOOGLE_API_KEY={new_key}\n'
            updated = True
            break
    
    if updated:
        with open(env_path, 'w') as f:
            f.writelines(lines)
        print(f"\n✅ API key updated successfully!")
        print(f"   Old key: AIzaSyCuckrGcWWy-V1V...")
        print(f"   New key: {new_key[:20]}...")
        print("\n🚀 Next steps:")
        print("   1. Restart the Website Eater server")
        print("   2. Try digesting a YouTube URL!")
    else:
        print("❌ Could not find GOOGLE_API_KEY in .env file")
else:
    print(f"❌ Could not find {env_path}")
    print("   Make sure you're in the website-eater directory")
