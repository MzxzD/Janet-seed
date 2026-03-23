#!/usr/bin/env python3
"""
JanetOS Core MCP Server
Provides direct access to Janet-seed WebSocket API, privilege guard, and memory systems.
"""

import asyncio
import json
import os
import sys
import websockets
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from pixel_inbox import pop_inbox, read_inbox
except ImportError:
    pop_inbox = read_inbox = None

# MCP Protocol implementation
class MCPServer:
    def __init__(self):
        self.core_url = "ws://127.0.0.1:8765"
        self.ws_connection: Optional[websockets.WebSocketClientProtocol] = None
    
    async def connect_to_core(self) -> bool:
        """Connect to Janet-seed WebSocket server"""
        try:
            self.ws_connection = await websockets.connect(self.core_url, timeout=5)
            return True
        except Exception as e:
            return False
    
    async def send_message(self, message_type: str, text: str) -> Dict[str, Any]:
        """Send message to Janet core and get response"""
        if not self.ws_connection:
            await self.connect_to_core()
        
        try:
            message = json.dumps({"type": message_type, "text": text})
            await self.ws_connection.send(message)
            
            # Wait for response
            response = await asyncio.wait_for(self.ws_connection.recv(), timeout=30)
            return json.loads(response)
        except Exception as e:
            return {"error": str(e)}
    
    def get_tools(self) -> list:
        """Return list of available MCP tools"""
        return [
            {
                "name": "janet_send_message",
                "description": "Send a message to Janet and get her response. Use this to interact with Janet's AI, ask questions, or execute commands.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The message or command to send to Janet"
                        },
                        "message_type": {
                            "type": "string",
                            "enum": ["user_message", "hey_janet", "thank_you_janet"],
                            "default": "user_message",
                            "description": "Type of message: user_message (default), hey_janet (wake), or thank_you_janet (end conversation)"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "janet_check_privilege_guard",
                "description": "Check the current state of Janet's privilege guard (awake/sleepy). When awake, Janet has sudo access. When sleepy, sudo is revoked.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_set_awake",
                "description": "Grant Janet sudo access (say 'Good morning Janet!'). This re-enables elevated privileges.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_set_sleepy",
                "description": "Revoke Janet's sudo access (say 'Good night Janet'). This disables elevated privileges for security.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "kill_processes": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether to kill all sudo processes (requires confirmation)"
                        }
                    }
                }
            },
            {
                "name": "janet_query_memory",
                "description": "Query Janet's memory vaults (green, blue, red) for stored information, conversation summaries, or learned knowledge.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What to search for in Janet's memory"
                        },
                        "vault": {
                            "type": "string",
                            "enum": ["green", "blue", "red", "all"],
                            "default": "all",
                            "description": "Which memory vault to search: green (facts), blue (personal), red (sensitive), or all"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "janet_get_conversation_summary",
                "description": "Get a summary of the current or recent conversation with Janet.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_end_conversation",
                "description": "End the current conversation and store a summary (say 'Thank you, Janet!'). This clears the context window.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_pixel_pop_inbox",
                "description": "Pop the next message from Pixel (Janet IDE on Pixel Fold) that was sent via Send to Cursor. Use this to receive and process messages from the Pixel app as if the user had typed them in Cursor. Returns the message text and metadata, or null if inbox is empty.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_pixel_list_inbox",
                "description": "List all pending messages in the Pixel-to-Cursor inbox (without removing them). Use to check if Pixel has sent messages before popping.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_foundation_model_invoke",
                "description": "Invoke Janet's on-device/ Ollama model with a prompt. Use Model equivalent for Shortcuts - send prompt, get generated text. Useful for summarization, extraction, or any LLM task from Cursor.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt to send to the model"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        try:
            if name == "janet_foundation_model_invoke":
                prompt = arguments.get("prompt", "")
                response = await self.send_message("user_message", prompt)
                text = response.get("text") or response.get("reply") or ""
                return {"content": [{"type": "text", "text": text}]}

            elif name == "janet_send_message":
                text = arguments.get("text", "")
                msg_type = arguments.get("message_type", "user_message")
                response = await self.send_message(msg_type, text)
                return {"content": [{"type": "text", "text": json.dumps(response, indent=2)}]}
            
            elif name == "janet_check_privilege_guard":
                response = await self.send_message("user_message", "What is your privilege guard status?")
                return {"content": [{"type": "text", "text": json.dumps(response, indent=2)}]}
            
            elif name == "janet_set_awake":
                response = await self.send_message("user_message", "Good morning Janet!")
                return {"content": [{"type": "text", "text": "Privilege guard set to awake. Janet now has sudo access."}]}
            
            elif name == "janet_set_sleepy":
                kill = arguments.get("kill_processes", False)
                msg = "Good night Janet" + (" (kill processes)" if kill else "")
                response = await self.send_message("user_message", msg)
                return {"content": [{"type": "text", "text": "Privilege guard set to sleepy. Sudo access revoked."}]}
            
            elif name == "janet_query_memory":
                query = arguments.get("query", "")
                vault = arguments.get("vault", "all")
                response = await self.send_message("user_message", f"Search {vault} vault for: {query}")
                return {"content": [{"type": "text", "text": json.dumps(response, indent=2)}]}
            
            elif name == "janet_get_conversation_summary":
                response = await self.send_message("user_message", "Summarize our conversation")
                return {"content": [{"type": "text", "text": json.dumps(response, indent=2)}]}
            
            elif name == "janet_end_conversation":
                response = await self.send_message("thank_you_janet", "Thank you, Janet!")
                return {"content": [{"type": "text", "text": "Conversation ended and summary stored."}]}

            elif name == "janet_pixel_pop_inbox":
                if pop_inbox is None:
                    return {"content": [{"type": "text", "text": json.dumps({"error": "pixel_inbox module not available"})}]}
                entry = pop_inbox()
                if entry is None:
                    return {"content": [{"type": "text", "text": json.dumps({"pending": False, "message": None})}]}
                return {"content": [{"type": "text", "text": json.dumps({"pending": True, "text": entry.get("text", ""), "id": entry.get("id"), "timestamp": entry.get("timestamp"), "source": "pixel"})}]}

            elif name == "janet_pixel_list_inbox":
                if read_inbox is None:
                    return {"content": [{"type": "text", "text": json.dumps({"error": "pixel_inbox module not available"})}]}
                entries = read_inbox()
                summary = [{"id": e.get("id"), "text": (e.get("text", "")[:80] + "...") if len(e.get("text", "")) > 80 else e.get("text", ""), "timestamp": e.get("timestamp")} for e in entries]
                return {"content": [{"type": "text", "text": json.dumps({"count": len(entries), "entries": summary})}]}

            else:
                return {"error": f"Unknown tool: {name}"}
        
        except Exception as e:
            return {"error": str(e)}
    
    async def run(self):
        """Run the MCP server (stdio protocol)"""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line.strip())
                
                if request.get("method") == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"tools": self.get_tools()}
                    }
                
                elif request.get("method") == "tools/call":
                    params = request.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await self.call_tool(tool_name, arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": result
                    }
                
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {"code": -32601, "message": "Method not found"}
                    }
                
                print(json.dumps(response), flush=True)
            
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    server = MCPServer()
    asyncio.run(server.run())
