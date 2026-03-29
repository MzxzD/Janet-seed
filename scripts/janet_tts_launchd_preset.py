#!/usr/bin/env python3
"""
Adjust Janet TTS-related env in ~/Library/LaunchAgents/com.janet.plist (XML).

Presets map user intent → LaunchAgent EnvironmentVariables so new API/menubar
processes pick up English Piper vs macOS say (Samantha) and HR mode.

Usage:
  janet_tts_launchd_preset.py status
  janet_tts_launchd_preset.py apply en-say-female [--restart]
  janet_tts_launchd_preset.py apply en-piper-ryan [--restart]
  janet_tts_launchd_preset.py apply hr-say [--restart]
  janet_tts_launchd_preset.py apply hr-piper [--restart]
  janet_tts_launchd_preset.py apply en-lynda-business [--restart]
  janet_tts_launchd_preset.py apply en-tts-clear-style [--restart]
  janet_tts_launchd_preset.py apply en-good-place-janet [--restart]
  janet_tts_launchd_preset.py apply en-piper-lessac [--restart]
  janet_tts_launchd_preset.py apply en-piper-amy [--restart]
  janet_tts_launchd_preset.py apply en-piper-ljspeech [--restart]
  janet_tts_launchd_preset.py apply en-piper-kristin [--restart]
  janet_tts_launchd_preset.py apply en-piper-hfc-female [--restart]
  janet_tts_launchd_preset.py probe [--url URL]
  janet_tts_launchd_preset.py restart-agent

--restart runs launchctl kickstart after a successful apply (reloads com.janet).
"""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

PLIST_DEFAULT = Path.home() / "Library/LaunchAgents/com.janet.plist"
LABEL = "com.janet"
TTS_KEYS = (
    "JANET_SEED_DIR",
    "JANET_PIPER_BINARY",
    "JANET_PIPER_EN_MODEL",
    "JANET_PIPER_EN_CONFIG",
    "JANET_PIPER_HR_MODEL",
    "JANET_PIPER_HR_CONFIG",
    "JANET_PIPER_HR_SPEAKER",
    "JANET_TTS_VOICE_HR",
    "JANET_TTS_HR_MODE",
    "JANET_TTS_ENGINE",
    "JANET_TTS_VOICE_EN",
    "JANET_TTS_EN_PRESET",
    "JANET_TTS_SAY_RATE_EN",
    "JANET_TTS_SAY_RATE_LYNDA",
    "JANET_TTS_SAY_RATE_HR",
    "JANET_TTS_SAY_RATE_DE_AT",
    "JANET_TTS_SAY_RATE_TGP_JANET",
)


