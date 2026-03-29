"""
Runtime defaults for /api/speak (TL;DR & IDE helpers): lang, voice, engine, piper_speaker.
Change via PATCH without restarting the API. Optional JSON persistence under data/.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException

router = APIRouter(prefix="/api/tts", tags=["tts"])

_lock = threading.Lock()
_state: Dict[str, Any] = {}

_VALID_ENGINE = frozenset({"say", "piper", "auto"})


def _seed_root() -> Path:
    # This file: janet-seed/src/api/tts_tldr_plugin.py
    default_root = Path(__file__).resolve().parent.parent
    return Path(os.getenv("JANET_SEED_DIR", str(default_root))).resolve()


def _defaults_file() -> Path:
    override = (os.getenv("JANET_TTS_TLDR_DEFAULTS_FILE") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    d = _seed_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "tts_tldr_defaults.json"


def load_defaults_from_disk() -> None:
    path = _defaults_file()
    global _state
    with _lock:
        if not path.is_file():
            _state = {}
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                _state = {}
                return
            _state = _normalize_incoming(raw)
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  [tts_tldr_defaults] could not load {path}: {e}")
            _state = {}


def _normalize_incoming(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if v := d.get("lang"):
        s = str(v).strip()
        if s:
            out["lang"] = s
    if v := d.get("voice"):
        s = str(v).strip()
        if s:
            out["voice"] = s
    if v := d.get("engine"):
        s = str(v).strip().lower()
        if s in _VALID_ENGINE:
            out["engine"] = s
    if "piper_speaker" in d and d["piper_speaker"] is not None:
        try:
            out["piper_speaker"] = int(d["piper_speaker"])
        except (TypeError, ValueError):
            pass
    return out


def _save_to_disk() -> None:
    path = _defaults_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            snap = dict(_state)
        path.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as e:
        print(f"⚠️  [tts_tldr_defaults] could not save {path}: {e}")


def get_tldr_defaults() -> Dict[str, Any]:
    with _lock:
        return dict(_state)


def patch_tldr_defaults(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    PATCH semantics: only keys present in `updates` are applied.
    Use null / empty string for lang|voice|engine to clear that key.
    """
    global _state
    with _lock:
        for key in ("lang", "voice", "engine", "piper_speaker"):
            if key not in updates:
                continue
            val = updates[key]
            if val is None or val == "":
                _state.pop(key, None)
                continue
            if key == "engine":
                s = str(val).strip().lower()
                if s not in _VALID_ENGINE:
                    raise ValueError(f"engine must be one of: {sorted(_VALID_ENGINE)}")
                _state["engine"] = s
            elif key == "piper_speaker":
                _state["piper_speaker"] = int(val)
            else:
                _state[key] = str(val).strip()
        out = dict(_state)
    _save_to_disk()
    return out


def apply_tldr_defaults_to_speak_body(body: Dict[str, Any]) -> None:
    """Fill missing lang/language, voice, engine, piper_speaker from runtime store (in place)."""
    d = get_tldr_defaults()
    if d.get("lang") and not (body.get("lang") or body.get("language")):
        body["lang"] = d["lang"]
    if d.get("voice") is not None and str(d["voice"]).strip():
        if body.get("voice") is None or str(body.get("voice", "")).strip() == "":
            body["voice"] = d["voice"]
    if d.get("engine"):
        if body.get("engine") is None or str(body.get("engine", "")).strip() == "":
            body["engine"] = d["engine"]
    ps = body.get("piper_speaker")
    has_ps = ps is not None and str(ps).strip() != ""
    if not has_ps and "piper_speaker" in d:
        body["piper_speaker"] = d["piper_speaker"]


@router.get("/tldr-defaults")
async def get_tldr_defaults_endpoint():
    path = _defaults_file()
    return {
        "defaults": get_tldr_defaults(),
        "persist_path": str(path),
    }


@router.patch("/tldr-defaults")
async def patch_tldr_defaults_endpoint(data: dict = Body(default={})):
    try:
        merged = patch_tldr_defaults(data or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "ok", "defaults": merged}

