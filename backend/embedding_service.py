"""
Embedding service using Gemini gemini-embedding-001 + in-memory index.
All chunks per document are sent in a single API call (one request per upload).
Free tier: 1000 requests/day, 100 req/min - one upload = one embedding request.
"""

import asyncio
import time
import logging
import os
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768
# Max strings per batch - gemini-embedding-001 supports lists directly
MAX_BATCH_SIZE = 100


class EmbeddingConfig(BaseModel):
    model_name: str = GEMINI_EMBEDDING_MODEL
    embedding_dimension: int = EMBEDDING_DIMENSION
    batch_size: int = MAX_BATCH_SIZE
    max_text_length: int = 2048


class DocumentEmbedding(BaseModel):
    section_id: str
    document_id: str
    text: str
    embedding: List[float]
    page_number: int
    section_type: str
    timestamp: datetime
    confidence: float = 1.0


class SearchResult(BaseModel):
    section_id: str
    document_id: str
    text: str
    similarity_score: float
    page_number: int
    section_type: str
    snippet: str


class EmbeddingService:
    """
    Gemini embedding service with in-memory cosine similarity search.
    No FAISS needed - numpy dot product on normalized vectors is fast enough
    for hundreds of chunks and uses negligible RAM.
    """

    def __init__(self, config: EmbeddingConfig = None):
        self.config = config or EmbeddingConfig()
        self.client: Optional[genai.Client] = None
        # Store embeddings as numpy matrix for fast dot product search
        self.vectors: Optional[np.ndarray] = None
        self.metadata: List[DocumentEmbedding] = []
        self.document_index: Dict[str, List[int]] = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.is_initialized = False

        self.stats = {
            "total_embeddings": 0,
            "average_embedding_time_ms": 0,
            "total_searches": 0,
            "average_search_time_ms": 0,
            "api_calls": 0,
        }

    async def initialize(self):
        if self.is_initialized:
            return
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        self.client = genai.Client(api_key=api_key)
        self.is_initialized = True
        logger.info(f"Embedding service initialized with {self.config.model_name}")

    def _load_model(self):
        pass  # kept for interface compatibility

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms

    def _call_embed_documents(self, texts: List[str]) -> np.ndarray:
        """
        Single API call for all texts using RETRIEVAL_DOCUMENT task.
        gemini-embedding-001 returns one embedding per string in the list.
        """
        result = self.client.models.embed_content(
            model=self.config.model_name,
            contents=texts,
            config=genai_types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self.config.embedding_dimension,
            ),
        )
        vectors = np.array([e.values for e in result.embeddings], dtype=np.float32)
        self.stats["api_calls"] += 1
        return self._normalize(vectors)

    def _call_embed_query(self, text: str) -> np.ndarray:
        """Single API call for a query string."""
        result = self.client.models.embed_content(
            model=self.config.model_name,
            contents=[text],
            config=genai_types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.config.embedding_dimension,
            ),
        )
        vector = np.array([result.embeddings[0].values], dtype=np.float32)
        self.stats["api_calls"] += 1
        return self._normalize(vector)

    async def generate_document_embeddings(
        self, document_id: str, sections: List[dict]
    ) -> List[DocumentEmbedding]:
        if not self.is_initialized:
            await self.initialize()

        logger.info(f"Embedding {len(sections)} sections for {document_id} in one API call")
        start_time = time.time()

        texts = [s.get("content", "")[: self.config.max_text_length] for s in sections]
        section_meta = [
            {
                "section_id": s.get("section_id"),
                "page_number": s.get("page_number", 1),
                "section_type": s.get("section_type", "paragraph"),
                "confidence": s.get("confidence", 1.0),
            }
            for s in sections
        ]

        # All chunks in one API call — counts as 1 request against rate limit
        all_vectors = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i: i + self.config.batch_size]
            vecs = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._call_embed_documents, batch
            )
            all_vectors.append(vecs)

        embeddings_matrix = np.vstack(all_vectors)

        document_embeddings = []
        start_idx = len(self.metadata)
        indices = []

        for i, (vec, meta) in enumerate(zip(embeddings_matrix, section_meta)):
            doc_emb = DocumentEmbedding(
                section_id=meta["section_id"],
                document_id=document_id,
                text=texts[i],
                embedding=vec.tolist(),
                page_number=meta["page_number"],
                section_type=meta["section_type"],
                timestamp=datetime.now(),
                confidence=meta["confidence"],
            )
            document_embeddings.append(doc_emb)
            self.metadata.append(doc_emb)
            indices.append(start_idx + i)

        # Rebuild vectors matrix
        all_vecs = [np.array(m.embedding) for m in self.metadata]
        self.vectors = np.array(all_vecs, dtype=np.float32)
        self.document_index[document_id] = indices

        processing_time = (time.time() - start_time) * 1000
        self._update_embedding_stats(len(sections), processing_time)
        logger.info(f"Generated {len(document_embeddings)} embeddings in {processing_time:.1f}ms (1 API call)")
        return document_embeddings

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        if not self.is_initialized:
            await self.initialize()

        if self.vectors is None or len(self.metadata) == 0:
            return []

        start_time = time.time()

        query_vec = await asyncio.get_event_loop().run_in_executor(
            self.executor, self._call_embed_query, query
        )

        # Cosine similarity via dot product (vectors are normalized)
        scores = (self.vectors @ query_vec.T).flatten()

        # Filter by document_ids if specified
        if document_ids:
            allowed = set()
            for doc_id in document_ids:
                allowed.update(self.document_index.get(doc_id, []))
            mask = np.zeros(len(scores), dtype=bool)
            for idx in allowed:
                if idx < len(mask):
                    mask[idx] = True
            scores = np.where(mask, scores, -1.0)

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] < 0:
                continue
            meta = self.metadata[idx]
            results.append(SearchResult(
                section_id=meta.section_id,
                document_id=meta.document_id,
                text=meta.text,
                similarity_score=float(scores[idx]),
                page_number=meta.page_number,
                section_type=meta.section_type,
                snippet=self._create_snippet(meta.text, query),
            ))

        search_time = (time.time() - start_time) * 1000
        self._update_search_stats(search_time)
        logger.info(f"Search done in {search_time:.1f}ms, {len(results)} results")
        return results

    def _create_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        if len(text) <= max_length:
            return text
        query_words = query.lower().split()
        text_lower = text.lower()
        best_start, best_score = 0, 0
        for i in range(0, len(text) - max_length, 50):
            score = sum(1 for w in query_words if w in text_lower[i: i + max_length])
            if score > best_score:
                best_score, best_start = score, i
        snippet = text[best_start: best_start + max_length]
        if best_start > 0:
            snippet = "..." + snippet
        if best_start + max_length < len(text):
            snippet += "..."
        return snippet

    def remove_document_embeddings(self, document_id: str):
        if document_id not in self.document_index:
            return
        indices_to_remove = set(self.document_index[document_id])
        self.metadata = [m for i, m in enumerate(self.metadata) if i not in indices_to_remove]
        if self.metadata:
            self.vectors = np.array([m.embedding for m in self.metadata], dtype=np.float32)
        else:
            self.vectors = None
        # Rebuild index
        self.document_index = {}
        for i, m in enumerate(self.metadata):
            self.document_index.setdefault(m.document_id, []).append(i)
        logger.info(f"Removed embeddings for {document_id}")

    def get_document_embedding_count(self, document_id: str) -> int:
        return len(self.document_index.get(document_id, []))

    def get_total_embedding_count(self) -> int:
        return len(self.metadata)

    def _update_embedding_stats(self, count: int, time_ms: float):
        self.stats["total_embeddings"] += count
        total = self.stats["total_embeddings"]
        avg = self.stats["average_embedding_time_ms"]
        self.stats["average_embedding_time_ms"] = (avg * (total - count) + time_ms) / total

    def _update_search_stats(self, time_ms: float):
        self.stats["total_searches"] += 1
        total = self.stats["total_searches"]
        avg = self.stats["average_search_time_ms"]
        self.stats["average_search_time_ms"] = (avg * (total - 1) + time_ms) / total

    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "total_documents": len(self.document_index),
            "total_vectors": self.get_total_embedding_count(),
            "is_initialized": self.is_initialized,
            "model_name": self.config.model_name,
            "embedding_dimension": self.config.embedding_dimension,
        }


embedding_service = EmbeddingService()
