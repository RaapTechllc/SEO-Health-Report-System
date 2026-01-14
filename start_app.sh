#!/bin/bash
# Start SEO Health Report System
# Runs both the API server and frontend

echo "🚀 Starting SEO Health Report System..."
echo ""

# Check for required packages
python3 -c "import fastapi, uvicorn" 2>/dev/null || {
    echo "Installing Python dependencies..."
    pip3 install --break-system-packages fastapi uvicorn httpx
}

# Start API server in background
echo "📡 Starting API server on http://localhost:8000..."
cd "$(dirname "$0")"
python3 api_server.py &
API_PID=$!

# Wait for API to start
sleep 2

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API server running"
else
    echo "❌ API server failed to start"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "============================================"
echo "SEO Health Report System is running!"
echo "============================================"
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "📡 API:      http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Handle shutdown
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait
