#!/usr/bin/env python3
"""
Simple WebSocket server for Call Janet iPhone app
Handles basic conversation with Ollama LLM
"""
import asyncio
import json
import websockets
import subprocess
from datetime import datetime
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
                
                elif msg_type in ['recognize_intent', 'create_shortcut', 'build_shortcut',
                                   'get_shortcuts', 'save_shortcut', 'delete_shortcut']:
                    # Dynamic Shortcuts
                    print(f"🔗 Handling shortcut message: {msg_type}")
                    response = await shortcut_handler.handle_message(data)
                    await websocket.send(json.dumps(response))
                
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

async def main():
    global shortcut_handler
    
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║              🧠 CALL JANET - WEBSOCKET SERVER 🧠                      ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("")
    print("✅ Starting WebSocket server...")
    print("📡 Listening on: ws://0.0.0.0:8765")
    print("📱 iPhone can connect via: ws://192.168.0.121:8765")
    print("")
    print("🧠 Using Ollama (qwen2) for responses")
    print("💚 Green Vault: In-memory (for testing)")
    print("🔗 Dynamic Shortcuts: ENABLED")
    print("")
    
    # Initialize shortcut handler
    shortcut_handler = ShortcutHandler(memory_manager=None, llm=query_ollama)
    print("✅ Shortcut handler initialized")
    print("")
    print("✅ Server ready! Waiting for iPhone connection...")
    print("")
    
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
