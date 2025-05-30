#!/bin/bash
echo "🔗 Opening Google Cloud Console to enable Generative Language API..."
echo "=================================================="
echo ""
echo "📍 When the page opens:"
echo "   1. Click the 'ENABLE' button"
echo "   2. Wait for it to activate (usually takes 10-30 seconds)"
echo "   3. Come back here and press Enter"
echo ""
echo "Opening browser..."

# Open the API enablement page
open "https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com?project=utlyze"

echo ""
read -p "Press Enter after you've enabled the API..."

echo ""
echo "✅ Great! Let's test if it's working now..."
echo ""

# Test the API
cd /Users/jamesbrady/website-eater
python3 test_google_api.py
