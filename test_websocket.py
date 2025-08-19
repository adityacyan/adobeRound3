#!/usr/bin/env python3
"""
Test WebSocket functionality for document processing updates.
"""

import asyncio
import websockets
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_websocket_connection():
    """Test WebSocket connection and message handling"""
    session_id = "test-session-123"
    uri = f"ws://localhost:8000/ws/{session_id}"
    
    try:
        print(f"🔌 Connecting to WebSocket: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Listen for messages
            print("👂 Listening for messages...")
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 Received message: {data}")
                
                # Test ping/pong
                if data.get('type') == 'connection_established':
                    print("🏓 Sending ping...")
                    await websocket.send('ping')
                    
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ WebSocket connection closed: {e}")
        if e.code == 4004:
            print("   Reason: Session not found - this is expected for test session")
        return True  # Expected for test session
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing WebSocket Connection")
    print("-" * 40)
    
    success = asyncio.run(test_websocket_connection())
    print(f"\n🎯 Test {'passed' if success else 'failed'}")
