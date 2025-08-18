#!/usr/bin/env python3
"""
Simple test script to check if backend can start without crashing
"""
import sys
import os
sys.path.append('.')

try:
    print("Testing backend imports...")
    from backend.main import app
    print("✓ Backend main module imported successfully")
    
    from backend.llm_service import get_llm_service
    print("✓ LLM service module imported successfully")
    
    # Test LLM service initialization
    llm_service = get_llm_service()
    if llm_service:
        print("✓ LLM service initialized successfully")
    else:
        print("⚠ LLM service initialization failed, but app should still work")
    
    print("Backend startup test completed successfully!")
    
except Exception as e:
    print(f"❌ Backend startup test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
