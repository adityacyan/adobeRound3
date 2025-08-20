# PDF Analysis Workbench

A web-based PDF document intelligence system designed for the Adobe India Hackathon 2025. The system enables users to upload multiple PDFs, perform semantic analysis across documents, generate AI-powered insights, and create audio summaries.

## Features

- **Multi-Document Upload**: Session-based workspace for multiple PDFs
- **AI-Powered Insights**: Automatic generation of takeaways, contradictions, and examples
- **Semantic Search**: Find related content across all your documents
- **Audio Summaries**: Generate podcast-style audio from your documents
- **3-Column Interface**: Efficient layout for document analysis
- **Progressive Processing**: Immediate interaction while documents process in background

## Architecture

- **Frontend**: Streamlit-based web interface with 3-column layout
- **Backend**: FastAPI with session management and document processing
- **Processing**: Background PDF analysis with semantic search capabilities
- **Deployment**: Single Docker container with both frontend and backend

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd pdf-analysis-workbench
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start Services**
   
   **Windows:**
   ```cmd
   start.bat
   ```
   
   **Linux/Mac:**
   ```bash
   ./start.sh
   ```
   
   **Manual Start:**
   ```bash
   # Terminal 1 - Backend
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   
   # Terminal 2 - Frontend
   cd frontend-react
   npm start
   
   ```

4. **Access Application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Docker Deployment

1. **Build and Run**
   ```bash
   docker-compose up --build
   ```

2. **Access Application**
   - Application: http://localhost:8080
   - Backend API: http://localhost:8000

## Project structure

```
adobeRound3/
├── backend/                    # FastAPI backend and processing modules
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, endpoints and session management
│   ├── document_processor.py   # PDF processing pipeline
│   ├── embedding_service.py    # Embeddings and semantic search glue
│   ├── llm_service.py          # LLM integration (Gemini/others)
│   ├── audio_service.py        # TTS / podcast generation helpers
│   └── search_engine.py        # Search ranking and strategy
├── frontend/                   # (Optional) Python-based frontend entrypoints
│   ├── __init__.py
│   └── main.py
├── frontend-react/             # React single-page app (production build lives in /frontend/build)
│   ├── package.json
│   └── src/                    # React source
├── sample_pdfs/                # Example PDFs used for demos and tests
├── entrypoint.sh               # Docker entrypoint (creates .env and starts services)
├── docker-start.sh             # In-container script that starts backend + frontend static server
├── Dockerfile                  # Multi-stage Dockerfile (build frontend, package backend)
├── docker-compose.yml          # Optional compose setup for local deployment
├── requirements.txt            # Python dependencies
├── start_backend.ps1/.bat      # Windows convenience scripts to run backend locally
├── start_frontend.ps1/.bat     # Windows convenience scripts to run frontend locally
├── test_*.py                   # Unit/integration tests and demos
└── README.md                   # Project documentation (this file)
```

## API Endpoints

### Health Check
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status

### Session Management
- `POST /session/create` - Create new session
- `GET /session/{session_id}` - Get session information
- `DELETE /session/{session_id}` - Delete session

## Configuration

Key environment variables:

```bash
# Core Settings
SPEED_PRIORITY=high
ACCURACY_MINIMUM=0.85
SESSION_TIMEOUT_HOURS=4

# Service Integration
GEMINI_API_KEY=your_gemini_api_key_here
AZURE_SPEECH_KEY=your_azure_speech_key_here
ADOBE_PDF_EMBED_KEY=your_adobe_api_key_here

# Application Ports
STREAMLIT_SERVER_PORT=8080
FASTAPI_BACKEND_PORT=8000
```

## Development

### Running Tests
```bash
pytest
```

### Code Structure
- Backend follows FastAPI best practices with dependency injection
- Frontend uses Streamlit's component-based architecture
- Session-based architecture with no persistent storage
- Progressive processing for optimal user experience

## Requirements Compliance

This implementation addresses the following requirements:
- **1.2**: Session-based workspace creation
- **7.1**: Python-based frontend technology (Streamlit)
- **7.6**: Health check endpoints for monitoring

## Next Steps

This is the foundation setup. Subsequent tasks will implement:
1. Document upload and processing
2. 3-column layout interface
3. PDF viewing capabilities
4. Semantic search and insights
5. Audio generation
6. Performance optimization

## License

Built for Adobe India Hackathon 2025