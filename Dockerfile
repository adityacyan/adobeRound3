# Multi-stage Docker build for PDF Analysis Workbench
# Target: Single container with React frontend and FastAPI backend

FROM node:18-slim as frontend-builder

# Set working directory for frontend build
WORKDIR /app/frontend-react

# Copy package files
COPY frontend-react/package*.json ./

# Install frontend dependencies
RUN npm ci --only=production

# Copy frontend source code
COPY frontend-react/ ./

# Build React app for production with correct API URL
RUN npm run build

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing, audio, and serving static files
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    poppler-utils \
    libsndfile1 \
    ffmpeg \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

FROM base as dependencies

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM dependencies as production

# Switch to app user
USER app
WORKDIR /home/app

# Copy application code
COPY --chown=app:app backend/ ./backend/
COPY --chown=app:app sample_pdfs/ ./sample_pdfs/

# Copy built React frontend from frontend-builder stage
COPY --from=frontend-builder --chown=app:app /app/frontend-react/build ./static/

# Create directories for credentials and environment
RUN mkdir -p /home/app/credentials
RUN mkdir -p /home/app/logs

# Switch back to root to configure nginx and supervisor
USER root

# Configure nginx to serve React frontend and proxy API calls
RUN echo 'server { \
    listen 8080; \
    server_name localhost; \
    \
    # Serve React static files \
    location / { \
        root /home/app/static; \
        try_files $uri $uri/ /index.html; \
        add_header Cache-Control "public, max-age=3600"; \
    } \
    \
    # Proxy API calls to FastAPI backend \
    location /api/ { \
        proxy_pass http://127.0.0.1:8000/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_connect_timeout 60s; \
        proxy_send_timeout 60s; \
        proxy_read_timeout 60s; \
    } \
    \
    # Handle WebSocket connections \
    location /ws { \
        proxy_pass http://127.0.0.1:8000/ws; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
    } \
}' > /etc/nginx/sites-available/default

# Configure supervisor to manage both nginx and FastAPI
RUN echo '[supervisord] \
nodaemon=true \
user=root \
logfile=/home/app/logs/supervisord.log \
pidfile=/home/app/logs/supervisord.pid \
\
[program:nginx] \
command=nginx -g "daemon off;" \
autostart=true \
autorestart=true \
stderr_logfile=/home/app/logs/nginx.err.log \
stdout_logfile=/home/app/logs/nginx.out.log \
user=root \
\
[program:fastapi] \
command=python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 \
directory=/home/app \
autostart=true \
autorestart=true \
stderr_logfile=/home/app/logs/fastapi.err.log \
stdout_logfile=/home/app/logs/fastapi.out.log \
user=app \
environment=PYTHONPATH="/home/app"' > /etc/supervisor/conf.d/supervisord.conf

# Create startup script to handle environment variables
RUN echo '#!/bin/bash \
set -e \
\
# Set default values for environment variables if not provided \
export ADOBE_EMBED_API_KEY=${ADOBE_EMBED_API_KEY:-""} \
export LLM_PROVIDER=${LLM_PROVIDER:-"gemini"} \
export GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-"/credentials/adbe-gcp.json"} \
export GEMINI_MODEL=${GEMINI_MODEL:-"gemini-2.5-flash"} \
export TTS_PROVIDER=${TTS_PROVIDER:-"azure"} \
export AZURE_TTS_KEY=${AZURE_TTS_KEY:-""} \
export AZURE_TTS_ENDPOINT=${AZURE_TTS_ENDPOINT:-""} \
\
# Log environment status \
echo "Starting PDF Analysis Workbench..." \
echo "LLM Provider: $LLM_PROVIDER" \
echo "TTS Provider: $TTS_PROVIDER" \
echo "Adobe Embed API configured: $([ -n "$ADOBE_EMBED_API_KEY" ] && echo "Yes" || echo "No")" \
echo "Google credentials: $([ -f "$GOOGLE_APPLICATION_CREDENTIALS" ] && echo "Found" || echo "Not found")" \
\
# Ensure log directory permissions \
chown -R app:app /home/app/logs \
\
# Start supervisor to manage nginx and FastAPI \
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf' > /start.sh

RUN chmod +x /start.sh

# Expose port 8080 (nginx will serve React frontend and proxy to FastAPI backend)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/ && curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/start.sh"]