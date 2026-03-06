#!/usr/bin/env python3
"""
JanetOS Testing Tools MCP Server
Provides tools to run acceptance criteria tests and validate JanetOS components.
"""

import asyncio
import json
import sys
import subprocess
from typing import Any, Dict
from pathlib import Path

class TestingMCPServer:
    def __init__(self):
        self.janetos_root = Path("/Users/mzxzd/Documents/JanetOS")
    
    def get_tools(self) -> list:
        """Return list of available MCP tools"""
        return [
            {
                "name": "janet_run_tests",
                "description": "Run JanetOS test suite. Can run all tests or specific test categories (privilege guard, overlay, websocket, etc.).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["all", "privilege_guard", "overlay", "websocket", "keywords", "memory", "integration"],
                            "default": "all",
                            "description": "Which test category to run"
                        },
                        "verbose": {
                            "type": "boolean",
                            "default": False,
                            "description": "Show detailed test output"
                        }
                    }
                }
            },
            {
                "name": "janet_test_privilege_guard",
                "description": "Test privilege guard functionality (AC-PG1-PG8): awake/sleepy states, sudo stripping, command preparation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_test_websocket_protocol",
                "description": "Test WebSocket protocol (AC-S1-S7): message types, connection, user_message, hey_janet, thank_you_janet events.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_test_keywords",
                "description": "Test keyword recognition (AC-K1-K5): Good night Janet, Good morning Janet, Thank you Janet, Hey Janet.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_validate_acceptance_criteria",
                "description": "Validate specific acceptance criteria by ID (e.g., AC-K1, AC-PG2, AC-O1). Returns pass/fail status and details.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ac_id": {
                            "type": "string",
                            "description": "Acceptance criteria ID to validate (e.g., 'AC-K1', 'AC-PG2')"
                        }
                    },
                    "required": ["ac_id"]
                }
            },
            {
                "name": "janet_get_test_coverage",
                "description": "Get test coverage report showing which acceptance criteria are covered by automated tests.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "janet_run_integration_test",
                "description": "Run full integration test: start core, connect shell, test conversation flow, verify overlay, test privilege guard.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "with_ollama": {
                            "type": "boolean",
                            "default": False,
                            "description": "Run with Ollama LLM (requires Ollama running)"
                        }
                    }
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        try:
            if name == "janet_run_tests":
                category = arguments.get("category", "all")
                verbose = arguments.get("verbose", False)
                
                test_files = {
                    "all": "tests/",
                    "privilege_guard": "tests/test_privilege_guard.py",
                    "overlay": "tests/test_overlay.py",
                    "websocket": "tests/test_websocket.py",
                    "keywords": "tests/test_keywords.py",
                    "memory": "tests/test_memory.py",
                    "integration": "tests/test_integration.py"
                }
                
                test_path = test_files.get(category, "tests/")
                cmd = ["python3", "-m", "pytest", test_path]
                if verbose:
                    cmd.append("-v")
                
                try:
                    result = subprocess.run(
                        cmd,
                        cwd=str(self.janetos_root),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    output = f"Exit code: {result.returncode}\n\n"
                    output += "STDOUT:\n" + result.stdout + "\n\n"
                    if result.stderr:
                        output += "STDERR:\n" + result.stderr
                    
                    return {"content": [{"type": "text", "text": output}]}
                except subprocess.TimeoutExpired:
                    return {"error": "Tests timed out after 60 seconds"}
            
            elif name == "janet_test_privilege_guard":
                try:
                    result = subprocess.run(
                        ["python3", "tests/test_privilege_guard.py"],
                        cwd=str(self.janetos_root),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
                    output = f"Privilege Guard Tests: {status}\n\n{result.stdout}"
                    if result.stderr:
                        output += f"\n\nErrors:\n{result.stderr}"
                    
                    return {"content": [{"type": "text", "text": output}]}
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_test_websocket_protocol":
                try:
                    result = subprocess.run(
                        ["python3", "-m", "pytest", "tests/test_websocket.py", "-v"],
                        cwd=str(self.janetos_root),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
                    output = f"WebSocket Protocol Tests: {status}\n\n{result.stdout}"
                    
                    return {"content": [{"type": "text", "text": output}]}
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_test_keywords":
                try:
                    result = subprocess.run(
                        ["python3", "-m", "pytest", "tests/test_keywords.py", "-v"],
                        cwd=str(self.janetos_root),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
                    output = f"Keyword Recognition Tests: {status}\n\n{result.stdout}"
                    
                    return {"content": [{"type": "text", "text": output}]}
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_validate_acceptance_criteria":
                ac_id = arguments.get("ac_id", "")
                
                # Map AC IDs to test commands
                ac_tests = {
                    "AC-K1": "python3 -m pytest tests/test_keywords.py::test_good_night_janet -v",
                    "AC-K2": "python3 -m pytest tests/test_keywords.py::test_good_morning_janet -v",
                    "AC-K3": "python3 -m pytest tests/test_keywords.py::test_thank_you_janet -v",
                    "AC-K4": "python3 -m pytest tests/test_keywords.py::test_hey_janet -v",
                    "AC-PG1": "python3 -m pytest tests/test_privilege_guard.py::test_awake_allows_sudo -v",
                    "AC-PG2": "python3 -m pytest tests/test_privilege_guard.py::test_sleepy_strips_sudo -v",
                    "AC-PG3": "python3 -m pytest tests/test_privilege_guard.py::test_sleepy_rejects_sudo -v",
                    "AC-PG4": "python3 -m pytest tests/test_privilege_guard.py::test_sleepy_allows_normal -v",
                }
                
                test_cmd = ac_tests.get(ac_id)
                if not test_cmd:
                    return {"content": [{"type": "text", "text": f"No automated test for {ac_id}. Manual verification required."}]}
                
                try:
                    result = subprocess.run(
                        test_cmd.split(),
                        cwd=str(self.janetos_root),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
                    output = f"Acceptance Criteria {ac_id}: {status}\n\n{result.stdout}"
                    
                    return {"content": [{"type": "text", "text": output}]}
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "janet_get_test_coverage":
                coverage = {
                    "automated": {
                        "keywords": ["AC-K1", "AC-K2", "AC-K3", "AC-K4", "AC-K5"],
                        "privilege_guard": ["AC-PG1", "AC-PG2", "AC-PG3", "AC-PG4", "AC-PG5", "AC-PG6", "AC-PG8"],
                        "websocket": ["AC-S1", "AC-S2", "AC-S3", "AC-S4", "AC-S5"],
                        "memory": ["AC-E1", "AC-E2", "AC-E3"]
                    },
                    "manual": {
                        "overlay": ["AC-O1", "AC-O2", "AC-O3", "AC-O4", "AC-O5", "AC-O6", "AC-O7"],
                        "startup": ["AC-R1", "AC-R2", "AC-R3", "AC-R4", "AC-R5", "AC-R6", "AC-R7"],
                        "core_integration": ["AC-C1", "AC-C2", "AC-C3", "AC-C4", "AC-C5"]
                    },
                    "stats": {
                        "total_acs": 50,
                        "automated": 22,
                        "manual": 28,
                        "coverage_percentage": 44
                    }
                }
                
                return {"content": [{"type": "text", "text": json.dumps(coverage, indent=2)}]}
            
            elif name == "janet_run_integration_test":
                with_ollama = arguments.get("with_ollama", False)
                
                try:
                    env = {"JANETOS_START_OLLAMA": "1"} if with_ollama else {}
                    result = subprocess.run(
                        ["python3", "test_janet_features.py"],
                        cwd=str(self.janetos_root),
                        capture_output=True,
                        text=True,
                        timeout=120,
                        env={**subprocess.os.environ, **env}
                    )
                    
                    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
                    output = f"Integration Test: {status}\n\n{result.stdout}"
                    if result.stderr:
                        output += f"\n\nErrors:\n{result.stderr}"
                    
                    return {"content": [{"type": "text", "text": output}]}
                except subprocess.TimeoutExpired:
                    return {"error": "Integration test timed out after 120 seconds"}
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
    server = TestingMCPServer()
    asyncio.run(server.run())