def _load_plist(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        return plistlib.load(f)


def _save_plist(path: Path, data: Dict[str, Any]) -> None:
    with path.open("wb") as f:
        plistlib.dump(data, f, fmt=plistlib.FMT_XML)


def _env_dict(root: Dict[str, Any]) -> Dict[str, str]:
    env = root.get("EnvironmentVariables")
    if env is None:
        env = {}
        root["EnvironmentVariables"] = env
    out: Dict[str, str] = {}
    for k, v in env.items():
        out[str(k)] = "" if v is None else str(v)
    return out


def _seed_dir(env: Dict[str, str]) -> Optional[Path]:
    raw = (env.get("JANET_SEED_DIR") or "").strip()
    if raw:
        p = Path(raw)
        if p.is_dir():
            return p
    return None


def _ryan_paths(seed: Path) -> tuple[Path, Path]:
    d = seed / "data" / "piper"
    onnx = d / "en_US-ryan-high.onnx"
    cfg = d / "en_US-ryan-high.onnx.json"
    return onnx, cfg


def _oss_en_paths(seed: Path, basename: str) -> tuple[Path, Path]:
    """Piper ONNX from scripts/download_piper_oss_natural_en.sh (e.g. en_US-lessac-medium)."""
    d = seed / "data" / "piper"
    onnx = d / f"{basename}.onnx"
    cfg = d / f"{basename}.onnx.json"
    return onnx, cfg


def _clear_en_say_preset_for_piper(env: Dict[str, str]) -> None:
    """English uses Piper first; drop say-only Samantha / Good Place preset so plist matches intent."""
    env.pop("JANET_TTS_EN_PRESET", None)
    env.pop("JANET_TTS_VOICE_EN", None)
    env.pop("JANET_TTS_SAY_RATE_EN", None)
    env.pop("JANET_TTS_SAY_RATE_TGP_JANET", None)


def cmd_status(plist_path: Path) -> int:
    if not plist_path.is_file():
        print(json.dumps({"ok": False, "error": f"missing_plist:{plist_path}"}))
        return 1
    root = _load_plist(plist_path)
    env = _env_dict(root)
    snap = {k: env.get(k, "") for k in TTS_KEYS}
    for k, v in sorted(env.items()):
        if k.startswith("JANET_") and k not in snap:
            snap[k] = v
    seed = _seed_dir(env)
    ryan_ok = False
    if seed:
        ro, rc = _ryan_paths(seed)
        ryan_ok = ro.is_file() and rc.is_file()
    health = None
    try:
        r = subprocess.run(
            ["curl", "-sS", "-m", "2", "http://127.0.0.1:8080/health"],
            capture_output=True,
            text=True,
        )
        health = r.stdout.strip() if r.returncode == 0 else None
    except OSError:
        health = None
    en_piper = bool(snap.get("JANET_PIPER_EN_MODEL", "").strip())
    hr_mode = (snap.get("JANET_TTS_HR_MODE") or "say").strip()
    inferred_en = "piper" if en_piper else "say_samantha_or_voice_en"
    print(
        json.dumps(
            {
                "ok": True,
                "plist": str(plist_path),
                "tts_env": snap,
                "english_route": inferred_en,
                "hr_mode": hr_mode,
                "ryan_files_present": ryan_ok,
                "health": health,
            },
            indent=2,
        )
    )
    return 0


def cmd_apply(plist_path: Path, preset: str, do_restart: bool) -> int:
    if not plist_path.is_file():
        print(json.dumps({"ok": False, "error": f"missing_plist:{plist_path}"}))
        return 1
    root = _load_plist(plist_path)
    env = _env_dict(root)
    seed = _seed_dir(env)
    changes: Dict[str, Any] = {"preset": preset}

    if preset == "en-say-female":
        env.pop("JANET_PIPER_EN_MODEL", None)
        env.pop("JANET_PIPER_EN_CONFIG", None)
        changes["note"] = "English → macOS say (default Samantha unless JANET_TTS_VOICE_EN)"
    elif preset == "en-piper-ryan":
        if not seed:
            print(json.dumps({"ok": False, "error": "JANET_SEED_DIR missing or invalid in plist"}))
            return 1
        ro, rc = _ryan_paths(seed)
        if not ro.is_file() or not rc.is_file():
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "ryan_model_missing",
                        "expected_onnx": str(ro),
                    }
                )
            )
            return 1
        env["JANET_PIPER_EN_MODEL"] = str(ro)
        env["JANET_PIPER_EN_CONFIG"] = str(rc)
        if not (env.get("JANET_TTS_ENGINE") or "").strip():
            env["JANET_TTS_ENGINE"] = "auto"
        _clear_en_say_preset_for_piper(env)
        changes["note"] = "English → Piper ryan-high"
    elif preset == "hr-say":
        env["JANET_TTS_HR_MODE"] = "say"
        env["JANET_TTS_VOICE_HR"] = env.get("JANET_TTS_VOICE_HR") or "Lana"
        changes["note"] = "Croatian → macOS say (Lana default)"
    elif preset == "hr-piper":
        env["JANET_TTS_HR_MODE"] = "piper"
        if not (env.get("JANET_TTS_ENGINE") or "").strip():
            env["JANET_TTS_ENGINE"] = "auto"
        changes["note"] = "Croatian → Piper when model env set"
    elif preset == "en-lynda-business":
        env.pop("JANET_PIPER_EN_MODEL", None)
        env.pop("JANET_PIPER_EN_CONFIG", None)
        env["JANET_TTS_EN_PRESET"] = "lynda-business"
        env["JANET_TTS_VOICE_EN"] = "Shelley (English (US))"
        env.pop("JANET_TTS_SAY_RATE_EN", None)
        env.pop("JANET_TTS_SAY_RATE_TGP_JANET", None)
        env["JANET_TTS_SAY_RATE_LYNDA"] = env.get("JANET_TTS_SAY_RATE_LYNDA") or "128"
        changes["note"] = (
            "English Lynda: softer timbre (Shelley US) + ~128 WPM unless SAY_RATE_LYNDA set; "
            "use JANET_TTS_VOICE_EN=Samantha for previous crisper voice"
        )
    elif preset == "en-good-place-janet":
        env.pop("JANET_PIPER_EN_MODEL", None)
        env.pop("JANET_PIPER_EN_CONFIG", None)
        env["JANET_TTS_EN_PRESET"] = "good-place-janet"
        env["JANET_TTS_VOICE_EN"] = "Samantha"
        env.pop("JANET_TTS_SAY_RATE_LYNDA", None)
        env.pop("JANET_TTS_SAY_RATE_TGP_JANET", None)
        env["JANET_TTS_SAY_RATE_EN"] = env.get("JANET_TTS_SAY_RATE_EN") or "148"
        changes["note"] = (
            "Fan homage: less robotic — Samantha + ~148 WPM (stock say); for neural TTS add a female Piper EN model. "
            "macOS: download Enhanced voices in System Settings and set JANET_TTS_VOICE_EN to that name."
        )
    elif preset == "en-piper-lessac":
        if not seed:
            print(json.dumps({"ok": False, "error": "JANET_SEED_DIR missing or invalid in plist"}))
            return 1
        onnx, cfg = _oss_en_paths(seed, "en_US-lessac-medium")
        if not onnx.is_file() or not cfg.is_file():
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "lessac_model_missing",
                        "hint": "Run janet-seed/scripts/download_piper_oss_natural_en.sh",
                        "expected_onnx": str(onnx),
                    }
                )
            )
            return 1
        env["JANET_PIPER_EN_MODEL"] = str(onnx)
        env["JANET_PIPER_EN_CONFIG"] = str(cfg)
        if not (env.get("JANET_TTS_ENGINE") or "").strip():
            env["JANET_TTS_ENGINE"] = "auto"
        _clear_en_say_preset_for_piper(env)
        changes["note"] = (
            "English → Piper en_US-lessac-medium (OSS): natural assistant-like; `auto` uses Piper when lang is en."
        )
    elif preset == "en-piper-amy":
        if not seed:
            print(json.dumps({"ok": False, "error": "JANET_SEED_DIR missing or invalid in plist"}))
            return 1
        onnx, cfg = _oss_en_paths(seed, "en_US-amy-medium")
        if not onnx.is_file() or not cfg.is_file():
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "amy_model_missing",
                        "hint": "Run janet-seed/scripts/download_piper_oss_natural_en.sh",
                        "expected_onnx": str(onnx),
                    }
                )
            )
            return 1
        env["JANET_PIPER_EN_MODEL"] = str(onnx)
        env["JANET_PIPER_EN_CONFIG"] = str(cfg)
        if not (env.get("JANET_TTS_ENGINE") or "").strip():
            env["JANET_TTS_ENGINE"] = "auto"
        _clear_en_say_preset_for_piper(env)
        changes["note"] = (
            "English → Piper en_US-amy-medium (OSS): brighter / younger; not Vocaloid — real neural TTS."
        )
    elif preset == "en-piper-ljspeech":
        if not seed:
            print(json.dumps({"ok": False, "error": "JANET_SEED_DIR missing or invalid in plist"}))
            return 1
        onnx, cfg = _oss_en_paths(seed, "en_US-ljspeech-medium")
        if not onnx.is_file() or not cfg.is_file():
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "ljspeech_model_missing",
                        "hint": "Run janet-seed/scripts/download_piper_oss_natural_en.sh",
                        "expected_onnx": str(onnx),
                    }
                )
            )
            return 1
        env["JANET_PIPER_EN_MODEL"] = str(onnx)
        env["JANET_PIPER_EN_CONFIG"] = str(cfg)
        if not (env.get("JANET_TTS_ENGINE") or "").strip():
            env["JANET_TTS_ENGINE"] = "auto"
        _clear_en_say_preset_for_piper(env)
        changes["note"] = (
            "English → Piper en_US-ljspeech-medium: adult female narrator timbre (try first for “~30s pro” vs Amy)."
        )
    elif preset == "en-piper-kristin":
        if not seed:
            print(json.dumps({"ok": False, "error": "JANET_SEED_DIR missing or invalid in plist"}))
            return 1
        onnx, cfg = _oss_en_paths(seed, "en_US-kristin-medium")
        if not onnx.is_file() or not cfg.is_file():
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "kristin_model_missing",
                        "hint": "Run janet-seed/scripts/download_piper_oss_natural_en.sh",
                        "expected_onnx": str(onnx),
                    }
                )
            )
            return 1
        env["JANET_PIPER_EN_MODEL"] = str(onnx)
        env["JANET_PIPER_EN_CONFIG"] = str(cfg)
        if not (env.get("JANET_TTS_ENGINE") or "").strip():
            env["JANET_TTS_ENGINE"] = "auto"
        _clear_en_say_preset_for_piper(env)
        changes["note"] = (
            "English → Piper en_US-kristin-medium: LibriVox US female — often warmer/older than Amy (subjective)."
        )
    elif preset == "en-piper-hfc-female":
        if not seed:
            print(json.dumps({"ok": False, "error": "JANET_SEED_DIR missing or invalid in plist"}))
            return 1
        onnx, cfg = _oss_en_paths(seed, "en_US-hfc_female-medium")
        if not onnx.is_file() or not cfg.is_file():
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "hfc_female_model_missing",
                        "hint": "Run janet-seed/scripts/download_piper_oss_natural_en.sh",
                        "expected_onnx": str(onnx),
                    }
                )
            )
            return 1
        env["JANET_PIPER_EN_MODEL"] = str(onnx)
        env["JANET_PIPER_EN_CONFIG"] = str(cfg)
        if not (env.get("JANET_TTS_ENGINE") or "").strip():
            env["JANET_TTS_ENGINE"] = "auto"
        _clear_en_say_preset_for_piper(env)
        changes["note"] = (
            "English → Piper en_US-hfc_female-medium: Hi-Fi Captain / lessac-finetune lineage — mature studio color."
        )
    elif preset == "en-tts-clear-style":
        env.pop("JANET_TTS_EN_PRESET", None)
        env.pop("JANET_TTS_SAY_RATE_EN", None)
        env.pop("JANET_TTS_SAY_RATE_LYNDA", None)
        env.pop("JANET_TTS_SAY_RATE_TGP_JANET", None)
        changes["note"] = "Cleared EN preset / per-utterance rate overrides (voice unchanged)"
    else:
        print(json.dumps({"ok": False, "error": f"unknown_preset:{preset}"}))
        return 1

    root["EnvironmentVariables"] = env
    _save_plist(plist_path, root)
    try:
        subprocess.run(["plutil", "-lint", str(plist_path)], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(json.dumps({"ok": False, "error": "plist_invalid_after_write", "detail": e.stderr.decode() if e.stderr else ""}))
        return 1

    changes["ok"] = True
    changes["plist"] = str(plist_path)
    print(json.dumps(changes, indent=2))
    if do_restart:
        return cmd_restart_agent()
    print(json.dumps({"hint": "Run: janet_tts_launchd_preset.py restart-agent"}, indent=2))
    return 0


def cmd_restart_agent() -> int:
    uid = os.getuid()
    try:
        subprocess.run(
            ["launchctl", "kickstart", "-k", f"gui/{uid}/{LABEL}"],
            check=True,
            capture_output=True,
        )
        print(json.dumps({"ok": True, "restarted": LABEL}))
        return 0
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or b"").decode("utf-8", errors="replace")
        print(json.dumps({"ok": False, "error": "kickstart_failed", "detail": err.strip()}))
        return 1


def cmd_probe(url: str) -> int:
    import urllib.error
    import urllib.request

    payload = json.dumps({"text": "Voice check.", "lang": "en"}).encode("utf-8")
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/speak",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        print(body)
        return 0
    except urllib.error.URLError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Janet TTS LaunchAgent presets")
    ap.add_argument("--plist", type=Path, default=PLIST_DEFAULT, help="Path to com.janet.plist")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    p_apply = sub.add_parser("apply")
    p_apply.add_argument(
        "preset",
        choices=(
            "en-say-female",
            "en-piper-ryan",
            "hr-say",
            "hr-piper",
            "en-lynda-business",
            "en-good-place-janet",
            "en-piper-lessac",
            "en-piper-amy",
            "en-piper-ljspeech",
            "en-piper-kristin",
            "en-piper-hfc-female",
            "en-tts-clear-style",
        ),
    )
    p_apply.add_argument("--restart", action="store_true", help="launchctl kickstart after apply")

    sub.add_parser("restart-agent")
    p_probe = sub.add_parser("probe")
    p_probe.add_argument("--url", default="http://127.0.0.1:8080", help="Janet API base URL")

    args = ap.parse_args()
    if args.cmd == "status":
        return cmd_status(args.plist)
    if args.cmd == "apply":
        return cmd_apply(args.plist, args.preset, args.restart)
    if args.cmd == "restart-agent":
        return cmd_restart_agent()
    if args.cmd == "probe":
        return cmd_probe(args.url)
    return 1


if __name__ == "__main__":
    sys.exit(main())
