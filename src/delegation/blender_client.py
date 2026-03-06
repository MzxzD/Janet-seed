"""
Blender Socket Client
Connects to the Blender MCP addon via TCP socket for 3D modelling delegation.
Protocol: JSON over TCP (localhost:9876 by default).
"""
import json
import os
import socket
from typing import Any, Dict, Optional


class BlenderClient:
    """Client for the Blender addon socket server."""

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 9876
    SOCKET_TIMEOUT = 180.0
    BUFFER_SIZE = 8192

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize Blender client.

        Args:
            host: Blender addon host (default: BLENDER_HOST env or localhost)
            port: Blender addon port (default: BLENDER_PORT env or 9876)
        """
        self.host = host or os.getenv("BLENDER_HOST", self.DEFAULT_HOST)
        self.port = int(port or os.getenv("BLENDER_PORT", str(self.DEFAULT_PORT)))
        self._sock: Optional[socket.socket] = None

    def _connect(self) -> bool:
        """Connect to the Blender addon socket server."""
        if self._sock:
            return True

        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10.0)
            self._sock.connect((self.host, self.port))
            self._sock.settimeout(self.SOCKET_TIMEOUT)
            return True
        except Exception:
            self._sock = None
            return False

    def disconnect(self) -> None:
        """Disconnect from Blender addon."""
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            finally:
                self._sock = None

    def _receive_full_response(self) -> bytes:
        """Receive complete JSON response, possibly in multiple chunks."""
        if not self._sock:
            raise ConnectionError("Not connected to Blender")

        chunks = []
        self._sock.settimeout(self.SOCKET_TIMEOUT)

        while True:
            chunk = self._sock.recv(self.BUFFER_SIZE)
            if not chunk:
                if not chunks:
                    raise ConnectionError("Connection closed before receiving data")
                break

            chunks.append(chunk)
            data = b"".join(chunks)
            try:
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError:
                continue

        if chunks:
            data = b"".join(chunks)
            try:
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response from Blender")

        raise Exception("No data received from Blender")

    def send_command(self, command_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a command to Blender and return the result.

        Args:
            command_type: Command type (e.g. execute_code, get_scene_info)
            params: Optional parameters dict

        Returns:
            Result dict from Blender (from response["result"])

        Raises:
            ConnectionError: If cannot connect
            Exception: On Blender error or timeout
        """
        if not self._connect():
            raise ConnectionError("Could not connect to Blender. Ensure Blender is running with the MCP addon connected.")

        command = {"type": command_type, "params": params or {}}

        try:
            self._sock.sendall(json.dumps(command).encode("utf-8"))
            response_data = self._receive_full_response()
            response = json.loads(response_data.decode("utf-8"))

            if response.get("status") == "error":
                raise Exception(response.get("message", "Unknown error from Blender"))

            return response.get("result", {})
        except (ConnectionError, BrokenPipeError, ConnectionResetError, socket.timeout) as e:
            self._sock = None
            raise Exception(f"Connection to Blender lost: {e}") from e

    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Execute Python code in Blender.

        Args:
            code: Python code to run in Blender's context (e.g. bpy.ops.mesh.primitive_cube_add())

        Returns:
            Result from Blender
        """
        return self.send_command("execute_code", {"code": code})

    def get_scene_info(self) -> Dict[str, Any]:
        """Get current Blender scene information."""
        return self.send_command("get_scene_info")

    def is_available(self) -> bool:
        """Check if Blender addon is available and reachable."""
        try:
            self.send_command("get_scene_info")
            return True
        except Exception:
            return False
