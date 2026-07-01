# Docker Deployment Guide - Multi-Service Architecture

## Overview

The PDF Analysis Workbench is deployed using Docker Compose with a multi-service architecture:
- **Frontend Service**: nginx serving React static files (port 8080)
- **Backend Service**: FastAPI Python application (internal port 8000)
- **Redis Service**: Optional caching service (with-redis profile)

## Quick Start

### Prerequisites
- Docker Engine 20.10+ and Docker Compose V2
- At least 4GB RAM available
- Ports 8080 available on host

### 1. Create Environment File

Create a `.env` file in the project root with your API keys:

```bash
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/credentials/service-account.json
ADOBE_EMBED_API_KEY=f3af072fa66b4a81bd773f77c7ec0070

# Service Configuration
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
SESSION_TIMEOUT_HOURS=4
MAX_FILE_SIZE_MB=50
SPEED_PRIORITY=high
ACCURACY_MINIMUM=0.85

# TTS Configuration (for podcast generation)
GEMINI_TTS_MODEL=gemini-2.5-flash-lite-preview-tts
GEMINI_TTS_HOST_VOICE=Kore
GEMINI_TTS_GUEST_VOICE=Puck
```

### 2. Build and Start Services

```bash
# Build both services
docker-compose build

# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 3. Access the Application

- **Frontend**: http://localhost:8080
- **Backend Health Check**: http://localhost:8080/health
- **API Documentation**: http://localhost:8080/api/docs (if enabled)

## Required API Keys

| Service | Environment Variable | Description | Required |
|---------|---------------------|-------------|----------|
| **Google Gemini** | `GEMINI_API_KEY` | LLM for insights and summarization | ✅ Yes |
| **Adobe PDF Embed** | `ADOBE_EMBED_API_KEY` | Enhanced PDF viewing | ✅ Yes |
| **GCP Credentials** | `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Optional |

**Gemini Authentication Options:**
- **Option A**: Use `GEMINI_API_KEY` directly (recommended, simpler)
- **Option B**: Use `GOOGLE_APPLICATION_CREDENTIALS` with mounted credentials file

## Architecture Details

### Service Configuration

**Frontend Service (nginx)**
- Serves React static files from `/usr/share/nginx/html`
- Proxies `/api/*` requests to backend service
- Proxies `/health` requests to backend service
- Port mapping: `8080:80` (host:container)
- Health check: `curl -f http://localhost:80/`

**Backend Service (FastAPI)**
- Python 3.11 runtime with FastAPI
- Exposed internally on port 8000 (not published to host)
- Accessible only via frontend nginx proxy
- Health check: `curl -f http://localhost:8000/health`
- Mounted credentials volume at `/credentials` (read-only)

**Redis Service (Optional)**
- Activated with `--profile with-redis` flag
- Used for caching and session storage
- Image: redis:7-alpine
- Data persisted in `redis_data` volume

### Network Architecture

```
Host                              Docker Network (app-network)
┌──────────────┐                 ┌─────────────────────────────┐
│              │                 │                             │
│  Browser     │──── :8080 ─────▶│  Frontend (nginx)          │
│              │                 │  - Serves React files       │
└──────────────┘                 │  - Proxies /api/* to backend│
                                 │                             │
                                 │          ▼                  │
                                 │                             │
                                 │  Backend (FastAPI)          │
                                 │  - Port 8000 (internal)     │
                                 │  - Not exposed to host      │
                                 │                             │
                                 │  Redis (optional)           │
                                 │  - Port 6379 (internal)     │
                                 └─────────────────────────────┘
```

## Service Management

### Basic Commands

```bash
# Build specific service
docker-compose build frontend
docker-compose build backend

# Start all services
docker-compose up -d

# Start with Redis
docker-compose --profile with-redis up -d

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart specific service
docker-compose restart frontend
docker-compose restart backend

# View logs for specific service
docker-compose logs -f frontend
docker-compose logs -f backend

# Check service health status
docker-compose ps
```

### Updating Configuration

**After changing nginx.conf:**
```bash
docker-compose build frontend
docker-compose up -d frontend
```

**After changing backend code:**
```bash
docker-compose build backend
docker-compose up -d backend
```

**After changing .env file:**
```bash
docker-compose down
docker-compose up -d
```

## Configuration Options

### Application Settings

```bash
SESSION_TIMEOUT_HOURS=4        # Session expiration time
MAX_FILE_SIZE_MB=50           # Maximum PDF upload size
SPEED_PRIORITY=high           # Processing speed preference
ACCURACY_MINIMUM=0.85         # Minimum accuracy threshold
```

### LLM Configuration

```bash
LLM_PROVIDER=gemini           # LLM provider
GEMINI_MODEL=gemini-2.5-flash # Model name
GEMINI_API_KEY=your_key       # API authentication
```

### TTS Configuration

```bash
GEMINI_TTS_MODEL=gemini-2.5-flash-lite-preview-tts
GEMINI_TTS_HOST_VOICE=Kore
GEMINI_TTS_GUEST_VOICE=Puck
```

## Health Checks

Both services have configured health checks:

**Backend Health Check:**
- Command: `curl -f http://localhost:8000/health`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 40 seconds

**Frontend Health Check:**
- Command: `curl -f http://localhost:80/`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 10 seconds

Check health status:
```bash
docker-compose ps
curl http://localhost:8080/health
```

## Troubleshooting

### 502 Bad Gateway

**Symptom**: Frontend shows 502 error for API requests

**Cause**: Backend service not started or unhealthy

**Solution**:
```bash
# Check backend status
docker-compose ps backend

# View backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### CORS Errors

**Symptom**: Browser blocks API requests with CORS error

**Cause**: Backend CORS middleware misconfigured

**Solution**:
- Verify backend CORSMiddleware allows frontend origin
- Check backend logs for CORS-related errors
- Ensure nginx is not adding CORS headers (backend handles it)

### Build Failures

**Frontend Build Fails**:
```bash
# Check Node.js and npm versions
docker run --rm node:22.14.0-alpine node --version

# Check package.json for errors
# Rebuild with no cache
docker-compose build --no-cache frontend
```

**Backend Build Fails**:
```bash
# Check Python version
docker run --rm python:3.11 python --version

# Check requirements.txt for errors
# Rebuild with no cache
docker-compose build --no-cache backend
```

### Container Won't Start

**Check Docker is running**:
```bash
docker info
```

**Check port availability**:
```bash
# Windows PowerShell
Get-NetTCPConnection -LocalPort 8080

# Linux/Mac
netstat -an | grep 8080
```

**Check environment variables**:
```bash
docker-compose config
```

### Health Check Failing

**Backend unhealthy**:
```bash
# Check if backend is responding
docker exec adoberound3-1-backend-1 curl -f http://localhost:8000/health

# View detailed logs
docker-compose logs backend --tail 50
```

**Frontend unhealthy**:
```bash
# Check if nginx is serving files
docker exec adoberound3-1-frontend-1 curl -f http://localhost:80/

# Check nginx configuration
docker exec adoberound3-1-frontend-1 cat /etc/nginx/conf.d/default.conf
```

### Environment Variable Not Set

**Symptom**: Backend fails to start with missing API key error

**Solution**:
```bash
# Verify .env file exists and has correct values
cat .env

# Check if docker-compose sees the variables
docker-compose config | grep GEMINI_API_KEY

# Restart services after updating .env
docker-compose down
docker-compose up -d
```

## Production Deployment

### Security Best Practices

1. **Never commit .env file** - Add to .gitignore
2. **Use secrets management** - Consider Docker Secrets or external vault
3. **Limit resource usage** - Set memory and CPU limits
4. **Use HTTPS** - Add reverse proxy with SSL certificate
5. **Enable logging** - Configure centralized logging

### Production docker-compose Example

```yaml
services:
  frontend:
    build:
      context: ./frontend-react
    ports:
      - "8080:80"
    depends_on:
      - backend
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      - GEMINI_API_KEY
      - ADOBE_EMBED_API_KEY
    volumes:
      - ./credentials:/credentials:ro
      - ./uploads:/app/uploads
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Monitoring

```bash
# View resource usage
docker stats

# View specific service resources
docker stats adoberound3-1-frontend-1 adoberound3-1-backend-1

# Export logs
docker-compose logs > logs.txt
```

## File Structure

```
adobeRound3-1/
├── docker-compose.yml           # Multi-service orchestration
├── .env                         # Environment variables (not in git)
├── .env.example                 # Template for environment variables
├── backend/
│   ├── Dockerfile              # Backend container definition
│   ├── main.py                 # FastAPI application
│   └── ...                     # Other backend modules
├── frontend-react/
│   ├── Dockerfile              # Frontend multi-stage build
│   ├── nginx.conf              # nginx reverse proxy config
│   ├── package.json            # Node dependencies
│   └── src/                    # React source code
└── credentials/                # Mounted to backend only
    └── service-account.json
```

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **nginx Configuration**: https://nginx.org/en/docs/
- **Docker Compose**: https://docs.docker.com/compose/
- **React Deployment**: https://create-react-app.dev/docs/deployment/

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Verify health: `docker-compose ps`
3. Review this guide for common issues
4. Check environment configuration: `docker-compose config`
