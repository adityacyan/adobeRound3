#!/usr/bin/env python3
"""
Simple test for podcast generation without requiring uploaded documents.
"""

import requests
import json

def test_simple_podcast():
    """Test podcast generation with minimal setup."""
    base_url = "http://localhost:8000"
    
    print("🎙️ Simple Podcast Generation Test")
    print("=" * 40)
    
    # 1. Create session
    print("1. Creating session...")
    response = requests.post(f"{base_url}/session/create")
    if response.status_code != 200:
        print(f"❌ Failed to create session: {response.status_code}")
        return
    
    session_id = response.json()["session_id"]
    print(f"✅ Session: {session_id}")
    
    # 2. Generate podcast with simple content
    print("\n2. Generating podcast...")
    podcast_request = {
        "content": "This is a test of the podcast generation feature using Azure OpenAI TTS.",
        "use_insights": False,
        "use_dual_speaker": True
    }
    
    response = requests.post(
        f"{base_url}/session/{session_id}/podcast/generate",
        json=podcast_request,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Podcast generated successfully!")
        print(f"   Audio URL: {result['audio_url']}")
        print(f"   Speakers: {result['speakers_used']}")
        
        # 3. Test audio download
        print("\n3. Testing audio download...")
        audio_url = result['audio_url']
        audio_response = requests.get(audio_url)
        if audio_response.status_code == 200:
            print(f"✅ Audio download works! Size: {len(audio_response.content)} bytes")
        else:
            print(f"❌ Audio download failed: {audio_response.status_code}")
            
    else:
        print(f"❌ Podcast generation failed: {response.status_code}")
        if response.headers.get('content-type') == 'application/json':
            print(f"   Error: {response.json().get('detail', 'Unknown error')}")
    
    print("\n" + "=" * 40)
    print("✅ Test complete!")

if __name__ == "__main__":
    test_simple_podcast()
