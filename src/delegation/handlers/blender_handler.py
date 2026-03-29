"""
Blender 3D Modelling Handler
Delegates 3D modelling tasks to Blender via the MCP addon socket.
"""
from typing import Any, Dict, List, Optional

from .base import (
    DelegationHandler,
    DelegationRequest,
    DelegationResult,
    HandlerCapability,
)
from ..blender_client import BlenderClient
from ..blender_reference import resolve_blender_action


# Simple mapping of common natural language phrases to Blender Python code
_BLENDER_COMMAND_MAP = [
    (["cube", "add cube", "create cube", "make a cube"], "import bpy; bpy.ops.mesh.primitive_cube_add()"),
    (["sphere", "add sphere", "create sphere", "make a sphere"], "import bpy; bpy.ops.mesh.primitive_uv_sphere_add()"),
    (["cylinder", "add cylinder", "create cylinder", "make a cylinder"], "import bpy; bpy.ops.mesh.primitive_cylinder_add()"),
    (["cone", "add cone", "create cone", "make a cone"], "import bpy; bpy.ops.mesh.primitive_cone_add()"),
    (["plane", "add plane", "create plane", "make a plane"], "import bpy; bpy.ops.mesh.primitive_plane_add()"),
    (["torus", "add torus", "create torus", "make a torus", "donut"], "import bpy; bpy.ops.mesh.primitive_torus_add()"),
    (["suzanne", "monkey", "add monkey"], "import bpy; bpy.ops.mesh.primitive_monkey_add()"),
    (["clear", "delete all", "clear scene"], "import bpy; bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()"),
]


def _query_to_blender_code(user_query: str) -> str:
    """Map natural language query to Blender Python code."""
    query_lower = user_query.lower().strip()
    for keywords, code in _BLENDER_COMMAND_MAP:
        if any(kw in query_lower for kw in keywords):
            return code
    return "import bpy; bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))"


class BlenderHandler(DelegationHandler):
    """Handler for 3D modelling tasks via Blender."""

    def __init__(self, blender_client: Optional[BlenderClient] = None):
        """Initialize Blender handler."""
        super().__init__("blender_3d", "Blender 3D Modelling Handler")
        self.client = blender_client or BlenderClient()

    def get_capabilities(self) -> List[HandlerCapability]:
        """Return 3D modelling capability."""
        return [HandlerCapability.THREE_D_MODELLING]

    def can_handle(self, request: DelegationRequest) -> bool:
        """Check if we can handle 3D modelling requests."""
        return (
            request.capability == HandlerCapability.THREE_D_MODELLING
            and self.is_available()
        )

    def handle(self, request: DelegationRequest) -> DelegationResult:
        """Handle 3D modelling delegation by sending commands to Blender."""
        user_query = (
            request.input_data.get("user_query")
            or request.task_description
            or "add a cube"
        )
        kind, info = resolve_blender_action(
            request.input_data, user_query, request.task_description
        )
        if kind == "error":
            return DelegationResult(
                success=False,
                output_data={},
                message=info.get("error", "Invalid Blender path"),
                error=info.get("error"),
                metadata={"user_query": user_query},
            )
        if kind == "primitive":
            code = _query_to_blender_code(user_query)
        else:
            code = info["code"]

        try:
            result = self.client.execute_code(code)
            result_str = str(result.get("result", result)) if result else "Done"
            meta: Dict[str, Any] = {
                "user_query": user_query,
                "blender_action": kind,
            }
            if info.get("path"):
                meta["path"] = info["path"]
            return DelegationResult(
                success=True,
                output_data={"result": result, "executed_code": code},
                message=f"Blender executed ({kind}): {result_str}",
                metadata=meta,
            )
        except Exception as e:
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Blender request failed: {e}",
                error=str(e),
            )

    def is_available(self) -> bool:
        """Check if Blender addon is available."""
        return self.client.is_available(            )
