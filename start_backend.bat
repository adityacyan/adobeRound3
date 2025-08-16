@echo off
echo Starting PDF Analysis Workbench Backend...
echo ==========================================

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

REM Start FastAPI backend
echo.
echo 🚀 Starting FastAPI backend on http://localhost:8000
echo Press Ctrl+C to stop the backend
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause