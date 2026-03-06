#!/usr/bin/env python3
"""
Janet Seed Heartbeat Server
Monitors health and status of Janet seed instances across devices
Accessible at: https://janet.health
"""
import asyncio
import json
import websockets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import hashlib
import secrets
from dataclasses import dataclass, asdict
from collections import defaultdict

# Store for registered Janet instances
janet_instances: Dict[str, 'JanetInstance'] = {}
# Store for WebSocket connections (for dashboard clients)
dashboard_clients = set()
# Store for heartbeat history
heartbeat_history = defaultdict(list)

# Configuration
HEARTBEAT_TIMEOUT = 60  # seconds - mark as offline if no heartbeat
HEARTBEAT_HISTORY_LIMIT = 100  # Keep last N heartbeats per instance
DATA_DIR = Path.home() / ".janet" / "heartbeat_server"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class JanetInstance:
    """Represents a registered Janet seed instance"""
    instance_id: str
    name: str
    device_type: str  # e.g., "iPhone", "MacBook Pro", "Surface Duo"
    platform: str  # e.g., "iOS", "macOS", "Linux"
    version: str  # Janet seed version
    capabilities: list  # List of enabled capabilities
    location: Optional[str]  # Optional location/description
    owner_id: str  # Hashed owner identifier
    registered_at: str
    last_heartbeat: str
    status: str  # "online", "offline", "degraded"
    websocket: Optional[object] = None
    
    def to_dict(self):
        """Convert to dictionary, excluding websocket"""
        data = asdict(self)
        data.pop('websocket', None)
        return data
    
    def is_online(self) -> bool:
        """Check if instance is online based on last heartbeat"""
        if not self.last_heartbeat:
            return False
        last_beat = datetime.fromisoformat(self.last_heartbeat)
        return (datetime.utcnow() - last_beat).total_seconds() < HEARTBEAT_TIMEOUT


