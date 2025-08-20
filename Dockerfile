# Multi-stage build for PDF Analysis Workbench
# Stage 1: Build React Frontend
FROM node:22.14.0-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend-react/package*.json ./
RUN npm ci --only=production

COPY frontend-react/ ./
RUN npm run build

# Stage 2: Python Backend with Frontend
FROM python:3.11 AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create directories for uploads and temp files
RUN mkdir -p /app/uploads /app/temp

# Copy scripts and ensure proper line endings
COPY entrypoint.sh docker-start.sh /app/
RUN mv /app/docker-start.sh /app/start.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh /app/start.sh && \
    chmod +x /app/entrypoint.sh /app/start.sh

# Expose port
EXPOSE 8080
EXPOSE 8000

# Set entrypoint and command
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/app/start.sh"]

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set environment defaults
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
