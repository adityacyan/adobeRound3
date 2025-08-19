#!/bin/bash

# Docker Build and Run Script for PDF Analysis Workbench
# Usage: ./docker-run.sh [API_KEYS]

echo "🐳 PDF Analysis Workbench - Docker Deployment"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build the image
echo "🔨 Building Docker image..."
docker build -t pdf-workbench:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "✅ Docker image built successfully!"

# Check if we should run with provided API keys
if [ "$1" = "run" ]; then
    echo ""
    echo "🚀 Starting PDF Analysis Workbench..."
    echo ""
    echo "📝 Please provide your API keys:"
    echo "   Choose Gemini authentication method:"
    echo "   1) Direct API Key (simpler)"
    echo "   2) Google Cloud Credentials file"
    echo ""
    read -p "Choose option (1 or 2): " auth_option
    
    if [ "$auth_option" = "1" ]; then
        # Direct API key method
        read -p "Enter Gemini API Key: " GEMINI_KEY
        read -p "Enter Azure TTS API Key: " AZURE_TTS_KEY  
        read -p "Enter Azure TTS Endpoint: " AZURE_TTS_ENDPOINT
        read -p "Enter Adobe Embed API Key: " ADOBE_EMBED_KEY
        
        echo ""
        echo "🔄 Starting container with direct API keys..."
        
        # Run with direct API keys
        docker run -d \
            --name pdf-workbench \
            -p 8080:8080 \
            -e GEMINI_API_KEY="$GEMINI_KEY" \
            -e AZURE_TTS_KEY="$AZURE_TTS_KEY" \
            -e AZURE_TTS_ENDPOINT="$AZURE_TTS_ENDPOINT" \
            -e ADOBE_EMBED_API_KEY="$ADOBE_EMBED_KEY" \
            pdf-workbench:latest
    else
        # Credentials file method
        read -p "Enter path to credentials folder: " CREDS_PATH
        read -p "Enter Azure TTS API Key: " AZURE_TTS_KEY  
        read -p "Enter Azure TTS Endpoint: " AZURE_TTS_ENDPOINT
        read -p "Enter Adobe Embed API Key: " ADOBE_EMBED_KEY
        
        echo ""
        echo "🔄 Starting container with credentials file..."
        
        # Run with credentials mounting
        docker run -d \
            --name pdf-workbench \
            -v "$CREDS_PATH:/credentials" \
            -p 8080:8080 \
            -e GOOGLE_APPLICATION_CREDENTIALS="/credentials/adbe-gcp.json" \
            -e AZURE_TTS_KEY="$AZURE_TTS_KEY" \
            -e AZURE_TTS_ENDPOINT="$AZURE_TTS_ENDPOINT" \
            -e ADOBE_EMBED_API_KEY="$ADOBE_EMBED_KEY" \
            pdf-workbench:latest
    fi
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ PDF Analysis Workbench is running!"
        echo "🌐 Access the application at: http://localhost:8080"
        echo "📚 API Documentation: http://localhost:8080/api/docs"
        echo "🔍 Health Check: http://localhost:8080/health"
        echo ""
        echo "📋 Container Management:"
        echo "   View logs: docker logs pdf-workbench -f"
        echo "   Stop: docker stop pdf-workbench"
        echo "   Remove: docker rm pdf-workbench"
    else
        echo "❌ Failed to start container!"
        exit 1
    fi
else
    echo ""
    echo "✅ Build complete! To run the container:"
    echo "   ./docker-run.sh run"
    echo ""
    echo "Or manually with docker-compose:"
    echo "   GEMINI_API_KEY=your-key AZURE_TTS_KEY=your-key docker-compose up"
fi
