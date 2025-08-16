"""
Basic tests for the FastAPI backend to verify core functionality.
"""
import time
from datetime import datetime
import pytest
import requests


# Test configuration
BACKEND_URL = "http://localhost:8000"

def test_backend_health():
    """Test that the backend health endpoint is working."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "session_count" in data
        assert "uptime_seconds" in data
        
        print("✅ Health check passed")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_session_management():
    """Test session creation and management."""
    try:
        # Create a new session
        response = requests.post(f"{BACKEND_URL}/session/create")
        assert response.status_code == 200
        
        session_data = response.json()
        session_id = session_data["session_id"]
        assert "session_id" in session_data
        assert "created_at" in session_data
        assert "expires_at" in session_data
        
        print(f"✅ Session created: {session_id[:8]}...")
        
        # Get session information
        response = requests.get(f"{BACKEND_URL}/session/{session_id}")
        assert response.status_code == 200
        
        session_info = response.json()
        assert session_info["session_id"] == session_id
        assert session_info["documents"] == []
        assert session_info["processing_status"] == "idle"
        
        print("✅ Session retrieval passed")
        
        # Delete the session
        response = requests.delete(f"{BACKEND_URL}/session/{session_id}")
        assert response.status_code == 200
        
        # Verify session is deleted
        response = requests.get(f"{BACKEND_URL}/session/{session_id}")
        assert response.status_code == 404
        
        print("✅ Session deletion passed")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Session management test failed: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Session management assertion failed: {e}")
        return False

def test_detailed_health():
    """Test detailed health endpoint."""
    try:
        response = requests.get(f"{BACKEND_URL}/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "system_info" in data
        assert "services" in data
        
        # Check system info structure
        system_info = data["system_info"]
        assert "session_count" in system_info
        assert "uptime_seconds" in system_info
        assert "environment" in system_info
        
        # Check services status
        services = data["services"]
        assert services["session_management"] == "operational"
        assert services["api_gateway"] == "operational"
        
        print("✅ Detailed health check passed")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Detailed health check failed: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Detailed health assertion failed: {e}")
        return False

def run_all_tests():
    """Run all backend tests."""
    print("🧪 Running backend tests...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_backend_health),
        ("Session Management", test_session_management),
        ("Detailed Health", test_detailed_health)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Check backend service.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)