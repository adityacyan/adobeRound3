#!/bin/bash
# Configuration script to switch between local and Docker modes

MODE=${1:-"local"}

echo "🔧 Configuring frontend for $MODE mode..."

if [ "$MODE" = "local" ]; then
    echo "REACT_APP_API_URL=http://localhost:8000" > frontend-react/.env.local
    echo "PORT=8080" >> frontend-react/.env.local
    echo "BROWSER=none" >> frontend-react/.env.local
    echo "REACT_APP_ADOBE_CLIENT_ID=f3af072fa66b4a81bd773f77c7ec0070" >> frontend-react/.env.local
    echo "✅ Configured for local development (Backend: http://localhost:8000)"
elif [ "$MODE" = "docker" ]; then
    echo "REACT_APP_API_URL=/api" > frontend-react/.env.local
    echo "PORT=8080" >> frontend-react/.env.local
    echo "BROWSER=none" >> frontend-react/.env.local
    echo "REACT_APP_ADOBE_CLIENT_ID=f3af072fa66b4a81bd773f77c7ec0070" >> frontend-react/.env.local
    echo "✅ Configured for Docker deployment (Backend: /api)"
else
    echo "❌ Invalid mode. Use: $0 [local|docker]"
    exit 1
fi

echo "🚀 You can now start the frontend with: npm start"
