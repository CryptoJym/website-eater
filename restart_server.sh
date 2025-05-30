#!/bin/bash
# Restart Website Eater with new API key

echo "🔄 Restarting Website Eater..."
echo "=============================="

# Kill existing servers
echo "📍 Stopping existing servers..."
lsof -ti:5002 | xargs kill -9 2>/dev/null
lsof -ti:5003 | xargs kill -9 2>/dev/null
sleep 2

# Start the URL digestion server
echo "🚀 Starting URL Digestion server on port 5003..."
cd backend
source venv/bin/activate
python app_url_digestion.py &

echo ""
echo "✅ Server restarted!"
echo "🌐 Access at: http://localhost:5003"
echo ""
echo "📹 Try these URLs:"
echo "  - YouTube: https://www.youtube.com/watch?v=any_video_id"
echo "  - GitHub: https://github.com/any/repository"
echo "  - Any webpage!"
