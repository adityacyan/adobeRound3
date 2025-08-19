FROM python:3.11 AS backend
WORKDIR /app/backend
COPY backend/ ./backend
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install Node.js for frontend
RUN apt-get update && apt-get install -y curl gnupg build-essential
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

WORKDIR /app/frontend
COPY frontend-react/package*.json ./
RUN npm install
COPY frontend-react/ ./

EXPOSE 8000 8080

# Script to run both backend and frontend
CMD bash -c "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & npm --prefix /app/frontend start"
