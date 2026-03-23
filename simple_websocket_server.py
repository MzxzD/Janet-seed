#!/usr/bin/env python3
"""
Simple WebSocket server for Call Janet iPhone app
Handles basic conversation with Ollama LLM
Supports pixel_forward_to_cursor for Pixel-to-Cursor closed loop.
Supports shell_command for Janet Terminal (remote shell execution).
Optional mDNS advertising (_janet._tcp) for auto-discovery.
"""
import argparse
import asyncio
import json
import uuid
import websockets
import subprocess
from datetime import datetime

from pixel_inbox import append_inbox as _append_pixel_inbox

# mDNS advertiser (optional)
try:
    from mdns_advertiser import JanetMdnsAdvertiser
    MDNS_AVAILABLE = True
except ImportError:
    MDNS_AVAILABLE = False
from src.handlers.shortcut_handler import ShortcutHandler

# Import Red Thread event for constitutional integration (Axiom 8)
try:
    from src.core.janet_core import RED_THREAD_EVENT
except ImportError:
    try:
        from core.janet_core import RED_THREAD_EVENT
    except ImportError:
        RED_THREAD_EVENT = None

# Store for conversation context
conversations = {}

# Initialize shortcut handler
shortcut_handler = None

# Server config (set from main)
ALLOW_SHELL = False


async def run_shell_command(cmd: str):
    """Execute shell command on host. Returns (stdout, stderr, exit_code)."""
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        return (
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
            proc.returncode or 0,
        )
    except asyncio.TimeoutError:
        return ("", "Command timed out after 30s", -1)
    except Exception as e:
        return ("", str(e), -1)


