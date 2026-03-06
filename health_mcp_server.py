#!/usr/bin/env python3
"""
JanetOS Health Monitor MCP Server
Provides health checks and diagnostics for Janet-seed and JanetOS components.
"""

import asyncio
import json
import sys
import subprocess
import socket
from typing import Any, Dict

class HealthMCPServer:
    def __init__(self):
        self.core_port = 8765
        self.core_host = "127.0.0.1"
    
    def check_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_process_running(self, process_name: str) -> bool:
        """Check if a process is running"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except:
            return False
    
    def get_tools(self) -> list:
        """Return list of available MCP tools"""
        return [
            {
                "name": "janet_health_check",
                "description": "Comprehensive health check of JanetOS components: Janet-seed core, WebSocket server, LLM (Ollama), and system status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_check_websocket",
                "description": "Check if Janet-seed WebSocket server is running and accepting connections on port 8765.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_check_ollama",
                "description": "Check if Ollama LLM server is running and available on port 11434.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_check_processes",
                "description": "List all running JanetOS-related processes (janet-seed, shells, overlays).",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_start_core",
                "description": "Start Janet-seed core server if not running. Equivalent to running ./start.sh",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "with_ollama": {
                            "type": "boolean",
                            "default": False,
                            "description": "Also start Ollama LLM server"
                        }
                    }
                }
            },
            {
                "name": "janet_stop_core",
                "description": "Stop Janet-seed core server and all related processes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        try:
            if name == "janet_health_check":
                websocket_ok = self.check_port_open(self.core_host, self.core_port)
                ollama_ok = self.check_port_open("127.0.0.1", 11434)
                core_running = self.check_process_running("janet-seed")
                
                status = {
                    "websocket_server": "✅ Running" if websocket_ok else "❌ Not running",
                    "websocket_port": self.core_port,
                    "ollama_llm": "✅ Running" if ollama_ok else "❌ Not running",
                    "ollama_port": 11434,
                    "janet_core_process": "✅ Running" if core_running else "❌ Not running",
                    "overall_status": "✅ Healthy" if (websocket_ok and core_running) else "⚠️ Issues detected"
                }
                
                return {"content": [{"type": "text", "text": json.dumps(status, indent=2)}]}
            
            elif name == "janet_check_websocket":
                is_open = self.check_port_open(self.core_host, self.core_port)
                status = {
                    "websocket_available": is_open,
                    "host": self.core_host,
                    "port": self.core_port,
                    "url": f"ws://{self.core_host}:{self.core_port}",
                    "status": "✅ Accepting connections" if is_open else "❌ Not reachable"
                }
                return {"content": [{"type": "text", "text": json.dumps(status, indent=2)}]}
            
            elif name == "janet_check_ollama":
                is_running = self.check_port_open("127.0.0.1", 11434)
                status = {
                    "ollama_available": is_running,
                    "port": 11434,
                    "status": "✅ Running" if is_running else "❌ Not running",
                    "note": "Ollama is optional. Janet can run without it using mock responses."
                }
                return {"content": [{"type": "text", "text": json.dumps(status, indent=2)}]}
            
            elif name == "janet_check_processes":
                try:
                    result = subprocess.run(
                        ["ps", "aux"],
                        capture_output=True,
                        text=True
                    )
                    lines = [line for line in result.stdout.split('\n') 
                            if 'janet' in line.lower() or 'ollama' in line.lower()]
                    
                    return {"content": [{"type": "text", "text": "\n".join(lines) if lines else "No JanetOS processes found"}]}
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_start_core":
                with_ollama = arguments.get("with_ollama", False)
                try:
                    env = {"JANETOS_START_OLLAMA": "1"} if with_ollama else {}
                    subprocess.Popen(
                        ["./start.sh"],
                        cwd="/Users/mzxzd/Documents/JanetOS",
                        env={**subprocess.os.environ, **env}
                    )
                    return {"content": [{"type": "text", "text": "✅ Starting Janet-seed core..." + (" with Ollama" if with_ollama else "")}]}
                except Exception as e:
                    return {"error": f"Failed to start: {str(e)}"}
            
            elif name == "janet_stop_core":
                try:
                    subprocess.run(["pkill", "-f", "janet-seed"], check=False)
                    subprocess.run(["pkill", "-f", "simple_websocket_server"], check=False)
                    return {"content": [{"type": "text", "text": "✅ Stopped Janet-seed core"}]}
                except Exception as e:
                    return {"error": f"Failed to stop: {str(e)}"}
            
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
    server = HealthMCPServer()
    asyncio.run(server.run())
