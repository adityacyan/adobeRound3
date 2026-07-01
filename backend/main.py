"""
FastAPI backend main application with session management and health check endpoints.
"""
from contextlib import asynccontextmanager
import uuid
import time
import tempfile
import shutil
import asyncio
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from pydantic import BaseModel
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

# Import enhanced document processor and embedding service
from .document_processor import document_processor, ProcessingProgress
from .embedding_service import embedding_service, SearchResult
from .search_engine import search_engine, EnhancedSearchResult, SearchContext
from .llm_service import get_llm_service
from .llm_service import get_llm_service, InsightResponse
from .audio_service import audio_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session storage (in-memory for session-based architecture)
sessions: Dict[str, dict] = {}

class DocumentSection(BaseModel):
    """Document section with extracted content."""
    section_id: str
    title: str
    content: str
    page_number: int
    section_type: str  # header, paragraph, list, table, etc.
    confidence: float = 1.0

class DocumentMetadata(BaseModel):
    """Document metadata for uploaded PDFs."""
    document_id: str
    filename: str
    original_filename: str
    title: Optional[str] = None  # Display title for frontend
    file_path: str
    file_size: int
    upload_timestamp: datetime
    processing_status: str = "pending"  # pending, processing, completed, failed
    processing_progress: float = 0.0
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    total_pages: Optional[int] = None
    extracted_text_length: Optional[int] = None
    sections: List[DocumentSection] = []
    processing_method: Optional[str] = None  # fitz, ocr, hybrid
    error_message: Optional[str] = None

class SessionData(BaseModel):
    """Session data model for temporary workspace."""
    session_id: str
    created_at: datetime
    expires_at: datetime
    documents: List[DocumentMetadata] = []
    processing_status: str = "idle"
    temp_directory: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    session_count: int
    uptime_seconds: float

class UploadResponse(BaseModel):
    """Response model for bulk PDF upload."""
    session_id: str
    uploaded_documents: List[DocumentMetadata]
    total_documents: int
    processing_started: bool
    message: str

class SummaryRequest(BaseModel):
    """Request model for content summarization."""
    content: str
    mode: str = "document"  # "selection" or "document"
    document_id: Optional[str] = None

class SummaryResponse(BaseModel):
    """Response model for content summarization."""
    summary: str
    mode: str
    content_length: int
    processing_time: float
    timestamp: datetime

class PodcastRequest(BaseModel):
    """Request model for podcast generation."""
    content: Optional[str] = None
    document_id: Optional[str] = None
    use_insights: bool = True
    use_dual_speaker: bool = True
    include_selection: bool = False

class PodcastResponse(BaseModel):
    """Response model for podcast generation."""
    audio_url: str
    duration_estimate: str
    format: str
    speakers_used: List[str]
    processing_time: float
    timestamp: datetime

# Application startup time for uptime calculation
startup_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("PDF Analysis Workbench backend starting up...")
    print(f"Session timeout: {os.getenv('SESSION_TIMEOUT_HOURS', '4')} hours")
    print(f"Max file size: {os.getenv('MAX_FILE_SIZE_MB', '50')} MB")
    yield
    # Shutdown
    print("PDF Analysis Workbench backend shutting down...")
    # Clean up all session temporary directories
    for session_id, session_data in sessions.items():
        temp_dir = session_data.get("temp_directory")
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temp directory for session {session_id}")
            except Exception as e:
                print(f"Warning: Failed to clean up temp directory for session {session_id}: {e}")
    
    # Clear all sessions
    sessions.clear()
    print("All sessions and temporary files cleaned up")

# Create FastAPI application with session management
app = FastAPI(
    title="PDF Analysis Workbench API",
    description="Backend API for multi-document PDF analysis with session-based processing",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", 
        "http://127.0.0.1:8080",
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_session() -> str:
    """Create a new session with expiration time and temporary directory."""
    session_id = str(uuid.uuid4())
    session_timeout_hours = int(os.getenv("SESSION_TIMEOUT_HOURS", "4"))
    
    # Create temporary directory for this session
    temp_dir = tempfile.mkdtemp(prefix=f"pdf_session_{session_id}_")
    
    session_data = SessionData(
        session_id=session_id,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=session_timeout_hours),
        temp_directory=temp_dir
    )
    
    sessions[session_id] = session_data.dict()
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    """Get session data if it exists and hasn't expired."""
    if session_id not in sessions:
        return None
    
    session = sessions[session_id]
    if datetime.now() > session["expires_at"]:
        # Session expired, remove it
        del sessions[session_id]
        return None
    
    return session

def cleanup_expired_sessions():
    """Remove expired sessions from memory and clean up temporary files."""
    current_time = datetime.now()
    expired_sessions = [
        session_id for session_id, session_data in sessions.items()
        if current_time > session_data["expires_at"]
    ]
    
    for session_id in expired_sessions:
        session_data = sessions[session_id]
        
        # Clean up embeddings for all documents in session
        documents = session_data.get("documents", [])
        for document in documents:
            document_id = document.get("document_id")
            if document_id:
                try:
                    embedding_service.remove_document_embeddings(document_id)
                except Exception as e:
                    logger.warning(f"Failed to clean up embeddings for document {document_id}: {e}")
        
        # Clean up temporary directory if it exists
        if session_data.get("temp_directory") and os.path.exists(session_data["temp_directory"]):
            try:
                shutil.rmtree(session_data["temp_directory"])
            except Exception as e:
                print(f"Warning: Failed to clean up temp directory for session {session_id}: {e}")
        
        del sessions[session_id]
    
    return len(expired_sessions)

def validate_pdf_file(file: UploadFile) -> bool:
    """Validate that uploaded file is a PDF."""
    if not file.filename:
        return False
    
    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        return False
    
    # Check content type
    if file.content_type and not file.content_type.startswith('application/pdf'):
        return False
    
    return True

async def save_uploaded_file(file: UploadFile, session_id: str) -> DocumentMetadata:
    """Save uploaded PDF file to session temporary directory."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    temp_dir = session.get("temp_directory")
    if not temp_dir or not os.path.exists(temp_dir):
        raise HTTPException(status_code=500, detail="Session temporary directory not available")
    
    # Generate unique document ID and filename
    document_id = str(uuid.uuid4())
    safe_filename = f"{document_id}_{file.filename}"
    file_path = os.path.join(temp_dir, safe_filename)
    
    # Save file to temporary directory
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create document metadata
        document_metadata = DocumentMetadata(
            document_id=document_id,
            filename=safe_filename,
            original_filename=file.filename,
            title=file.filename,  # Set title to original filename for display
            file_path=file_path,
            file_size=len(content),
            upload_timestamp=datetime.now(),
            processing_status="pending"
        )
        
        return document_metadata
        
    except Exception as e:
        # Clean up file if it was partially created
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}") from e

def update_session_processing_status(session_id: str):
    """Update session processing status based on document statuses."""
    session = sessions.get(session_id)
    if not session:
        return
    
    documents = session.get("documents", [])
    if not documents:
        session["processing_status"] = "idle"
        return
    
    # Count document statuses
    pending_count = sum(1 for doc in documents if doc.get("processing_status") == "pending")
    processing_count = sum(1 for doc in documents if doc.get("processing_status") == "processing")
    completed_count = sum(1 for doc in documents if doc.get("processing_status") == "completed")
    failed_count = sum(1 for doc in documents if doc.get("processing_status") == "failed")
    
    if pending_count > 0 or processing_count > 0:
        session["processing_status"] = "processing"
    elif completed_count > 0 and failed_count == 0:
        session["processing_status"] = "completed"
    elif failed_count > 0:
        session["processing_status"] = "partial_failure"
    else:
        session["processing_status"] = "idle"

def extract_text_with_fitz(pdf_path: str) -> tuple[str, List[DocumentSection], str]:
    """Extract text from PDF using PyMuPDF (fitz) with section identification."""
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        sections = []
        print("using fitz")
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text blocks with formatting information
            blocks = page.get_text("dict")
            page_text = ""
            
            for block in blocks["blocks"]:
                if "lines" in block:  # Text block
                    block_text = ""
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"]
                        block_text += line_text + "\n"
                    
                    if block_text.strip():
                        page_text += block_text
                        
                        # Simple section identification based on text formatting
                        section_type = identify_section_type(block_text)
                        if section_type != "paragraph" or len(block_text.strip()) > 50:
                            section = DocumentSection(
                                section_id=f"page_{page_num + 1}_section_{len(sections)}",
                                title=extract_section_title(block_text),
                                content=block_text.strip(),
                                page_number=page_num + 1,
                                section_type=section_type,
                                confidence=1.0
                            )
                            sections.append(section)
            
            full_text += page_text
        
        doc.close()
        return full_text, sections, "fitz"
        
    except Exception as e:
        raise Exception(f"Fitz extraction failed: {str(e)}") from e

def extract_text_with_ocr(pdf_path: str) -> tuple[str, List[DocumentSection], str]:
    """Extract text from PDF using OCR as fallback method."""
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        sections = []
        print('using ocr')
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Perform OCR
            page_text = pytesseract.image_to_string(img, config='--psm 6')
            
            if page_text.strip():
                full_text += page_text + "\n"
                
                # Create sections from OCR text (simpler approach)
                paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
                for i, paragraph in enumerate(paragraphs):
                    if len(paragraph) > 20:  # Only meaningful paragraphs
                        section = DocumentSection(
                            section_id=f"page_{page_num + 1}_ocr_section_{i}",
                            title=extract_section_title(paragraph),
                            content=paragraph,
                            page_number=page_num + 1,
                            section_type="paragraph",
                            confidence=0.8  # Lower confidence for OCR
                        )
                        sections.append(section)
        
        doc.close()
        return full_text, sections, "ocr"
        
    except Exception as e:
        raise Exception(f"OCR extraction failed: {str(e)}") from e

def identify_section_type(text: str) -> str:
    """Identify the type of section based on text characteristics."""
    text = text.strip()
    
    if not text:
        return "empty"
    
    # Check for headers (short, often capitalized, no ending punctuation)
    if len(text) < 100 and text.isupper():
        return "header"
    
    # Check for lists (starts with bullet points or numbers)
    if re.match(r'^[\s]*[•\-\*\d+\.]\s', text):
        return "list"
    
    # Check for potential headers (short lines, title case)
    if len(text) < 100 and text.istitle() and not text.endswith('.'):
        return "header"
    
    # Default to paragraph
    return "paragraph"

def extract_section_title(text: str) -> str:
    """Extract a title from section text."""
    lines = text.strip().split('\n')
    first_line = lines[0].strip()
    
    # If first line is short and looks like a title, use it
    if len(first_line) < 100 and (first_line.istitle() or first_line.isupper()):
        return first_line
    
    # Otherwise, use first 50 characters as title
    return (first_line[:50] + "...") if len(first_line) > 50 else first_line

async def process_document(document_id: str, session_id: str):
    """Process a single PDF document using enhanced processing pipeline."""
    session = sessions.get(session_id)
    if not session:
        return
    
    # Find the document in session
    document = None
    for doc in session["documents"]:
        if doc["document_id"] == document_id:
            document = doc
            break
    
    if not document:
        return
    
    # Set up progress callback to update document status
    def progress_callback(progress: ProcessingProgress):
        """Update document progress based on processor updates."""
        # Map processing stages to standard status values
        if progress.stage in ["starting", "extracting", "chunking", "embedding"]:
            document["processing_status"] = "processing"
        elif progress.stage == "completed":
            document["processing_status"] = "completed"
        elif progress.stage == "failed":
            document["processing_status"] = "failed"
        else:
            document["processing_status"] = "processing"  # fallback for any other stages
            
        document["processing_progress"] = progress.progress
        
        if progress.stage == "starting":
            document["processing_start_time"] = progress.timestamp
        elif progress.stage == "completed":
            document["processing_end_time"] = progress.timestamp
        elif progress.stage == "failed":
            document["processing_end_time"] = progress.timestamp
            document["error_message"] = progress.message
        
        # Update session status
        update_session_processing_status(session_id)
        
        # Send WebSocket notification (schedule it if event loop is running)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(send_processing_update(
                session_id, 
                progress.stage, 
                progress.message, 
                int(progress.progress * 100)
            ))
        except RuntimeError:
            # No event loop running, skip WebSocket update
            logger.debug(f"No event loop for WebSocket update: {progress.stage}")
        
        # Log progress for monitoring
        logger.info(f"Document {document_id} progress: {progress.stage} - {progress.progress:.1%} - {progress.message}")
    
    # Register progress callback
    document_processor.add_progress_callback(document_id, progress_callback)
    
    try:
        # Use enhanced processor
        processed_doc = await document_processor.process_document_async(
            pdf_path=document["file_path"],
            document_id=document_id,
            filename=document["original_filename"]
        )
        
        # Update document with processed results
        document["extracted_text_length"] = processed_doc.extracted_text_length
        document["sections"] = [section.dict() for section in processed_doc.sections]
        document["processing_method"] = processed_doc.processing_method
        document["total_pages"] = processed_doc.total_pages
        document["processing_progress"] = 1.0
        document["processing_status"] = "completed"
        document["processing_end_time"] = datetime.now()
        
        # Add quality metrics
        document["quality_score"] = processed_doc.quality_score
        document["processing_metadata"] = processed_doc.metadata
        
        # Update session status
        update_session_processing_status(session_id)
        
        # Send completion notification via WebSocket
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(send_processing_update(
                session_id, 
                "completed", 
                f"Document '{document['original_filename']}' processed successfully", 
                100
            ))
        except RuntimeError:
            logger.debug("No event loop for completion WebSocket update")
        
        logger.info(f"Successfully processed document {document_id} in {processed_doc.processing_time_ms}ms using {processed_doc.processing_method}")
        
    except Exception as e:
        # Mark as failed
        document["processing_status"] = "failed"
        document["processing_end_time"] = datetime.now()
        document["error_message"] = str(e)
        document["processing_progress"] = 0.0
        
        # Update session status
        update_session_processing_status(session_id)
        
        # Send failure notification via WebSocket
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(send_processing_update(
                session_id, 
                "failed", 
                f"Failed to process '{document['original_filename']}': {str(e)}", 
                0
            ))
        except RuntimeError:
            logger.debug("No event loop for failure WebSocket update")
        
        logger.error(f"Failed to process document {document_id}: {e}")
    
    finally:
        # Clean up progress callbacks
        document_processor.cleanup_callbacks(document_id)
        update_session_processing_status(session_id)

def start_background_processing(session_id: str):
    """Start background processing for all pending documents in a session."""
    session = sessions.get(session_id)
    if not session:
        return
    
    pending_documents = [
        doc for doc in session["documents"] 
        if doc.get("processing_status") in ["pending", "priority"]
    ]
    
    if not pending_documents:
        return
    
    # Sort by priority (priority status first)
    pending_documents.sort(key=lambda x: 0 if x.get("processing_status") == "priority" else 1)
    
    # Process documents sequentially to avoid overwhelming the system
    async def process_all_documents():
        for document in pending_documents:
            await process_document(document["document_id"], session_id)
            # Small delay between documents to prevent resource exhaustion
            await asyncio.sleep(0.1)
    
    # Run in background
    asyncio.create_task(process_all_documents())

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring system status.
    Requirements: 7.6 - health check endpoints for monitoring
    """
    # Clean up expired sessions before reporting
    cleanup_expired_sessions()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        session_count=len(sessions),
        uptime_seconds=time.time() - startup_time
    )

