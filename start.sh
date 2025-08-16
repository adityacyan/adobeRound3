#!/bin/bash

# PDF Analysis Workbench Startup Script
# This script starts both the FastAPI backend and Streamlit frontend

echo "🚀 Starting PDF Analysis Workbench..."

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default ports if not specified
export FASTAPI_BACKEND_PORT=${FASTAPI_BACKEND_PORT:-8000}
export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-8080}

echo "🔧 Configuration:"
echo "   Backend Port: $FASTAPI_BACKEND_PORT"
echo "   Frontend Port: $STREAMLIT_SERVER_PORT"

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start FastAPI backend in background
echo "🔄 Starting FastAPI backend on port $FASTAPI_BACKEND_PORT..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port $FASTAPI_BACKEND_PORT --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:$FASTAPI_BACKEND_PORT/health > /dev/null; then
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend started successfully"

# Start Streamlit frontend
echo "🔄 Starting Streamlit frontend on port $STREAMLIT_SERVER_PORT..."
streamlit run frontend/main.py --server.port $STREAMLIT_SERVER_PORT --server.address 0.0.0.0 --server.headless false &
FRONTEND_PID=$!

echo "✅ Both services started successfully!"
echo "🌐 Access the application at: http://localhost:$STREAMLIT_SERVER_PORT"
echo "🔗 Backend API available at: http://localhost:$FASTAPI_BACKEND_PORT"
echo "📊 API Documentation: http://localhost:$FASTAPI_BACKEND_PORT/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID