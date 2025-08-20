#!/bin/bash

echo "🚀 Starting PDF Analysis Workbench..."

# Start the integrated application using a heredoc to avoid shell quoting issues
python - <<'PY'
import os
import sys
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend is in Python path
sys.path.insert(0, '/app')

# Import the backend app
from backend.main import app as backend_app

# Create main app
app = FastAPI(title='PDF Analysis Workbench')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Mount backend API with /api prefix
app.mount('/api', backend_app)

# Serve React static files
static_path = Path('/app/frontend/build')
if static_path.exists():
    # Mount static assets
    app.mount('/static', StaticFiles(directory=str(static_path / 'static')), name='static')
    
    # Serve React app for all other routes
    @app.get('/{path:path}')
    async def serve_react_app(path: str = ''):
        # Don't interfere with API routes
        if path.startswith('api/'):
            return
            
        # Try to serve the requested file
        if path:
            file_path = static_path / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
        
        # Fallback to index.html for React SPA routing
        return FileResponse(static_path / 'index.html')

# Health check endpoint at root level
@app.get('/health')
async def health_check():
    return {
        'status': 'healthy', 
        'service': 'pdf-workbench',
        'frontend': static_path.exists(),
        'backend': True
    }

if __name__ == '__main__':
    import subprocess
    backend_port = int(os.getenv('FASTAPI_BACKEND_PORT', '8000'))
    frontend_port = int(os.getenv('PORT', '8080'))

    print(f'🌐 Starting backend on http://0.0.0.0:{backend_port} (mounted at /api)')
    print(f'Serving frontend static files on http://0.0.0.0:{frontend_port}')

    # Start backend using uvicorn in a subprocess (serve the backend_app mounted at /api)
    backend_cmd = [
        'python', '-c',
        'import uvicorn; from backend.main import app as backend_app; uvicorn.run(backend_app, host="0.0.0.0", port=%d)' % backend_port
    ]

    # Start a simple static file server for the built React app on frontend_port
    static_dir = '/app/frontend/build'
    frontend_cmd = [
        'python', '-m', 'http.server', str(frontend_port), '--directory', static_dir
    ]

    # Launch both processes and wait
    procs = []
    try:
        procs.append(subprocess.Popen(backend_cmd))
        # Give backend a moment to start
        import time; time.sleep(0.5)
        # Start frontend static server (only if build exists)
        import os
        if os.path.exists(static_dir):
            procs.append(subprocess.Popen(frontend_cmd))

        # Wait for processes
        for p in procs:
            p.wait()

    except KeyboardInterrupt:
        for p in procs:
            p.terminate()
        raise
PY