@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with additional system information.
    Requirements: 7.6 - monitoring endpoints
    """
    cleanup_expired_sessions()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "system_info": {
            "session_count": len(sessions),
            "uptime_seconds": time.time() - startup_time,
            "environment": {
                "session_timeout_hours": os.getenv("SESSION_TIMEOUT_HOURS", "4"),
                "speed_priority": os.getenv("SPEED_PRIORITY", "high"),
                "accuracy_minimum": os.getenv("ACCURACY_MINIMUM", "0.85")
            }
        },
        "services": {
            "session_management": "operational",
            "document_processing": "ready",
            "api_gateway": "operational"
        }
    }

@app.post("/session/create")
async def create_new_session():
    """
    Create a new session for document analysis.
    Requirements: 1.2 - session-based workspace creation
    """
    session_id = create_session()
    return {
        "session_id": session_id,
        "created_at": sessions[session_id]["created_at"],
        "expires_at": sessions[session_id]["expires_at"],
        "status": "created"
    }

@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a specific session.
    Requirements: 1.2 - session management
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    return {
        "session_id": session_id,
        "created_at": session["created_at"],
        "expires_at": session["expires_at"],
        "documents": session["documents"],
        "processing_status": session["processing_status"]
    }

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and all associated data.
    Requirements: 1.6 - automatic session cleanup
    """
    if session_id in sessions:
        session_data = sessions[session_id]
        
        # Clean up embeddings for all documents in session
        documents = session_data.get("documents", [])
        for document in documents:
            document_id = document.get("document_id")
            if document_id:
                try:
                    embedding_service.remove_document_embeddings(document_id)
                except Exception as e:
                    logger.warning(f"Failed to clean up embeddings for document {document_id}: {e}")
        
        # Clean up temporary directory
        if session_data.get("temp_directory") and os.path.exists(session_data["temp_directory"]):
            try:
                shutil.rmtree(session_data["temp_directory"])
            except Exception as e:
                print(f"Warning: Failed to clean up temp directory: {e}")
        
        del sessions[session_id]
        return {"message": "Session deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/upload/bulk", response_model=UploadResponse)
