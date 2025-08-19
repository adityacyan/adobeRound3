@echo off
REM Docker Build and Run Script for PDF Analysis Workbench (Windows)

echo 🐳 PDF Analysis Workbench - Docker Deployment
echo ==============================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker first.
    exit /b 1
)

REM Build the image
echo 🔨 Building Docker image...
docker build -t pdf-workbench:latest .

if errorlevel 1 (
    echo ❌ Docker build failed!
    exit /b 1
)

echo ✅ Docker image built successfully!

REM Check if we should run with provided API keys
if "%1"=="run" (
    echo.
    echo 🚀 Starting PDF Analysis Workbench...
    echo.
    echo 📝 Please provide your API keys:
    
    REM Prompt for API keys
    set /p GEMINI_KEY="Enter Gemini API Key: "
    set /p AZURE_TTS_KEY="Enter Azure TTS API Key: "
    set /p AZURE_TTS_ENDPOINT="Enter Azure TTS Endpoint: "
    set /p ADOBE_EMBED_KEY="Enter Adobe Embed API Key: "
    
    echo.
    echo 🔄 Starting container with provided API keys...
    
    REM Run with API keys
    docker run -d ^
        --name pdf-workbench ^
        -p 8080:8080 ^
        -e GEMINI_API_KEY="%GEMINI_KEY%" ^
        -e AZURE_TTS_KEY="%AZURE_TTS_KEY%" ^
        -e AZURE_TTS_ENDPOINT="%AZURE_TTS_ENDPOINT%" ^
        -e ADOBE_EMBED_API_KEY="%ADOBE_EMBED_KEY%" ^
        pdf-workbench:latest
    
    if not errorlevel 1 (
        echo.
        echo ✅ PDF Analysis Workbench is running!
        echo 🌐 Access the application at: http://localhost:8080
        echo 📚 API Documentation: http://localhost:8080/api/docs
        echo 🔍 Health Check: http://localhost:8080/health
        echo.
        echo 📋 Container Management:
        echo    View logs: docker logs pdf-workbench -f
        echo    Stop: docker stop pdf-workbench
        echo    Remove: docker rm pdf-workbench
    ) else (
        echo ❌ Failed to start container!
        exit /b 1
    )
) else (
    echo.
    echo ✅ Build complete! To run the container:
    echo    docker-run.bat run
    echo.
    echo Or manually with docker-compose:
    echo    set GEMINI_API_KEY=your-key^&set AZURE_TTS_KEY=your-key^&docker-compose up
)
