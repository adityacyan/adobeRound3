#!/bin/bash

echo "🚀 Starting PDF Analysis Workbench..."

# Start the integrated application
python -c "
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
    port = int(os.getenv('FASTAPI_BACKEND_PORT', '8080'))
    print(f'🌐 Server starting on http://0.0.0.0:{port}')
    print(f'📱 Frontend: http://0.0.0.0:{port}/')
    print(f'🔗 API: http://0.0.0.0:{port}/api/')
    print(f'📚 Docs: http://0.0.0.0:{port}/api/docs')
    uvicorn.run(app, host='0.0.0.0', port=port)
"