async def upload_bulk_pdfs(
    session_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Bulk upload multiple PDF files to a session for analysis.
    
    Requirements:
    - 1.1: Multiple PDF uploads to create temporary analysis workspace
    - 1.2: Session-based workspace creation with immediate first PDF viewing
    - 1.6: Progress tracking for background processing
    """
    # Validate session exists
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Validate that files were provided
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided for upload")
    
    # Validate all files are PDFs
    invalid_files = []
    for file in files:
        if not validate_pdf_file(file):
            invalid_files.append(file.filename or "unknown")
    
    if invalid_files:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file types. Only PDF files are allowed. Invalid files: {', '.join(invalid_files)}"
        )
    
    # Check file size limits (optional - can be configured)
    max_file_size = int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024  # Default 50MB
    oversized_files = []
    for file in files:
        if file.size and file.size > max_file_size:
            oversized_files.append(f"{file.filename} ({file.size / 1024 / 1024:.1f}MB)")
    
    if oversized_files:
        raise HTTPException(
            status_code=400,
            detail=f"Files exceed maximum size limit of {max_file_size / 1024 / 1024}MB: {', '.join(oversized_files)}"
        )
    
    uploaded_documents = []
    failed_uploads = []
    
    # Process each file upload
    for file in files:
        try:
            document_metadata = await save_uploaded_file(file, session_id)
            uploaded_documents.append(document_metadata)
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            failed_uploads.append(f"{file.filename}: {str(e)}")
    
    # If some uploads failed, return error
    if failed_uploads:
        # Clean up any successfully uploaded files from this batch
        for doc in uploaded_documents:
            try:
                if os.path.exists(doc.file_path):
                    os.remove(doc.file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload some files: {'; '.join(failed_uploads)}"
        )
    
    # Update session with new documents
    session["documents"].extend([doc.dict() for doc in uploaded_documents])
    
    # Set first document as priority for immediate processing
    if uploaded_documents:
        session["documents"][0]["processing_status"] = "priority"
    
    # Update session processing status
    update_session_processing_status(session_id)
    
    # Start background processing for uploaded documents
    processing_started = len(uploaded_documents) > 0
    if processing_started:
        start_background_processing(session_id)
        
        # Send upload completion notification via WebSocket
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(send_processing_update(
                session_id, 
                "upload_completed", 
                f"Successfully uploaded {len(uploaded_documents)} PDF files. Processing started.", 
                None
            ))
        except RuntimeError:
            logger.debug("No event loop for upload completion WebSocket update")
    
    return UploadResponse(
        session_id=session_id,
        uploaded_documents=uploaded_documents,
        total_documents=len(uploaded_documents),
        processing_started=processing_started,
        message=f"Successfully uploaded {len(uploaded_documents)} PDF files. Background processing will begin shortly."
    )

@app.get("/session/{session_id}/documents")
async def get_session_documents(session_id: str):
    """
    Get list of documents in a session with their processing status.
    Requirements: 1.6 - progress tracking for background processing
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    documents = session.get("documents", [])
    
    # Add title field to documents for frontend display
    for doc in documents:
        if "title" not in doc and "original_filename" in doc:
            doc["title"] = doc["original_filename"]
    
    # Calculate overall progress
    total_docs = len(documents)
    if total_docs == 0:
        overall_progress = 0.0
    else:
        completed_docs = sum(1 for doc in documents if doc.get("processing_status") == "completed")
        processing_docs = sum(1 for doc in documents if doc.get("processing_status") == "processing")
        # Count processing docs as 50% complete for progress calculation
        overall_progress = (completed_docs + (processing_docs * 0.5)) / total_docs * 100
    
    return {
        "session_id": session_id,
        "documents": documents,
        "total_documents": total_docs,
        "overall_progress": round(overall_progress, 1),
        "processing_status": session.get("processing_status", "idle")
    }

@app.get("/session/{session_id}/documents/{document_id}")
async def get_document_info(session_id: str, document_id: str):
    """
    Get detailed information about a specific document.
    Requirements: 1.6 - progress tracking for individual documents
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    documents = session.get("documents", [])
    document = next((doc for doc in documents if doc.get("document_id") == document_id), None)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found in session")
    
    # Add title field for frontend display
    if "title" not in document and "original_filename" in document:
        document["title"] = document["original_filename"]
    
    # Add file existence check
    file_exists = os.path.exists(document.get("file_path", ""))
    
    # Calculate processing time if available
    processing_time = None
    if document.get("processing_start_time") and document.get("processing_end_time"):
        start_time = datetime.fromisoformat(document["processing_start_time"]) if isinstance(document["processing_start_time"], str) else document["processing_start_time"]
        end_time = datetime.fromisoformat(document["processing_end_time"]) if isinstance(document["processing_end_time"], str) else document["processing_end_time"]
        processing_time = (end_time - start_time).total_seconds()
    
    return {
        "document_id": document_id,
        "document_info": document,
        "file_exists": file_exists,
        "session_id": session_id,
        "processing_time_seconds": processing_time,
        "sections_count": len(document.get("sections", [])),
        "text_preview": document.get("sections", [{}])[0].get("content", "")[:200] + "..." if document.get("sections") else None
    }

@app.get("/session/{session_id}/documents/{document_id}/sections")
async def get_document_sections(session_id: str, document_id: str):
    """
    Get all sections of a processed document.
    Requirements: 1.4 - section identification and content chunking
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    documents = session.get("documents", [])
    document = next((doc for doc in documents if doc.get("document_id") == document_id), None)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found in session")
    
    if document.get("processing_status") != "completed":
        raise HTTPException(status_code=400, detail="Document processing not completed")
    
    sections = document.get("sections", [])
    
    return {
        "document_id": document_id,
        "total_sections": len(sections),
        "sections": sections,
        "processing_method": document.get("processing_method"),
        "total_pages": document.get("total_pages"),
        "extracted_text_length": document.get("extracted_text_length")
    }

@app.get("/documents/{document_id}/content")
async def get_document_content(document_id: str, session_id: str):
    """
    Get full text content of a processed document for AI insights.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    documents = session.get("documents", [])
    document = next((doc for doc in documents if doc.get("document_id") == document_id), None)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found in session")
    
    if document.get("processing_status") != "completed":
        raise HTTPException(status_code=400, detail="Document processing not completed")
    
    # Combine all section content
    sections = document.get("sections", [])
    full_content = ""
    
    for section in sections:
        content = section.get("content", "")
        if content.strip():
            full_content += content + "\n\n"
    
    return {
        "document_id": document_id,
        "content": full_content.strip(),
        "content_length": len(full_content),
        "sections_count": len(sections),
        "title": document.get("title", ""),
        "total_pages": document.get("total_pages", 0)
    }

class TextSelectionRequest(BaseModel):
    """Request model for text selection updates."""
    selected_text: str
    selection_length: int
    coordinates: Optional[dict] = None
    timestamp: Optional[datetime] = None

class TextSelectionResponse(BaseModel):
    """Response model for text selection operations."""
    success: bool
    message: str
    selection_id: Optional[str] = None
    timestamp: datetime

@app.post("/session/{session_id}/text-selection", response_model=TextSelectionResponse)
async def update_text_selection(
    session_id: str,
    selection_data: TextSelectionRequest
):
    """
    Update text selection state for a session.
    
    Requirements:
    - 3.2: Capture text selection and provide visual feedback
    - 3.7: Clear visual indication of current selection mode
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Generate selection ID for tracking
    selection_id = str(uuid.uuid4())
    
    # Store selection in session
    if "text_selections" not in session:
        session["text_selections"] = []
    
    selection_record = {
        "selection_id": selection_id,
        "text": selection_data.selected_text,
        "length": selection_data.selection_length,
        "coordinates": selection_data.coordinates,
        "timestamp": selection_data.timestamp or datetime.now(),
        "session_id": session_id
    }
    
    session["text_selections"].append(selection_record)
    session["current_selection"] = selection_record
    
    logger.info(f"Text selection updated for session {session_id}: {selection_data.selection_length} characters")
    
    return TextSelectionResponse(
        success=True,
        message=f"Text selection captured ({selection_data.selection_length} characters)",
        selection_id=selection_id,
        timestamp=datetime.now()
    )

@app.delete("/session/{session_id}/text-selection")
async def clear_text_selection(session_id: str):
    """
    Clear current text selection for a session.
    
    Requirements:
    - 3.7: Clear visual indication of current selection mode
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Clear current selection
    session["current_selection"] = None
    
    logger.info(f"Text selection cleared for session {session_id}")
    
    return TextSelectionResponse(
        success=True,
        message="Text selection cleared",
        selection_id=None,
        timestamp=datetime.now()
    )

@app.get("/session/{session_id}/text-selection")
async def get_current_text_selection(session_id: str):
    """
    Get current text selection state for a session.
    
    Requirements:
    - 3.7: Clear visual indication of current selection mode
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    current_selection = session.get("current_selection")
    
    return {
        "session_id": session_id,
        "has_selection": current_selection is not None,
        "current_selection": current_selection,
        "selection_history": session.get("text_selections", [])[-5:]  # Last 5 selections
    }

@app.get("/session/{session_id}/documents/{document_id}/pdf")
async def serve_pdf_file(session_id: str, document_id: str):
    """
    Serve PDF file for viewing in the frontend.
    Requirements: 3.1 - PDF viewing capabilities in central content area
    """
    from fastapi.responses import FileResponse
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    documents = session.get("documents", [])
    document = next((doc for doc in documents if doc.get("document_id") == document_id), None)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found in session")
    
    file_path = document.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    # Return the PDF file with CORS headers
    response = FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document.get("original_filename", "document.pdf")
    )
    
    # Add CORS headers for PDF viewing
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    return response

@app.post("/session/{session_id}/documents/{document_id}/reprocess")
async def reprocess_document(session_id: str, document_id: str):
    """
    Reprocess a document (useful if processing failed or needs to be redone).
    Requirements: 1.5 - processing status tracking
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    documents = session.get("documents", [])
    document = next((doc for doc in documents if doc.get("document_id") == document_id), None)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found in session")
    
    # Reset document processing status
    document["processing_status"] = "pending"
    document["processing_progress"] = 0.0
    document["processing_start_time"] = None
    document["processing_end_time"] = None
    document["error_message"] = None
    document["sections"] = []
    
    # Start processing
    start_background_processing(session_id)
    
    return {
        "message": "Document reprocessing started",
        "document_id": document_id,
        "status": "pending"
    }

@app.get("/processing/stats")
async def get_processing_stats():
    """
    Get processing performance statistics.
    Requirements: 1.4 - process documents at approximately 1 second per PDF
    """
    stats = document_processor.get_processing_stats()
    
    return {
        "processing_stats": stats,
        "performance_metrics": {
            "target_time_per_pdf_ms": 1000,
            "actual_average_time_ms": stats["average_time_ms"],
            "performance_ratio": stats["performance_ratio"],
            "meets_target": stats["average_time_ms"] <= 1200,  # Allow 20% tolerance
            "total_processed": stats["total_processed"],
            "success_rate": stats["success_rate"]
        },
        "system_status": {
            "active_sessions": len(sessions),
            "active_workers": stats["active_workers"]
        }
    }

@app.get("/session/{session_id}/processing/progress")
async def get_processing_progress(session_id: str):
    """
    Get detailed processing progress for all documents in a session.
    Requirements: 1.5 - show progress indicators for background processing
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    documents = session.get("documents", [])
    
    # Calculate detailed progress metrics
    progress_details = []
    total_progress = 0.0
    
    for doc in documents:
        doc_progress = {
            "document_id": doc["document_id"],
            "filename": doc["original_filename"],
            "status": doc.get("processing_status", "pending"),
            "progress": doc.get("processing_progress", 0.0),
            "processing_time_ms": None,
            "quality_score": doc.get("quality_score"),
            "processing_method": doc.get("processing_method"),
            "error_message": doc.get("error_message")
        }
        
        # Calculate processing time if available
        if doc.get("processing_start_time") and doc.get("processing_end_time"):
            start_time = doc["processing_start_time"]
            end_time = doc["processing_end_time"]
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            doc_progress["processing_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        progress_details.append(doc_progress)
        total_progress += doc_progress["progress"]
    
    overall_progress = (total_progress / len(documents)) if documents else 0.0
    
    # Count status distribution
    status_counts = {}
    for doc in documents:
        status = doc.get("processing_status", "pending")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "session_id": session_id,
        "overall_progress": round(overall_progress * 100, 1),
        "total_documents": len(documents),
        "status_distribution": status_counts,
        "documents": progress_details,
        "processing_complete": all(
            doc.get("processing_status") in ["completed", "failed"] 
            for doc in documents
        ),
        "estimated_completion_time": None  # Could add ETA calculation
    }

