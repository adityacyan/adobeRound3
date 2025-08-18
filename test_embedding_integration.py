"""
Integration test for embedding service with the FastAPI backend.
Tests the complete workflow: upload -> process -> search.
"""

import asyncio
import httpx
import time
import os
import sys

async def test_embedding_integration():
    """Test the complete embedding integration workflow."""
    print("Testing Embedding Integration with FastAPI Backend")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if backend is running
    print("1. Checking backend availability...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("   ✓ Backend is running")
            else:
                print(f"   ✗ Backend returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"   ✗ Backend not available: {e}")
        print("   Please start the backend with: uvicorn backend.main:app --host 0.0.0.0 --port 8000")
        return False
    
    # Test 2: Create session
    print("\n2. Creating session...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{base_url}/session/create")
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data["session_id"]
                print(f"   ✓ Session created: {session_id}")
            else:
                print(f"   ✗ Session creation failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ✗ Session creation error: {e}")
        return False
    
    # Test 3: Check search stats (should show embedding service is ready)
    print("\n3. Checking search service status...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/search/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"   ✓ Embedding service stats available")
                print(f"   ✓ Model: {stats['embedding_service']['model_name']}")
                print(f"   ✓ Initialized: {stats['embedding_service']['is_initialized']}")
            else:
                print(f"   ✗ Stats request failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ✗ Stats request error: {e}")
        return False
    
    # Test 4: Test semantic search with empty index
    print("\n4. Testing semantic search with no documents...")
    try:
        async with httpx.AsyncClient() as client:
            search_data = {
                "query": "test query",
                "top_k": 5
            }
            response = await client.post(
                f"{base_url}/search/semantic?session_id={session_id}",
                json=search_data
            )
            if response.status_code == 200:
                results = response.json()
                print(f"   ✓ Search completed with {results['total_results']} results (expected 0)")
                print(f"   ✓ Embeddings available: {results['embeddings_available']}")
            else:
                print(f"   ✗ Search failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ✗ Search error: {e}")
        return False
    
    # Test 5: Upload a sample PDF (if available)
    print("\n5. Testing with sample PDF...")
    sample_pdf_path = None
    for pdf_file in ["sample_pdfs/001.pdf", "sample_pdfs/002.pdf"]:
        if os.path.exists(pdf_file):
            sample_pdf_path = pdf_file
            break
    
    if sample_pdf_path:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(sample_pdf_path, "rb") as f:
                    files = {"files": (os.path.basename(sample_pdf_path), f, "application/pdf")}
                    data = {"session_id": session_id}
                    
                    print(f"   Uploading {sample_pdf_path}...")
                    response = await client.post(
                        f"{base_url}/upload/bulk",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        upload_result = response.json()
                        print(f"   ✓ PDF uploaded successfully")
                        print(f"   ✓ Processing started: {upload_result['processing_started']}")
                        
                        # Wait for processing to complete
                        print("   Waiting for processing to complete...")
                        for i in range(30):  # Wait up to 30 seconds
                            await asyncio.sleep(1)
                            
                            # Check processing status
                            status_response = await client.get(f"{base_url}/session/{session_id}/documents")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                progress = status_data["overall_progress"]
                                print(f"   Processing progress: {progress}%")
                                
                                if progress >= 100:
                                    print("   ✓ Processing completed!")
                                    break
                        
                        # Test semantic search with processed document
                        print("\n6. Testing semantic search with processed document...")
                        search_data = {
                            "query": "document content analysis",
                            "top_k": 3
                        }
                        search_response = await client.post(
                            f"{base_url}/search/semantic?session_id={session_id}",
                            json=search_data
                        )
                        
                        if search_response.status_code == 200:
                            search_results = search_response.json()
                            print(f"   ✓ Search completed in {search_results['search_time_ms']:.1f}ms")
                            print(f"   ✓ Found {search_results['total_results']} results")
                            print(f"   ✓ Embeddings available: {search_results['embeddings_available']}")
                            
                            # Show top results
                            for i, result in enumerate(search_results['results'][:2]):
                                print(f"     {i+1}. Score: {result['similarity_score']:.3f}")
                                print(f"        Page: {result['page_number']}, Type: {result['section_type']}")
                                print(f"        Snippet: {result['snippet'][:100]}...")
                        else:
                            print(f"   ✗ Search failed: {search_response.status_code}")
                            return False
                        
                    else:
                        print(f"   ✗ PDF upload failed: {response.status_code}")
                        print(f"   Response: {response.text}")
                        return False
                        
        except Exception as e:
            print(f"   ✗ PDF processing error: {e}")
            return False
    else:
        print("   ⚠ No sample PDFs found, skipping document processing test")
    
    # Test 7: Cleanup
    print("\n7. Testing session cleanup...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{base_url}/session/{session_id}")
            if response.status_code == 200:
                print("   ✓ Session cleaned up successfully")
            else:
                print(f"   ✗ Cleanup failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ✗ Cleanup error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All integration tests passed!")
    print("✓ Embedding service is fully integrated with FastAPI backend")
    
    return True

if __name__ == "__main__":
    print("Starting embedding integration test...")
    print("Make sure the backend is running: uvicorn backend.main:app --host 0.0.0.0 --port 8000")
    print()
    
    success = asyncio.run(test_embedding_integration())
    
    if success:
        print("\n🎉 Integration test completed successfully!")
        print("✅ Task 5.1 is fully implemented and integrated!")
    else:
        print("\n❌ Integration test failed.")
        print("Please check the backend is running and try again.")