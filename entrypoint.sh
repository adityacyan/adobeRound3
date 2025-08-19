#!/bin/bash

# Create .env file from environment variables and defaults
cat > /app/.env << 'EOL'
# API Keys (provided at runtime)
GEMINI_API_KEY=${GEMINI_API_KEY:-}
AZURE_TTS_KEY=${AZURE_TTS_KEY:-}
AZURE_TTS_ENDPOINT=${AZURE_TTS_ENDPOINT:-}

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-}

# Adobe Configuration
ADOBE_EMBED_API_KEY=${ADOBE_EMBED_API_KEY:-}
REACT_APP_ADOBE_CLIENT_ID=f3af072fa66b4a81bd773f77c7ec0070

# Service Configuration (defaults from current setup)
LLM_PROVIDER=${LLM_PROVIDER:-gemini}
GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.5-flash}
TTS_PROVIDER=${TTS_PROVIDER:-azure}
AZURE_TTS_DEPLOYMENT=${AZURE_TTS_DEPLOYMENT:-tts}
AZURE_TTS_API_VERSION=${AZURE_TTS_API_VERSION:-2025-03-01-preview}
AZURE_TTS_HOST_VOICE=${AZURE_TTS_HOST_VOICE:-nova}
AZURE_TTS_GUEST_VOICE=${AZURE_TTS_GUEST_VOICE:-onyx}
AZURE_TTS_VOICE=${AZURE_TTS_VOICE:-alloy}

# Application Configuration
SESSION_TIMEOUT_HOURS=${SESSION_TIMEOUT_HOURS:-4}
MAX_FILE_SIZE_MB=${MAX_FILE_SIZE_MB:-50}
SPEED_PRIORITY=${SPEED_PRIORITY:-high}
ACCURACY_MINIMUM=${ACCURACY_MINIMUM:-0.85}
FASTAPI_BACKEND_PORT=${FASTAPI_BACKEND_PORT:-8080}

# Frontend Configuration
REACT_APP_API_URL=/api
GENERATE_SOURCEMAP=false
PORT=8080
BROWSER=none
EOL

echo "✅ Environment file created successfully!"
echo "🔧 Configuration loaded:"
echo "   LLM Provider: $LLM_PROVIDER"
echo "   TTS Provider: $TTS_PROVIDER"
echo "   Session Timeout: $SESSION_TIMEOUT_HOURS hours"
echo "   Max File Size: $MAX_FILE_SIZE_MB MB"

# Start the application
exec "$@"
