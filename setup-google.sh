#!/bin/bash

# Website Eater Setup Script - Google URL Context Version

echo "🌐 Website Eater Setup (Google URL Context Edition)"
echo "================================================="

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"
    PLATFORM="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux"
    PLATFORM="linux"
else
    echo "Unsupported platform: $OSTYPE"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check for Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker found: $(docker --version)"
    DOCKER_AVAILABLE=true
else
    echo "⚠️  Docker not found. You can still run locally."
    DOCKER_AVAILABLE=false
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
cd backend
python3 -m venv venv

# Activate virtual environment
if [[ "$PLATFORM" == "macos" ]] || [[ "$PLATFORM" == "linux" ]]; then
    source venv/bin/activate
fi

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.template .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit backend/.env and add your API keys:"
    echo ""
    echo "   1. GOOGLE_API_KEY - Get from https://makersuite.google.com/app/apikey"
    echo "   2. MEM0_API_KEY - Optional, for mem0 cloud features"
    echo ""
    echo "   The Google URL Context tool requires a valid Google API key."
    echo "   Daily quotas: 1,500 API requests, 100 Google AI Studio requests"
fi

# Create data directory
mkdir -p data

cd ..

# Test the setup with simple example
echo ""
echo "Testing Google URL Context tool..."
echo ""

# Create a test script
cat > test_setup.py << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')
if api_key and api_key != 'your_google_api_key_here':
    print("✅ Google API key is configured")
    print("   You can now use the URL Context tool!")
else:
    print("❌ Google API key is not configured")
    print("   Please edit backend/.env and add your GOOGLE_API_KEY")

mem0_key = os.getenv('MEM0_API_KEY')
if mem0_key and mem0_key != 'your_mem0_api_key_here':
    print("✅ Mem0 API key is configured")
else:
    print("⚠️  Mem0 API key is not configured (optional)")

print("\nSupported Gemini models:")
print("  - gemini-2.5-flash-preview-05-20 (default)")
print("  - gemini-2.5-pro-preview-05-06")
print("  - gemini-2.0-flash")
print("")
print("URL Context capabilities:")
print("  - Extract content from up to 20 URLs per request")
print("  - Combine with Google Search for deeper analysis")
print("  - Free during experimental phase")
EOF

cd backend
source venv/bin/activate
python ../test_setup.py
rm ../test_setup.py
cd ..

# Success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Quick Start Guide:"
echo ""
echo "1. Run the web interface:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python app.py"
echo "   Then open http://localhost:5000"
echo ""
echo "2. Try the simple example:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   cd .."
echo "   python simple_example.py"
echo ""
echo "3. Use the CLI:"
echo "   python cli.py process https://example.com"
echo ""
echo "4. For production with Docker:"
echo "   docker-compose up -d"
echo ""
echo "📖 Documentation: See README.md for full details"
echo "🔗 Google URL Context Docs: https://ai.google.dev/gemini-api/docs/url-context"
