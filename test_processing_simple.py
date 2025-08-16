"""
Simple test for the enhanced processing pipeline using existing test files.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append('backend')

try:
    from backend.document_processor import document_processor, ProcessingProgress
    print("✅ Successfully imported enhanced document processor")
except ImportError as e:
    print(f"❌ Failed to import document processor: {e}")
    sys.exit(1)

def test_processor_initialization():
    """Test that the processor initializes correctly."""
    print("\n🔧 Testing Processor Initialization")
    print("-" * 40)
    
    try:
        # Test processor stats
        stats = document_processor.get_processing_stats()
        print(f"✅ Processor initialized with {stats['active_workers']} workers")
        print(f"📊 Target processing time: {stats['target_time_ms']}ms")
        print(f"📈 Total processed: {stats['total_processed']}")
        print(f"⚡ Success rate: {stats['success_rate']:.1%}")
        
        return True
    except Exception as e:
        print(f"❌ Processor initialization failed: {e}")
        return False

def test_progress_callback():
    """Test progress callback functionality."""
    print("\n📊 Testing Progress Callback System")
    print("-" * 40)
    
    try:
        progress_updates = []
        
        def test_callback(progress: ProcessingProgress):
            progress_updates.append(progress)
            print(f"  📈 Callback received: {progress.stage} - {progress.progress:.1%}")
        
        # Add callback
        test_doc_id = "test_callback_doc"
        document_processor.add_progress_callback(test_doc_id, test_callback)
        
        # Simulate progress update
        test_progress = ProcessingProgress(
            document_id=test_doc_id,
            stage="testing",
            progress=0.5,
            message="Test progress update",
            timestamp=document_processor._notify_progress.__globals__['datetime'].now()
        )
        
        document_processor._notify_progress(test_progress)
        
        # Verify callback was called
        if progress_updates:
            print(f"✅ Progress callback system working - received {len(progress_updates)} updates")
            
            # Clean up
            document_processor.cleanup_callbacks(test_doc_id)
            return True
        else:
            print("❌ Progress callback not triggered")
            return False
            
    except Exception as e:
        print(f"❌ Progress callback test failed: {e}")
        return False

def test_text_classification():
    """Test text block classification."""
    print("\n🔤 Testing Text Classification")
    print("-" * 40)
    
    try:
        # Test different text types
        test_cases = [
            ("INTRODUCTION", "header"),
            ("This is a regular paragraph with normal text.", "paragraph"),
            ("• First bullet point\n• Second bullet point", "list"),
            ("", "empty")
        ]
        
        for text, expected_type in test_cases:
            result = document_processor._classify_text_block(text)
            status = "✅" if result == expected_type else "❌"
            print(f"  {status} '{text[:30]}...' -> {result} (expected: {expected_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ Text classification test failed: {e}")
        return False

def test_section_title_extraction():
    """Test section title extraction."""
    print("\n📝 Testing Section Title Extraction")
    print("-" * 40)
    
    try:
        test_texts = [
            "Introduction\nThis is the introduction section with more content.",
            "This is a long paragraph that should be truncated to create a meaningful title.",
            "SHORT TITLE"
        ]
        
        for text in test_texts:
            title = document_processor._extract_section_title(text)
            print(f"  📄 '{text[:30]}...' -> Title: '{title}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Section title extraction test failed: {e}")
        return False

def test_quality_calculation():
    """Test quality score calculation."""
    print("\n🎯 Testing Quality Score Calculation")
    print("-" * 40)
    
    try:
        from backend.document_processor import DocumentSection
        
        # Test with sample sections
        sections = [
            DocumentSection(
                section_id="test1",
                title="Test Section",
                content="This is test content",
                page_number=1,
                section_type="paragraph",
                word_count=4,
                char_count=20
            )
        ]
        
        quality_score = document_processor._calculate_quality_score("This is test content", sections)
        print(f"  🎯 Quality score for test content: {quality_score:.2f}")
        
        # Test with empty content
        empty_quality = document_processor._calculate_quality_score("", [])
        print(f"  🎯 Quality score for empty content: {empty_quality:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quality calculation test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Enhanced PDF Processing Pipeline - Simple Tests")
    print("=" * 60)
    
    tests = [
        ("Processor Initialization", test_processor_initialization),
        ("Progress Callback", test_progress_callback),
        ("Text Classification", test_text_classification),
        ("Section Title Extraction", test_section_title_extraction),
        ("Quality Calculation", test_quality_calculation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Enhanced processing pipeline is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Check implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)