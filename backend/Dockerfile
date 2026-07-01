FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies (cached layer)
COPY requirements.txt .

# Install PyTorch CPU-only first (avoids CUDA downloads)
RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip \
    pip install torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Create runtime directories
RUN mkdir -p /app/uploads /app/temp

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port 8000
EXPOSE 8000

# Run uvicorn directly (no wrapper scripts)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
