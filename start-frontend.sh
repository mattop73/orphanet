#!/bin/bash

echo "🚀 Starting Orphanet API Frontend..."
echo ""
echo "✅ Server Status Check..."

# Check if server is running
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ API Server is running on port 3000"
else
    echo "❌ API Server is not running!"
    echo "🔧 Starting server..."
    npm start &
    sleep 3
fi

echo ""
echo "🌐 Frontend URLs:"
echo "📱 Interactive Web Interface: http://localhost:3000/index.html"
echo "📊 API Documentation: http://localhost:3000/"
echo "🔍 Example API Call: http://localhost:3000/api/disorders?limit=5"
echo ""

# Try to open the frontend in default browser
echo "🌐 Opening frontend in browser..."
if command -v open >/dev/null 2>&1; then
    # macOS
    open "http://localhost:3000/index.html"
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open "http://localhost:3000/index.html"
elif command -v start >/dev/null 2>&1; then
    # Windows
    start "http://localhost:3000/index.html"
else
    echo "Please manually open: http://localhost:3000/index.html"
fi

echo ""
echo "🎯 Quick Test Commands:"
echo "curl http://localhost:3000/health"
echo "curl \"http://localhost:3000/api/disorders?limit=3\""
echo "curl \"http://localhost:3000/api/disorders/search/alexander\""