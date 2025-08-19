#!/usr/bin/env python3
"""
Simple test script to verify Azure OpenAI TTS API connection.
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_azure_openai_tts():
    """Test Azure OpenAI TTS API directly."""
    
    # Get configuration
    api_key = os.getenv("AZURE_TTS_KEY", "").strip()
    endpoint = os.getenv("AZURE_TTS_ENDPOINT", "").strip()
    deployment = os.getenv("AZURE_TTS_DEPLOYMENT", "tts-test")
    api_version = os.getenv("AZURE_TTS_API_VERSION", "2025-03-01-preview")
    
    print("🧪 Testing Azure OpenAI TTS API Connection")
    print("=" * 50)
    print(f"Endpoint: {endpoint}")
    print(f"Deployment: {deployment}")
    print(f"API Version: {api_version}")
    print(f"API Key: {api_key[:20]}..." if api_key else "❌ No API key")
    print()
    
    if not api_key or not endpoint:
        print("❌ Missing API key or endpoint")
        return False
    
    # Construct URL
    url = f"{endpoint}/openai/deployments/{deployment}/audio/speech?api-version={api_version}"
    print(f"Full URL: {url}")
    print()
    
    # Test with api-key header
    print("1. Testing with api-key header...")
    headers1 = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "tts-1",
        "input": "Hello, this is a test.",
        "voice": "alloy",
        "response_format": "mp3"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers1, json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Success with api-key header!")
                print(f"Response length: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test with Authorization Bearer header
    print("\n2. Testing with Authorization Bearer header...")
    headers2 = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers2, json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Success with Authorization Bearer header!")
                print(f"Response length: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return False

if __name__ == "__main__":
    asyncio.run(test_azure_openai_tts())
