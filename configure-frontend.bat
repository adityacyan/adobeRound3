@echo off
REM Configuration script to switch between local and Docker modes

set MODE=%1
if "%MODE%"=="" set MODE=local

echo 🔧 Configuring frontend for %MODE% mode...

if "%MODE%"=="local" (
    echo REACT_APP_API_URL=http://localhost:8000 > frontend-react\.env.local
    echo PORT=8080 >> frontend-react\.env.local
    echo BROWSER=none >> frontend-react\.env.local
    echo REACT_APP_ADOBE_CLIENT_ID=f3af072fa66b4a81bd773f77c7ec0070 >> frontend-react\.env.local
    echo ✅ Configured for local development ^(Backend: http://localhost:8000^)
) else if "%MODE%"=="docker" (
    echo REACT_APP_API_URL=/api > frontend-react\.env.local
    echo PORT=8080 >> frontend-react\.env.local
    echo BROWSER=none >> frontend-react\.env.local
    echo REACT_APP_ADOBE_CLIENT_ID=f3af072fa66b4a81bd773f77c7ec0070 >> frontend-react\.env.local
    echo ✅ Configured for Docker deployment ^(Backend: /api^)
) else (
    echo ❌ Invalid mode. Use: %0 [local^|docker]
    exit /b 1
)

echo 🚀 You can now start the frontend with: npm start
