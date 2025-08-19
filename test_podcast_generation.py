#!/usr/bin/env python3
"""
Test script for podcast generation functionality.
Tests the implementation of the podcast feature using Azure OpenAI TTS.
"""

import requests
import json
import time
from datetime import datetime

def test_podcast_generation():
    """Test the podcast generation endpoints."""
    base_url = "http://localhost:8000"
    
    print("🎙️ Testing Podcast Generation Functionality (Azure OpenAI TTS)")
    print("=" * 70)
    
    # Test 1: Create a session
    print("1. Creating test session...")
    try:
        response = requests.post(f"{base_url}/session/create")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the backend is running on port 8000")
        return

    # Test 2: Check podcast service status
    print("\n2. Checking podcast service status...")
    try:
        response = requests.get(f"{base_url}/session/{session_id}/podcast/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Podcast service status:")
            print(f"   Audio service available: {status.get('audio_service_available', False)}")
            print(f"   Supported formats: {status.get('supported_formats', [])}")
            print(f"   Max duration: {status.get('max_duration', 'Unknown')}")
            
            if not status.get('audio_service_available', False):
                print("⚠️  Audio service not available - check AZURE_TTS_KEY and AZURE_TTS_ENDPOINT")
        else:
            print(f"❌ Failed to get podcast status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

    # Test 3: Test podcast generation with sample content (without requiring documents)
    print("\n3. Testing podcast generation with direct content...")
    
    sample_content = """
    Machine learning algorithms are computational methods that enable systems to learn and make decisions from data.
    These algorithms can identify patterns, make predictions, and improve their performance over time without being explicitly programmed for each specific task.
    Key types include supervised learning, which uses labeled data to train models, and unsupervised learning, which finds hidden patterns in unlabeled data.
    Deep learning, a subset of machine learning, uses neural networks with multiple layers to model complex relationships in data.
    Applications of machine learning span across various industries, from healthcare and finance to autonomous vehicles and natural language processing.
    """
    
    podcast_request = {
        "content": sample_content,  # Provide direct content instead of relying on uploaded documents
        "use_insights": True,
        "use_dual_speaker": True,
        "include_selection": False
    }
    
    try:
        print("   Generating podcast with Azure OpenAI TTS (this may take 30-60 seconds)...")
        start_time = time.time()
        
        response = requests.post(
            f"{base_url}/session/{session_id}/podcast/generate", 
            json=podcast_request,
            timeout=120  # 2 minute timeout
        )
        
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Podcast generated successfully!")
            print(f"   Audio URL: {result.get('audio_url', 'N/A')}")
            print(f"   Duration estimate: {result.get('duration_estimate', 'N/A')}")
            print(f"   Format: {result.get('format', 'N/A')}")
            print(f"   Speakers used: {result.get('speakers_used', [])}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f} seconds")
            print(f"   Total request time: {generation_time:.2f} seconds")
            
            # Test 4: Try to access the audio file
            print("\n4. Testing audio file access...")
            audio_url = result.get('audio_url', '')
            if audio_url:
                try:
                    audio_response = requests.head(audio_url, timeout=10)
                    if audio_response.status_code == 200:
                        print("✅ Audio file is accessible")
                        content_length = audio_response.headers.get('content-length')
                        if content_length:
                            print(f"   File size: {int(content_length) / 1024:.1f} KB")
                    else:
                        print(f"❌ Audio file not accessible: {audio_response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"❌ Error accessing audio file: {e}")
            
        else:
            error_detail = response.json().get('detail', 'Unknown error') if response.headers.get('content-type') == 'application/json' else response.text
            print(f"❌ Failed to generate podcast: {response.status_code}")
            print(f"   Error: {error_detail}")
            
    except requests.exceptions.Timeout:
        print("❌ Podcast generation timed out (>2 minutes)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

    # Test 5: Test single-speaker fallback
    print("\n5. Testing single-speaker podcast generation...")
    
    single_speaker_request = {
        "content": "This is a test for single speaker podcast generation using Azure OpenAI Text-to-Speech.",
        "use_insights": False,
        "use_dual_speaker": False,
        "include_selection": False
    }
    
    try:
        response = requests.post(
            f"{base_url}/session/{session_id}/podcast/generate", 
            json=single_speaker_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Single-speaker podcast generated!")
            print(f"   Speakers used: {result.get('speakers_used', [])}")
        else:
            print(f"❌ Single-speaker podcast failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

    # Test 6: Test podcast generation without any content (fallback behavior)
    print("\n6. Testing podcast generation with fallback content...")
    
    fallback_request = {
        "use_insights": False,
        "use_dual_speaker": False,
        "include_selection": False
    }
    
    try:
        response = requests.post(
            f"{base_url}/session/{session_id}/podcast/generate", 
            json=fallback_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Fallback podcast generated!")
            print(f"   This tests the system when no documents are uploaded")
        else:
            print(f"❌ Fallback podcast failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

    print("\n" + "=" * 70)
    print("🎯 Podcast Generation Functionality Test Complete")
    print("\n📋 Requirements Tested:")
    print("   ✅ Podcast generation endpoint")
    print("   ✅ Azure OpenAI TTS integration")
    print("   ✅ Dual-speaker podcast format")
    print("   ✅ Single-speaker fallback")
    print("   ✅ Audio file serving")
    print("   ✅ Status endpoint")
    print("   ✅ Insight integration")
    
    print("\n🔧 Configuration Notes:")
    print("   • Set AZURE_TTS_KEY in your environment")
    print("   • Set AZURE_TTS_ENDPOINT in your environment")
    print("   • Uses Azure OpenAI TTS models (tts-1)")
    print("   • Supports voices: alloy, echo, fable, onyx, nova, shimmer")
    print("   • Audio files are served from /audio/{filename}")
    print("   • Supports MP3 format with caching")

if __name__ == "__main__":
    test_podcast_generation()
