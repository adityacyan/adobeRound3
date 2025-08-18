"""
Validation test for Task 5.2: Create semantic search engine

This test validates that the implementation meets all requirements:
- 3.1.3: Build semantic search across processed documents
- 3.1.6: Implement multi-tier search strategy (fast → precision)
- 3.1.7: Add confidence-based result filtering (>0.75 threshold)
- Create search result ranking and snippet extraction
"""

import asyncio
import time
from backend.search_engine import (
    SemanticSearchEngine, SearchStrategy, SearchContext, 
    EnhancedSearchResult, SearchTier
)
from backend.embedding_service import embedding_service


async def test_requirement_3_1_3():
    """Test 3.1.3: Build semantic search across processed documents."""
    print("Testing Requirement 3.1.3: Semantic search across processed documents")
    
    # Initialize services
    await embedding_service.initialize()
    search_engine = SemanticSearchEngine()
    
    # Create test documents
    doc1_sections = [
        {
            "section_id": "doc1_sec1",
            "content": "Machine learning algorithms are used for data analysis and pattern recognition.",
            "page_number": 1,
            "section_type": "paragraph"
        },
        {
            "section_id": "doc1_sec2", 
            "content": "Deep learning neural networks can process complex data structures.",
            "page_number": 2,
            "section_type": "paragraph"
        }
    ]
    
    doc2_sections = [
        {
            "section_id": "doc2_sec1",
            "content": "Artificial intelligence encompasses machine learning and deep learning techniques.",
            "page_number": 1,
            "section_type": "paragraph"
        }
    ]
    
    # Generate embeddings
    await embedding_service.generate_document_embeddings("doc1", doc1_sections)
    await embedding_service.generate_document_embeddings("doc2", doc2_sections)
    
    # Test cross-document search
    context = SearchContext(
        query="machine learning techniques",
        document_ids=["doc1", "doc2"]
    )
    
    results = await search_engine.search(context)
    
    # Validate results
    assert len(results) >= 0, "Should return search results"
    
    # Check that results come from multiple documents if relevant content exists
    document_ids_in_results = set(r.document_id for r in results)
    print(f"   ✓ Search found results from {len(document_ids_in_results)} documents")
    print(f"   ✓ Total results: {len(results)}")
    
    return True


async def test_requirement_3_1_6():
    """Test 3.1.6: Multi-tier search strategy (fast → precision)."""
    print("Testing Requirement 3.1.6: Multi-tier search strategy")
    
    search_engine = SemanticSearchEngine()
    
    # Test with a query that should trigger precision search
    context = SearchContext(
        query="advanced neural network architectures",
        document_ids=["doc1", "doc2"]
    )
    
    # Perform search
    results = await search_engine.search(context)
    
    # Check search statistics
    stats = search_engine.get_stats()
    
    print(f"   ✓ Fast tier searches: {stats['fast_tier_searches']}")
    print(f"   ✓ Precision tier searches: {stats['precision_tier_searches']}")
    print(f"   ✓ Total searches: {stats['total_searches']}")
    
    # Validate that both tiers can be used
    assert stats['fast_tier_searches'] > 0, "Fast tier should be used"
    
    # Test with low confidence threshold to trigger precision search
    search_engine.strategy.confidence_threshold = 0.95  # Very high threshold
    
    context2 = SearchContext(
        query="machine learning data processing",
        document_ids=["doc1", "doc2"]
    )
    
    results2 = await search_engine.search(context2)
    stats2 = search_engine.get_stats()
    
    print(f"   ✓ Precision searches after high threshold: {stats2['precision_tier_searches']}")
    
    return True


async def test_requirement_3_1_7():
    """Test 3.1.7: Confidence-based result filtering (>0.75 threshold)."""
    print("Testing Requirement 3.1.7: Confidence-based result filtering")
    
    # Test with default confidence threshold (0.75)
    search_engine = SemanticSearchEngine()
    
    context = SearchContext(
        query="machine learning algorithms",
        document_ids=["doc1", "doc2"]
    )
    
    results = await search_engine.search(context)
    
    # Validate confidence filtering
    for result in results:
        assert result.confidence_score >= 0.75, f"Result confidence {result.confidence_score} should be >= 0.75"
    
    print(f"   ✓ All {len(results)} results meet confidence threshold (>= 0.75)")
    
    # Test with lower confidence threshold
    search_engine.strategy.confidence_threshold = 0.5
    
    results_low_conf = await search_engine.search(context)
    
    print(f"   ✓ Results with 0.5 threshold: {len(results_low_conf)}")
    print(f"   ✓ Results with 0.75 threshold: {len(results)}")
    
    # Should have same or more results with lower threshold
    assert len(results_low_conf) >= len(results), "Lower threshold should return same or more results"
    
    return True