@app.get("/processing/performance")
async def get_processing_performance():
    """
    Get overall processing statistics across all sessions.
    Requirements: 1.5 - processing status tracking
    """
    total_documents = 0
    completed_documents = 0
    processing_documents = 0
    failed_documents = 0
    total_processing_time = 0.0
    
    for session_data in sessions.values():
        for doc in session_data.get("documents", []):
            total_documents += 1
            status = doc.get("processing_status", "pending")
            
            if status == "completed":
                completed_documents += 1
                # Calculate processing time if available
                if doc.get("processing_start_time") and doc.get("processing_end_time"):
                    try:
                        start_time = datetime.fromisoformat(doc["processing_start_time"]) if isinstance(doc["processing_start_time"], str) else doc["processing_start_time"]
                        end_time = datetime.fromisoformat(doc["processing_end_time"]) if isinstance(doc["processing_end_time"], str) else doc["processing_end_time"]
                        total_processing_time += (end_time - start_time).total_seconds()
                    except:
                        pass
            elif status == "processing":
                processing_documents += 1
            elif status == "failed":
                failed_documents += 1
    
    avg_processing_time = total_processing_time / completed_documents if completed_documents > 0 else 0
    
    return {
        "total_documents": total_documents,
        "completed_documents": completed_documents,
        "processing_documents": processing_documents,
        "failed_documents": failed_documents,
        "pending_documents": total_documents - completed_documents - processing_documents - failed_documents,
        "completion_rate": (completed_documents / total_documents * 100) if total_documents > 0 else 0,
        "average_processing_time_seconds": round(avg_processing_time, 2),
        "total_sessions": len(sessions)
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "PDF Analysis Workbench API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "detailed_health": "/health/detailed",
            "create_session": "/session/create",
            "session_info": "/session/{session_id}",
            "delete_session": "/session/{session_id}",
            "upload_bulk": "/upload/bulk",
            "session_documents": "/session/{session_id}/documents",
            "document_info": "/session/{session_id}/documents/{document_id}",
            "document_sections": "/session/{session_id}/documents/{document_id}/sections",
            "reprocess_document": "/session/{session_id}/documents/{document_id}/reprocess",
            "processing_stats": "/processing/stats"
        }
    }

class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str
    top_k: int = 5
    document_ids: Optional[List[str]] = None

class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    embeddings_available: bool

@app.post("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    session_id: str,
    search_request: SemanticSearchRequest
):
    """
    Perform semantic search across processed documents in a session.
    
    Requirements:
    - 3.1.1: Semantic search across processed documents within 1 second
    - 3.1.2: Search within available processed documents
    - 6.1: Fast similarity search using FAISS
    """
    # Validate session exists
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Check if embedding service is initialized
    if not embedding_service.is_initialized:
        try:
            await embedding_service.initialize()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize embedding service: {str(e)}")
    
    # Get processed documents in session
    documents = session.get("documents", [])
    processed_documents = [
        doc for doc in documents 
        if doc.get("processing_status") == "completed"
    ]
    
    if not processed_documents:
        return SemanticSearchResponse(
            query=search_request.query,
            results=[],
            total_results=0,
            search_time_ms=0.0,
            embeddings_available=False
        )
    
    # Filter by document IDs if specified
    document_ids = search_request.document_ids
    if document_ids:
        processed_document_ids = [doc["document_id"] for doc in processed_documents]
        document_ids = [doc_id for doc_id in document_ids if doc_id in processed_document_ids]
    else:
        document_ids = [doc["document_id"] for doc in processed_documents]
    
    if not document_ids:
        return SemanticSearchResponse(
            query=search_request.query,
            results=[],
            total_results=0,
            search_time_ms=0.0,
            embeddings_available=False
        )
    
    try:
        start_time = time.time()
        
        # Print API request info to console
        print(f"\n🌐 API REQUEST: Basic Semantic Search")
        print(f"   Session: {session_id}")
        print(f"   Query: '{search_request.query}'")
        print(f"   Top K: {search_request.top_k}")
        print(f"   Documents: {len(document_ids) if document_ids else 'all'}")
        
        # Perform semantic search
        results = await embedding_service.semantic_search(
            query=search_request.query,
            top_k=search_request.top_k,
            document_ids=document_ids
        )
        
        # Print basic results summary
        print(f"   ✅ Found {len(results)} results in {(time.time() - start_time) * 1000:.1f}ms")
        
        search_time_ms = (time.time() - start_time) * 1000
        
        return SemanticSearchResponse(
            query=search_request.query,
            results=results,
            total_results=len(results),
            search_time_ms=search_time_ms,
            embeddings_available=True
        )
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")

@app.get("/search/stats")
async def get_search_stats():
    """
    Get embedding service statistics.
    Requirements: 6.1 - performance monitoring for search capabilities
    """
    return {
        "embedding_service": embedding_service.get_stats(),
        "document_processor": document_processor.get_processing_stats(),
        "search_engine": search_engine.get_stats()
    }

