#!/bin/bash
# AI Trading System - Startup Script
# Starts both the API backend and the Next.js dashboard

echo "🚀 AI Trading System - Starting..."
echo "=================================="

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3."
    exit 1
fi

# Check if Node is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $API_PID 2>/dev/null
    kill $DASHBOARD_PID 2>/dev/null
    echo "👋 Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start the FastAPI backend
echo ""
echo "📡 Starting API Backend (port 8000)..."
cd "$SCRIPT_DIR/trading-system-v3"

# Check if uvicorn is installed
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo "   Installing uvicorn..."
    pip3 install uvicorn fastapi --quiet
fi

python3 dashboard_api.py &
API_PID=$!
echo "   API PID: $API_PID"

# Wait for API to start
sleep 2

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ API is running at http://localhost:8000"
else
    echo "   ⚠️  API may still be starting..."
fi

# Start the Next.js dashboard
echo ""
echo "🎨 Starting Dashboard (port 3000)..."
cd "$SCRIPT_DIR/dashboard"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install --silent
fi

npm run dev &
DASHBOARD_PID=$!
echo "   Dashboard PID: $DASHBOARD_PID"

# Wait for dashboard to start
sleep 3

echo ""
echo "=================================="
echo "✅ AI Trading System is LIVE!"
echo "=================================="
echo ""
echo "📊 Dashboard:  http://localhost:3000"
echo "📡 API:        http://localhost:8000"
echo "📋 API Docs:   http://localhost:8000/docs"
echo ""
echo "🔴 Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait
