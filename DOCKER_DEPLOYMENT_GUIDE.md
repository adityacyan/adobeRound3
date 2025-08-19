# 🐳 Docker Deployment Guide

## Quick Start

### Option 1: Your Sample Command Format

Based on your provided sample, here are the command formats you can use:

**Option A: Using Google Cloud Credentials File**
```bash
# Build the image first
docker build -t pdf-workbench:latest .

# Run with credentials mounting
docker run -d \
  --name pdf-workbench \
  -v /path/to/credentials:/credentials \
  -e ADOBE_EMBED_API_KEY=<ADOBE_EMBED_API_KEY> \
  -e LLM_PROVIDER=gemini \
  -e GOOGLE_APPLICATION_CREDENTIALS=/credentials/adbe-gcp.json \
  -e GEMINI_MODEL=gemini-2.5-flash \
  -e TTS_PROVIDER=azure \
  -e AZURE_TTS_KEY=<TTS_KEY> \
  -e AZURE_TTS_ENDPOINT=<TTS_ENDPOINT> \
  -p 8080:8080 \
  pdf-workbench:latest
```

**Option B: Using Direct Gemini API Key (Simpler)**
```bash
# Run with direct API keys (no credentials file needed)
docker run -d \
  --name pdf-workbench \
  -e ADOBE_EMBED_API_KEY=<ADOBE_EMBED_API_KEY> \
  -e LLM_PROVIDER=gemini \
  -e GEMINI_API_KEY=<GEMINI_API_KEY> \
  -e GEMINI_MODEL=gemini-2.5-flash \
  -e TTS_PROVIDER=azure \
  -e AZURE_TTS_KEY=<TTS_KEY> \
  -e AZURE_TTS_ENDPOINT=<TTS_ENDPOINT> \
  -p 8080:8080 \
  pdf-workbench:latest
```

**Windows PowerShell Example:**
```powershell
docker run -d `
  --name pdf-workbench `
  --env ADOBE_EMBED_API_KEY="your-adobe-key" `
  --env LLM_PROVIDER="gemini" `
  --env GEMINI_API_KEY="AIzaSyDdHcwg4yRWzY73r3k-Ujsq5EWXvfioNrk" `
  --env GEMINI_MODEL="gemini-2.5-flash" `
  --env TTS_PROVIDER="azure" `
  --env AZURE_TTS_KEY="your-azure-key" `
  --env AZURE_TTS_ENDPOINT="https://your-region.tts.speech.microsoft.com/" `
  -p 8080:8080 `
  pdf-workbench:latest
```

### Option 2: Using the Build Script (Interactive)

**Windows:**
```bash
.\docker-run.bat run
```

**Linux/Mac:**
```bash
chmod +x docker-run.sh
./docker-run.sh run
```

### Option 3: Using Docker Compose

```bash
# Set your API keys and run
GEMINI_API_KEY=your-key \
AZURE_TTS_KEY=your-key \
AZURE_TTS_ENDPOINT=https://your-region.tts.speech.microsoft.com/ \
ADOBE_EMBED_API_KEY=your-key \
docker-compose up
```

### Option 4: Alternative Manual Commands

```bash
# Build the image
docker build -t pdf-workbench:latest .

# Option A: With direct Gemini API key (recommended for development)
docker run -d \
  --name pdf-workbench \
  -p 8080:8080 \
  -e GEMINI_API_KEY="your-gemini-api-key" \
  -e AZURE_TTS_KEY="your-azure-tts-key" \
  -e AZURE_TTS_ENDPOINT="https://your-region.tts.speech.microsoft.com/" \
  -e ADOBE_EMBED_API_KEY="your-adobe-embed-key" \
  pdf-workbench:latest

# Option B: With Google Cloud credentials file
docker run -d \
  --name pdf-workbench \
  -v /path/to/credentials:/credentials \
  -p 8080:8080 \
  -e GOOGLE_APPLICATION_CREDENTIALS="/credentials/adbe-gcp.json" \
  -e AZURE_TTS_KEY="your-azure-tts-key" \
  -e AZURE_TTS_ENDPOINT="https://your-region.tts.speech.microsoft.com/" \
  -e ADOBE_EMBED_API_KEY="your-adobe-embed-key" \
  pdf-workbench:latest
```

## 🔑 Required API Keys

You need to provide these API keys when running the container. You have **two options** for Gemini authentication:

| Service | Environment Variable | Description | Required |
|---------|---------------------|-------------|----------|
| **Google Gemini** | `GEMINI_API_KEY` | Direct API key for LLM functionality | ✅ Option A |
| **Google Gemini** | `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON | ✅ Option B |
| **Azure TTS** | `AZURE_TTS_KEY` | For podcast generation | ✅ Yes |
| **Azure TTS** | `AZURE_TTS_ENDPOINT` | Azure TTS service endpoint | ✅ Yes |
| **Adobe PDF Embed** | `ADOBE_EMBED_API_KEY` | For enhanced PDF viewing | ✅ Yes |

**Choose one authentication method for Gemini:**
- **Option A**: Use `GEMINI_API_KEY` directly (simpler, no file mounting needed)
- **Option B**: Use `GOOGLE_APPLICATION_CREDENTIALS` with service account file (more secure for production)

## 🖥️ **Platform-Specific Syntax:**

### **Linux/Mac (Bash):**
```bash
docker run -d \
  -e GEMINI_API_KEY="your-key" \
  -e AZURE_TTS_KEY="your-key" \
  pdf-workbench:latest
```

### **Windows PowerShell:**
```powershell
docker run -d `
  --env GEMINI_API_KEY="your-key" `
  --env AZURE_TTS_KEY="your-key" `
  pdf-workbench:latest
```

### **Windows Command Prompt (cmd):**
```cmd
docker run -d ^
  --env GEMINI_API_KEY="your-key" ^
  --env AZURE_TTS_KEY="your-key" ^
  pdf-workbench:latest
```

## 🌐 Access Points

Once running, the application will be available at:

- **Frontend**: http://localhost:8080
- **API Documentation**: http://localhost:8080/api/docs
- **Health Check**: http://localhost:8080/health

## 🛠️ Configuration

The Docker container automatically configures most settings, but you can override them:

### Application Settings
```bash
-e SESSION_TIMEOUT_HOURS=4
-e MAX_FILE_SIZE_MB=50
-e SPEED_PRIORITY=high
-e ACCURACY_MINIMUM=0.85
```

### LLM Configuration
```bash
-e LLM_PROVIDER=gemini
-e GEMINI_MODEL=gemini-2.5-flash
```

### TTS Configuration
```bash
-e TTS_PROVIDER=azure
-e AZURE_TTS_DEPLOYMENT=tts
-e AZURE_TTS_API_VERSION=2025-03-01-preview
-e AZURE_TTS_HOST_VOICE=nova
-e AZURE_TTS_GUEST_VOICE=onyx
```

## 📁 File Structure in Container

```
/app/
├── backend/          # FastAPI backend
├── frontend/build/   # Built React frontend
├── .env             # Auto-generated environment file
├── entrypoint.sh    # Environment setup script
└── start.sh         # Application startup script
```

## 🔍 Monitoring & Debugging

### View Logs
```bash
docker logs pdf-workbench -f
```

### Health Check
```bash
curl http://localhost:8080/health
```

### Container Management
```bash
# Stop the container
docker stop pdf-workbench

# Remove the container
docker rm pdf-workbench

# Restart with new API keys
docker stop pdf-workbench && docker rm pdf-workbench
# Then run again with new environment variables
```

## 🚀 Production Deployment

For production, consider:

1. **Environment Files**: Use a `.env` file instead of command-line variables
2. **Reverse Proxy**: Use nginx or similar for HTTPS and load balancing
3. **Persistent Storage**: Mount volumes for uploaded files
4. **Resource Limits**: Set memory and CPU limits

Example production docker-compose:

```yaml
version: '3.8'
services:
  pdf-workbench:
    image: pdf-workbench:latest
    restart: unless-stopped
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - AZURE_TTS_KEY=${AZURE_TTS_KEY}
      - AZURE_TTS_ENDPOINT=${AZURE_TTS_ENDPOINT}
      - ADOBE_EMBED_API_KEY=${ADOBE_EMBED_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./temp:/app/temp
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

## 🔧 Troubleshooting

### Container Won't Start
- Check Docker is running: `docker info`
- Check API keys are provided
- Check port 8000 is available: `netstat -an | grep 8000`

### Frontend Not Loading
- Check health endpoint: `curl http://localhost:8000/health`
- Verify React build exists in container: `docker exec pdf-workbench ls /app/frontend/build`

### API Errors
- Check environment variables: `docker exec pdf-workbench env | grep API`
- Check logs for authentication errors: `docker logs pdf-workbench`

### Performance Issues
- Increase memory limits
- Check system resources: `docker stats pdf-workbench`
- Consider using Redis for caching: `docker-compose --profile with-redis up`
