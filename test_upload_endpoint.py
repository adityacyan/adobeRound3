"""
Test script for the PDF upload endpoint functionality.
"""
import asyncio
import httpx
import tempfile
import os
from pathlib import Path

async def test_upload_endpoint():
    """Test the bulk PDF upload endpoint."""
    base_url = "http://localhost:8000"
    
    # Create a test PDF file (minimal PDF content)
    test_pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health check
            print("Testing health check...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✓ Health check passed")
            else:
                print(f"✗ Health check failed: {response.status_code}")
                return
            
            # Create a session
            print("Creating session...")
            response = await client.post(f"{base_url}/session/create")
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data["session_id"]
                print(f"✓ Session created: {session_id}")
            else:
                print(f"✗ Session creation failed: {response.status_code}")
                return
            
            # Create temporary test PDF files
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f1:
                f1.write(test_pdf_content)
                test_file1 = f1.name
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f2:
                f2.write(test_pdf_content)
                test_file2 = f2.name
            
            try:
                # Test bulk upload
                print("Testing bulk PDF upload...")
                files = [
                    ("files", (os.path.basename(test_file1), open(test_file1, "rb"), "application/pdf")),
                    ("files", (os.path.basename(test_file2), open(test_file2, "rb"), "application/pdf"))
                ]
                data = {"session_id": session_id}
                
                response = await client.post(f"{base_url}/upload/bulk", files=files, data=data)
                
                # Close file handles
                for _, (_, file_handle, _) in files:
                    file_handle.close()
                
                if response.status_code == 200:
                    upload_result = response.json()
                    print(f"✓ Upload successful: {upload_result['total_documents']} documents uploaded")
                    print(f"  Message: {upload_result['message']}")
                else:
                    print(f"✗ Upload failed: {response.status_code}")
                    print(f"  Error: {response.text}")
                    return
                
                # Test getting session documents
                print("Testing document list retrieval...")
                response = await client.get(f"{base_url}/session/{session_id}/documents")
                if response.status_code == 200:
                    docs_data = response.json()
                    print(f"✓ Document list retrieved: {docs_data['total_documents']} documents")
                    print(f"  Processing status: {docs_data['processing_status']}")
                    print(f"  Overall progress: {docs_data['overall_progress']}%")
                else:
                    print(f"✗ Document list retrieval failed: {response.status_code}")
                
                # Test getting individual document info
                if upload_result.get("uploaded_documents"):
                    doc_id = upload_result["uploaded_documents"][0]["document_id"]
                    print(f"Testing individual document info for {doc_id}...")
                    response = await client.get(f"{base_url}/session/{session_id}/documents/{doc_id}")
                    if response.status_code == 200:
                        doc_info = response.json()
                        print(f"✓ Document info retrieved: {doc_info['document_info']['original_filename']}")
                        print(f"  File exists: {doc_info['file_exists']}")
                    else:
                        print(f"✗ Document info retrieval failed: {response.status_code}")
                
            finally:
                # Clean up test files
                try:
                    os.unlink(test_file1)
                    os.unlink(test_file2)
                except:
                    pass
            
            # Test session cleanup
            print("Testing session cleanup...")
            response = await client.delete(f"{base_url}/session/{session_id}")
            if response.status_code == 200:
                print("✓ Session cleanup successful")
            else:
                print(f"✗ Session cleanup failed: {response.status_code}")
            
            print("\n✓ All tests completed successfully!")
            
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")

if __name__ == "__main__":
    print("PDF Upload Endpoint Test")
    print("=" * 40)
    print("Make sure the backend server is running on localhost:8000")
    print("Run: python backend/main.py")
    print()
    
    asyncio.run(test_upload_endpoint())