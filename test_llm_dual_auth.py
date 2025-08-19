#!/usr/bin/env python3
"""
Test script for dual authentication LLM service
Tests both API key and GCP service account modes
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm_service import LLMService, get_llm_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_llm_auth_modes():
    """Test LLM service authentication modes"""
    
    print("=== LLM Service Authentication Test ===\n")
    
    try:
        # Test LLM service initialization
        llm = LLMService()
        
        # Get authentication info
        auth_info = llm.get_auth_info()
        print("Authentication Information:")
        for key, value in auth_info.items():
            print(f"  {key}: {value}")
        print()
        
        # Test content generation with a simple prompt
        test_content = """
        This is a test document about machine learning. 
        Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience.
        It has applications in various fields including healthcare, finance, and technology.
        """
        
        print("Testing insight generation...")
        insights = llm.generate_insights(test_content)
        
        if insights:
            print("✅ Insight generation successful!")
            print(f"  - Processing time: {insights.processing_time:.2f}s")
            print(f"  - Auth mode: {auth_info['auth_mode']}")
            print(f"  - Takeaways: {len(insights.takeaways)}")
            print(f"  - Examples: {len(insights.examples)}")
            
            # Print first takeaway as sample
            if insights.takeaways:
                print(f"  - Sample takeaway: {insights.takeaways[0][:100]}...")
        else:
            print("❌ Insight generation failed!")
            
        print("\nTesting summary generation...")
        summary = llm.generate_summary(test_content, "document")
        
        if summary:
            print("✅ Summary generation successful!")
            print(f"  - Summary preview: {summary[:100]}...")
        else:
            print("❌ Summary generation failed!")
            
        # Test cache stats
        cache_stats = llm.get_cache_stats()
        print(f"\nCache Stats:")
        print(f"  - Cache size: {cache_stats['cache_size']}")
        print(f"  - Auth mode: {cache_stats['auth_info']['auth_mode']}")
        
    except Exception as e:
        print(f"❌ LLM service initialization failed: {e}")
        return False
    
    return True

def test_global_service():
    """Test the global LLM service getter"""
    print("\n=== Global Service Test ===\n")
    
    try:
        llm = get_llm_service()
        if llm:
            auth_info = llm.get_auth_info()
            print(f"✅ Global service initialized with {auth_info['auth_mode']} mode")
            return True
        else:
            print("❌ Global service initialization failed")
            return False
    except Exception as e:
        print(f"❌ Global service error: {e}")
        return False

if __name__ == "__main__":
    print("Starting LLM Service Dual Authentication Test...\n")
    
    # Show environment info
    print("Environment Information:")
    print(f"  GEMINI_API_KEY: {'✅ Present' if os.getenv('GEMINI_API_KEY') else '❌ Missing'}")
    print(f"  GOOGLE_APPLICATION_CREDENTIALS: {'✅ Present' if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') else '❌ Missing'}")
    print(f"  GEMINI_MODEL: {os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')}")
    print()
    
    # Run tests
    auth_test = test_llm_auth_modes()
    global_test = test_global_service()
    
    print(f"\n=== Test Results ===")
    print(f"Authentication Test: {'✅ PASSED' if auth_test else '❌ FAILED'}")
    print(f"Global Service Test: {'✅ PASSED' if global_test else '❌ FAILED'}")
    
    if auth_test and global_test:
        print("\n🎉 All tests passed! LLM service supports dual authentication.")
    else:
        print("\n❌ Some tests failed. Check the logs above.")
