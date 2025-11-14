#!/usr/bin/env python3
"""Simple WebSocket test for session validation."""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    session_id = "1da7d374-1e20-4dba-b6ba-b076c818d86b"  # Database-generated session
    uri = f"ws://127.0.0.1:8000/chat/ws/{session_id}"

    try:
        print(f"Connecting to: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established")

            # Wait for initial connection message
            response = await websocket.recv()
            initial_msg = json.loads(response)
            print(f"📨 Initial message: {initial_msg}")

            if initial_msg.get("type") == "status":
                print("✅ Session validation successful")
                return True
            elif initial_msg.get("type") == "error":
                print(f"❌ Session validation failed: {initial_msg}")
                return False
            else:
                print(f"⚠️ Unexpected initial message: {initial_msg}")
                return False

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    sys.exit(0 if result else 1)