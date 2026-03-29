"""Tests for blender_reference path validation and codegen (no Blender required)."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "blender_reference",
    _ROOT / "src" / "delegation" / "blender_reference.py",
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
sys.modules["blender_reference_tested"] = _mod

build_import_mesh_code = _mod.build_import_mesh_code
build_reference_image_plane_code = _mod.build_reference_image_plane_code
blender_delegation_touches_disk = _mod.blender_delegation_touches_disk
extract_path_from_query = _mod.extract_path_from_query
resolve_blender_action = _mod.resolve_blender_action
validate_file_path = _mod.validate_file_path
MESH_EXTENSIONS = _mod.MESH_EXTENSIONS


class TestValidateFilePath(unittest.TestCase):
    def test_rejects_missing_file(self):
        p, err = validate_file_path("/nonexistent/xyz999.glb", allowed_extensions=MESH_EXTENSIONS)
        self.assertIsNone(p)
        self.assertIn("Not a file", err or "")

    def test_rejects_wrong_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            path = tf.name
        try:
            p, err = validate_file_path(path, allowed_extensions=MESH_EXTENSIONS)
            self.assertIsNone(p)
            self.assertIn("not allowed", (err or "").lower())
        finally:
            os.unlink(path)

    def test_asset_root_allows_inside(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "vault"
            root.mkdir()
            f = root / "a.glb"
            f.write_bytes(b"x")
            with patch.dict(os.environ, {"JANET_BLENDER_ASSET_ROOT": str(root)}):
                p, err = validate_file_path(str(f), allowed_extensions=MESH_EXTENSIONS)
            self.assertIsNone(err)
            self.assertEqual(p, str(f.resolve()))

    def test_asset_root_denies_outside(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "vault"
            root.mkdir()
            outside = Path(d) / "evil.glb"
            outside.write_bytes(b"x")
            with patch.dict(os.environ, {"JANET_BLENDER_ASSET_ROOT": str(root)}):
                p, err = validate_file_path(str(outside), allowed_extensions=MESH_EXTENSIONS)
            self.assertIsNone(p)
            self.assertIn("JANET_BLENDER_ASSET_ROOT", err or "")


class TestExtractPath(unittest.TestCase):
    def test_quoted_path(self):
        q = 'Import "/Users/x/mesh.glb" in Blender'
        self.assertEqual(extract_path_from_query(q), "/Users/x/mesh.glb")

    def test_bare_unix_path(self):
        q = "load mesh /data/a.obj please"
        self.assertEqual(extract_path_from_query(q), "/data/a.obj")


class TestCodegen(unittest.TestCase):
    def test_glb_import_contains_gltf_operator(self):
        code = build_import_mesh_code("/tmp/x.glb")
        self.assertIn("import_scene.gltf", code)
        self.assertIn("/tmp/x.glb", code)

    def test_reference_uses_emission(self):
        code = build_reference_image_plane_code("/tmp/r.png")
        self.assertIn("ShaderNodeEmission", code)
        self.assertIn("/tmp/r.png", code)


class TestResolveAction(unittest.TestCase):
    def test_mesh_path_key_wrong_ext(self):
        kind, info = resolve_blender_action(
            {"mesh_path": __file__},
            "",
            "",
        )
        self.assertEqual(kind, "error")
        self.assertIn("error", info)


class TestBlenderTouchesDisk(unittest.TestCase):
    def test_explicit_keys(self):
        self.assertTrue(
            blender_delegation_touches_disk({"mesh_path": "/x.glb"}, "task")
        )

    def test_path_in_query(self):
        self.assertTrue(
            blender_delegation_touches_disk(
                {"user_query": 'import "/tmp/a.glb"'}, "3d"
            )
        )


if __name__ == "__main__":
    unittest.main()
