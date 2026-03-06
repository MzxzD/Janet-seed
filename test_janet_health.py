#!/usr/bin/env python3
"""
Test script for Janet Health heartbeat system
Tests both local and production endpoints
"""
import asyncio
import json
import websockets
from datetime import datetime
import sys


async def test_heartbeat_server(url: str):
    """Test heartbeat server functionality"""
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print(f"{'='*60}\n")
    
    try:
        # Connect
        print("1️⃣  Connecting...")
        async with websockets.connect(url) as ws:
            print("✅ Connected successfully\n")
            
            # Test 1: Register
            print("2️⃣  Testing registration...")
            register_msg = {
                "type": "register",
                "name": "Test Janet",
                "device_type": "Test Device",
                "platform": "Test Platform",
                "version": "0.1.0",
                "capabilities": ["core", "test"],
                "location": "Test Location",
                "owner": "test-user",
                "device_info": {
                    "platform": "Test",
                    "machine": "test-machine",
                    "hostname": "test-host"
                },
                "registered_at": datetime.utcnow().isoformat()
            }
            
            await ws.send(json.dumps(register_msg))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get('type') == 'registered':
                instance_id = data.get('instance_id')
                print(f"✅ Registered successfully")
                print(f"   Instance ID: {instance_id}\n")
            else:
                print(f"❌ Registration failed: {data}")
                return False
            
            # Test 2: Heartbeat
            print("3️⃣  Testing heartbeat...")
            heartbeat_msg = {
                "type": "heartbeat",
                "status": "online",
                "metrics": {
                    "cpu_percent": 25.5,
                    "memory_percent": 45.2,
                    "disk_percent": 60.1
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await ws.send(json.dumps(heartbeat_msg))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get('type') == 'heartbeat_ack':
                print(f"✅ Heartbeat acknowledged\n")
            else:
                print(f"❌ Heartbeat failed: {data}")
                return False
            
            # Test 3: Get status
            print("4️⃣  Testing status query...")
            status_msg = {"type": "get_status"}
            
            await ws.send(json.dumps(status_msg))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get('type') == 'status':
                print(f"✅ Status received")
                print(f"   Total instances: {data.get('total', 0)}")
                print(f"   Online: {data.get('online', 0)}\n")
            else:
                print(f"❌ Status query failed: {data}")
                return False
            
            # Test 4: Unregister
            print("5️⃣  Testing unregister...")
            unregister_msg = {
                "type": "unregister",
                "instance_id": instance_id
            }
            
            await ws.send(json.dumps(unregister_msg))
            print(f"✅ Unregistered successfully\n")
            
            print(f"{'='*60}")
            print(f"✅ All tests passed for {url}")
            print(f"{'='*60}\n")
            return True
    
    except asyncio.TimeoutError:
        print(f"❌ Timeout connecting to {url}")
        print(f"   Server may not be running or DNS not propagated\n")
        return False
    except Exception as status_error:
        if "InvalidStatusCode" in str(type(status_error)):
            print(f"❌ Invalid status code: {status_error}")
            print(f"   Check if server is running and tunnel is configured\n")
            return False
    except ConnectionRefusedError:
        print(f"❌ Connection refused")
        print(f"   Server is not running on {url}\n")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_dashboard_connection(url: str):
    """Test dashboard connection"""
    print(f"\n{'='*60}")
    print(f"Testing Dashboard: {url}")
    print(f"{'='*60}\n")
    
    try:
        print("1️⃣  Connecting as dashboard...")
        async with websockets.connect(url) as ws:
            print("✅ Connected successfully\n")
            
            # Send dashboard connect
            print("2️⃣  Sending dashboard connect...")
            dashboard_msg = {"type": "dashboard_connect"}
            
            await ws.send(json.dumps(dashboard_msg))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get('type') == 'initial_state':
                print(f"✅ Received initial state")
                print(f"   Instances: {len(data.get('instances', []))}\n")
                
                print(f"{'='*60}")
                print(f"✅ Dashboard test passed")
                print(f"{'='*60}\n")
                return True
            else:
                print(f"❌ Unexpected response: {data}")
                return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("JANET HEALTH HEARTBEAT SYSTEM TEST")
    print("="*60)
    
    # Test local server
    local_url = "ws://localhost:8766"
    print(f"\n📍 Testing local server: {local_url}")
    local_result = await test_heartbeat_server(local_url)
    
    if local_result:
        # Test dashboard connection
        dashboard_result = await test_dashboard_connection(local_url)
    
    # Test production server (if available)
    production_url = "wss://janet.health"
    print(f"\n📍 Testing production server: {production_url}")
    print("   (This will fail if DNS hasn't propagated or tunnel isn't running)")
    production_result = await test_heartbeat_server(production_url)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Local server:      {'✅ PASS' if local_result else '❌ FAIL'}")
    print(f"Production server: {'✅ PASS' if production_result else '❌ FAIL (expected if not deployed)'}")
    print("="*60)
    
    if local_result:
        print("\n✅ Local server is working correctly!")
        print("\nNext steps:")
        print("1. Deploy to production server")
        print("2. Configure Cloudflare Tunnel")
        print("3. Update DNS records")
        print("4. Test production URL: wss://janet.health")
        print("5. Visit dashboard: https://janet.health")
    else:
        print("\n❌ Local server test failed")
        print("\nTroubleshooting:")
        print("1. Make sure heartbeat_server.py is running:")
        print("   python3 heartbeat_server.py")
        print("2. Check if port 8766 is available:")
        print("   lsof -i :8766")
        print("3. Check server logs for errors")
    
    return 0 if local_result else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")
        sys.exit(1)
