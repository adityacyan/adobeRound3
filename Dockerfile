# Multi-stage Docker build for PDF Analysis Workbench
# Target: Single Python container <20GB with both frontend and backend

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing and audio
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    poppler-utils \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

FROM base as dependencies

# Copy requirements and install Python dependencies
COPY --chown=app:app requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM dependencies as production

# Copy application code
COPY --chown=app:app backend/ ./backend/
COPY --chown=app:app frontend/ ./frontend/
COPY --chown=app:app .env.example ./.env

# Create credentials directory for external service keys
RUN mkdir -p /home/app/credentials

# Expose port for the application
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Startup script to run both FastAPI backend and Streamlit frontend
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/main.py --server.port 8080 --server.address 0.0.0.0 --server.headless true"]