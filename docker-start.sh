#!/bin/bash

echo "Starting PDF Analysis Workbench..."

python - <<'PY'
import os
import sys
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, '/app')

from backend.main import app as backend_app

app = FastAPI(title='PDF Analysis Workbench')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Mount backend API at /api
app.mount('/api', backend_app)

# Serve React static files
static_path = Path('/app/frontend/build')
if static_path.exists():
    app.mount('/static', StaticFiles(directory=str(static_path / 'static')), name='static')

    @app.get('/{path:path}')
    async def serve_react(path: str = ''):
        if path.startswith('api/') or path.startswith('static/'):
            return
        file_path = static_path / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(static_path / 'index.html')

@app.get('/health')
async def health():
    return {'status': 'healthy', 'frontend': static_path.exists(), 'backend': True}

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    print(f'Serving on http://0.0.0.0:{port}')
    uvicorn.run(app, host='0.0.0.0', port=port)
PY
