@echo off
REM PDF Analysis Workbench Startup Script for Windows
REM This script starts both the FastAPI backend and Streamlit frontend

echo 🚀 Starting PDF Analysis Workbench...

REM Set default ports if not specified
if not defined FASTAPI_BACKEND_PORT set FASTAPI_BACKEND_PORT=8000
if not defined STREAMLIT_SERVER_PORT set STREAMLIT_SERVER_PORT=8080

echo 🔧 Configuration:
echo    Backend Port: %FASTAPI_BACKEND_PORT%
echo    Frontend Port: %STREAMLIT_SERVER_PORT%

REM Start FastAPI backend in background
echo 🔄 Starting FastAPI backend on port %FASTAPI_BACKEND_PORT%...
start "FastAPI Backend" python -m uvicorn backend.main:app --host 0.0.0.0 --port %FASTAPI_BACKEND_PORT% --reload

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start Streamlit frontend
echo 🔄 Starting Streamlit frontend on port %STREAMLIT_SERVER_PORT%...
start "Streamlit Frontend" streamlit run frontend/main.py --server.port %STREAMLIT_SERVER_PORT% --server.address 0.0.0.0

echo ✅ Both services started successfully!
echo 🌐 Access the application at: http://localhost:%STREAMLIT_SERVER_PORT%
echo 🔗 Backend API available at: http://localhost:%FASTAPI_BACKEND_PORT%
echo 📊 API Documentation: http://localhost:%FASTAPI_BACKEND_PORT%/docs
echo.
echo Press any key to continue...
pause >nul