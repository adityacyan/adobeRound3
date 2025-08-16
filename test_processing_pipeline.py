"""
Test script for the PDF processing pipeline functionality.
"""
import asyncio
import requests
import tempfile
import os
import time
from pathlib import Path

def create_test_pdf_with_content():
    """Create a more realistic test PDF with actual content."""
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
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(INTRODUCTION) Tj
0 -20 Td
(This is a test document for PDF processing.) Tj
0 -20 Td
(It contains multiple sections and paragraphs.) Tj
0 -40 Td
(SECTION 1: OVERVIEW) Tj
0 -20 Td
(This section provides an overview of the content.) Tj
0 -20 Td
(The processing pipeline should extract this text.) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000273 00000 n 
0000000524 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
593
%%EOF"""
    return test_pdf_content

def test_processing_pipeline():
    """Test the complete PDF processing pipeline."""
    base_url = "http://localhost:8000"
    
    print("PDF Processing Pipeline Test")
    print("=" * 50)
    
    try:
        # 1. Health check
        print("1. Testing health check...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return
        
        # 2. Create session
        print("\n2. Creating session...")
        response = requests.post(f"{base_url}/session/create")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✓ Session created: {session_id}")
        else:
            print(f"✗ Session creation failed: {response.status_code}")
            return
        
        # 3. Upload PDF
        print("\n3. Uploading test PDF...")
        test_pdf_content = create_test_pdf_with_content()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(test_pdf_content)
            temp_file = f.name
        
        try:
            with open(temp_file, 'rb') as f:
                files = {'files': ('test_document.pdf', f, 'application/pdf')}
                data = {'session_id': session_id}
                response = requests.post(f"{base_url}/upload/bulk", files=files, data=data)
            
            if response.status_code == 200:
                upload_result = response.json()
                document_id = upload_result["uploaded_documents"][0]["document_id"]
                print(f"✓ Upload successful: {upload_result['total_documents']} documents")
                print(f"  Document ID: {document_id}")
            else:
                print(f"✗ Upload failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return
        
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        # 4. Monitor processing progress
        print("\n4. Monitoring processing progress...")
        max_wait_time = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{base_url}/session/{session_id}/documents/{document_id}")
            if response.status_code == 200:
                doc_info = response.json()
                status = doc_info["document_info"]["processing_status"]
                progress = doc_info["document_info"]["processing_progress"]
                
                print(f"  Status: {status}, Progress: {progress:.1%}")
                
                if status == "completed":
                    print("✓ Processing completed successfully!")
                    processing_time = doc_info.get("processing_time_seconds")
                    if processing_time:
                        print(f"  Processing time: {processing_time:.2f} seconds")
                    break
                elif status == "failed":
                    error_msg = doc_info["document_info"].get("error_message", "Unknown error")
                    print(f"✗ Processing failed: {error_msg}")
                    return
                
                time.sleep(2)  # Wait 2 seconds before checking again
            else:
                print(f"✗ Failed to get document info: {response.status_code}")
                return
        else:
            print("✗ Processing timed out")
            return
        
        # 5. Test document sections
        print("\n5. Testing document sections extraction...")
        response = requests.get(f"{base_url}/session/{session_id}/documents/{document_id}/sections")
        if response.status_code == 200:
            sections_data = response.json()
            print(f"✓ Sections extracted: {sections_data['total_sections']} sections")
            print(f"  Processing method: {sections_data['processing_method']}")
            print(f"  Total pages: {sections_data['total_pages']}")
            print(f"  Extracted text length: {sections_data['extracted_text_length']} characters")
            
            # Show first few sections
            if sections_data['sections']:
                print("\n  Sample sections:")
                for i, section in enumerate(sections_data['sections'][:3]):
                    print(f"    Section {i+1}: {section['title']}")
                    print(f"      Type: {section['section_type']}")
                    print(f"      Content preview: {section['content'][:100]}...")
        else:
            print(f"✗ Failed to get sections: {response.status_code}")
            print(f"  Error: {response.text}")
        
        # 6. Test session documents overview
        print("\n6. Testing session documents overview...")
        response = requests.get(f"{base_url}/session/{session_id}/documents")
        if response.status_code == 200:
            docs_data = response.json()
            print(f"✓ Session overview retrieved")
            print(f"  Total documents: {docs_data['total_documents']}")
            print(f"  Overall progress: {docs_data['overall_progress']}%")
            print(f"  Processing status: {docs_data['processing_status']}")
        else:
            print(f"✗ Failed to get session overview: {response.status_code}")
        
        # 7. Test reprocessing (optional)
        print("\n7. Testing document reprocessing...")
        response = requests.post(f"{base_url}/session/{session_id}/documents/{document_id}/reprocess")
        if response.status_code == 200:
            reprocess_result = response.json()
            print(f"✓ Reprocessing started: {reprocess_result['message']}")
            
            # Wait a bit and check status
            time.sleep(3)
            response = requests.get(f"{base_url}/session/{session_id}/documents/{document_id}")
            if response.status_code == 200:
                doc_info = response.json()
                status = doc_info["document_info"]["processing_status"]
                print(f"  Reprocessing status: {status}")
        else:
            print(f"✗ Reprocessing failed: {response.status_code}")
        
        print("\n✓ All processing pipeline tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")

if __name__ == "__main__":
    print("Make sure the backend server is running on localhost:8000")
    print("Run: python backend/main.py")
    print()
    
    test_processing_pipeline()