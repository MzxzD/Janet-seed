"""
Janet Seed Heartbeat Client
Sends periodic heartbeats to janet.health monitoring server
"""
import asyncio
import json
import websockets
from datetime import datetime
from typing import Optional, Dict
import platform
import psutil
from pathlib import Path


class HeartbeatClient:
    """Client for sending heartbeats to janet.health server"""
    
    def __init__(
        self,
        server_url: str = "wss://janet.health",
        name: str = "Janet",
        device_type: Optional[str] = None,
        owner: str = "anonymous",
        location: Optional[str] = None,
        heartbeat_interval: int = 30
    ):
        self.server_url = server_url
        self.name = name
        self.device_type = device_type or self._detect_device_type()
        self.owner = owner
        self.location = location
        self.heartbeat_interval = heartbeat_interval
        
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.instance_id: Optional[str] = None
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        # Get Janet version
        self.version = self._get_janet_version()
        self.capabilities = self._detect_capabilities()
    
    def _detect_device_type(self) -> str:
        """Detect device type from platform"""
        system = platform.system()
        machine = platform.machine()
        
        if system == "Darwin":
            if "arm" in machine.lower():
                return "MacBook Pro (Apple Silicon)"
            return "MacBook Pro (Intel)"
        elif system == "Linux":
            return "Linux Device"
        elif system == "Windows":
            return "Windows PC"
        else:
            return f"{system} {machine}"
    
    def _get_janet_version(self) -> str:
        """Get Janet seed version"""
        try:
            version_file = Path(__file__).parent.parent / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
        except Exception:
            pass
        return "0.1.0"
    
    def _detect_capabilities(self) -> list:
        """Detect enabled capabilities"""
        capabilities = ["core", "constitution"]
        
        # Check for voice
        try:
            from src.voice import WakeWordDetector
            capabilities.append("voice")
        except ImportError:
            pass
        
        # Check for memory
        try:
            from src.memory import MemoryManager
            capabilities.append("memory")
        except ImportError:
            pass
        
        # Check for delegation
        try:
            from src.delegation import DelegationManager
            capabilities.append("delegation")
        except ImportError:
            pass
        
        return capabilities
    
    def _get_device_info(self) -> dict:
        """Get device information for instance ID generation"""
        return {
            "platform": platform.system(),
            "machine": platform.machine(),
            "hostname": platform.node()
        }
    
    def _get_metrics(self) -> dict:
        """Get current system metrics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        except Exception:
            return {}
    
    async def connect(self) -> bool:
        """Connect to heartbeat server and register"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Send registration
            registration = {
                "type": "register",
                "name": self.name,
                "device_type": self.device_type,
                "platform": platform.system(),
                "version": self.version,
                "capabilities": self.capabilities,
                "location": self.location,
                "owner": self.owner,
                "device_info": self._get_device_info(),
                "registered_at": datetime.utcnow().isoformat()
            }
            
            await self.websocket.send(json.dumps(registration))
            
            # Wait for confirmation
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=5.0
            )
            data = json.loads(response)
            
            if data.get('type') == 'registered':
                self.instance_id = data.get('instance_id')
                print(f"💚 Registered with janet.health - ID: {self.instance_id}")
                return True
            
            return False
        
        except Exception as e:
            print(f"❌ Failed to connect to heartbeat server: {e}")
            return False
    
    async def send_heartbeat(self):
        """Send a single heartbeat"""
        if not self.websocket:
            return
        
        try:
            heartbeat = {
                "type": "heartbeat",
                "status": "online",
                "metrics": self._get_metrics(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.websocket.send(json.dumps(heartbeat))
            
            # Wait for ack
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=5.0
            )
            data = json.loads(response)
            
            if data.get('type') == 'heartbeat_ack':
                return True
        
        except asyncio.TimeoutError:
            print("⚠️  Heartbeat timeout")
        except Exception as e:
            print(f"❌ Heartbeat error: {e}")
        
        return False
    
    async def heartbeat_loop(self):
        """Main heartbeat loop"""
        while self.running:
            success = await self.send_heartbeat()
            
            if not success:
                # Try to reconnect
                print("🔄 Reconnecting to heartbeat server...")
                try:
                    await self.disconnect()
                    await asyncio.sleep(5)
                    if await self.connect():
                        print("✅ Reconnected successfully")
                    else:
                        print("❌ Reconnection failed, will retry")
                except Exception as e:
                    print(f"❌ Reconnection error: {e}")
            
            await asyncio.sleep(self.heartbeat_interval)
    
    async def start(self):
        """Start sending heartbeats"""
        if self.running:
            return
        
        if not await self.connect():
            raise RuntimeError("Failed to connect to heartbeat server")
        
        self.running = True
        self.task = asyncio.create_task(self.heartbeat_loop())
        print(f"💚 Heartbeat started (interval: {self.heartbeat_interval}s)")
    
    async def stop(self):
        """Stop sending heartbeats"""
        if not self.running:
            return
        
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        await self.disconnect()
        print("💚 Heartbeat stopped")
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            try:
                # Send unregister message
                await self.websocket.send(json.dumps({
                    "type": "unregister",
                    "instance_id": self.instance_id
                }))
                await self.websocket.close()
            except Exception:
                pass
            finally:
                self.websocket = None


# Convenience functions for integration

_global_client: Optional[HeartbeatClient] = None


async def start_heartbeat(
    server_url: str = "wss://janet.health",
    name: str = "Janet",
    device_type: Optional[str] = None,
    owner: str = "anonymous",
    location: Optional[str] = None,
    heartbeat_interval: int = 30
):
    """Start global heartbeat client"""
    global _global_client
    
    if _global_client and _global_client.running:
        print("⚠️  Heartbeat already running")
        return
    
    _global_client = HeartbeatClient(
        server_url=server_url,
        name=name,
        device_type=device_type,
        owner=owner,
        location=location,
        heartbeat_interval=heartbeat_interval
    )
    
    await _global_client.start()


async def stop_heartbeat():
    """Stop global heartbeat client"""
    global _global_client
    
    if _global_client:
        await _global_client.stop()
        _global_client = None


def is_heartbeat_running() -> bool:
    """Check if heartbeat is running"""
    return _global_client is not None and _global_client.running
