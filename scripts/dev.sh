#!/bin/bash

echo "🚀 Starting Tauri + Next.js + FastAPI Development Environment"
echo "============================================================"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down development environment..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start backend
echo "🐍 Starting FastAPI backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

source venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "⚛️  Starting tauri frontend..."
npm run tauri:dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

echo ""
echo "✅ Development environment started!"
echo ""
echo "🌐 Services running:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🖥️  To run the desktop app, open a new terminal and run:"
echo "   npm run tauri:dev"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait 