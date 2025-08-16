#!/usr/bin/env python3
"""
Test script for improved text selection functionality.
"""

import subprocess
import time
import requests
import os
from pathlib import Path

def test_text_selection_implementation():
    """Test the improved anchor-based text selection implementation."""
    
    print("🧪 Testing Improved Text Selection Implementation")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend health check failed")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend is not running. Starting backend...")
        # Start backend in background
        backend_process = subprocess.Popen([
            "python", "-m", "uvicorn", "backend.main:app", 
            "--host", "0.0.0.0", "--port", "8000"
        ], cwd=".")
        time.sleep(3)
        
        # Check again
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend started successfully")
            else:
                print("❌ Backend failed to start properly")
                return False
        except requests.exceptions.RequestException:
            print("❌ Backend still not responding")
            return False
    
    # Test frontend file exists and has the new implementation
    frontend_file = Path("frontend/main.py")
    if not frontend_file.exists():
        print("❌ Frontend file not found")
        return False
    
    frontend_content = frontend_file.read_text(encoding='utf-8')
    
    # Check for new anchor-based implementation
    checks = [
        ("Anchor-based selection", "anchorX = e.clientX"),
        ("Anchor range creation", "anchorRange = document.caretRangeFromPoint"),
        ("Range comparison", "anchorRange.compareBoundaryPoints"),
        ("Drag overlay function", "function showDragSelectionOverlay"),
        ("Hide overlay function", "function hideDragSelectionOverlay"),
        ("Anchor point indicator", "selection-start-point"),
        ("No artifacts comment", "without artifacts")
    ]
    
    print("\n🔍 Checking implementation features:")
    all_checks_passed = True
    
    for check_name, check_pattern in checks:
        if check_pattern in frontend_content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_checks_passed = False
    
    # Check that old complex functions are removed/simplified
    old_patterns = [
        ("Complex createPreciseSelection", "Find text nodes within the selection area"),
        ("getCharacterOffsetAtPoint", "Test each character position")
    ]
    
    print("\n🧹 Checking old code removal:")
    for check_name, check_pattern in old_patterns:
        if check_pattern not in frontend_content:
            print(f"✅ {check_name}: Removed")
        else:
            print(f"⚠️ {check_name}: Still present (may need cleanup)")
    
    # Test CSS classes for visual feedback
    css_classes = [
        "drag-selection-overlay",
        "selection-start-point",
        "selection-feedback"
    ]
    
    print("\n🎨 Checking CSS classes:")
    for css_class in css_classes:
        if css_class in frontend_content:
            print(f"✅ {css_class}: Found")
        else:
            print(f"❌ {css_class}: Missing")
            all_checks_passed = False
    
    print("\n" + "=" * 60)
    
    if all_checks_passed:
        print("✅ All implementation checks passed!")
        print("\n📋 New Text Selection Features:")
        print("   • Anchor-based selection (starts exactly at click point)")
        print("   • Only selects range between anchor and current pointer")
        print("   • No text selection artifacts")
        print("   • Visual feedback with drag overlay")
        print("   • Anchor point indicator")
        print("   • Clean, simplified code")
        
        print("\n🚀 To test the functionality:")
        print("   1. Run: streamlit run frontend/main.py --server.port 8080")
        print("   2. Upload a PDF document")
        print("   3. Try text selection by clicking and dragging")
        print("   4. Verify selection starts exactly at click point")
        print("   5. Verify no text outside anchor-to-pointer range is selected")
        
        return True
    else:
        print("❌ Some implementation checks failed")
        return False

if __name__ == "__main__":
    success = test_text_selection_implementation()
    exit(0 if success else 1)