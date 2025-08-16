#!/usr/bin/env powershell

Write-Host "Starting PDF Analysis Workbench Backend..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

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

# Start FastAPI backend
Write-Host ""
Write-Host "🚀 Starting FastAPI backend on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the backend" -ForegroundColor Yellow
Write-Host ""

try {
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host "❌ Error starting backend: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}