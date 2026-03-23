#!/usr/bin/env python3
"""
Test Pixel-to-Cursor relay (Courier).
1. Send pixel_forward_to_cursor via WebSocket
2. Pop from pixel inbox via pixel_inbox module
Run with: janet-seed on 8765, then: python3 test_pixel_to_cursor.py
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import websockets
except ImportError:
    print("pip install websockets")
    sys.exit(1)

from pixel_inbox import read_inbox, pop_inbox, PIXEL_INBOX_PATH


async def main():
    url = os.environ.get("JANET_WS_URL", "ws://127.0.0.1:8765")
    print(f"Testing Pixel-to-Cursor relay")
    print(f"  WebSocket: {url}")
    print(f"  Inbox: {PIXEL_INBOX_PATH}")
    print()

    # 1. Send pixel_forward_to_cursor
    print("1. Sending pixel_forward_to_cursor...")
    try:
        async with websockets.connect(url, open_timeout=5) as ws:
            msg = {"type": "pixel_forward_to_cursor", "text": "Hello from Pixel! Test message for Cursor."}
            await ws.send(json.dumps(msg))
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(resp)
                if data.get("type") == "pixel_forward_ack":
                    print("   OK: pixel_forward_ack received")
                else:
                    print("   Response:", data)
            except asyncio.TimeoutError:
                print("   (no ack; server may need restart to support pixel_forward_to_cursor)")
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")
        print("   Is janet-seed running on 8765? Restart: cd janet-seed && python3 simple_websocket_server.py")
        return 1

    # 2. List inbox
    entries = read_inbox()
    print(f"2. Inbox count: {len(entries)}")
    for i, e in enumerate(entries):
        print(f"   [{i}] {e.get('text', '')[:50]}...")

    # 3. Pop
    popped = pop_inbox()
    if popped:
        print(f"3. Popped: {popped.get('text', '')[:50]}...")
        print("   OK: Pixel-to-Cursor relay works!")
    else:
        print("3. Pop returned None (inbox empty?)")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
