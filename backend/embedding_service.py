"""
Embedding service using fastembed (ONNX Runtime, no PyTorch) + FAISS.
Model is baked into the Docker image at build time - no runtime download.
~100MB RAM vs ~700MB for sentence-transformers+torch.
"""

import asyncio
import time
import logging
import os
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from fastembed import TextEmbedding
import faiss
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FASTEMBED_MODEL = "BAAI/bge-small-en-v1.5"  # 33MB, 384-dim, fast ONNX
MODEL_CACHE_DIR = "/app/models"
EMBEDDING_DIMENSION = 384


class EmbeddingConfig(BaseModel):
    model_name: str = FASTEMBED_MODEL
    embedding_dimension: int = EMBEDDING_DIMENSION
    faiss_index_type: str = "IndexFlatIP"
    batch_size: int = 64
    max_text_length: int = 512


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
    """ONNX-based local embedding service using fastembed + FAISS."""

    def __init__(self, config: EmbeddingConfig = None):
        self.config = config or EmbeddingConfig()
        self.model: Optional[TextEmbedding] = None
        self.faiss_index: Optional[faiss.Index] = None
        self.embeddings_metadata: Dict[int, DocumentEmbedding] = {}
        self.document_embeddings: Dict[str, List[int]] = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.is_initialized = False

        self.stats = {
            "total_embeddings": 0,
            "average_embedding_time_ms": 0,
            "total_searches": 0,
            "average_search_time_ms": 0,
        }

    async def initialize(self):
        if self.is_initialized:
            return

        logger.info(f"Loading fastembed model: {self.config.model_name}")
        start_time = time.time()

        self.model = await asyncio.get_event_loop().run_in_executor(
            self.executor, self._load_model
        )
        self.faiss_index = faiss.IndexFlatIP(self.config.embedding_dimension)
        self.is_initialized = True

        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Embedding model loaded in {elapsed:.1f}ms")

    def _load_model(self) -> TextEmbedding:
        cache_dir = MODEL_CACHE_DIR if os.path.isdir(MODEL_CACHE_DIR) else None
        return TextEmbedding(
            model_name=self.config.model_name,
            cache_dir=cache_dir,
        )

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        # fastembed returns a generator, collect into array
        embeddings = list(self.model.embed(texts, batch_size=self.config.batch_size))
        vectors = np.array(embeddings, dtype=np.float32)
        # normalize for cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms

    async def _generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, self._encode_texts, texts
        )

    async def generate_document_embeddings(
        self, document_id: str, sections: List[dict]
    ) -> List[DocumentEmbedding]:
        if not self.is_initialized:
            await self.initialize()

        logger.info(
            f"Generating embeddings for {document_id} with {len(sections)} sections"
        )
        start_time = time.time()

        texts = []
        section_metadata = []
        for section in sections:
            text = section.get("content", "")[: self.config.max_text_length]
            texts.append(text)
            section_metadata.append({
                "section_id": section.get("section_id"),
                "page_number": section.get("page_number", 1),
                "section_type": section.get("section_type", "paragraph"),
                "confidence": section.get("confidence", 1.0),
            })

        embeddings = await self._generate_embeddings_batch(texts)

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
                confidence=metadata["confidence"],
            )
            document_embeddings.append(doc_embedding)

            idx = self.faiss_index.ntotal
            self.faiss_index.add(embedding.reshape(1, -1))
            self.embeddings_metadata[idx] = doc_embedding
            embedding_indices.append(idx)

        self.document_embeddings[document_id] = embedding_indices

        processing_time = (time.time() - start_time) * 1000
        self._update_embedding_stats(len(sections), processing_time)
        logger.info(
            f"Generated {len(document_embeddings)} embeddings in {processing_time:.1f}ms"
        )
        return document_embeddings

    def _encode_texts_sync(self, texts: List[str]) -> np.ndarray:
        return self._encode_texts(texts)

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        if not self.is_initialized:
            await self.initialize()

        if self.faiss_index.ntotal == 0:
            return []

        start_time = time.time()

        query_embedding = await self._generate_embeddings_batch([query])
        query_vector = query_embedding[0].reshape(1, -1)

        similarities, indices = self.faiss_index.search(
            query_vector, min(top_k * 2, self.faiss_index.ntotal)
        )

        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if idx == -1:
                continue
            meta = self.embeddings_metadata.get(idx)
            if not meta:
                continue
            if document_ids and meta.document_id not in document_ids:
                continue
            results.append(SearchResult(
                section_id=meta.section_id,
                document_id=meta.document_id,
                text=meta.text,
                similarity_score=float(similarity),
                page_number=meta.page_number,
                section_type=meta.section_type,
                snippet=self._create_snippet(meta.text, query),
            ))
            if len(results) >= top_k:
                break

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
        if document_id not in self.document_embeddings:
            return
        for idx in self.document_embeddings[document_id]:
            self.embeddings_metadata.pop(idx, None)
        del self.document_embeddings[document_id]
        logger.info(f"Removed embeddings for {document_id}")

    def get_document_embedding_count(self, document_id: str) -> int:
        return len(self.document_embeddings.get(document_id, []))

    def get_total_embedding_count(self) -> int:
        return self.faiss_index.ntotal if self.faiss_index else 0

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
            "total_documents": len(self.document_embeddings),
            "total_vectors": self.get_total_embedding_count(),
            "is_initialized": self.is_initialized,
            "model_name": self.config.model_name,
            "embedding_dimension": self.config.embedding_dimension,
        }


embedding_service = EmbeddingService()