def generate_instance_id(device_info: dict) -> str:
    """Generate unique instance ID from device info"""
    data = json.dumps(device_info, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def generate_owner_id(owner_info: str) -> str:
    """Generate hashed owner ID for privacy"""
    return hashlib.sha256(owner_info.encode()).hexdigest()[:16]


async def broadcast_to_dashboards(message: dict):
    """Broadcast update to all connected dashboard clients"""
    if not dashboard_clients:
        return
    
    message_json = json.dumps(message)
    disconnected = set()
    
    for client in dashboard_clients:
        try:
            await client.send(message_json)
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(client)
    
    # Remove disconnected clients
    for client in disconnected:
        dashboard_clients.discard(client)


async def handle_janet_client(websocket):
    """Handle WebSocket connection from Janet seed instance or dashboard"""
    client_type = None
    instance_id = None
    
    print(f"📱 New connection from {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                if msg_type == 'register':
                    # Janet instance registering
                    client_type = 'janet'
                    device_info = data.get('device_info', {})
                    instance_id = generate_instance_id(device_info)
                    
                    # Create or update instance
                    instance = JanetInstance(
                        instance_id=instance_id,
                        name=data.get('name', 'Unnamed Janet'),
                        device_type=data.get('device_type', 'Unknown'),
                        platform=data.get('platform', 'Unknown'),
                        version=data.get('version', '0.0.0'),
                        capabilities=data.get('capabilities', []),
                        location=data.get('location'),
                        owner_id=generate_owner_id(data.get('owner', 'anonymous')),
                        registered_at=data.get('registered_at', datetime.utcnow().isoformat()),
                        last_heartbeat=datetime.utcnow().isoformat(),
                        status='online',
                        websocket=websocket
                    )
                    
                    janet_instances[instance_id] = instance
                    
                    print(f"✅ Registered: {instance.name} ({instance.device_type}) - ID: {instance_id}")
                    
                    # Send registration confirmation
                    await websocket.send(json.dumps({
                        'type': 'registered',
                        'instance_id': instance_id,
                        'timestamp': datetime.utcnow().isoformat()
                    }))
                    
                    # Broadcast update to dashboards
                    await broadcast_to_dashboards({
                        'type': 'instance_update',
                        'instance': instance.to_dict()
                    })
                
                elif msg_type == 'heartbeat':
                    # Heartbeat from Janet instance
                    if instance_id and instance_id in janet_instances:
                        instance = janet_instances[instance_id]
                        instance.last_heartbeat = datetime.utcnow().isoformat()
                        instance.status = data.get('status', 'online')
                        
                        # Store heartbeat in history
                        heartbeat_data = {
                            'timestamp': instance.last_heartbeat,
                            'status': instance.status,
                            'metrics': data.get('metrics', {})
                        }
                        heartbeat_history[instance_id].append(heartbeat_data)
                        
                        # Trim history
                        if len(heartbeat_history[instance_id]) > HEARTBEAT_HISTORY_LIMIT:
                            heartbeat_history[instance_id] = heartbeat_history[instance_id][-HEARTBEAT_HISTORY_LIMIT:]
                        
                        # Send acknowledgment
                        await websocket.send(json.dumps({
                            'type': 'heartbeat_ack',
                            'timestamp': datetime.utcnow().isoformat()
                        }))
                        
                        # Broadcast to dashboards
                        await broadcast_to_dashboards({
                            'type': 'heartbeat',
                            'instance_id': instance_id,
                            'status': instance.status,
                            'timestamp': instance.last_heartbeat
                        })
                
                elif msg_type == 'dashboard_connect':
                    # Dashboard client connecting
                    client_type = 'dashboard'
                    dashboard_clients.add(websocket)
                    
                    print(f"📊 Dashboard connected from {websocket.remote_address}")
                    
                    # Send current state
                    instances_list = [inst.to_dict() for inst in janet_instances.values()]
                    await websocket.send(json.dumps({
                        'type': 'initial_state',
                        'instances': instances_list,
                        'timestamp': datetime.utcnow().isoformat()
                    }))
                
                elif msg_type == 'get_status':
                    # Status request (can be from anyone)
                    instances_list = [inst.to_dict() for inst in janet_instances.values()]
                    await websocket.send(json.dumps({
                        'type': 'status',
                        'instances': instances_list,
                        'total': len(instances_list),
                        'online': sum(1 for inst in janet_instances.values() if inst.is_online()),
                        'timestamp': datetime.utcnow().isoformat()
                    }))
                
                elif msg_type == 'get_history':
                    # Get heartbeat history for an instance
                    req_instance_id = data.get('instance_id')
                    if req_instance_id in heartbeat_history:
                        await websocket.send(json.dumps({
                            'type': 'history',
                            'instance_id': req_instance_id,
                            'history': heartbeat_history[req_instance_id],
                            'timestamp': datetime.utcnow().isoformat()
                        }))
                
                elif msg_type == 'unregister':
                    # Janet instance unregistering
                    if instance_id and instance_id in janet_instances:
                        instance = janet_instances[instance_id]
                        instance.status = 'offline'
                        
                        print(f"👋 Unregistered: {instance.name} - ID: {instance_id}")
                        
                        # Broadcast to dashboards
                        await broadcast_to_dashboards({
                            'type': 'instance_offline',
                            'instance_id': instance_id,
                            'timestamp': datetime.utcnow().isoformat()
                        })
                
                else:
                    print(f"⚠️  Unknown message type: {msg_type}")
            
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON: {message}")
            except Exception as e:
                print(f"❌ Error handling message: {e}")
                import traceback
                traceback.print_exc()
    
    except websockets.exceptions.ConnectionClosed:
        print(f"📱 Connection closed: {websocket.remote_address}")
    finally:
        # Cleanup
        if client_type == 'dashboard':
            dashboard_clients.discard(websocket)
        elif client_type == 'janet' and instance_id:
            if instance_id in janet_instances:
                janet_instances[instance_id].status = 'offline'
                await broadcast_to_dashboards({
                    'type': 'instance_offline',
                    'instance_id': instance_id,
                    'timestamp': datetime.utcnow().isoformat()
                })


async def cleanup_stale_instances():
    """Periodically mark stale instances as offline"""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        
        now = datetime.utcnow()
        for instance_id, instance in janet_instances.items():
            if instance.status == 'online' and not instance.is_online():
                instance.status = 'offline'
                print(f"⏰ Marked offline (timeout): {instance.name} - ID: {instance_id}")
                
                await broadcast_to_dashboards({
                    'type': 'instance_offline',
                    'instance_id': instance_id,
                    'timestamp': now.isoformat()
                })


async def save_state_periodically():
    """Periodically save state to disk"""
    while True:
        await asyncio.sleep(300)  # Save every 5 minutes
        
        try:
            state_file = DATA_DIR / "instances.json"
            instances_data = {
                iid: inst.to_dict() 
                for iid, inst in janet_instances.items()
            }
            
            with open(state_file, 'w') as f:
                json.dump({
                    'instances': instances_data,
                    'saved_at': datetime.utcnow().isoformat()
                }, f, indent=2)
            
            print(f"💾 State saved: {len(instances_data)} instances")
        except Exception as e:
            print(f"❌ Error saving state: {e}")


def load_state():
    """Load saved state from disk"""
    state_file = DATA_DIR / "instances.json"
    if not state_file.exists():
        return
    
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        for iid, inst_data in data.get('instances', {}).items():
            # Mark all loaded instances as offline initially
            inst_data['status'] = 'offline'
            inst_data['websocket'] = None
            janet_instances[iid] = JanetInstance(**inst_data)
        
        print(f"📂 Loaded {len(janet_instances)} instances from disk")
    except Exception as e:
        print(f"❌ Error loading state: {e}")


async def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║              💚 JANET SEED HEARTBEAT SERVER 💚                        ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("")
    print("✅ Starting heartbeat server...")
    print("📡 Listening on: ws://0.0.0.0:8766")
    print("🌐 Public URL: wss://janet.health (via Cloudflare Tunnel)")
    print("")
    print("📊 Dashboard: https://janet.health")
    print("💚 Monitoring Janet seed instances worldwide")
    print("")
    
    # Load saved state
    load_state()
    
    print("✅ Server ready! Waiting for connections...")
    print("")
    
    # Start background tasks
    cleanup_task = asyncio.create_task(cleanup_stale_instances())
    save_task = asyncio.create_task(save_state_periodically())
    
    # Start WebSocket server
    async with websockets.serve(handle_janet_client, "0.0.0.0", 8766):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
