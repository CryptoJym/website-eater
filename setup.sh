#!/bin/bash

# Website Eater Setup Script

echo "🌐 Website Eater Setup"
echo "===================="

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

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers..."
playwright install chromium

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.template .env
    echo "⚠️  Please edit backend/.env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - MEM0_API_KEY (optional)"
fi

# Create data directory
mkdir -p data

cd ..

# Docker setup
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo ""
    echo "Docker Setup"
    echo "------------"
    echo "To run with Docker:"
    echo "  docker-compose up -d"
    echo ""
fi

# Success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the application:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Then open http://localhost:5000 in your browser"
echo ""
echo "For production deployment with Docker:"
echo "  docker-compose up -d"
