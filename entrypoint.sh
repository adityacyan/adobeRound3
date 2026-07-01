#!/bin/bash

# Validate required env vars
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY is not set. Set it in Railway environment variables."
    exit 1
fi

echo "GEMINI_API_KEY is set (length: ${#GEMINI_API_KEY})"
echo "LLM Provider: ${LLM_PROVIDER:-gemini}"
echo "Gemini Model: ${GEMINI_MODEL:-gemini-2.5-flash}"
echo "Session Timeout: ${SESSION_TIMEOUT_HOURS:-4} hours"
echo "Max File Size: ${MAX_FILE_SIZE_MB:-50} MB"

# Write runtime .env so load_dotenv() in Python picks it up
cat > /app/.env <<EOL
GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=${GEMINI_MODEL:-gemini-3.1-flash-lite}
GEMINI_TTS_MODEL=${GEMINI_TTS_MODEL:-gemini-3.1-flash-tts-preview}
GEMINI_TTS_HOST_VOICE=${GEMINI_TTS_HOST_VOICE:-Kore}
GEMINI_TTS_GUEST_VOICE=${GEMINI_TTS_GUEST_VOICE:-Puck}
LLM_PROVIDER=${LLM_PROVIDER:-gemini}
SESSION_TIMEOUT_HOURS=${SESSION_TIMEOUT_HOURS:-4}
MAX_FILE_SIZE_MB=${MAX_FILE_SIZE_MB:-50}
SPEED_PRIORITY=${SPEED_PRIORITY:-high}
ACCURACY_MINIMUM=${ACCURACY_MINIMUM:-0.85}
PROCESSING_TIMEOUT_S=${PROCESSING_TIMEOUT_S:-60}
PORT=${PORT:-8080}
EOL

echo "Runtime .env written successfully"

exec "$@"