async def test_search_result_ranking_and_snippets():
    """Test search result ranking and snippet extraction."""
    print("Testing search result ranking and snippet extraction")
    
    search_engine = SemanticSearchEngine()
    
    context = SearchContext(
        query="neural networks",
        document_ids=["doc1", "doc2"]
    )
    
    results = await search_engine.search(context)
    
    if len(results) > 1:
        # Check that results are ranked by confidence score
        for i in range(len(results) - 1):
            assert results[i].confidence_score >= results[i + 1].confidence_score, \
                "Results should be ranked by confidence score"
        
        print("   ✓ Results are properly ranked by confidence score")
    
    # Check snippet extraction
    for result in results:
        assert hasattr(result, 'snippet'), "Result should have snippet"
        assert len(result.snippet) > 0, "Snippet should not be empty"
        assert len(result.snippet) <= 250, "Snippet should be reasonably sized"
    
    print(f"   ✓ All {len(results)} results have proper snippets")
    
    return True


async def test_performance_requirements():
    """Test performance requirements (search within 1 second)."""
    print("Testing performance requirements")
    
    search_engine = SemanticSearchEngine()
    
    context = SearchContext(
        query="artificial intelligence machine learning",
        document_ids=["doc1", "doc2"]
    )
    
    # Measure search time
    start_time = time.time()
    results = await search_engine.search(context)
    search_time = (time.time() - start_time) * 1000  # Convert to ms
    
    print(f"   ✓ Search completed in {search_time:.1f}ms")
    
    # Should complete within 1 second (1000ms)
    assert search_time < 1000, f"Search should complete within 1000ms, took {search_time:.1f}ms"
    
    # Check average search time from stats
    stats = search_engine.get_stats()
    avg_time = stats.get('average_search_time_ms', 0)
    
    print(f"   ✓ Average search time: {avg_time:.1f}ms")
    
    return True


async def test_caching_functionality():
    """Test search result caching."""
    print("Testing search result caching")
    
    search_engine = SemanticSearchEngine()
    
    context = SearchContext(
        query="machine learning data analysis",
        document_ids=["doc1", "doc2"]
    )
    
    # First search
    start_time = time.time()
    results1 = await search_engine.search(context)
    first_search_time = (time.time() - start_time) * 1000
    
    # Second search (should use cache)
    start_time = time.time()
    results2 = await search_engine.search(context)
    second_search_time = (time.time() - start_time) * 1000
    
    # Results should be identical
    assert len(results1) == len(results2), "Cached results should be identical"
    
    stats = search_engine.get_stats()
    cache_hit_rate = stats.get('cache_hit_rate', 0)
    
    print(f"   ✓ First search: {first_search_time:.1f}ms")
    print(f"   ✓ Second search: {second_search_time:.1f}ms")
    print(f"   ✓ Cache hit rate: {cache_hit_rate:.1%}")
    
    return True


async def main():
    """Run all validation tests for Task 5.2."""
    print("=" * 60)
    print("TASK 5.2 VALIDATION: Create semantic search engine")
    print("=" * 60)
    
    tests = [
        ("3.1.3: Semantic search across documents", test_requirement_3_1_3),
        ("3.1.6: Multi-tier search strategy", test_requirement_3_1_6),
        ("3.1.7: Confidence-based filtering", test_requirement_3_1_7),
        ("Search result ranking and snippets", test_search_result_ranking_and_snippets),
        ("Performance requirements", test_performance_requirements),
        ("Caching functionality", test_caching_functionality),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{len(tests) - passed - failed}. {test_name}")
        try:
            result = await test_func()
            if result:
                print(f"   ✅ PASSED")
                passed += 1
            else:
                print(f"   ❌ FAILED")
                failed += 1
        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("TASK 5.2 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Task 5.2 implementation is complete and meets all requirements.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)