#!/usr/bin/env python3
"""
Test script for simple native text selection functionality.
"""

import subprocess
import time
import requests
import os
from pathlib import Path

def test_simple_text_selection():
    """Test the simplified native text selection implementation."""
    
    print("🧪 Testing Simple Native Text Selection")
    print("=" * 50)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend health check failed")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend is not running")
        return False
    
    # Test frontend file has the simplified implementation
    frontend_file = Path("frontend/main.py")
    if not frontend_file.exists():
        print("❌ Frontend file not found")
        return False
    
    frontend_content = frontend_file.read_text(encoding='utf-8')
    
    # Check for simplified implementation
    checks = [
        ("Native text selection", "textLayerDiv.style.userSelect = 'text'"),
        ("Selection change listener", "document.addEventListener('selectionchange'"),
        ("Simple cursor style", "textLayerDiv.style.cursor = 'text'"),
        ("No complex overlays", "showDragSelectionOverlay" not in frontend_content),
        ("No anchor tracking", "anchorRange" not in frontend_content),
        ("No drag tracking", "isDragging" not in frontend_content)
    ]
    
    print("\n🔍 Checking simplified implementation:")
    all_checks_passed = True
    
    for check_name, check_condition in checks:
        if isinstance(check_condition, str):
            # String check
            if check_condition in frontend_content:
                print(f"✅ {check_name}: Found")
            else:
                print(f"❌ {check_name}: Missing")
                all_checks_passed = False
        else:
            # Boolean check
            if check_condition:
                print(f"✅ {check_name}: Confirmed")
            else:
                print(f"❌ {check_name}: Failed")
                all_checks_passed = False
    
    print("\n" + "=" * 50)
    
    if all_checks_passed:
        print("✅ Simple text selection implementation ready!")
        print("\n📋 How it works now:")
        print("   • Click and drag to select text (like any normal text)")
        print("   • No boxes, overlays, or complex tracking")
        print("   • Uses browser's native text selection")
        print("   • Listens for selection changes automatically")
        print("   • Clean and simple implementation")
        
        print("\n🚀 To test:")
        print("   1. Open http://localhost:8080")
        print("   2. Upload a PDF")
        print("   3. Click the 'Select Text' button")
        print("   4. Simply click and drag to select text")
        print("   5. Text selection works like any normal webpage!")
        
        return True
    else:
        print("❌ Some implementation checks failed")
        return False

if __name__ == "__main__":
    success = test_simple_text_selection()
    exit(0 if success else 1)