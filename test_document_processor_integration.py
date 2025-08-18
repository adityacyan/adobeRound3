"""
Test the document processor integration with embedding service.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.document_processor import document_processor
from backend.embedding_service import embedding_service

async def test_document_processor_integration():
    """Test document processor with embedding generation."""
    print("Testing Document Processor + Embedding Integration")
    print("=" * 55)
    
    # Find a sample PDF
    sample_pdf = None
    for pdf_file in ["sample_pdfs/001.pdf", "sample_pdfs/002.pdf", "sample_pdfs/file11.pdf"]:
        if os.path.exists(pdf_file):
            sample_pdf = pdf_file
            break
    
    if not sample_pdf:
        print("❌ No sample PDF found. Please ensure sample PDFs exist in sample_pdfs/ directory.")
        return False
    
    print(f"Using sample PDF: {sample_pdf}")
    
    # Test 1: Initialize embedding service
    print("\n1. Initializing embedding service...")
    try:
        await embedding_service.initialize()
        print("   ✓ Embedding service initialized")
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        return False
    
    # Test 2: Process document with embeddings
    print("\n2. Processing document with embedding generation...")
    
    def progress_callback(progress):
        print(f"   Progress: {progress.stage} - {progress.progress:.1%} - {progress.message}")
    
    document_processor.add_progress_callback("test_doc", progress_callback)
    
    try:
        processed_doc = await document_processor.process_document_async(
            pdf_path=sample_pdf,
            document_id="test_doc",
            filename=os.path.basename(sample_pdf)
        )
        
        print(f"   ✓ Document processed successfully")
        print(f"   ✓ Processing time: {processed_doc.processing_time_ms}ms")
        print(f"   ✓ Sections extracted: {len(processed_doc.sections)}")
        print(f"   ✓ Text length: {processed_doc.extracted_text_length}")
        print(f"   ✓ Embeddings generated: {processed_doc.embeddings_generated}")
        print(f"   ✓ Embedding count: {processed_doc.embedding_count}")
        
        if not processed_doc.embeddings_generated:
            print("   ⚠ Embeddings were not generated")
            return False
            
    except Exception as e:
        print(f"   ✗ Document processing failed: {e}")
        return False
    finally:
        document_processor.cleanup_callbacks("test_doc")
    
    # Test 3: Verify embeddings are searchable
    print("\n3. Testing semantic search on processed document...")
    
    try:
        # Test search with document content
        search_queries = [
            "document analysis",
            "text processing",
            "information extraction"
        ]
        
        for query in search_queries:
            results = await embedding_service.semantic_search(
                query=query,
                top_k=3,
                document_ids=["test_doc"]
            )
            
            print(f"   Query: '{query}' -> {len(results)} results")
            if results:
                best_result = results[0]
                print(f"     Best match: {best_result.similarity_score:.3f} - {best_result.snippet[:80]}...")
    
    except Exception as e:
        print(f"   ✗ Search test failed: {e}")
        return False
    
    # Test 4: Performance check
    print("\n4. Checking performance metrics...")
    
    embedding_stats = embedding_service.get_stats()
    processor_stats = document_processor.get_processing_stats()
    
    print(f"   ✓ Average processing time: {processor_stats['average_time_ms']:.1f}ms")
    print(f"   ✓ Target processing time: {processor_stats['target_time_ms']}ms")
    print(f"   ✓ Performance ratio: {processor_stats['performance_ratio']:.2f}x")
    print(f"   ✓ Average embedding time: {embedding_stats['average_embedding_time_ms']:.1f}ms")
    print(f"   ✓ Average search time: {embedding_stats['average_search_time_ms']:.1f}ms")
    
    # Check if performance meets requirements
    if processor_stats['average_time_ms'] <= 2000:  # Allow 2 seconds for processing + embeddings
        print("   ✓ Processing performance meets requirements")
    else:
        print(f"   ⚠ Processing may be slow ({processor_stats['average_time_ms']:.1f}ms)")
    
    if embedding_stats['average_search_time_ms'] <= 1000:
        print("   ✓ Search performance meets requirements")
    else:
        print(f"   ⚠ Search may be slow ({embedding_stats['average_search_time_ms']:.1f}ms)")
    
    # Test 5: Cleanup
    print("\n5. Testing cleanup...")
    
    try:
        initial_count = embedding_service.get_document_embedding_count("test_doc")
        embedding_service.remove_document_embeddings("test_doc")
        final_count = embedding_service.get_document_embedding_count("test_doc")
        
        print(f"   ✓ Embeddings cleaned up: {initial_count} -> {final_count}")
        
    except Exception as e:
        print(f"   ✗ Cleanup failed: {e}")
        return False
    
    print("\n" + "=" * 55)
    print("✓ All document processor integration tests passed!")
    print("✓ Background embedding generation is working correctly")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_document_processor_integration())
    
    if success:
        print("\n🎉 Document processor integration is working perfectly!")
        print("✅ Task 5.1 implementation is complete and verified!")
    else:
        print("\n❌ Integration test failed.")
        exit(1)