#!/usr/bin/env powershell

Write-Host "Starting PDF Analysis Workbench Frontend..." -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Activate conda environment
Write-Host "🔧 Activating conda environment..." -ForegroundColor Yellow
conda activate .\.conda

# Check if environment is activated
$condaEnv = $env:CONDA_DEFAULT_ENV
if ($condaEnv -eq ".conda") {
    Write-Host "✅ Conda environment activated: $condaEnv" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to activate conda environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Wait a moment for backend to be ready
Write-Host ""
Write-Host "⏳ Waiting 3 seconds for backend to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Check if backend is running
Write-Host "🔍 Checking backend health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is ready" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend not responding properly" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️  Backend may not be running. Make sure to start backend first." -ForegroundColor Yellow
    Write-Host "   Run start_backend.ps1 in another terminal" -ForegroundColor Yellow
    Write-Host ""
}

# Start Streamlit frontend
Write-Host ""
Write-Host "🚀 Starting Streamlit frontend on http://localhost:8080" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the frontend" -ForegroundColor Yellow
Write-Host ""

try {
    streamlit run frontend/main.py --server.port 8080 --server.address 0.0.0.0
} catch {
    Write-Host "❌ Error starting frontend: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}