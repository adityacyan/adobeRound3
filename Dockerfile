# syntax=docker/dockerfile:1
# Multi-stage build for PDF Analysis Workbench
# Stage 1: Build React Frontend
FROM node:22.14.0-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend-react/package*.json ./
RUN npm ci

COPY frontend-react/ ./
RUN npm run build

# Stage 2: Python Backend with Frontend
FROM python:3.11 AS backend

# Install system dependencies (stable layer - rarely changes)
RUN apt-get update && apt-get install -y \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies (cached as long as requirements.txt is unchanged)
COPY requirements.txt .
# Install PyTorch CPU-only first (avoids downloading 2GB+ CUDA deps)
RUN pip install torch --extra-index-url https://download.pytorch.org/whl/cpu --no-cache-dir && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source (changes most often, placed last)
COPY backend/ ./backend/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create directories for uploads and temp files
RUN mkdir -p /app/uploads /app/temp

# Copy and prepare scripts
COPY entrypoint.sh docker-start.sh /app/
RUN mv /app/docker-start.sh /app/start.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh /app/start.sh && \
    chmod +x /app/entrypoint.sh /app/start.sh

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/app/start.sh"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
