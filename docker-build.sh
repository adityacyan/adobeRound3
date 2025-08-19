#!/bin/bash

# Docker build and run script for PDF Analysis Workbench
# This script follows the exact commands specified in the requirements

echo "Building Docker image..."
docker build --platform linux/amd64 -t yourimageidentifier .

echo "Build completed. To run the container, use:"
echo ""
echo "docker run -v /path/to/credentials:/credentials \\"
echo "  -e ADOBE_EMBED_API_KEY=<ADOBE_EMBED_API_KEY> \\"
echo "  -e LLM_PROVIDER=gemini \\"
echo "  -e GOOGLE_APPLICATION_CREDENTIALS=/credentials/adbe-gcp.json \\"
echo "  -e GEMINI_MODEL=gemini-2.5-flash \\"
echo "  -e TTS_PROVIDER=azure \\"
echo "  -e AZURE_TTS_KEY=TTS_KEY \\"
echo "  -e AZURE_TTS_ENDPOINT=TTS_ENDPOINT \\"
echo "  -p 8080:8080 yourimageidentifier"
echo ""
echo "After running, the application will be accessible on http://localhost:8080"
