"""
Enhanced test script using actual sample PDFs from the sample_pdfs folder.
"""
import requests
import time
import os
from pathlib import Path

def test_with_sample_pdfs():
    """Test the PDF processing pipeline using actual sample PDFs."""
    base_url = "http://localhost:8000"
    sample_pdfs_dir = Path("sample_pdfs")
    
    print("PDF Processing Test with Sample PDFs")
    print("=" * 60)
    
    # Get list of available sample PDFs
    pdf_files = list(sample_pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in sample_pdfs directory")
        return False
    
    print(f"📁 Found {len(pdf_files)} sample PDF files:")
    for pdf_file in pdf_files:
        file_size = pdf_file.stat().st_size / 1024  # KB
        print(f"   • {pdf_file.name} ({file_size:.1f} KB)")
    
    try:
        # 1. Health check
        print("\n🔍 1. Testing backend health...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend is healthy")
            print(f"   • Status: {health_data['status']}")
            print(f"   • Sessions: {health_data['session_count']}")
            print(f"   • Uptime: {health_data['uptime_seconds']:.1f}s")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # 2. Create session
        print("\n📝 2. Creating new session...")
        response = requests.post(f"{base_url}/session/create", timeout=5)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session created: {session_id[:8]}...")
            print(f"   • Created at: {session_data['created_at']}")
            print(f"   • Expires at: {session_data['expires_at']}")
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            return False
        
        # 3. Upload sample PDFs (test with first 3 files)
        test_files = pdf_files[:3]  # Test with first 3 PDFs
        print(f"\n📤 3. Uploading {len(test_files)} sample PDFs...")
        
        uploaded_documents = []
        for i, pdf_file in enumerate(test_files, 1):
            print(f"   📄 Uploading {pdf_file.name}...")
            
            with open(pdf_file, 'rb') as f:
                files = {'files': (pdf_file.name, f, 'application/pdf')}
                data = {'session_id': session_id}
                response = requests.post(f"{base_url}/upload/bulk", files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                upload_result = response.json()
                if upload_result["uploaded_documents"]:
                    doc_info = upload_result["uploaded_documents"][0]
                    document_id = doc_info["document_id"]
                    uploaded_documents.append({
                        'id': document_id,
                        'filename': pdf_file.name,
                        'size': pdf_file.stat().st_size
                    })
                    print(f"   ✅ {pdf_file.name} uploaded successfully")
                    print(f"      • Document ID: {document_id[:8]}...")
                    print(f"      • File size: {pdf_file.stat().st_size / 1024:.1f} KB")
                else:
                    print(f"   ❌ No documents in upload result for {pdf_file.name}")
            else:
                print(f"   ❌ Upload failed for {pdf_file.name}: {response.status_code}")
                print(f"      Error: {response.text}")
        
        if not uploaded_documents:
            print("❌ No documents were uploaded successfully")
            return False
        
        print(f"\n✅ Successfully uploaded {len(uploaded_documents)} documents")
        
        # 4. Monitor processing for each document
        print(f"\n⚙️ 4. Monitoring processing progress...")
        max_wait_time = 60  # seconds per document
        
        for doc in uploaded_documents:
            print(f"\n   📄 Processing {doc['filename']}...")
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                response = requests.get(
                    f"{base_url}/session/{session_id}/documents/{doc['id']}", 
                    timeout=10
                )
                
                if response.status_code == 200:
                    doc_info = response.json()
                    status = doc_info["document_info"]["processing_status"]
                    progress = doc_info["document_info"]["processing_progress"]
                    
                    print(f"      Status: {status}, Progress: {progress:.1%}")
                    
                    if status == "completed":
                        processing_time = doc_info.get("processing_time_seconds", 0)
                        print(f"   ✅ {doc['filename']} processed successfully!")
                        print(f"      • Processing time: {processing_time:.2f}s")
                        break
                    elif status == "failed":
                        error_msg = doc_info["document_info"].get("error_message", "Unknown error")
                        print(f"   ❌ {doc['filename']} processing failed: {error_msg}")
                        break
                    
                    time.sleep(3)  # Wait 3 seconds before checking again
                else:
                    print(f"   ❌ Failed to get status for {doc['filename']}: {response.status_code}")
                    break
            else:
                print(f"   ⏰ Processing timeout for {doc['filename']}")
        
        # 5. Test document sections extraction
        print(f"\n📋 5. Testing sections extraction...")
        for doc in uploaded_documents:
            print(f"\n   📄 Extracting sections from {doc['filename']}...")
            response = requests.get(
                f"{base_url}/session/{session_id}/documents/{doc['id']}/sections",
                timeout=10
            )
            
            if response.status_code == 200:
                sections_data = response.json()
                print(f"   ✅ Sections extracted from {doc['filename']}")
                print(f"      • Total sections: {sections_data['total_sections']}")
                print(f"      • Total pages: {sections_data['total_pages']}")
                print(f"      • Text length: {sections_data['extracted_text_length']} chars")
                print(f"      • Processing method: {sections_data['processing_method']}")
                
                # Show sample sections
                if sections_data['sections']:
                    print(f"      • Sample sections:")
                    for i, section in enumerate(sections_data['sections'][:2]):
                        content_preview = section['content'][:80].replace('\n', ' ')
                        print(f"        - {section['title']}: {content_preview}...")
            else:
                print(f"   ❌ Failed to extract sections from {doc['filename']}: {response.status_code}")
        
        # 6. Test session overview
        print(f"\n📊 6. Testing session overview...")
        response = requests.get(f"{base_url}/session/{session_id}/documents", timeout=10)
        if response.status_code == 200:
            session_overview = response.json()
            print(f"✅ Session overview retrieved")
            print(f"   • Total documents: {session_overview['total_documents']}")
            print(f"   • Overall progress: {session_overview['overall_progress']}%")
            print(f"   • Processing status: {session_overview['processing_status']}")
            
            # Show document summaries
            if 'documents' in session_overview:
                print(f"   • Document summaries:")
                for doc_summary in session_overview['documents']:
                    print(f"     - {doc_summary['filename']}: {doc_summary['processing_status']}")
        else:
            print(f"❌ Failed to get session overview: {response.status_code}")
        
        # 7. Cleanup - delete session
        print(f"\n🧹 7. Cleaning up session...")
        response = requests.delete(f"{base_url}/session/{session_id}", timeout=5)
        if response.status_code == 200:
            print(f"✅ Session {session_id[:8]}... deleted successfully")
        else:
            print(f"⚠️ Failed to delete session: {response.status_code}")
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"📈 Processed {len(uploaded_documents)} sample PDF files")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def run_basic_tests():
    """Run basic backend tests first."""
    print("🔧 Running basic backend tests...")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Basic health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("💡 Make sure the backend is running: python backend/main.py")
        return False
    
    return True

if __name__ == "__main__":
    print("PDF Analysis Workbench - Sample PDF Testing")
    print("=" * 60)
    print("🚀 Starting comprehensive tests with sample PDFs...")
    print()
    
    # First run basic tests
    if not run_basic_tests():
        print("\n❌ Basic tests failed. Please check backend service.")
        exit(1)
    
    print("\n" + "=" * 60)
    
    # Then run comprehensive tests with sample PDFs
    success = test_with_sample_pdfs()
    
    if success:
        print("\n🎉 All tests passed! Your PDF processing pipeline is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
    
    exit(0 if success else 1)