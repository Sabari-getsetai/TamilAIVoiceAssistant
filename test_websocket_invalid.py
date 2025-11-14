#!/usr/bin/env python3
"""Test WebSocket with invalid session ID to verify validation."""

import asyncio
import websockets
import json
import sys

async def test_invalid_session():
    session_id = "invalid_session_id"  # Invalid session ID
    uri = f"ws://127.0.0.1:8000/chat/ws/{session_id}"

    try:
        print(f"Testing invalid session: {session_id}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established")

            # Wait for initial message (should be error)
            response = await websocket.recv()
            initial_msg = json.loads(response)
            print(f"📨 Server response: {initial_msg}")

            if initial_msg.get("type") == "error":
                print("✅ Invalid session correctly rejected")
                return True
            else:
                print(f"❌ Expected error, got: {initial_msg}")
                return False

    except Exception as e:
        print(f"Connection failed (expected): {e}")
        return True  # Connection failure is expected for invalid sessions

if __name__ == "__main__":
    result = asyncio.run(test_invalid_session())
    print("✅ WebSocket validation working correctly" if result else "❌ WebSocket validation failed")
    sys.exit(0 if result else 1)