#!/usr/bin/env python3
"""
JanetOS iOS Tools MCP Server
Provides tools for iOS development, deployment, and testing.
"""

import asyncio
import json
import sys
import subprocess
from typing import Any, Dict
from pathlib import Path

class iOSMCPServer:
    def __init__(self):
        self.janetos_root = Path("/Users/mzxzd/Documents/JanetOS")
        self.ios_root = self.janetos_root / "platforms" / "ios"
    
    def get_tools(self) -> list:
        """Return list of available MCP tools"""
        return [
            {
                "name": "janet_build_ios_app",
                "description": "Build JanetOS iOS app using Xcode. Supports iPhone and Apple Watch targets.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "enum": ["iphone", "watch", "both"],
                            "default": "both",
                            "description": "Which target to build"
                        },
                        "configuration": {
                            "type": "string",
                            "enum": ["Debug", "Release"],
                            "default": "Debug",
                            "description": "Build configuration"
                        }
                    }
                }
            },
            {
                "name": "janet_deploy_to_device",
                "description": "Deploy JanetOS iOS app to connected iPhone or Apple Watch.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device": {
                            "type": "string",
                            "description": "Device name or ID (optional, uses first connected device if not specified)"
                        }
                    }
                }
            },
            {
                "name": "janet_list_ios_devices",
                "description": "List all connected iOS devices (iPhone, iPad, Apple Watch) available for deployment.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_create_shortcut",
                "description": "Create an iOS Shortcut for Janet integration (Hey Janet trigger, Play Music, etc.).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "shortcut_type": {
                            "type": "string",
                            "enum": ["hey_janet", "play_music", "smart_music", "custom"],
                            "description": "Type of shortcut to create"
                        },
                        "name": {
                            "type": "string",
                            "description": "Shortcut name (for custom shortcuts)"
                        },
                        "actions": {
                            "type": "string",
                            "description": "Shortcut actions in JSON format (for custom shortcuts)"
                        }
                    },
                    "required": ["shortcut_type"]
                }
            },
            {
                "name": "janet_install_shortcut",
                "description": "Install a shortcut file (.shortcut) to connected iOS device via AirDrop or direct transfer.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "shortcut_path": {
                            "type": "string",
                            "description": "Path to .shortcut file"
                        },
                        "method": {
                            "type": "string",
                            "enum": ["airdrop", "direct"],
                            "default": "airdrop",
                            "description": "Installation method"
                        }
                    },
                    "required": ["shortcut_path"]
                }
            },
            {
                "name": "janet_test_watch_integration",
                "description": "Test Apple Watch integration: voice input, Hey Janet trigger, notification display.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_configure_ios_core_url",
                "description": "Configure Janet core WebSocket URL in iOS app (for remote or local Janet-seed).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "core_url": {
                            "type": "string",
                            "description": "WebSocket URL (e.g., ws://192.168.1.100:8765 or ws://127.0.0.1:8765)"
                        }
                    },
                    "required": ["core_url"]
                }
            },
            {
                "name": "janet_get_ios_logs",
                "description": "Get logs from JanetOS iOS app running on connected device.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lines": {
                            "type": "integer",
                            "default": 100,
                            "description": "Number of log lines to retrieve"
                        }
                    }
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        try:
            if name == "janet_build_ios_app":
                target = arguments.get("target", "both")
                config = arguments.get("configuration", "Debug")
                
                try:
                    if target in ["iphone", "both"]:
                        result = subprocess.run(
                            ["xcodebuild", "-project", "JanetOS.xcodeproj", 
                             "-scheme", "JanetOS", "-configuration", config,
                             "-destination", "generic/platform=iOS"],
                            cwd=str(self.ios_root),
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        
                        if result.returncode != 0:
                            return {"error": f"iPhone build failed:\n{result.stderr}"}
                    
                    if target in ["watch", "both"]:
                        result = subprocess.run(
                            ["xcodebuild", "-project", "JanetOS.xcodeproj",
                             "-scheme", "JanetOS Watch App", "-configuration", config,
                             "-destination", "generic/platform=watchOS"],
                            cwd=str(self.ios_root),
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        
                        if result.returncode != 0:
                            return {"error": f"Watch build failed:\n{result.stderr}"}
                    
                    return {"content": [{"type": "text", "text": f"✅ Successfully built {target} app ({config})"}]}
                
                except subprocess.TimeoutExpired:
                    return {"error": "Build timed out after 5 minutes"}
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_deploy_to_device":
                device = arguments.get("device")
                
                try:
                    # List devices first
                    result = subprocess.run(
                        ["xcrun", "xctrace", "list", "devices"],
                        capture_output=True,
                        text=True
                    )
                    
                    devices = [line for line in result.stdout.split('\n') if 'iPhone' in line or 'iPad' in line]
                    
                    if not devices:
                        return {"error": "No iOS devices connected"}
                    
                    # Deploy to device
                    deploy_cmd = ["xcodebuild", "-project", "JanetOS.xcodeproj",
                                 "-scheme", "JanetOS", "-configuration", "Debug",
                                 "-destination", f"name={device}" if device else "generic/platform=iOS",
                                 "install"]
                    
                    result = subprocess.run(
                        deploy_cmd,
                        cwd=str(self.ios_root),
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        return {"content": [{"type": "text", "text": "✅ Successfully deployed to device"}]}
                    else:
                        return {"error": f"Deployment failed:\n{result.stderr}"}
                
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_list_ios_devices":
                try:
                    result = subprocess.run(
                        ["xcrun", "xctrace", "list", "devices"],
                        capture_output=True,
                        text=True
                    )
                    
                    devices = [line.strip() for line in result.stdout.split('\n') 
                              if any(x in line for x in ['iPhone', 'iPad', 'Watch', 'iPod'])]
                    
                    if devices:
                        output = "Connected iOS Devices:\n\n" + "\n".join(devices)
                    else:
                        output = "No iOS devices connected"
                    
                    return {"content": [{"type": "text", "text": output}]}
                
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_create_shortcut":
                shortcut_type = arguments.get("shortcut_type")
                
                scripts = {
                    "hey_janet": "create_hey_janet_shortcut.py",
                    "play_music": "create_music_shortcut.py",
                    "smart_music": "create_smart_music_shortcut.py"
                }
                
                script = scripts.get(shortcut_type)
                if not script:
                    return {"error": f"Unknown shortcut type: {shortcut_type}"}
                
                try:
                    result = subprocess.run(
                        ["python3", script],
                        cwd=str(self.janetos_root),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        return {"content": [{"type": "text", "text": f"✅ Created {shortcut_type} shortcut\n\n{result.stdout}"}]}
                    else:
                        return {"error": f"Failed to create shortcut:\n{result.stderr}"}
                
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_install_shortcut":
                shortcut_path = arguments.get("shortcut_path")
                method = arguments.get("method", "airdrop")
                
                try:
                    if method == "airdrop":
                        result = subprocess.run(
                            ["./airdrop_shortcuts.sh", shortcut_path],
                            cwd=str(self.janetos_root),
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                    else:
                        # Direct install via USB
                        result = subprocess.run(
                            ["./install_music_shortcut.sh"],
                            cwd=str(self.janetos_root),
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                    
                    if result.returncode == 0:
                        return {"content": [{"type": "text", "text": f"✅ Shortcut installed via {method}"}]}
                    else:
                        return {"error": f"Installation failed:\n{result.stderr}"}
                
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_test_watch_integration":
                try:
                    # Run Watch integration tests
                    result = subprocess.run(
                        ["python3", "-m", "pytest", "platforms/ios/tests/test_watch_integration.py", "-v"],
                        cwd=str(self.janetos_root),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
                    output = f"Apple Watch Integration Tests: {status}\n\n{result.stdout}"
                    
                    return {"content": [{"type": "text", "text": output}]}
                
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_configure_ios_core_url":
                core_url = arguments.get("core_url")
                
                # Update iOS app configuration
                config_content = f"""
// Auto-generated by MCP server
let janetCoreURL = "{core_url}"
"""
                
                config_path = self.ios_root / "Sources" / "Config.swift"
                try:
                    with open(config_path, 'w') as f:
                        f.write(config_content)
                    
                    return {"content": [{"type": "text", "text": f"✅ Configured iOS app to use: {core_url}"}]}
                
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_get_ios_logs":
                lines = arguments.get("lines", 100)
                
                try:
                    result = subprocess.run(
                        ["xcrun", "simctl", "spawn", "booted", "log", "stream", 
                         "--predicate", "subsystem == 'com.janetos.app'",
                         "--last", str(lines)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    return {"content": [{"type": "text", "text": result.stdout or "No logs available"}]}
                
                except Exception as e:
                    return {"error": str(e)}
            
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
    server = iOSMCPServer()
    asyncio.run(server.run())