@app.post("/session/{session_id}/summary", response_model=SummaryResponse)
async def generate_summary(session_id: str, request: SummaryRequest):
    """
    Generate a summary of content using LLM service.
    Supports both selection and document mode summarization.
    Requirements: 2.2.3, 2.2.4, 2.2.5, 2.2.6, 2.2.7
    """
    # Validate session
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Get LLM service
    llm = get_llm_service()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM service not available")
    
    # Validate mode
    if request.mode not in ["selection", "document"]:
        raise HTTPException(status_code=400, detail="Mode must be 'selection' or 'document'")
    
    start_time = time.time()
    content = request.content
    
    try:
        # For document mode, get the full document content automatically
        if request.mode == "document" and request.document_id:
            logger.info(f"Document mode: retrieving full content for document {request.document_id}")
            
            # Find the document in the session
            documents = session.get("documents", [])
            document = next((doc for doc in documents if doc.get("document_id") == request.document_id), None)
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found in session")
            
            # Wait up to 60s for processing to complete instead of rejecting immediately
            if document.get("processing_status") != "completed":
                max_wait = 60
                waited = 0
                while document.get("processing_status") not in ("completed", "failed") and waited < max_wait:
                    await asyncio.sleep(2)
                    waited += 2
                    # Re-fetch from session in case it was updated
                    documents = session.get("documents", [])
                    document = next((doc for doc in documents if doc.get("document_id") == request.document_id), None)
                    if not document:
                        raise HTTPException(status_code=404, detail="Document not found in session")
                
                if document.get("processing_status") == "failed":
                    raise HTTPException(status_code=400, detail="Document processing failed")
                if document.get("processing_status") != "completed":
                    raise HTTPException(status_code=400, detail="Document processing timed out")
            
            # Get all section content
            sections = document.get("sections", [])
            full_content = ""
            
            for section in sections:
                section_content = section.get("content", "")
                if section_content.strip():
                    full_content += section_content + "\n\n"
            
            if not full_content.strip():
                raise HTTPException(status_code=400, detail="No content available in document")
            
            content = full_content.strip()
            logger.info(f"Retrieved {len(content)} characters from document {request.document_id}")
        
        # Validate content
        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Generate summary
        summary = llm.generate_summary(content, request.mode)
        
        if not summary:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        processing_time = time.time() - start_time
        
        logger.info(f"Generated {request.mode} summary in {processing_time:.2f}s for session {session_id}")
        
        return SummaryResponse(
            summary=summary,
            mode=request.mode,
            content_length=len(content),
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

class EnhancedSearchRequest(BaseModel):
    """Request model for enhanced semantic search with multi-tier strategy."""
    query: str
    document_ids: Optional[List[str]] = None
    selected_text: Optional[str] = None
    active_document_id: Optional[str] = None
    max_results: int = 5
    confidence_threshold: float = 0.75

class EnhancedSearchResponse(BaseModel):
    """Response model for enhanced semantic search."""
    query: str
    results: List[dict]  # Will contain EnhancedSearchResult data
    total_results: int
    search_time_ms: float
    confidence_filtered_count: int
    processing_status: Dict[str, bool]
    search_strategy_used: str

@app.post("/search/enhanced", response_model=EnhancedSearchResponse)
async def enhanced_semantic_search(
    session_id: str,
    search_request: EnhancedSearchRequest
):
    """
    Perform enhanced semantic search with multi-tier strategy and confidence filtering.
    
    Requirements:
    - 3.1.3: Build semantic search across processed documents
    - 3.1.6: Implement multi-tier search strategy (fast → precision)
    - 3.1.7: Add confidence-based result filtering (>0.75 threshold)
    - 3.1.6: Create search result ranking and snippet extraction
    """
    # Validate session exists
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Check if embedding service is initialized
    if not embedding_service.is_initialized:
        try:
            await embedding_service.initialize()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize embedding service: {str(e)}")
    
    # Get document processing status
    documents = session.get("documents", [])
    processing_status = {}
    available_document_ids = []
    
    for doc in documents:
        doc_id = doc["document_id"]
        is_processed = doc.get("processing_status") == "completed"
        processing_status[doc_id] = is_processed
        if is_processed:
            available_document_ids.append(doc_id)
    
    # Filter document IDs if specified
    if search_request.document_ids:
        available_document_ids = [
            doc_id for doc_id in search_request.document_ids 
            if doc_id in available_document_ids
        ]
    
    if not available_document_ids:
        return EnhancedSearchResponse(
            query=search_request.query,
            results=[],
            total_results=0,
            search_time_ms=0.0,
            confidence_filtered_count=0,
            processing_status=processing_status,
            search_strategy_used="none"
        )
    
    try:
        start_time = time.time()
        
        # Create search context
        context = SearchContext(
            query=search_request.query,
            document_ids=available_document_ids,
            selected_text=search_request.selected_text,
            active_document_id=search_request.active_document_id,
            processing_status=processing_status
        )
        
        # Update search engine strategy if needed
        if search_request.confidence_threshold != search_engine.strategy.confidence_threshold:
            search_engine.strategy.confidence_threshold = search_request.confidence_threshold
        if search_request.max_results != search_engine.strategy.max_results:
            search_engine.strategy.max_results = search_request.max_results
        
        # Print API request info to console
        print(f"\n🌐 API REQUEST: Enhanced Search")
        print(f"   Session: {session_id}")
        print(f"   Query: '{search_request.query}'")
        print(f"   Documents: {len(available_document_ids)} available")
        print(f"   Confidence Threshold: {search_request.confidence_threshold}")
        
        # Perform enhanced search
        enhanced_results = await search_engine.search(context)
        
        search_time_ms = (time.time() - start_time) * 1000
        
        # Convert results to dict format for JSON response
        results_data = []
        for result in enhanced_results:
            result_dict = {
                "section_id": result.section_id,
                "document_id": result.document_id,
                "text": result.text,
                "similarity_score": result.similarity_score,
                "confidence_score": result.confidence_score,
                "page_number": result.page_number,
                "section_type": result.section_type,
                "snippet": result.snippet,
                "search_tier": result.search_tier.value,
                "related_sections": result.related_sections,
                "processing_time_ms": result.processing_time_ms
            }
            results_data.append(result_dict)
        
        # Determine search strategy used
        search_strategy = "fast_only"
        if any(r["search_tier"] == "precision" for r in results_data):
            search_strategy = "multi_tier"
        
        # Get confidence filtering stats
        stats = search_engine.get_stats()
        confidence_filtered_count = stats.get("confidence_filtered_results", 0)
        
        return EnhancedSearchResponse(
            query=search_request.query,
            results=results_data,
            total_results=len(results_data),
            search_time_ms=search_time_ms,
            confidence_filtered_count=confidence_filtered_count,
            processing_status=processing_status,
            search_strategy_used=search_strategy
        )
        
    except Exception as e:
        logger.error(f"Enhanced semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced semantic search failed: {str(e)}")

@app.post("/search/related-content")
async def search_related_content(
    session_id: str,
    selected_text: str,
    document_ids: Optional[List[str]] = None
):
    """
    Search for content related to selected text across processed documents.
    
    Requirements:
    - 3.1: Find related content across all uploaded documents when text is selected
    - 3.1.3: Semantic search across processed documents within 1 second
    - 3.1.7: Maintain minimum 85% semantic relevance
    """
    # Validate session exists
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Check if embedding service is initialized
    if not embedding_service.is_initialized:
        try:
            await embedding_service.initialize()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize embedding service: {str(e)}")
    
    # Get document processing status
    documents = session.get("documents", [])
    processing_status = {}
    available_document_ids = []
    
    for doc in documents:
        doc_id = doc["document_id"]
        is_processed = doc.get("processing_status") == "completed"
        processing_status[doc_id] = is_processed
        if is_processed:
            available_document_ids.append(doc_id)
    
    # Filter document IDs if specified
    if document_ids:
        available_document_ids = [
            doc_id for doc_id in document_ids 
            if doc_id in available_document_ids
        ]
    
    # Determine whether any documents are still being processed
    any_still_processing = any(
        doc.get("processing_status") in ("pending", "processing", "priority")
        for doc in documents
    )

    if not available_document_ids:
        return {
            "selected_text": selected_text,
            "related_sections": [],
            "total_results": 0,
            "search_time_ms": 0.0,
            "processing_status": processing_status,
            "documents_still_processing": any_still_processing,
            "message": (
                "Documents are still processing. Search will be available shortly."
                if any_still_processing
                else "No processed documents available for search"
            )
        }
    
    try:
        start_time = time.time()
        
        # Print API request info to console
        print(f"\n🌐 API REQUEST: Related Content Search")
        print(f"   Session: {session_id}")
        print(f"   Selected Text: '{selected_text[:100]}{'...' if len(selected_text) > 100 else ''}'")
        print(f"   Documents: {len(available_document_ids)} available")
        
        # Use search engine for related content search
        related_results = await search_engine.search_related_content(
            selected_text=selected_text,
            document_ids=available_document_ids,
            processing_status=processing_status
        )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        # Convert results to response format
        related_sections = []
        for result in related_results:
            section_data = {
                "section_id": result.section_id,
                "document_id": result.document_id,
                "snippet": result.snippet,
                "similarity_score": result.similarity_score,
                "confidence_score": result.confidence_score,
                "page_number": result.page_number,
                "section_type": result.section_type,
                "related_sections": result.related_sections
            }
            related_sections.append(section_data)
        
        # Add processing status note if some documents are still processing
        processing_note = ""
        still_processing = [doc_id for doc_id, is_processed in processing_status.items() if not is_processed]
        if still_processing:
            processing_note = f"Note: {len(still_processing)} documents are still processing and not included in search results."
        
        return {
            "selected_text": selected_text,
            "related_sections": related_sections,
            "total_results": len(related_sections),
            "search_time_ms": search_time_ms,
            "processing_status": processing_status,
            "processing_note": processing_note,
            "meets_time_target": search_time_ms <= 1000,  # 1 second target
            "confidence_threshold": search_engine.strategy.confidence_threshold
        }
        
    except Exception as e:
        logger.error(f"Related content search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Related content search failed: {str(e)}")

@app.get("/search/cache/stats")
async def get_search_cache_stats():
    """
    Get search cache statistics and performance metrics.
    
    Requirements:
    - 6.6: Response caching for performance optimization
    - 6.2: Cache hit rate monitoring
    """
    stats = search_engine.get_stats()
    
    return {
        "cache_stats": {
            "cache_size": stats["cache_size"],
            "cache_hit_rate": stats["cache_hit_rate"],
            "total_searches": stats["total_searches"],
            "cache_hits": stats["cache_hits"]
        },
        "performance_stats": {
            "average_search_time_ms": stats["average_search_time_ms"],
            "fast_tier_searches": stats["fast_tier_searches"],
            "precision_tier_searches": stats["precision_tier_searches"],
            "precision_search_rate": stats["precision_search_rate"]
        },
        "quality_stats": {
            "confidence_threshold": stats["confidence_threshold"],
            "confidence_filtered_results": stats["confidence_filtered_results"]
        }
    }

@app.delete("/search/cache")
async def clear_search_cache():
    """
    Clear the search cache (useful for testing or memory management).
    
    Requirements:
    - 6.6: Cache management for performance optimization
    """
    search_engine.clear_cache()
    
    return {
        "message": "Search cache cleared successfully",
        "timestamp": datetime.now()
    }

@app.get("/static/{file_path:path}")
async def serve_static_file(file_path: str):
    """
    Serve static files (sample PDFs) for demo purposes.
    Requirements: 3.1 - PDF viewing capabilities for demo content
    """
    from fastapi.responses import FileResponse
    
    # Security check - only allow files from sample_pdfs directory
    if not file_path.startswith("sample_pdfs/"):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Construct full file path
    full_path = os.path.join(os.getcwd(), file_path)
    
    # Check if file exists
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if it's a PDF file
    if not file_path.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Return the PDF file with CORS headers
    response = FileResponse(
        path=full_path,
        media_type="application/pdf",
        filename=os.path.basename(file_path)
    )
    
    # Add CORS headers for PDF viewing
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    return response

@app.post("/insights/generate")
async def generate_insights(request: dict):
    """Generate comprehensive insights for document content"""
    try:
        llm_service = get_llm_service()
        if not llm_service:
            return {"error": "LLM service not available"}
            
        content = request.get('content', '')
        if not content:
            return {"error": "Content is required"}
        
        # Run blocking LLM call in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        insights = await loop.run_in_executor(None, llm_service.generate_insights, content)
        if not insights:
            return {"error": "Failed to generate insights"}
        
        return {
            "success": True,
            "insights": {
                "takeaways": insights.takeaways,
                "contradictions": insights.contradictions,
                "examples": insights.examples,
                "did_you_know": insights.did_you_know,
                "processing_time": insights.processing_time
            }
        }
    except Exception as e:
        logger.error(f"Error in generate_insights endpoint: {e}")
        return {"error": f"Failed to generate insights: {str(e)}"}

@app.post("/insights/takeaways")
async def generate_takeaways_only(request: dict):
    """Generate only takeaways for faster response"""
    try:
        llm_service = get_llm_service()
        if not llm_service:
            return {"error": "LLM service not available"}
            
        content = request.get('content', '')
        if not content:
            return {"error": "Content is required"}
        
        takeaways = llm_service.generate_takeaways(content)
        return {"success": True, "takeaways": takeaways}
    except Exception as e:
        return {"error": f"Failed to generate takeaways: {str(e)}"}

@app.post("/insights/contradictions")
async def generate_contradictions_only(request: dict):
    """Generate only contradictions for faster response"""
    try:
        llm_service = get_llm_service()
        if not llm_service:
            return {"error": "LLM service not available"}
            
        content = request.get('content', '')
        if not content:
            return {"error": "Content is required"}
        
        contradictions = llm_service.generate_contradictions(content)
        return {"success": True, "contradictions": contradictions}
    except Exception as e:
        return {"error": f"Failed to generate contradictions: {str(e)}"}

@app.post("/insights/examples")
async def generate_examples_only(request: dict):
    """Generate only examples for faster response"""
    try:
        llm_service = get_llm_service()
        if not llm_service:
            return {"error": "LLM service not available"}
            
        content = request.get('content', '')
        if not content:
            return {"error": "Content is required"}
        
        examples = llm_service.generate_examples(content)
        return {"success": True, "examples": examples}
    except Exception as e:
        return {"error": f"Failed to generate examples: {str(e)}"}

@app.post("/insights/facts")
async def generate_facts_only(request: dict):
    """Generate only 'did you know' facts for faster response"""
    try:
        llm_service = get_llm_service()
        if not llm_service:
            return {"error": "LLM service not available"}
            
        content = request.get('content', '')
        if not content:
            return {"error": "Content is required"}
        
        facts = llm_service.generate_facts(content)
        return {"success": True, "facts": facts}
    except Exception as e:
        return {"error": f"Failed to generate facts: {str(e)}"}

@app.get("/insights/cache/stats")
async def get_cache_stats():
    """Get LLM cache statistics"""
    llm_service = get_llm_service()
    if not llm_service:
        return {"error": "LLM service not available"}
    return llm_service.get_cache_stats()

@app.post("/insights/cache/clear")
async def clear_cache():
    """Clear LLM cache"""
    llm_service = get_llm_service()
    if not llm_service:
        return {"error": "LLM service not available"}
    llm_service.clear_cache()
    return {"success": True, "message": "Cache cleared"}

# ===== PODCAST GENERATION ENDPOINTS =====

@app.post("/session/{session_id}/podcast/generate", response_model=PodcastResponse)
async def generate_podcast(session_id: str, request: PodcastRequest, background_tasks: BackgroundTasks):
    """
    Generate podcast-style audio from document content and insights.
    """
    start_time = time.time()
    
    # Validate session
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = sessions[session_id]
    
    try:
        # Send initial WebSocket update
        await send_processing_update(session_id, "started", "Generating podcast audio...")
        
        # Gather content - be more flexible about content sources
        content = ""
        
        # Priority 1: Direct content provided in request
        if request.content:
            content = request.content
            logger.info("Using direct content from request")
        
        # Priority 2: Try to get content from specific document (but don't fail if not found)
        elif request.document_id:
            documents = session_data.get("documents", {})
            
            # Handle both dict and list formats for documents
            if isinstance(documents, dict) and request.document_id in documents:
                doc_data = documents[request.document_id]
                if isinstance(doc_data, dict):
                    sections = doc_data.get("sections", [])
                    content_parts = []
                    for section in sections:
                        if isinstance(section, dict):
                            section_content = section.get("content", "")
                            if isinstance(section_content, str) and section_content.strip():
                                content_parts.append(section_content)
                        elif isinstance(section, str):
                            content_parts.append(section)
                    content = " ".join(content_parts)
                    logger.info(f"Using content from document {request.document_id}")
            elif isinstance(documents, list):
                # If documents is a list, search by ID
                found_doc = None
                for doc_data in documents:
                    if isinstance(doc_data, dict) and doc_data.get("id") == request.document_id:
                        found_doc = doc_data
                        break
                
                if found_doc:
                    sections = found_doc.get("sections", [])
                    content_parts = []
                    for section in sections:
                        if isinstance(section, dict):
                            section_content = section.get("content", "")
                            if isinstance(section_content, str) and section_content.strip():
                                content_parts.append(section_content)
                        elif isinstance(section, str):
                            content_parts.append(section)
                    content = " ".join(content_parts)
                    logger.info(f"Using content from document {request.document_id}")
                else:
                    logger.warning(f"Document {request.document_id} not found, falling back to all available content")
            else:
                logger.warning(f"Document {request.document_id} not found, falling back to all available content")
                # Fall through to Priority 3
        
        # Priority 3: Use all available session content
        if not content.strip():
            documents = session_data.get("documents", {})
            all_sections = []
            
            # Handle both dict and list formats for documents
            if isinstance(documents, dict):
                for doc_id, doc_data in documents.items():
                    if isinstance(doc_data, dict):
                        sections = doc_data.get("sections", [])
                        if isinstance(sections, list):
                            all_sections.extend(sections)
            elif isinstance(documents, list):
                # If documents is a list, iterate directly
                for doc_data in documents:
                    if isinstance(doc_data, dict):
                        sections = doc_data.get("sections", [])
                        if isinstance(sections, list):
                            all_sections.extend(sections)
            
            if all_sections:
                # Extract content from sections with better error handling
                content_parts = []
                for section in all_sections:
                    if isinstance(section, dict):
                        section_content = section.get("content", "")
                        if isinstance(section_content, str) and section_content.strip():
                            content_parts.append(section_content)
                    elif isinstance(section, str):
                        # In case sections are stored as strings directly
                        content_parts.append(section)
                
                content = " ".join(content_parts)
                document_count = len(documents) if isinstance(documents, dict) else len(documents) if isinstance(documents, list) else 0
                logger.info(f"Using content from {document_count} documents in session")
            
        # Priority 4: Try text selection
        if not content.strip() and session_data.get("text_selection"):
            content = session_data["text_selection"].get("text", "")
            logger.info("Using text selection as content")
        
        # Priority 5: Provide demo content
        if not content.strip():
            content = """
            Welcome to this AI-generated podcast demonstration. This feature converts document content 
            into natural-sounding audio conversations between AI hosts. Upload PDF documents to generate 
            podcasts from your actual content, or this demonstration will show you how the feature works.
            The system can create engaging discussions about complex topics, making information more accessible.
            """
            logger.info("Using demo content for podcast generation")
        
        # Include text selection if specifically requested
        if request.include_selection and session_data.get("text_selection"):
            selection_text = session_data["text_selection"].get("text", "")
            if selection_text and selection_text not in content:
                content = f"Selected text: {selection_text}. Full context: {content}"
        
        # Generate insights if requested
        insights = None
        if request.use_insights:
            await send_processing_update(session_id, "processing", "Generating insights for podcast...")
            
            llm_service = get_llm_service()
            if llm_service:
                try:
                    # Generate comprehensive insights
                    insight_content = content[:4000]  # Limit content for LLM processing
                    
                    takeaways = llm_service.generate_takeaways(insight_content)
                    contradictions = llm_service.generate_contradictions(insight_content)
                    examples = llm_service.generate_examples(insight_content)
                    
                    insights = {
                        "takeaways": takeaways,
                        "contradictions": contradictions,
                        "examples": examples
                    }
                    
                    logger.info(f"Generated insights for podcast: {len(takeaways)} takeaways, {len(contradictions)} contradictions, {len(examples)} examples")
                except Exception as e:
                    logger.warning(f"Failed to generate insights for podcast: {e}")
                    insights = None
        
        # Generate audio
        await send_processing_update(session_id, "processing", "Creating audio content...")
        
        audio_path = await audio_service.generate_podcast(
            session_id=session_id,
            content=content,
            insights=insights,
            use_dual_speaker=request.use_dual_speaker
        )
        
        if not audio_path:
            raise HTTPException(status_code=500, detail="Failed to generate podcast audio")
        
        # Generate audio URL
        audio_url = audio_service.get_audio_url(audio_path)
        
        # Determine speakers used
        speakers_used = []
        if request.use_dual_speaker:
            speakers_used = ["Host", "Guest"]
        else:
            speakers_used = ["Narrator"]
        
        processing_time = time.time() - start_time
        
        # Send completion update
        await send_processing_update(session_id, "completed", f"Podcast generated successfully in {processing_time:.1f} seconds")
        
        # Schedule cleanup
        background_tasks.add_task(audio_service.cleanup_old_audio_files)
        
        response = PodcastResponse(
            audio_url=audio_url,
            duration_estimate="2-5 minutes",
            format="WAV",
            speakers_used=speakers_used,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
        logger.info(f"Podcast generated successfully for session {session_id}: {audio_url}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Podcast generation error for session {session_id}: {e}")
        await send_processing_update(session_id, "error", f"Failed to generate podcast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Podcast generation failed: {str(e)}")

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio files."""
    try:
        audio_path = audio_service.audio_dir / filename
        
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        suffix = Path(filename).suffix.lower()
        media_type = "audio/wav" if suffix == ".wav" else "audio/mpeg"
        return FileResponse(
            path=str(audio_path),
            media_type=media_type,
            filename=filename,
            headers={"Cache-Control": "public, max-age=3600"}
        )
        
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve audio file")

@app.get("/session/{session_id}/podcast/status")
async def get_podcast_status(session_id: str):
    """Get podcast generation status and available podcasts."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # This could be expanded to track podcast generation status
    # For now, return basic status
    return {
        "session_id": session_id,
        "audio_service_available": audio_service._validate_config(),
        "supported_formats": ["WAV"],
        "max_duration": "5 minutes"
    }

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")

    async def send_personal_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
                logger.debug(f"WebSocket message sent to {session_id}: {message}")
            except Exception as e:
                logger.error(f"Failed to send WebSocket message to {session_id}: {e}")
                self.disconnect(session_id)
        else:
            logger.warning(f"No active WebSocket connection for session {session_id}")

manager = ConnectionManager()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates"""
    
    # Validate session exists
    if session_id not in sessions:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    try:
        await manager.connect(websocket, session_id)
        
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)
        
        # Keep connection alive
        while True:
            try:
                # Wait for ping/keepalive messages
                data = await websocket.receive_text()
                # Echo back for ping/pong
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, session_id)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for session {session_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error for session {session_id}: {e}")
    finally:
        manager.disconnect(session_id)

# Helper function to send processing updates via WebSocket
async def send_processing_update(session_id: str, status: str, message: str = None, progress: int = None):
    """Send processing updates to connected WebSocket clients"""
    update_data = {
        "type": "processing_update",
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        update_data["message"] = message
    if progress is not None:
        update_data["progress"] = progress
    
    logger.info(f"Sending WebSocket update to session {session_id}: {update_data}")
    await manager.send_personal_message(update_data, session_id)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("FASTAPI_BACKEND_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)