async def query_ollama(prompt: str) -> str:
    """Query Ollama LLM"""
    try:
        result = subprocess.run(
            ['ollama', 'run', 'qwen2', prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip() or "I'm here to help!"
    except Exception as e:
        return f"Error querying LLM: {e}"

async def handle_client(websocket):
    """Handle WebSocket client connection"""
    global shortcut_handler
    
    client_id = id(websocket)
    conversations[client_id] = []
    
    print(f"📱 Client connected: {client_id}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                print(f"📨 Received: {msg_type}")
                
                # Axiom 8: Red Thread Protocol - block all operations when active
                if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
                    await websocket.send(json.dumps({
                        "type": "red_thread_active",
                        "message": "Red Thread active - operations paused"
                    }))
                    continue
                
                if msg_type == 'user_message':
                    # User sent a message
                    user_text = data.get('text', '')
                    context_window = data.get('context_window', [])
                    
                    print(f"💬 User: {user_text}")
                    
                    # Axiom 8: Red Thread - detect "red thread" and activate
                    if "red thread" in user_text.lower():
                        if RED_THREAD_EVENT:
                            RED_THREAD_EVENT.set()
                        await websocket.send(json.dumps({
                            "type": "red_thread_ack",
                            "message": "Red Thread activated - all operations paused"
                        }))
                        continue
                    
                    # Query Ollama
                    response_text = await query_ollama(user_text)
                    print(f"🤖 Janet: {response_text[:100]}...")
                    
                    # Send response
                    response = {
                        'type': 'janet_response',
                        'text': response_text,
                        'timestamp': datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(response))
                
                elif msg_type == 'end_conversation':
                    # "Thank you, Janet!" - store in Green Vault
                    context = data.get('context_window', [])
                    
                    print(f"💚 Storing conversation in Green Vault ({len(context)} messages)")
                    
                    # Create summary
                    summary_text = f"Conversation with {len(context)} messages"
                    topics = ["General"]
                    
                    # Send summary back
                    response = {
                        'type': 'summary',
                        'summary': {
                            'id': str(client_id),
                            'timestamp': datetime.now().isoformat(),
                            'topics': topics,
                            'summary': summary_text,
                            'emotionalTone': 'neutral',
                            'actionableInsights': []
                        }
                    }
                    await websocket.send(json.dumps(response))
                
                elif msg_type == 'get_green_vault_summaries':
                    # Request summaries
                    print("📚 Sending Green Vault summaries")
                    
                    response = {
                        'type': 'summaries',
                        'summaries': []  # Empty for now
                    }
                    await websocket.send(json.dumps(response))
                
                elif msg_type == 'heartbeat':
                    # Heartbeat
                    await websocket.send(json.dumps({'type': 'heartbeat_ack'}))

                elif msg_type == 'pixel_forward_to_cursor':
                    # Pixel-to-Cursor relay (Courier / closed loop)
                    user_text = data.get('text', '')
                    entry = {
                        'id': str(uuid.uuid4()),
                        'text': user_text,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'pixel',
                    }
                    _append_pixel_inbox(entry)
                    print(f"📤 Pixel -> Cursor: {user_text[:60]}...")
                    response = {
                        'type': 'pixel_forward_ack',
                        'id': entry['id'],
                        'message': 'Queued for Cursor',
                    }
                    await websocket.send(json.dumps(response))
                
                elif msg_type in ['recognize_intent', 'create_shortcut', 'build_shortcut',
                                   'get_shortcuts', 'save_shortcut', 'delete_shortcut']:
                    # Dynamic Shortcuts
                    print(f"🔗 Handling shortcut message: {msg_type}")
                    response = await shortcut_handler.handle_message(data)
                    await websocket.send(json.dumps(response))

                elif msg_type == 'shell_command':
                    # Janet Terminal: remote shell execution
                    if not ALLOW_SHELL:
                        await websocket.send(json.dumps({
                            "type": "shell_output",
                            "stdout": "",
                            "stderr": "Shell execution disabled. Start with --allow-shell to enable.",
                            "exit_code": -1,
                        }))
                    else:
                        cmd = data.get('command', '').strip()
                        if not cmd:
                            await websocket.send(json.dumps({
                                "type": "shell_output",
                                "stdout": "",
                                "stderr": "No command provided",
                                "exit_code": -1,
                            }))
                        else:
                            print(f"🖥️  Shell: {cmd[:60]}...")
                            stdout, stderr, exit_code = await run_shell_command(cmd)
                            await websocket.send(json.dumps({
                                "type": "shell_output",
                                "stdout": stdout,
                                "stderr": stderr,
                                "exit_code": exit_code,
                            }))

                else:
                    print(f"⚠️  Unknown message type: {msg_type}")
            
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON: {message}")
            except Exception as e:
                print(f"❌ Error handling message: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        print(f"📱 Client disconnected: {client_id}")
    finally:
        if client_id in conversations:
            del conversations[client_id]

async def main(args):
    global shortcut_handler, ALLOW_SHELL
    ALLOW_SHELL = args.allow_shell

    mdns_advertiser = None
    if args.mdns and MDNS_AVAILABLE:
        mdns_advertiser = JanetMdnsAdvertiser(port=args.port)
        mdns_advertiser.advertise()
    elif args.mdns and not MDNS_AVAILABLE:
        print("⚠️  --mdns requested but zeroconf not installed. pip install zeroconf")

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║              🧠 CALL JANET - WEBSOCKET SERVER 🧠                      ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("")
    print("✅ Starting WebSocket server...")
    print(f"📡 Listening on: ws://0.0.0.0:{args.port}")
    print("📱 iPhone / Pixel can connect via: ws://<your-ip>:8765")
    if args.mdns:
        print("📢 mDNS: Auto-discovery enabled (_janet._tcp)")
    if args.allow_shell:
        print("🖥️  Shell: Remote shell execution ENABLED")
    print("")
    print("🧠 Using Ollama (qwen2) for responses")
    print("💚 Green Vault: In-memory (for testing)")
    print("🔗 Dynamic Shortcuts: ENABLED")
    print("")
    
    # Initialize shortcut handler
    shortcut_handler = ShortcutHandler(memory_manager=None, llm=query_ollama)
    print("✅ Shortcut handler initialized")
    print("")
    print("✅ Server ready! Waiting for connections...")
    print("")

    try:
        async with websockets.serve(handle_client, "0.0.0.0", args.port):
            await asyncio.Future()  # run forever
    finally:
        if mdns_advertiser:
            mdns_advertiser.stop()


def parse_args():
    p = argparse.ArgumentParser(description="Janet WebSocket server")
    p.add_argument("--port", type=int, default=8765, help="WebSocket port")
    p.add_argument("--mdns", action="store_true", help="Advertise via mDNS for auto-discovery")
    p.add_argument("--allow-shell", action="store_true", help="Allow shell_command for Janet Terminal")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
