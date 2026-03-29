"""
Reference image and mesh import helpers for JanetXBlender (Singularity pipeline).

Validates local paths (optional JANET_BLENDER_ASSET_ROOT), generates bpy code for
Blender MCP execute_code. No network access — disk only.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

MESH_EXTENSIONS = frozenset({".glb", ".gltf", ".obj", ".fbx", ".stl", ".ply"})
IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})


def resolve_local_path(path: str) -> Path:
    """Expand user and return a Path (not necessarily validated)."""
    p = Path(path).expanduser()
    return p


def validate_file_path(
    path: str, *, allowed_extensions: frozenset
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve and validate a local file for Blender import/reference.

    If env JANET_BLENDER_ASSET_ROOT is set, the resolved path must be under that
    directory (prefix check after realpath).

    Returns:
        (absolute_path_str, None) on success, or (None, error_message).
    """
    try:
        p = resolve_local_path(path)
        if not p.is_file():
            return None, f"Not a file or not found: {path}"
        resolved = p.resolve()
        ext = resolved.suffix.lower()
        if ext not in allowed_extensions:
            return None, f"Extension {ext!r} not allowed for this operation"
        root = os.getenv("JANET_BLENDER_ASSET_ROOT", "").strip()
        if root:
            root_real = Path(root).expanduser().resolve()
            try:
                resolved.relative_to(root_real)
            except ValueError:
                return None, (
                    f"Path must be under JANET_BLENDER_ASSET_ROOT ({root_real})"
                )
        return str(resolved), None
    except OSError as e:
        return None, str(e)


def build_import_mesh_code(abs_path: str) -> str:
    """Generate Blender Python to import a mesh file by absolute path."""
    fp = json.dumps(abs_path)
    ext = Path(abs_path).suffix.lower()
    if ext in (".glb", ".gltf"):
        return f"import bpy\nfp = {fp}\nbpy.ops.import_scene.gltf(filepath=fp)"
    if ext == ".obj":
        return (
            f"import bpy\nfp = {fp}\n"
            "if hasattr(bpy.ops.wm, 'obj_import'):\n"
            "    bpy.ops.wm.obj_import(filepath=fp)\n"
            "else:\n"
            "    bpy.ops.import_scene.obj(filepath=fp)\n"
        )
    if ext == ".fbx":
        return f"import bpy\nfp = {fp}\nbpy.ops.import_scene.fbx(filepath=fp)"
    if ext == ".stl":
        return f"import bpy\nfp = {fp}\nbpy.ops.import_mesh.stl(filepath=fp)"
    if ext == ".ply":
        return f"import bpy\nfp = {fp}\nbpy.ops.import_mesh.ply(filepath=fp)"
    raise ValueError(f"Unsupported mesh extension: {ext}")


def build_reference_image_plane_code(abs_path: str) -> str:
    """Add a plane with an unshaded image texture for ortho / blockout reference."""
    fp = json.dumps(abs_path)
    return f"""
import bpy
fp = {fp}
img = bpy.data.images.load(fp, check_existing=True)
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, 0, 0))
obj = bpy.context.active_object
mat = bpy.data.materials.new(name="JanetReferenceImage")
mat.use_nodes = True
mat.blend_method = 'OPAQUE'
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()
tex = nodes.new("ShaderNodeTexImage")
tex.image = img
emit = nodes.new("ShaderNodeEmission")
emit.inputs["Strength"].default_value = 1.0
links.new(tex.outputs["Color"], emit.inputs["Color"])
out = nodes.new("ShaderNodeOutputMaterial")
links.new(emit.outputs["Emission"], out.inputs["Surface"])
obj.data.materials.append(mat)
""".strip()


_PATH_IN_QUOTES = re.compile(
    r'["\']([^"\']+\.(?:glb|gltf|obj|fbx|stl|ply|png|jpe?g|webp))["\']',
    re.IGNORECASE,
)
_PATH_BARE = re.compile(
    r"(?:(?:~|/)[^\s\"']+\.(?:glb|gltf|obj|fbx|stl|ply|png|jpe?g|webp))\b",
    re.IGNORECASE,
)


def extract_path_from_query(user_query: str) -> Optional[str]:
    """Best-effort path extraction from natural language (quoted preferred)."""
    m = _PATH_IN_QUOTES.search(user_query)
    if m:
        return m.group(1)
    m = _PATH_BARE.search(user_query)
    if m:
        return m.group(0).rstrip(").,;")
    return None


def classify_reference_vs_mesh(_user_query: str, path: str) -> str:
    """Return 'mesh' or 'image' for how to treat the extracted path."""
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in MESH_EXTENSIONS:
        return "mesh"
    return "mesh"


def input_data_requires_disk_soul_check(input_data: Dict[str, Any]) -> bool:
    """True if explicit mesh_path / reference_image_path keys are set."""
    if input_data.get("mesh_path") or input_data.get("reference_image_path"):
        return True
    return False


def blender_delegation_touches_disk(
    input_data: Dict[str, Any], task_description: str
) -> bool:
    """True if this 3D delegation will read a local file (Soul Check messaging)."""
    if input_data_requires_disk_soul_check(input_data):
        return True
    q = (input_data.get("user_query") or task_description or "").strip()
    return extract_path_from_query(q) is not None


def resolve_blender_action(
    request_input_data: Dict[str, Any], user_query: str, task_description: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Decide executed action kind and Blender Python source.

    Returns:
        (kind, info) where kind is 'mesh_import' | 'reference_image' | 'primitive'
        and info includes 'code', optional 'path', optional 'error'.
    """
    q = (user_query or task_description or "").strip()
    mesh_key = request_input_data.get("mesh_path")
    ref_key = request_input_data.get("reference_image_path")
    path_mesh = None
    path_ref = None
    if mesh_key:
        path_mesh, err = validate_file_path(str(mesh_key), allowed_extensions=MESH_EXTENSIONS)
        if err:
            return "error", {"error": err, "code": ""}
        code = build_import_mesh_code(path_mesh)
        return "mesh_import", {"code": code, "path": path_mesh}
    if ref_key:
        path_ref, err = validate_file_path(str(ref_key), allowed_extensions=IMAGE_EXTENSIONS)
        if err:
            return "error", {"error": err, "code": ""}
        code = build_reference_image_plane_code(path_ref)
        return "reference_image", {"code": code, "path": path_ref}

    extracted = extract_path_from_query(q)
    if extracted:
        kind = classify_reference_vs_mesh(q, extracted)
        if kind == "image":
            path_ref, err = validate_file_path(extracted, allowed_extensions=IMAGE_EXTENSIONS)
            if err:
                return "error", {"error": err, "code": ""}
            code = build_reference_image_plane_code(path_ref)
            return "reference_image", {"code": code, "path": path_ref}
        path_mesh, err = validate_file_path(extracted, allowed_extensions=MESH_EXTENSIONS)
        if err:
            return "error", {"error": err, "code": ""}
        code = build_import_mesh_code(path_mesh)
        return "mesh_import", {"code": code, "path": path_mesh}

    return "primitive", {"code": "", "path": None}
