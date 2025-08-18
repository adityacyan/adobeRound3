"""
Embedding service for document semantic search using sentence transformers and FAISS.

Requirements:
- 3.1.1: Set up sentence-transformers for document embedding generation
- 3.1.2: Create vector storage using FAISS for fast similarity search
- 6.1: Background embedding generation during PDF processing
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from sentence_transformers import SentenceTransformer
import faiss
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingConfig(BaseModel):
    """Configuration for embedding service."""
    model_name: str = "all-MiniLM-L6-v2"  # Fast, good quality model
    embedding_dimension: int = 384
    faiss_index_type: str = "IndexFlatIP"  # Inner Product for cosine similarity
    batch_size: int = 32
    max_text_length: int = 512

class DocumentEmbedding(BaseModel):
    """Document section embedding with metadata."""
    section_id: str
    document_id: str
    text: str
    embedding: List[float]
    page_number: int
    section_type: str
    timestamp: datetime
    confidence: float = 1.0

class SearchResult(BaseModel):
    """Semantic search result."""
    section_id: str
    document_id: str
    text: str
    similarity_score: float
    page_number: int
    section_type: str
    snippet: str

class EmbeddingService:
    """Service for generating and managing document embeddings."""
    
    def __init__(self, config: EmbeddingConfig = None):
        self.config = config or EmbeddingConfig()
        self.model: Optional[SentenceTransformer] = None
        self.faiss_index: Optional[faiss.Index] = None
        self.embeddings_metadata: Dict[int, DocumentEmbedding] = {}
        self.document_embeddings: Dict[str, List[int]] = {}  # document_id -> list of embedding indices
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.is_initialized = False
        
        # Performance tracking
        self.stats = {
            "total_embeddings": 0,
            "average_embedding_time_ms": 0,
            "total_searches": 0,
            "average_search_time_ms": 0
        }
    
    async def initialize(self):
        """Initialize the embedding model and FAISS index."""
        if self.is_initialized:
            return
        
        logger.info(f"Initializing embedding service with model: {self.config.model_name}")
        start_time = time.time()
        
        try:
            # Load sentence transformer model
            self.model = await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                self._load_model
            )
            
            # Initialize FAISS index
            self.faiss_index = faiss.IndexFlatIP(self.config.embedding_dimension)
            
            # Enable GPU if available (optional)
            if faiss.get_num_gpus() > 0:
                logger.info("GPU detected, using GPU-accelerated FAISS")
                self.faiss_index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, self.faiss_index)
            
            self.is_initialized = True
            init_time = (time.time() - start_time) * 1000
            logger.info(f"Embedding service initialized in {init_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise
    
    def _load_model(self) -> SentenceTransformer:
        """Load the sentence transformer model."""
        return SentenceTransformer(self.config.model_name) 
   
    async def generate_document_embeddings(self, document_id: str, sections: List[dict]) -> List[DocumentEmbedding]:
        """Generate embeddings for all sections of a document."""
        if not self.is_initialized:
            await self.initialize()
        
        logger.info(f"Generating embeddings for document {document_id} with {len(sections)} sections")
        start_time = time.time()
        
        try:
            # Prepare texts for embedding
            texts = []
            section_metadata = []
            
            for section in sections:
                # Truncate text if too long
                text = section.get("content", "")
                if len(text) > self.config.max_text_length:
                    text = text[:self.config.max_text_length]
                
                texts.append(text)
                section_metadata.append({
                    "section_id": section.get("section_id"),
                    "page_number": section.get("page_number", 1),
                    "section_type": section.get("section_type", "paragraph"),
                    "confidence": section.get("confidence", 1.0)
                })
            
            # Generate embeddings in batches
            embeddings = await self._generate_embeddings_batch(texts)
            
            # Create embedding objects
            document_embeddings = []
            embedding_indices = []
            
            for i, (embedding, metadata) in enumerate(zip(embeddings, section_metadata)):
                doc_embedding = DocumentEmbedding(
                    section_id=metadata["section_id"],
                    document_id=document_id,
                    text=texts[i],
                    embedding=embedding.tolist(),
                    page_number=metadata["page_number"],
                    section_type=metadata["section_type"],
                    timestamp=datetime.now(),
                    confidence=metadata["confidence"]
                )
                document_embeddings.append(doc_embedding)
                
                # Add to FAISS index
                embedding_index = self.faiss_index.ntotal
                self.faiss_index.add(embedding.reshape(1, -1))
                self.embeddings_metadata[embedding_index] = doc_embedding
                embedding_indices.append(embedding_index)
            
            # Track document embeddings
            self.document_embeddings[document_id] = embedding_indices
            
            # Update stats
            processing_time = (time.time() - start_time) * 1000
            self._update_embedding_stats(len(sections), processing_time)
            
            logger.info(f"Generated {len(document_embeddings)} embeddings for document {document_id} in {processing_time:.1f}ms")
            return document_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for document {document_id}: {e}")
            raise
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts."""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._encode_texts,
            texts
        )
    
    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """Encode texts using sentence transformer."""
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # For cosine similarity
        )
        return embeddings  
  
    async def semantic_search(self, query: str, top_k: int = 5, document_ids: Optional[List[str]] = None) -> List[SearchResult]:
        """Perform semantic search across document embeddings."""
        if not self.is_initialized:
            await self.initialize()
        
        if self.faiss_index.ntotal == 0:
            return []
        
        logger.info(f"Performing semantic search for query: '{query[:50]}...' with top_k={top_k}")
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embeddings_batch([query])
            query_vector = query_embedding[0].reshape(1, -1)
            
            # Perform FAISS search
            similarities, indices = self.faiss_index.search(query_vector, min(top_k * 2, self.faiss_index.ntotal))
            
            # Process results
            results = []
            for similarity, idx in zip(similarities[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                embedding_metadata = self.embeddings_metadata.get(idx)
                if not embedding_metadata:
                    continue
                
                # Filter by document IDs if specified
                if document_ids and embedding_metadata.document_id not in document_ids:
                    continue
                
                # Create search result
                snippet = self._create_snippet(embedding_metadata.text, query)
                result = SearchResult(
                    section_id=embedding_metadata.section_id,
                    document_id=embedding_metadata.document_id,
                    text=embedding_metadata.text,
                    similarity_score=float(similarity),
                    page_number=embedding_metadata.page_number,
                    section_type=embedding_metadata.section_type,
                    snippet=snippet
                )
                results.append(result)
                
                if len(results) >= top_k:
                    break
            
            # Update search stats
            search_time = (time.time() - start_time) * 1000
            self._update_search_stats(search_time)
            
            logger.info(f"Semantic search completed in {search_time:.1f}ms, found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise
    
    def _create_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """Create a snippet from text highlighting relevance to query."""
        # Simple snippet creation - could be enhanced with more sophisticated highlighting
        if len(text) <= max_length:
            return text
        
        # Try to find query terms in text
        query_words = query.lower().split()
        text_lower = text.lower()
        
        best_start = 0
        best_score = 0
        
        # Find the position with most query word matches
        for i in range(0, len(text) - max_length, 50):
            snippet = text_lower[i:i + max_length]
            score = sum(1 for word in query_words if word in snippet)
            if score > best_score:
                best_score = score
                best_start = i
        
        snippet = text[best_start:best_start + max_length]
        if best_start > 0:
            snippet = "..." + snippet
        if best_start + max_length < len(text):
            snippet = snippet + "..."
        
        return snippet    

    def remove_document_embeddings(self, document_id: str):
        """Remove all embeddings for a document (for session cleanup)."""
        if document_id not in self.document_embeddings:
            return
        
        embedding_indices = self.document_embeddings[document_id]
        
        # Remove from metadata
        for idx in embedding_indices:
            if idx in self.embeddings_metadata:
                del self.embeddings_metadata[idx]
        
        # Remove from document tracking
        del self.document_embeddings[document_id]
        
        # Note: FAISS doesn't support efficient removal, so we keep the vectors
        # In a production system, you might rebuild the index periodically
        logger.info(f"Removed embeddings for document {document_id}")
    
    def get_document_embedding_count(self, document_id: str) -> int:
        """Get the number of embeddings for a document."""
        return len(self.document_embeddings.get(document_id, []))
    
    def get_total_embedding_count(self) -> int:
        """Get total number of embeddings in the index."""
        return self.faiss_index.ntotal if self.faiss_index else 0
    
    def _update_embedding_stats(self, count: int, time_ms: float):
        """Update embedding generation statistics."""
        self.stats["total_embeddings"] += count
        
        # Update average time
        current_avg = self.stats["average_embedding_time_ms"]
        total_ops = self.stats["total_embeddings"]
        self.stats["average_embedding_time_ms"] = (
            (current_avg * (total_ops - count) + time_ms) / total_ops
        )
    
    def _update_search_stats(self, time_ms: float):
        """Update search statistics."""
        self.stats["total_searches"] += 1
        
        # Update average search time
        current_avg = self.stats["average_search_time_ms"]
        total_searches = self.stats["total_searches"]
        self.stats["average_search_time_ms"] = (
            (current_avg * (total_searches - 1) + time_ms) / total_searches
        )
    
    def get_stats(self) -> Dict:
        """Get embedding service statistics."""
        return {
            **self.stats,
            "total_documents": len(self.document_embeddings),
            "total_vectors": self.get_total_embedding_count(),
            "is_initialized": self.is_initialized,
            "model_name": self.config.model_name,
            "embedding_dimension": self.config.embedding_dimension
        }

# Global embedding service instance
embedding_service = EmbeddingService()