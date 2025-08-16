@echo off
echo Starting PDF Analysis Workbench Frontend...
echo ===========================================

REM Activate conda environment
call conda activate .\.conda

REM Check if environment is activated
if "%CONDA_DEFAULT_ENV%"==".conda" (
    echo ✅ Conda environment activated: %CONDA_DEFAULT_ENV%
) else (
    echo ❌ Failed to activate conda environment
    pause
    exit /b 1
)

REM Wait a moment for backend to be ready
echo.
echo ⏳ Waiting 3 seconds for backend to be ready...
timeout /t 3 /nobreak > nul

REM Check if backend is running
echo 🔍 Checking backend health...
python -c "import requests; r=requests.get('http://localhost:8000/health', timeout=5); print('✅ Backend is ready') if r.status_code==200 else print('❌ Backend not responding')" 2>nul
if errorlevel 1 (
    echo ⚠️  Backend may not be running. Make sure to start backend first.
    echo    Run start_backend.bat in another terminal
    echo.
)

REM Start Streamlit frontend
echo.
echo 🚀 Starting Streamlit frontend on http://localhost:8080
echo Press Ctrl+C to stop the frontend
echo.

streamlit run frontend/main.py --server.port 8080 --server.address 0.0.0.0

pause