"""
Semantic search engine with multi-tier search strategy and confidence filtering.

Requirements:
- 3.1.3: Build semantic search across processed documents
- 3.1.6: Implement multi-tier search strategy (fast → precision)
- 3.1.7: Add confidence-based result filtering (>0.75 threshold)
- 3.1.6: Create search result ranking and snippet extraction
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchTier(Enum):
    """Search tier levels for multi-tier strategy."""
    FAST = "fast"
    PRECISION = "precision"


class SearchStrategy(BaseModel):
    """Configuration for search strategy."""
    confidence_threshold: float = 0.75
    fast_search_k: int = 20  # Initial broad search
    precision_search_k: int = 10  # Final refined results
    max_results: int = 5
    snippet_length: int = 200
    enable_cross_document: bool = True
    processing_timeout_ms: int = 1000  # 1 second target


class EnhancedSearchResult(BaseModel):
    """Enhanced search result with additional metadata."""
    section_id: str
    document_id: str
    text: str
    similarity_score: float
    confidence_score: float
    page_number: int
    section_type: str
    snippet: str
    search_tier: SearchTier
    related_sections: List[str] = []
    processing_time_ms: float = 0


class SearchContext(BaseModel):
    """Context for search operation."""
    query: str
    document_ids: Optional[List[str]] = None
    selected_text: Optional[str] = None
    active_document_id: Optional[str] = None
    processing_status: Dict[str, bool] = {}  # document_id -> is_processed


class SemanticSearchEngine:
    """Advanced semantic search engine with multi-tier strategy."""
    
    def __init__(self, strategy: SearchStrategy = None):
        self.strategy = strategy or SearchStrategy()
        self.search_cache: Dict[str, List[EnhancedSearchResult]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl_seconds = 300  # 5 minutes
        
        # Performance tracking
        self.stats = {
            "total_searches": 0,
            "fast_tier_searches": 0,
            "precision_tier_searches": 0,
            "cache_hits": 0,
            "average_search_time_ms": 0,
            "confidence_filtered_results": 0
        }
    
    async def search(self, context: SearchContext) -> List[EnhancedSearchResult]:
        """
        Perform multi-tier semantic search with confidence filtering.
        
        Args:
            context: Search context with query and metadata
            
        Returns:
            List of enhanced search results
        """
        logger.info("Starting semantic search with query: '%s'", context.query[:50])
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(context)
            cached_results = self._get_cached_results(cache_key)
            if cached_results:
                self.stats["cache_hits"] += 1
                logger.info("Returning cached search results")
                return cached_results
            
            # Tier 1: Fast search
            fast_results = await self._fast_search(context)
            
            # Tier 2: Precision search if needed
            final_results = await self._precision_search(context, fast_results)
            
            # Apply confidence filtering
            filtered_results = self._apply_confidence_filtering(final_results)
            
            # Enhance results with cross-document relationships
            if self.strategy.enable_cross_document:
                enhanced_results = await self._enhance_with_relationships(filtered_results)
            else:
                enhanced_results = filtered_results
            
            # Cache results
            self._cache_results(cache_key, enhanced_results)
            
            # Update statistics
            search_time = (time.time() - start_time) * 1000
            self._update_search_stats(search_time, len(enhanced_results))
            
            # Print detailed search results to console
            self._print_search_results(context.query, enhanced_results[:self.strategy.max_results], search_time)
            
            logger.info("Search completed in %.1fms, found %d results", 
                       search_time, len(enhanced_results))
            
            return enhanced_results[:self.strategy.max_results]
            
        except Exception as e:
            logger.error("Semantic search failed: %s", str(e))
            raise
    
    async def _fast_search(self, context: SearchContext) -> List[EnhancedSearchResult]:
        """Tier 1: Fast approximate search."""
        logger.debug("Performing fast search tier")
        
        # Import here to avoid circular imports
        from backend.embedding_service import embedding_service
        
        # Use broader search to capture more potential matches
        raw_results = await embedding_service.semantic_search(
            query=context.query,
            top_k=self.strategy.fast_search_k,
            document_ids=context.document_ids
        )
        
        # Convert to enhanced results
        enhanced_results = []
        for result in raw_results:
            enhanced_result = EnhancedSearchResult(
                section_id=result.section_id,
                document_id=result.document_id,
                text=result.text,
                similarity_score=result.similarity_score,
                confidence_score=result.similarity_score,  # Initial confidence = similarity
                page_number=result.page_number,
                section_type=result.section_type,
                snippet=result.snippet,
                search_tier=SearchTier.FAST
            )
            enhanced_results.append(enhanced_result)
        
        self.stats["fast_tier_searches"] += 1
        return enhanced_results
    
    async def _precision_search(self, context: SearchContext, 
                              fast_results: List[EnhancedSearchResult]) -> List[EnhancedSearchResult]:
        """Tier 2: Precision search for low-confidence results."""
        
        # Check if precision search is needed
        high_confidence_results = [
            r for r in fast_results 
            if r.confidence_score >= self.strategy.confidence_threshold
        ]
        
        if len(high_confidence_results) >= self.strategy.max_results:
            logger.debug("Sufficient high-confidence results, skipping precision search")
            return fast_results
        
        logger.debug("Performing precision search tier")
        self.stats["precision_tier_searches"] += 1
        
        # Enhanced query for precision search
        enhanced_query = self._enhance_query_for_precision(context)
        
        # Import here to avoid circular imports
        from backend.embedding_service import embedding_service
        
        # Perform more focused search
        precision_results = await embedding_service.semantic_search(
            query=enhanced_query,
            top_k=self.strategy.precision_search_k,
            document_ids=context.document_ids
        )
        
        # Merge and re-rank results
        all_results = fast_results.copy()
        
        for result in precision_results:
            # Check if this result is already in fast results
            existing = next(
                (r for r in all_results if r.section_id == result.section_id), 
                None
            )
            
            if existing:
                # Update confidence score with precision search
                existing.confidence_score = max(
                    existing.confidence_score, 
                    result.similarity_score * 1.1  # Boost precision results
                )
                existing.search_tier = SearchTier.PRECISION
            else:
                # Add new precision result
                enhanced_result = EnhancedSearchResult(
                    section_id=result.section_id,
                    document_id=result.document_id,
                    text=result.text,
                    similarity_score=result.similarity_score,
                    confidence_score=result.similarity_score * 1.1,
                    page_number=result.page_number,
                    section_type=result.section_type,
                    snippet=result.snippet,
                    search_tier=SearchTier.PRECISION
                )
                all_results.append(enhanced_result)
        
        # Re-rank by confidence score
        all_results.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return all_results
    
    def _enhance_query_for_precision(self, context: SearchContext) -> str:
        """Enhance query for precision search."""
        enhanced_query = context.query
        
        # Add selected text context if available
        if context.selected_text:
            enhanced_query = f"{context.query} {context.selected_text}"
        
        return enhanced_query
    
    def _apply_confidence_filtering(self, results: List[EnhancedSearchResult]) -> List[EnhancedSearchResult]:
        """Apply confidence-based filtering."""
        filtered_results = [
            result for result in results 
            if result.confidence_score >= self.strategy.confidence_threshold
        ]
        
        filtered_count = len(results) - len(filtered_results)
        if filtered_count > 0:
            self.stats["confidence_filtered_results"] += filtered_count
            logger.debug("Filtered out %d low-confidence results", filtered_count)
        
        return filtered_results
    
    async def _enhance_with_relationships(self, results: List[EnhancedSearchResult]) -> List[EnhancedSearchResult]:
        """Enhance results with cross-document relationships."""
        if len(results) <= 1:
            return results
        
        # Group results by document
        document_groups: Dict[str, List[EnhancedSearchResult]] = {}
        for result in results:
            if result.document_id not in document_groups:
                document_groups[result.document_id] = []
            document_groups[result.document_id].append(result)
        
        # Find cross-document relationships
        for result in results:
            related_sections = []
            
            # Look for related sections in other documents
            for doc_id, doc_results in document_groups.items():
                if doc_id != result.document_id:
                    # Find most similar section in this document
                    best_match = max(doc_results, 
                                   key=lambda x: x.similarity_score)
                    if best_match.similarity_score > 0.7:  # Relationship threshold
                        related_sections.append(best_match.section_id)
            
            result.related_sections = related_sections
        
        return results
    
    def _generate_cache_key(self, context: SearchContext) -> str:
        """Generate cache key for search context."""
        key_parts = [
            context.query,
            str(sorted(context.document_ids or [])),
            context.selected_text or "",
            context.active_document_id or ""
        ]
        return "|".join(key_parts)
    
    def _get_cached_results(self, cache_key: str) -> Optional[List[EnhancedSearchResult]]:
        """Get cached search results if valid."""
        if cache_key not in self.search_cache:
            return None
        
        # Check if cache is still valid
        cache_time = self.cache_timestamps.get(cache_key)
        if not cache_time:
            return None
        
        age_seconds = (datetime.now() - cache_time).total_seconds()
        if age_seconds > self.cache_ttl_seconds:
            # Remove expired cache
            del self.search_cache[cache_key]
            del self.cache_timestamps[cache_key]
            return None
        
        return self.search_cache[cache_key]
    
    def _cache_results(self, cache_key: str, results: List[EnhancedSearchResult]):
        """Cache search results."""
        self.search_cache[cache_key] = results
        self.cache_timestamps[cache_key] = datetime.now()
        
        # Clean up old cache entries (simple LRU)
        if len(self.search_cache) > 100:  # Max cache size
            oldest_key = min(self.cache_timestamps.keys(),
                           key=lambda k: self.cache_timestamps[k])
            del self.search_cache[oldest_key]
            del self.cache_timestamps[oldest_key]
    
    def _update_search_stats(self, search_time_ms: float, result_count: int):
        """Update search statistics."""
        self.stats["total_searches"] += 1
        
        # Update average search time
        current_avg = self.stats["average_search_time_ms"]
        total_searches = self.stats["total_searches"]
        self.stats["average_search_time_ms"] = (
            (current_avg * (total_searches - 1) + search_time_ms) / total_searches
        )
        
        # Log result count for monitoring
        logger.debug(f"Search returned {result_count} results")
    
    def _print_search_results(self, query: str, results: List[EnhancedSearchResult], search_time_ms: float):
        """Print detailed search results to console for debugging and monitoring."""
        print("\n" + "="*80)
        print(f"🔍 SEMANTIC SEARCH RESULTS")
        print("="*80)
        print(f"Query: '{query}'")
        print(f"Search Time: {search_time_ms:.1f}ms")
        print(f"Results Found: {len(results)}")
        print(f"Confidence Threshold: {self.strategy.confidence_threshold}")
        
        if not results:
            print("❌ No results found matching the confidence threshold")
            print("="*80)
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n📄 Result #{i}")
            print(f"   Document: {result.document_id}")
            print(f"   Section: {result.section_id}")
            print(f"   Page: {result.page_number}")
            print(f"   Type: {result.section_type}")
            print(f"   Similarity: {result.similarity_score:.3f}")
            print(f"   Confidence: {result.confidence_score:.3f}")
            print(f"   Search Tier: {result.search_tier.value}")
            
            # Print snippet with highlighting
            snippet = result.snippet
            if len(snippet) > 150:
                snippet = snippet[:150] + "..."
            print(f"   📝 Snippet: {snippet}")
            
            # Print related sections if any
            if result.related_sections:
                print(f"   🔗 Related: {', '.join(result.related_sections[:3])}")
        
        # Print search statistics
        stats = self.get_stats()
        print(f"\n📊 Search Statistics:")
        print(f"   Cache Hit Rate: {stats.get('cache_hit_rate', 0):.1%}")
        print(f"   Precision Search Rate: {stats.get('precision_search_rate', 0):.1%}")
        print(f"   Average Search Time: {stats.get('average_search_time_ms', 0):.1f}ms")
        print(f"   Total Searches: {stats.get('total_searches', 0)}")
        print("="*80)
    
    async def search_related_content(self, selected_text: str,
                                   document_ids: Optional[List[str]] = None,
                                   processing_status: Optional[Dict[str, bool]] = None) -> List[EnhancedSearchResult]:
        """
        Search for content related to selected text.
        
        Args:
            selected_text: Text selected by user
            document_ids: Optional list of document IDs to search within
            processing_status: Status of document processing
            
        Returns:
            List of related content sections
        """
        context = SearchContext(
            query=selected_text,
            document_ids=document_ids,
            selected_text=selected_text,
            processing_status=processing_status or {}
        )
        
        results = await self.search(context)
        
        # Add processing status information
        if processing_status:
            for result in results:
                is_processed = processing_status.get(result.document_id, True)
                if not is_processed:
                    result.snippet += " [Document still processing...]"
        
        return results
    
    def get_stats(self) -> Dict:
        """Get search engine statistics."""
        return {
            **self.stats,
            "cache_size": len(self.search_cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(self.stats["total_searches"], 1)
            ),
            "precision_search_rate": (
                self.stats["precision_tier_searches"] / 
                max(self.stats["total_searches"], 1)
            ),
            "confidence_threshold": self.strategy.confidence_threshold
        }
    
    def clear_cache(self):
        """Clear search cache."""
        self.search_cache.clear()
        self.cache_timestamps.clear()
        logger.info("Search cache cleared")


# Global search engine instance
search_engine = SemanticSearchEngine()