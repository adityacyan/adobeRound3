"""
Test script for enhanced PDF processing pipeline.
Tests the new document processor with performance and progress tracking.
"""

import asyncio
import time
import tempfile
import os
from pathlib import Path
import sys

# Add backend to path
sys.path.append('backend')

from backend.document_processor import document_processor, ProcessingProgress

async def test_processing_pipeline():
    """Test the enhanced processing pipeline."""
    print("Testing Enhanced PDF Processing Pipeline")
    print("=" * 50)
    
    # Test with a simple PDF (we'll create a mock one for testing)
    test_pdf_path = create_test_pdf()
    
    if not test_pdf_path:
        print("❌ Could not create test PDF")
        return False
    
    try:
        # Test progress tracking
        progress_updates = []
        
        def progress_callback(progress: ProcessingProgress):
            progress_updates.append(progress)
            print(f"📊 Progress: {progress.stage} - {progress.progress:.1%} - {progress.message}")
        
        # Register callback
        test_doc_id = "test_document_123"
        document_processor.add_progress_callback(test_doc_id, progress_callback)
        
        # Process document
        start_time = time.time()
        print(f"🚀 Starting processing of test PDF...")
        
        processed_doc = await document_processor.process_document_async(
            pdf_path=test_pdf_path,
            document_id=test_doc_id,
            filename="test.pdf"
        )
        
        processing_time = time.time() - start_time
        
        # Verify results
        print(f"\n✅ Processing completed in {processing_time:.2f} seconds")
        print(f"📄 Document ID: {processed_doc.document_id}")
        print(f"📊 Total pages: {processed_doc.total_pages}")
        print(f"🔤 Extracted text length: {processed_doc.extracted_text_length}")
        print(f"📑 Number of sections: {len(processed_doc.sections)}")
        print(f"⚡ Processing method: {processed_doc.processing_method}")
        print(f"🎯 Quality score: {processed_doc.quality_score:.2f}")
        print(f"⏱️ Processing time: {processed_doc.processing_time_ms}ms")
        
        # Check performance target (1 second)
        meets_target = processed_doc.processing_time_ms <= 1200  # Allow 20% tolerance
        print(f"🎯 Meets 1-second target: {'✅ Yes' if meets_target else '❌ No'}")
        
        # Verify progress updates
        print(f"\n📈 Progress updates received: {len(progress_updates)}")
        for i, update in enumerate(progress_updates):
            print(f"  {i+1}. {update.stage}: {update.progress:.1%} - {update.message}")
        
        # Test processing stats
        stats = document_processor.get_processing_stats()
        print(f"\n📊 Processing Statistics:")
        print(f"  Total processed: {stats['total_processed']}")
        print(f"  Average time: {stats['average_time_ms']:.0f}ms")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print(f"  Performance ratio: {stats['performance_ratio']:.2f}")
        
        # Verify sections have proper metadata
        if processed_doc.sections:
            sample_section = processed_doc.sections[0]
            print(f"\n📑 Sample section:")
            print(f"  ID: {sample_section.section_id}")
            print(f"  Title: {sample_section.title}")
            print(f"  Type: {sample_section.section_type}")
            print(f"  Word count: {sample_section.word_count}")
            print(f"  Confidence: {sample_section.confidence}")
            print(f"  Content preview: {sample_section.content[:100]}...")
        
        # Clean up
        document_processor.cleanup_callbacks(test_doc_id)
        
        return True
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return False
    
    finally:
        # Clean up test file
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)

def create_test_pdf():
    """Create a simple test PDF for processing."""
    try:
        import fitz  # PyMuPDF
        
        # Create a simple PDF with text
        doc = fitz.open()  # New empty document
        page = doc.new_page()  # Add a page
        
        # Add some text content
        text_content = """
        Test Document Title
        
        This is a test document for the PDF processing pipeline.
        
        Section 1: Introduction
        This section contains introductory text that should be properly extracted
        and processed by the enhanced document processor.
        
        Section 2: Main Content
        • This is a bullet point
        • Another bullet point with more content
        • Third bullet point
        
        The processor should identify different section types including headers,
        paragraphs, and lists. It should also calculate quality scores and
        processing times to meet the 1-second target.
        
        Conclusion
        This concludes the test document.
        """
        
        # Insert text
        page.insert_text((50, 50), text_content, fontsize=12)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        doc.save(temp_file.name)
        doc.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Failed to create test PDF: {e}")
        return None

async def test_concurrent_processing():
    """Test concurrent processing of multiple documents."""
    print("\n" + "=" * 50)
    print("Testing Concurrent Processing")
    print("=" * 50)
    
    # Create multiple test PDFs
    test_files = []
    for i in range(3):
        test_pdf = create_test_pdf()
        if test_pdf:
            test_files.append(test_pdf)
    
    if not test_files:
        print("❌ Could not create test PDFs")
        return False
    
    try:
        # Process all documents concurrently
        tasks = []
        start_time = time.time()
        
        for i, pdf_path in enumerate(test_files):
            task = document_processor.process_document_async(
                pdf_path=pdf_path,
                document_id=f"concurrent_test_{i}",
                filename=f"test_{i}.pdf"
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]
        
        print(f"✅ Processed {len(successful)} documents successfully")
        print(f"❌ Failed to process {len(failed)} documents")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        print(f"📊 Average time per document: {total_time/len(test_files):.2f} seconds")
        
        # Check if concurrent processing is faster than sequential
        expected_sequential_time = len(test_files) * 1.0  # Assuming 1 second per PDF
        efficiency = expected_sequential_time / total_time
        print(f"🚀 Concurrency efficiency: {efficiency:.2f}x")
        
        return len(failed) == 0
        
    except Exception as e:
        print(f"❌ Concurrent processing test failed: {e}")
        return False
    
    finally:
        # Clean up test files
        for test_file in test_files:
            if os.path.exists(test_file):
                os.remove(test_file)

async def main():
    """Run all tests."""
    print("🧪 Enhanced PDF Processing Pipeline Tests")
    print("=" * 60)
    
    # Test basic processing
    test1_passed = await test_processing_pipeline()
    
    # Test concurrent processing
    test2_passed = await test_concurrent_processing()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    print(f"Basic Processing: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Concurrent Processing: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    overall_success = test1_passed and test2_passed
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)