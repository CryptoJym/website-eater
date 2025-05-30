#!/bin/bash
# Quick command to open the right page for API key creation

echo "🔑 Opening Google Cloud Console to create API key..."
echo "=================================================="
echo ""
echo "Steps to follow:"
echo "1. Make sure you're in the 'utlyze' project (or create a new one)"
echo "2. Click '+ CREATE CREDENTIALS'"
echo "3. Select 'API key' (NOT OAuth client)"
echo "4. Copy the key that starts with 'AIza...'"
echo ""
echo "Opening browser..."

# Open the credentials page
open "https://console.cloud.google.com/apis/credentials?project=utlyze"
