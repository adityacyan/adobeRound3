# Docker Deployment Guide

This guide explains how to build and run the PDF Analysis Workbench using Docker as specified in the requirements.

## Architecture

The Docker container includes:
- **React Frontend**: Served by nginx on port 8080
- **FastAPI Backend**: Running on internal port 8000, proxied through nginx
- **Nginx**: Acts as reverse proxy and static file server
- **Supervisor**: Manages both nginx and FastAPI processes

## Building the Docker Image

Use the exact command specified in the requirements:

```bash
docker build --platform linux/amd64 -t yourimageidentifier .
```

## Running the Container

Use the exact command specified in the requirements:

```bash
docker run -v /path/to/credentials:/credentials \
  -e ADOBE_EMBED_API_KEY=<ADOBE_EMBED_API_KEY> \
  -e LLM_PROVIDER=gemini \
  -e GOOGLE_APPLICATION_CREDENTIALS=/credentials/adbe-gcp.json \
  -e GEMINI_MODEL=gemini-2.5-flash \
  -e TTS_PROVIDER=azure \
  -e AZURE_TTS_KEY=TTS_KEY \
  -e AZURE_TTS_ENDPOINT=TTS_ENDPOINT \
  -p 8080:8080 yourimageidentifier
```

### Environment Variables

The container supports all the specified environment variables:

- `ADOBE_EMBED_API_KEY`: Adobe PDF Embed API key
- `LLM_PROVIDER`: LLM provider (default: "gemini")
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google service account JSON file
- `GEMINI_MODEL`: Gemini model name (default: "gemini-2.5-flash")
- `TTS_PROVIDER`: Text-to-speech provider (default: "azure")
- `AZURE_TTS_KEY`: Azure TTS API key
- `AZURE_TTS_ENDPOINT`: Azure TTS service endpoint

### Credentials Volume

Mount your credentials directory to `/credentials` in the container. This should contain:
- `adbe-gcp.json`: Google Cloud service account credentials file

## Accessing the Application

After running the container, the application will be accessible at:
- **Frontend**: http://localhost:8080
- **API Documentation**: http://localhost:8080/api/docs (proxied to internal FastAPI)

## Health Checks

The container includes health checks for both:
- Frontend availability (nginx serving React app)
- Backend API health endpoint

## Architecture Benefits

1. **Single Port**: Everything accessible through port 8080
2. **Optimized**: Multi-stage build for smaller image size
3. **Secure**: Non-root user for application processes
4. **Robust**: Supervisor manages process lifecycle
5. **Production Ready**: Nginx serves static files efficiently

## Build Scripts

Use the provided build scripts for convenience:
- `docker-build.sh` (Linux/macOS)
- `docker-build.bat` (Windows)

## Optional Features

- External LLM calls use the provided environment variables
- On-device alternatives (like Ollama) can be configured
- TTS can use Azure or on-device alternatives (like Festival)
