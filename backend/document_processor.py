"""
Enhanced document processing service for PDF analysis workbench.
Implements background processing pipeline with ~1 second per PDF target.

Requirements:
- 1.3: Immediately show first PDF while processing others in background
- 1.4: Process documents at approximately 1 second per PDF
- 1.5: Show progress indicators for background processing
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
import logging
from concurrent.futures import ThreadPoolExecutor
import re

import fitz  # PyMuPDF
from pydantic import BaseModel

# Import embedding service for background embedding generation
from .embedding_service import embedding_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingProgress(BaseModel):
    """Progress tracking for document processing."""
    document_id: str
    stage: str  # starting, extracting, chunking, completed, failed
    progress: float  # 0.0 to 1.0
    message: str
    timestamp: datetime
    processing_time_ms: Optional[int] = None

class DocumentSection(BaseModel):
    """Enhanced document section with improved metadata."""
    section_id: str
    title: str
    content: str
    page_number: int
    section_type: str  # header, paragraph, list, table
    confidence: float = 1.0
    word_count: int = 0
    char_count: int = 0

class ProcessedDocument(BaseModel):
    """Complete processed document with all extracted content."""
    document_id: str
    filename: str
    total_pages: int
    processing_method: str  # fitz, ocr, hybrid
    processing_time_ms: int
    extracted_text_length: int
    sections: List[DocumentSection]
    metadata: Dict
    quality_score: float = 1.0
    embeddings_generated: bool = False
    embedding_count: int = 0

class DocumentProcessor:
    """Enhanced document processor with performance optimization."""
   
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self.processing_stats = {
            "total_processed": 0,
            "average_time_ms": 0,
            "success_rate": 0.0
        }
        
    def add_progress_callback(self, document_id: str, callback: Callable):
        """Add a callback function to receive progress updates."""
        if document_id not in self.progress_callbacks:
            self.progress_callbacks[document_id] = []
        self.progress_callbacks[document_id].append(callback)
    
    def _notify_progress(self, progress: ProcessingProgress):
        """Notify all registered callbacks about progress updates."""
        callbacks = self.progress_callbacks.get(progress.document_id, [])
        for callback in callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error for {progress.document_id}: {e}")
    
    def _extract_text_optimized(self, pdf_path: str, document_id: str) -> Tuple[str, List[DocumentSection], str, float]:
        """Optimized text extraction with performance monitoring."""
        start_time = time.time()
        
        self._notify_progress(ProcessingProgress(
            document_id=document_id,
            stage="extracting",
            progress=0.1,
            message="Starting text extraction",
            timestamp=datetime.now()
        ))
        
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            sections = []
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # Update progress
                progress = 0.1 + (page_num / total_pages) * 0.6
                self._notify_progress(ProcessingProgress(
                    document_id=document_id,
                    stage="extracting",
                    progress=progress,
                    message=f"Processing page {page_num + 1}/{total_pages}",
                    timestamp=datetime.now()
                ))
                
                # Extract text blocks
                blocks = page.get_text("dict")
                page_text = ""
                
                for block_idx, block in enumerate(blocks["blocks"]):
                    if "lines" in block:  # Text block
                        block_text = ""
                        for line in block["lines"]:
                            line_text = ""
                            for span in line["spans"]:
                                line_text += span["text"]
                            block_text += line_text + "\n"
                        
                        if block_text.strip():
                            page_text += block_text
                            
                            # Determine section type
                            section_type = self._classify_text_block(block_text)
                            
                            # Create section
                            section = DocumentSection(
                                section_id=f"page_{page_num + 1}_block_{block_idx}",
                                title=self._extract_section_title(block_text),
                                content=block_text.strip(),
                                page_number=page_num + 1,
                                section_type=section_type,
                                confidence=0.9,
                                word_count=len(block_text.split()),
                                char_count=len(block_text)
                            )
                            sections.append(section)
                
                full_text += page_text
            
            doc.close()
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(full_text, sections)
            
            return full_text, sections, "fitz", quality_score
            
        except Exception as e:
            logger.error(f"Text extraction failed for {document_id}: {e}")
            raise
    
    def _classify_text_block(self, text: str) -> str:
        """Classify text block type."""
        text = text.strip()
        
        if not text:
            return "empty"
        
        # Header detection (short, often capitalized)
        if len(text) < 100 and (text.isupper() or text.istitle()) and not text.endswith('.'):
            return "header"
        
        # List detection
        if re.match(r'^[\s]*[•\-\*\d+\.]\s', text) or '\n•' in text or '\n-' in text:
            return "list"
        
        # Default to paragraph
        return "paragraph"
    
    def _extract_section_title(self, text: str) -> str:
        """Extract meaningful title from section text."""
        lines = text.strip().split('\n')
        first_line = lines[0].strip()
        
        # If first line looks like a title, use it
        if len(first_line) < 100 and (first_line.istitle() or first_line.isupper() or not first_line.endswith('.')):
            return first_line
        
        # Otherwise, create title from first few words
        words = first_line.split()[:8]
        title = ' '.join(words)
        return (title + "...") if len(first_line) > len(title) else title
    
    def _calculate_quality_score(self, text: str, sections: List[DocumentSection]) -> float:
        """Calculate extraction quality score."""
        if not text or not sections:
            return 0.0
        
        # Simple quality assessment
        text_length_score = min(len(text) / 1000, 1.0)
        section_count_score = min(len(sections) / 10, 1.0)
        
        quality_score = (text_length_score + section_count_score) / 2
        return max(0.0, min(1.0, quality_score))
    
    def _chunk_content(self, sections: List[DocumentSection], document_id: str) -> List[DocumentSection]:
        """Merge small blocks into meaningful chunks, then split oversized ones."""
        self._notify_progress(ProcessingProgress(
            document_id=document_id,
            stage="chunking",
            progress=0.8,
            message="Optimizing content chunks",
            timestamp=datetime.now()
        ))

        TARGET_CHUNK_CHARS = 800
        MAX_CHUNK_CHARS = 1200
        merged = []
        buffer = ""
        buffer_page = 1
        buffer_type = "paragraph"
        buffer_idx = 0

        for section in sections:
            content = section.content.strip()
            if not content:
                continue

            # Always keep headers as standalone anchors
            if section.section_type == "header":
                if buffer.strip():
                    merged.append(DocumentSection(
                        section_id=f"chunk_{buffer_idx}",
                        title=self._extract_section_title(buffer),
                        content=buffer.strip(),
                        page_number=buffer_page,
                        section_type=buffer_type,
                        confidence=0.9,
                        word_count=len(buffer.split()),
                        char_count=len(buffer),
                    ))
                    buffer_idx += 1
                    buffer = ""
                merged.append(section)
                continue

            # Accumulate into buffer
            if len(buffer) + len(content) <= TARGET_CHUNK_CHARS:
                buffer += " " + content if buffer else content
                buffer_page = section.page_number
                buffer_type = section.section_type
            else:
                if buffer.strip():
                    merged.append(DocumentSection(
                        section_id=f"chunk_{buffer_idx}",
                        title=self._extract_section_title(buffer),
                        content=buffer.strip(),
                        page_number=buffer_page,
                        section_type=buffer_type,
                        confidence=0.9,
                        word_count=len(buffer.split()),
                        char_count=len(buffer),
                    ))
                    buffer_idx += 1
                buffer = content
                buffer_page = section.page_number
                buffer_type = section.section_type

        # Flush remaining buffer
        if buffer.strip():
            merged.append(DocumentSection(
                section_id=f"chunk_{buffer_idx}",
                title=self._extract_section_title(buffer),
                content=buffer.strip(),
                page_number=buffer_page,
                section_type=buffer_type,
                confidence=0.9,
                word_count=len(buffer.split()),
                char_count=len(buffer),
            ))

        # Split any chunks that are still too large
        final = []
        for chunk in merged:
            if chunk.char_count > MAX_CHUNK_CHARS:
                final.extend(self._split_section_into_chunks(chunk))
            else:
                final.append(chunk)

        logger.info(f"Chunking: {len(sections)} blocks -> {len(final)} chunks")
        return final
    
    def _split_section_into_chunks(self, section: DocumentSection) -> List[DocumentSection]:
        """Split large sections into smaller chunks."""
        content = section.content
        sentences = re.split(r'[.!?]+\s+', content)
        
        chunks = []
        current_chunk = ""
        chunk_count = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > 800:
                if current_chunk.strip():
                    chunk_section = DocumentSection(
                        section_id=f"{section.section_id}_chunk_{chunk_count}",
                        title=f"{section.title} (Part {chunk_count + 1})",
                        content=current_chunk.strip(),
                        page_number=section.page_number,
                        section_type=section.section_type,
                        confidence=section.confidence,
                        word_count=len(current_chunk.split()),
                        char_count=len(current_chunk)
                    )
                    chunks.append(chunk_section)
                    chunk_count += 1
                    current_chunk = sentence
            else:
                current_chunk += sentence + ". "
        
        # Add remaining content
        if current_chunk.strip():
            chunk_section = DocumentSection(
                section_id=f"{section.section_id}_chunk_{chunk_count}",
                title=f"{section.title} (Part {chunk_count + 1})" if chunk_count > 0 else section.title,
                content=current_chunk.strip(),
                page_number=section.page_number,
                section_type=section.section_type,
                confidence=section.confidence,
                word_count=len(current_chunk.split()),
                char_count=len(current_chunk)
            )
            chunks.append(chunk_section)
        
        return chunks if chunks else [section]
    
    async def process_document_async(self, pdf_path: str, document_id: str, filename: str) -> ProcessedDocument:
        """Asynchronously process a single document with progress tracking."""
        start_time = time.time()
        
        try:
            self._notify_progress(ProcessingProgress(
                document_id=document_id,
                stage="starting",
                progress=0.0,
                message="Initializing document processing",
                timestamp=datetime.now()
            ))
            
            # Extract text and sections
            full_text, sections, method, quality_score = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._extract_text_optimized, pdf_path, document_id
            )
            
            # Enhanced content chunking
            chunked_sections = self._chunk_content(sections, document_id)
            
            # Get document metadata
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Generate embeddings in background
            embeddings_generated = False
            embedding_count = 0
            
            try:
                self._notify_progress(ProcessingProgress(
                    document_id=document_id,
                    stage="embedding",
                    progress=0.9,
                    message="Generating embeddings for semantic search",
                    timestamp=datetime.now()
                ))
                
                # Convert sections to dict format for embedding service
                sections_dict = [section.dict() for section in chunked_sections]
                document_embeddings = await embedding_service.generate_document_embeddings(
                    document_id, sections_dict
                )
                embeddings_generated = True
                embedding_count = len(document_embeddings)
                
                logger.info(f"Generated {embedding_count} embeddings for document {document_id}")
                
            except Exception as e:
                logger.warning(f"Failed to generate embeddings for document {document_id}: {e}")
                # Continue without embeddings - this is not a critical failure
            
            # Final progress update
            self._notify_progress(ProcessingProgress(
                document_id=document_id,
                stage="completed",
                progress=1.0,
                message=f"Processing completed in {processing_time_ms}ms with {embedding_count} embeddings",
                timestamp=datetime.now(),
                processing_time_ms=processing_time_ms
            ))
            
            # Update processing stats
            self._update_processing_stats(processing_time_ms, True)
            
            return ProcessedDocument(
                document_id=document_id,
                filename=filename,
                total_pages=total_pages,
                processing_method=method,
                processing_time_ms=processing_time_ms,
                extracted_text_length=len(full_text),
                sections=chunked_sections,
                metadata={
                    "quality_score": quality_score,
                    "original_sections": len(sections),
                    "chunked_sections": len(chunked_sections),
                    "processing_timestamp": datetime.now().isoformat(),
                    "embeddings_generated": embeddings_generated,
                    "embedding_count": embedding_count
                },
                quality_score=quality_score,
                embeddings_generated=embeddings_generated,
                embedding_count=embedding_count
            )
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            self._notify_progress(ProcessingProgress(
                document_id=document_id,
                stage="failed",
                progress=0.0,
                message=f"Processing failed: {str(e)}",
                timestamp=datetime.now(),
                processing_time_ms=processing_time_ms
            ))
            
            self._update_processing_stats(processing_time_ms, False)
            raise
    
    def _update_processing_stats(self, processing_time_ms: int, success: bool):
        """Update processing statistics."""
        self.processing_stats["total_processed"] += 1
        
        # Update average processing time
        current_avg = self.processing_stats["average_time_ms"]
        total_processed = self.processing_stats["total_processed"]
        self.processing_stats["average_time_ms"] = (
            (current_avg * (total_processed - 1) + processing_time_ms) / total_processed
        )
        
        # Update success rate
        if success:
            current_success_count = int(self.processing_stats["success_rate"] * (total_processed - 1))
            self.processing_stats["success_rate"] = (current_success_count + 1) / total_processed
        else:
            current_success_count = int(self.processing_stats["success_rate"] * (total_processed - 1))
            self.processing_stats["success_rate"] = current_success_count / total_processed
    
    def get_processing_stats(self) -> Dict:
        """Get current processing statistics."""
        return {
            **self.processing_stats,
            "target_time_ms": 1000,  # 1 second target
            "performance_ratio": 1000 / max(self.processing_stats["average_time_ms"], 1),
            "active_workers": self.max_workers
        }
    
    def cleanup_callbacks(self, document_id: str):
        """Clean up progress callbacks for a document."""
        if document_id in self.progress_callbacks:
            del self.progress_callbacks[document_id]

# Global processor instance
document_processor = DocumentProcessor(max_workers=3)