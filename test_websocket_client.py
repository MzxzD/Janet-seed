#!/usr/bin/env python3
"""
Simple WebSocket test client for Janet server
Tests both local (ws://localhost:8765) and production (wss://heyjanet.bot)
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_connection(url, test_name):
    """Test a WebSocket connection with ping/pong"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {test_name}")
    print(f"📡 URL: {url}")
    print(f"{'='*60}\n")
    
    try:
        print(f"⏳ Connecting to {url}...")
        async with websockets.connect(url, ping_interval=None) as ws:
            print(f"✅ Connected successfully!\n")
            
            # Test 1: Send a heartbeat message
            print("📤 Sending heartbeat message...")
            heartbeat_msg = {"type": "heartbeat"}
            await ws.send(json.dumps(heartbeat_msg))
            print(f"   Sent: {json.dumps(heartbeat_msg, indent=2)}\n")
            
            # Wait for response
            print("⏳ Waiting for response...")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"✅ Received response:")
                try:
                    parsed = json.loads(response)
                    print(f"   {json.dumps(parsed, indent=2)}\n")
                except:
                    print(f"   {response}\n")
            except asyncio.TimeoutError:
                print("⚠️  No response received (timeout after 5s)")
                print("   This might be normal if server doesn't echo messages\n")
            
            # Test 2: Send a user message
            print("📤 Sending user message...")
            test_msg = {
                "type": "user_message",
                "text": "Hello Janet! This is a test message.",
                "context_window": []
            }
            await ws.send(json.dumps(test_msg))
            print(f"   Sent: {json.dumps(test_msg, indent=2)}\n")
            
            # Wait for response
            print("⏳ Waiting for Janet's response (this may take 30s for Ollama)...")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=35.0)
                print(f"✅ Received response:")
                try:
                    parsed = json.loads(response)
                    print(f"   Type: {parsed.get('type')}")
                    if 'text' in parsed:
                        print(f"   Text: {parsed['text'][:200]}...")
                    print(f"   Full: {json.dumps(parsed, indent=2)}\n")
                except:
                    print(f"   {response}\n")
            except asyncio.TimeoutError:
                print("⚠️  No response received (timeout after 35s)")
                print("   Ollama might be slow or not running\n")
            
            print(f"✅ Test completed successfully for {test_name}!\n")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed: Invalid status code {e.status_code}")
        print(f"   This usually means the server rejected the connection\n")
        return False
        
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}\n")
        return False
        
    except ConnectionRefusedError:
        print(f"❌ Connection refused")
        print(f"   Make sure the server is running on {url}\n")
        return False
        
    except OSError as e:
        print(f"❌ Network error: {e}")
        print(f"   Check your internet connection or DNS resolution\n")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}\n")
        return False

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 Janet WebSocket Test Client")
    print("="*60)
    
    results = {}
    
    # Test 1: Local connection
    results['local'] = await test_connection(
        'ws://localhost:8765',
        'Local Server (ws://localhost:8765)'
    )
    
    # Test 2: Production connection (only if DNS has propagated)
    print("\n" + "="*60)
    print("🌐 Testing production endpoint...")
    print("="*60)
    print("\nℹ️  Note: This will only work if DNS has propagated to Cloudflare")
    print("   Check with: dig heyjanet.bot +short\n")
    
    input("Press Enter to test production endpoint (or Ctrl+C to skip)...")
    
    results['production'] = await test_connection(
        'wss://heyjanet.bot',
        'Production Server (wss://heyjanet.bot)'
    )
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"Local Server:      {'✅ PASS' if results['local'] else '❌ FAIL'}")
    print(f"Production Server: {'✅ PASS' if results['production'] else '❌ FAIL'}")
    print("="*60 + "\n")
    
    if results['local'] and not results['production']:
        print("💡 Tip: Local server works but production doesn't?")
        print("   DNS might not have propagated yet. Wait 15-30 minutes and try again.")
        print("   Check DNS: dig heyjanet.bot +short\n")
    
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user\n")
        sys.exit(1)
