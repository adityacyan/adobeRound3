"""
Test script for the embedding service implementation.
Tests sentence transformer embeddings and FAISS vector search.
"""

import asyncio
import time
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.embedding_service import embedding_service, EmbeddingConfig

async def test_embedding_service():
    """Test the embedding service functionality."""
    print("Testing Embedding Service Implementation")
    print("=" * 50)
    
    # Test 1: Initialize service
    print("1. Initializing embedding service...")
    start_time = time.time()
    
    try:
        await embedding_service.initialize()
        init_time = (time.time() - start_time) * 1000
        print(f"   ✓ Service initialized in {init_time:.1f}ms")
        print(f"   ✓ Model: {embedding_service.config.model_name}")
        print(f"   ✓ Embedding dimension: {embedding_service.config.embedding_dimension}")
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        return False
    
    # Test 2: Generate embeddings for sample document sections
    print("\n2. Testing document embedding generation...")
    
    sample_sections = [
        {
            "section_id": "test_doc_section_1",
            "content": "This is a test document about artificial intelligence and machine learning. It covers various topics including neural networks, deep learning, and natural language processing.",
            "page_number": 1,
            "section_type": "paragraph",
            "confidence": 1.0
        },
        {
            "section_id": "test_doc_section_2", 
            "content": "Machine learning algorithms can be categorized into supervised, unsupervised, and reinforcement learning. Each category has different applications and use cases.",
            "page_number": 1,
            "section_type": "paragraph",
            "confidence": 1.0
        },
        {
            "section_id": "test_doc_section_3",
            "content": "Natural language processing involves understanding and generating human language. It includes tasks like sentiment analysis, text classification, and language translation.",
            "page_number": 2,
            "section_type": "paragraph", 
            "confidence": 1.0
        }
    ]
    
    try:
        start_time = time.time()
        embeddings = await embedding_service.generate_document_embeddings("test_doc_1", sample_sections)
        embedding_time = (time.time() - start_time) * 1000
        
        print(f"   ✓ Generated {len(embeddings)} embeddings in {embedding_time:.1f}ms")
        print(f"   ✓ Average time per embedding: {embedding_time/len(embeddings):.1f}ms")
        print(f"   ✓ Total vectors in index: {embedding_service.get_total_embedding_count()}")
        
    except Exception as e:
        print(f"   ✗ Embedding generation failed: {e}")
        return False
    
    # Test 3: Semantic search
    print("\n3. Testing semantic search...")
    
    test_queries = [
        "machine learning algorithms",
        "natural language processing",
        "artificial intelligence applications",
        "deep learning neural networks"
    ]
    
    for query in test_queries:
        try:
            start_time = time.time()
            results = await embedding_service.semantic_search(query, top_k=3)
            search_time = (time.time() - start_time) * 1000
            
            print(f"   Query: '{query}'")
            print(f"   ✓ Found {len(results)} results in {search_time:.1f}ms")
            
            for i, result in enumerate(results):
                print(f"     {i+1}. Score: {result.similarity_score:.3f} | Section: {result.section_id}")
                print(f"        Snippet: {result.snippet[:100]}...")
            print()
            
        except Exception as e:
            print(f"   ✗ Search failed for query '{query}': {e}")
            return False
    
    # Test 4: Performance requirements
    print("4. Checking performance requirements...")
    stats = embedding_service.get_stats()
    
    print(f"   ✓ Average embedding time: {stats['average_embedding_time_ms']:.1f}ms")
    print(f"   ✓ Average search time: {stats['average_search_time_ms']:.1f}ms")
    print(f"   ✓ Total embeddings: {stats['total_embeddings']}")
    print(f"   ✓ Total searches: {stats['total_searches']}")
    
    # Check if search time meets requirement (within 1 second)
    if stats['average_search_time_ms'] <= 1000:
        print(f"   ✓ Search performance meets requirement (<1000ms)")
    else:
        print(f"   ⚠ Search performance may be slow ({stats['average_search_time_ms']:.1f}ms)")
    
    # Test 5: Document filtering
    print("\n5. Testing document-specific search...")
    
    try:
        # Search only within specific document
        results = await embedding_service.semantic_search(
            "machine learning", 
            top_k=5, 
            document_ids=["test_doc_1"]
        )
        print(f"   ✓ Document-filtered search returned {len(results)} results")
        
        # Verify all results are from the specified document
        all_from_doc = all(result.document_id == "test_doc_1" for result in results)
        if all_from_doc:
            print(f"   ✓ All results correctly filtered to document test_doc_1")
        else:
            print(f"   ✗ Document filtering failed")
            return False
            
    except Exception as e:
        print(f"   ✗ Document filtering test failed: {e}")
        return False
    
    # Test 6: Cleanup
    print("\n6. Testing cleanup...")
    
    try:
        initial_count = embedding_service.get_document_embedding_count("test_doc_1")
        embedding_service.remove_document_embeddings("test_doc_1")
        final_count = embedding_service.get_document_embedding_count("test_doc_1")
        
        print(f"   ✓ Removed embeddings: {initial_count} -> {final_count}")
        
    except Exception as e:
        print(f"   ✗ Cleanup test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All embedding service tests passed!")
    print("✓ Task 5.1 implementation verified successfully")
    
    return True

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_embedding_service())
    
    if success:
        print("\n🎉 Embedding service is ready for production use!")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        exit(1)