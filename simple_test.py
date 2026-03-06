#!/usr/bin/env python3
"""Simple test to verify Janet Health server works"""
import asyncio
import json
import websockets

async def test():
    print("Connecting to ws://localhost:8766...")
    
    try:
        async with websockets.connect("ws://localhost:8766") as ws:
            print("✅ Connected!")
            
            # Send registration
            print("\nSending registration...")
            await ws.send(json.dumps({
                "type": "register",
                "name": "Test Janet",
                "device_type": "Test Device",
                "platform": "Test",
                "version": "0.1.0",
                "capabilities": ["test"],
                "owner": "test",
                "device_info": {"test": "test"}
            }))
            
            # Get response
            response = await ws.recv()
            data = json.loads(response)
            print(f"✅ Registration response: {data['type']}")
            print(f"   Instance ID: {data.get('instance_id', 'N/A')}")
            
            # Send heartbeat
            print("\nSending heartbeat...")
            await ws.send(json.dumps({
                "type": "heartbeat",
                "status": "online"
            }))
            
            # Get response
            response = await ws.recv()
            data = json.loads(response)
            print(f"✅ Heartbeat response: {data['type']}")
            
            print("\n✅ All tests passed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
