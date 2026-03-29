"""
Text-to-Speech: macOS `say`, Piper (offline), or pyttsx3.
See src/voice/README.md for JANET_TTS_* and JANET_PIPER_* env vars.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from typing import Optional, Tuple

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


@dataclass
class SpeakOutcome:
    """Result of speak(); bool(outcome) is outcome.spoken for backward compatibility."""

    spoken: bool
    skipped: bool
    resolved_lang: str
    reason: Optional[str] = None
    effective_lang: Optional[str] = None
    backend: Optional[str] = None  # say | piper | pyttsx3
    voice_used: Optional[str] = None  # macOS voice name or piper model basename (+ #spkN)

    def __bool__(self) -> bool:
        return self.spoken

    def as_dict(self) -> dict:
        d = {
            "spoken": self.spoken,
            "skipped": self.skipped,
            "resolved_lang": self.resolved_lang,
        }
        if self.reason is not None:
            d["reason"] = self.reason
        if self.effective_lang is not None:
            d["effective_lang"] = self.effective_lang
        if self.backend is not None:
            d["backend"] = self.backend
        if self.voice_used is not None:
            d["voice_used"] = self.voice_used
        return d


def _env_truthy(name: str) -> bool:
    v = (os.getenv(name) or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _parse_say_rate(name: str) -> Optional[int]:
    v = (os.getenv(name) or "").strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _hr_mode() -> str:
    """off | say | piper — Croatian output policy."""
    if _env_truthy("JANET_TTS_SKIP_HR"):
        return "off"
    m = (os.getenv("JANET_TTS_HR_MODE") or "say").strip().lower()
    if m in ("off", "none", "disabled"):
        return "off"
    if m == "piper":
        return "piper"
    return "say"


def _tts_engine() -> str:
    """say | piper | auto"""
    e = (os.getenv("JANET_TTS_ENGINE") or "auto").strip().lower()
    if e in ("say", "piper", "auto"):
        return e
    return "auto"


def _normalize_engine(override: Optional[str]) -> str:
    """Per-request engine: say | piper | auto; invalid or empty → env."""
    if override is None:
        return _tts_engine()
    e = str(override).strip().lower()
    if e in ("say", "piper", "auto"):
        return e
    return _tts_engine()


def _detect_croatian(text: str) -> bool:
    return any(c in text for c in "čćžšđČĆŽŠĐ")


def _detect_german(text: str) -> bool:
    return any(c in text for c in "äöüßÄÖÜ")


def _detect_japanese(text: str) -> bool:
    """Hiragana / katakana / half-width kana → likely Japanese (romaji-only needs lang=ja)."""
    for c in text:
        o = ord(c)
        if (
            0x3040 <= o <= 0x309F  # Hiragana
            or 0x30A0 <= o <= 0x30FF  # Katakana
            or 0xFF66 <= o <= 0xFF9F  # Half-width katakana
        ):
            return True
    return False


def resolve_speak_lang(text: str, lang: Optional[str] = None) -> str:
    """Public helper: resolved language for a speak request (matches /api/speak)."""
    return _resolve_lang(text, lang)


def _resolve_lang(text: str, lang: Optional[str]) -> str:
    """
    en | hr | de_at | ja | auto (default via JANET_TTS_LANG, else auto from diacritics/kana).

    German is routed as ``de_at`` (Austrian tag / general German text). macOS ``say``
    uses bundled ``de_DE`` voices (e.g. Anna); there is usually no separate ``de_AT`` voice.
    Japanese uses macOS ``say`` voices (e.g. Kyoko); [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) has no ``ja`` pack — optional ``JANET_PIPER_JA_MODEL`` if you supply an ONNX.
    """
    default_mode = (os.getenv("JANET_TTS_LANG", "auto") or "auto").strip().lower()
    raw = (lang or default_mode).strip().lower().replace("-", "_")
    if raw in ("hr", "croatian", "hrv", "hrvatski"):
        return "hr"
    if raw in ("en", "english"):
        return "en"
    if raw in (
        "de_at",
        "deat",
        "de",
        "de_de",
        "german",
        "deutsch",
        "german_at",
        "austrian",
        "osterreich",
        "oesterreich",
        "österreich",
    ):
        return "de_at"
    if raw in ("ja", "jp", "japanese", "nihongo"):
        return "ja"
    if raw == "auto":
        if _detect_croatian(text):
            return "hr"
        if _detect_german(text):
            return "de_at"
        if _detect_japanese(text):
            return "ja"
        return "en"
    return "en"


def _piper_binary() -> Optional[str]:
    b = (os.getenv("JANET_PIPER_BINARY") or "").strip()
    if b and os.path.isfile(b) and os.access(b, os.X_OK):
        return b
    return shutil.which("piper")


def _piper_paths(lang: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (onnx_path, config_path_or_none)."""
    if lang == "hr":
        m = (os.getenv("JANET_PIPER_HR_MODEL") or "").strip()
        c = (os.getenv("JANET_PIPER_HR_CONFIG") or "").strip()
    elif lang == "de_at":
        m = (
            (os.getenv("JANET_PIPER_DE_AT_MODEL") or os.getenv("JANET_PIPER_DE_MODEL") or "")
            .strip()
        )
        c = (
            (os.getenv("JANET_PIPER_DE_AT_CONFIG") or os.getenv("JANET_PIPER_DE_CONFIG") or "")
            .strip()
        )
    elif lang == "ja":
        m = (os.getenv("JANET_PIPER_JA_MODEL") or "").strip()
        c = (os.getenv("JANET_PIPER_JA_CONFIG") or "").strip()
    else:
        m = (os.getenv("JANET_PIPER_EN_MODEL") or "").strip()
        c = (os.getenv("JANET_PIPER_EN_CONFIG") or "").strip()
    if not m or not os.path.isfile(m):
        return None, None
    if c and os.path.isfile(c):
        return m, c
    json_guess = m + ".json"
    if os.path.isfile(json_guess):
        return m, json_guess
    alt = os.path.splitext(m)[0] + ".onnx.json"
    if os.path.isfile(alt):
        return m, alt
    return m, None


def _play_wav(path: str) -> bool:
    try:
        if sys.platform == "darwin":
            subprocess.run(["afplay", path], check=True, timeout=600)
            return True
        if sys.platform.startswith("linux"):
            for player in (
                ["aplay", "-q", path],
                ["paplay", path],
                ["pw-play", path],
            ):
                try:
                    subprocess.run(player, check=True, timeout=600)
                    return True
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue
            print("⚠️  No WAV player found (aplay/paplay/pw-play)")
            return False
        subprocess.run(["afplay", path], check=True, timeout=600)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"⚠️  play wav failed: {e}")
        return False


def _piper_speaker_id(lang: str) -> Optional[int]:
    """Piper multi-speaker models: per-lang envs, then JANET_PIPER_SPEAKER."""
    if lang == "hr":
        keys = ("JANET_PIPER_HR_SPEAKER",)
    elif lang == "de_at":
        keys = ("JANET_PIPER_DE_AT_SPEAKER", "JANET_PIPER_DE_SPEAKER")
    elif lang == "ja":
        keys = ("JANET_PIPER_JA_SPEAKER",)
    else:
        keys = ("JANET_PIPER_EN_SPEAKER",)
    for key in keys:
        v = (os.getenv(key) or "").strip()
        if v:
            try:
                return int(v)
            except ValueError:
                continue
    v = (os.getenv("JANET_PIPER_SPEAKER") or "").strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _speak_piper(
    text: str,
    model: str,
    config: Optional[str],
    speaker_id: Optional[int] = None,
) -> bool:
    binary = _piper_binary()
    if not binary:
        print("⚠️  Piper binary not found; set JANET_PIPER_BINARY or install `piper` in PATH")
        return False
    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        cmd = [binary, "--model", model, "--output_file", wav_path]
        if config:
            cmd.extend(["--config", config])
        if speaker_id is not None:
            cmd.extend(["--speaker", str(speaker_id)])
        r = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            timeout=600,
            capture_output=True,
        )
        if r.returncode != 0:
            err = (r.stderr or b"").decode("utf-8", errors="replace")[:400]
            print(f"⚠️  piper failed ({r.returncode}): {err}")
            return False
        return _play_wav(wav_path)
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass


class TextToSpeech:
    """Text-to-speech: Piper (optional), macOS `say`, or pyttsx3."""

    def __init__(self, voice_style: str = "clear, warm, slightly synthetic"):
        self.voice_style = voice_style
        self.engine = None
        self.initialized = False
        self._use_say = sys.platform == "darwin"

        self._say_rate = int(os.getenv("JANET_TTS_SAY_RATE", "165"))
        self._say_rate_hr = _parse_say_rate("JANET_TTS_SAY_RATE_HR")
        self._say_rate_de_at = _parse_say_rate("JANET_TTS_SAY_RATE_DE_AT")
        self._say_rate_ja = _parse_say_rate("JANET_TTS_SAY_RATE_JA")
        self._say_rate_en = _parse_say_rate("JANET_TTS_SAY_RATE_EN")
        _preset_raw = (os.getenv("JANET_TTS_EN_PRESET") or "").strip().lower().replace("_", "-")
        self._lynda_business = _preset_raw in ("lynda", "lynda-business")
        # The Good Place–style “Janet” assistant (fan homage; not affiliated with the show). Cheery, brisk US English.
        self._good_place_janet = _preset_raw in ("good-place-janet", "tgp-janet")
        # Slower default for Lynda / boardroom delivery (softer, less “sharp” than stock Samantha pace).
        # Override with JANET_TTS_SAY_RATE_LYNDA (try 120–135 for gentler delivery).
        self._say_rate_lynda = (
            _parse_say_rate("JANET_TTS_SAY_RATE_LYNDA") if self._lynda_business else None
        )
        if self._lynda_business and self._say_rate_lynda is None:
            self._say_rate_lynda = 132
        self._say_rate_tgp = (
            _parse_say_rate("JANET_TTS_SAY_RATE_TGP_JANET") if self._good_place_janet else None
        )
        if self._good_place_janet and self._say_rate_tgp is None:
            self._say_rate_tgp = 148

        # Default EN: Samantha (female, en_US). Override with JANET_TTS_VOICE_EN.
        # good-place-janet → Samantha: least “chipper robot” among stock US `say` voices; slower WPM for human pacing.
        # JANET_TTS_EN_PRESET=lynda-business → Kathy unless VOICE_EN is set (use Samantha+lynda for refined Samantha).
        # Slavic-coloured English: JANET_TTS_SLAVIC_ACCENT=1 → Daria unless VOICE_EN set.
        _en_explicit = os.getenv("JANET_TTS_VOICE_EN")
        if _en_explicit is not None and str(_en_explicit).strip():
            self.voice_en = str(_en_explicit).strip()
        elif self._good_place_janet:
            self.voice_en = "Samantha"
        elif self._lynda_business:
            self.voice_en = "Kathy"
        elif _env_truthy("JANET_TTS_SLAVIC_ACCENT"):
            self.voice_en = "Daria"
        else:
            self.voice_en = "Samantha"
        # HR: macOS ships Lana (female, hr_HR) — default for fluid native Croatian via `say`.
        # Override JANET_TTS_VOICE_HR=Fred for former male timbre, or use Piper per README.
        self.voice_hr = os.getenv("JANET_TTS_VOICE_HR", "Lana")
        self.voice_de_at = os.getenv("JANET_TTS_VOICE_DE_AT", "Anna")
        # Japanese: bundled ja_JP (e.g. Kyoko). List: say -v '?' | rg ja_JP
        self.voice_ja = os.getenv("JANET_TTS_VOICE_JA", "Kyoko")

        if self._use_say:
            self.initialized = True
            print("✅ TTS: macOS say (en/hr/de/ja); Piper optional via JANET_TTS_ENGINE")
            return

        if HAS_PYTTSX3:
            self._initialize_pyttsx3()
        if not self.initialized and _piper_binary() and (
            _piper_paths("en")[0] or _piper_paths("hr")[0] or _piper_paths("de_at")[0]
        ):
            self.initialized = True
            print("✅ TTS: Piper (no pyttsx3)")
        elif not self.initialized:
            print("⚠️  No TTS engine. Install pyttsx3 and/or Piper + set JANET_PIPER_*_MODEL")

    def _initialize_pyttsx3(self):
        try:
            self.engine = pyttsx3.init()
            rate = self.engine.getProperty("rate")
            self.engine.setProperty("rate", rate - 45)
            self.engine.setProperty("volume", 0.82)
            voices = self.engine.getProperty("voices")
            if voices:
                for voice in voices:
                    if "female" in voice.name.lower() or "karen" in voice.name.lower():
                        self.engine.setProperty("voice", voice.id)
                        break
            self.initialized = True
            print("✅ TTS initialized (pyttsx3)")
        except Exception as e:
            print(f"⚠️  TTS initialization failed: {e}")
            self.initialized = False

    def is_available(self) -> bool:
        if self._use_say:
            return self.initialized
        if self.engine is not None and self.initialized:
            return True
        if _piper_binary() and (
            _piper_paths("en")[0]
            or _piper_paths("hr")[0]
            or _piper_paths("de_at")[0]
            or _piper_paths("ja")[0]
        ):
            return True
        return False

    def _can_synthesize(self, effective_lang: str) -> bool:
        if self._use_say:
            return True
        if self.engine is not None:
            return True
        model, _ = _piper_paths(effective_lang)
        return bool(model and _piper_binary())

    def _strip_emoji(self, text: str) -> str:
        # Avoid ranges that cross Hiragana/Katakana/CJK (e.g. never use U+24C2–U+1F251 as one block).
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U0001F900-\U0001F9FF"
            "\U00002600-\U000026FF"
            "]+",
            flags=re.UNICODE,
        )
        text = emoji_pattern.sub("", text)
        return text.replace(":)", "").replace(":(", "").replace(":D", "")

    def _say_rate_for_lang(self, lang: str) -> int:
        if lang == "hr" and self._say_rate_hr is not None:
            return self._say_rate_hr
        if lang == "de_at" and self._say_rate_de_at is not None:
            return self._say_rate_de_at
        if lang == "ja" and self._say_rate_ja is not None:
            return self._say_rate_ja
        if lang == "en":
            if self._say_rate_en is not None:
                return self._say_rate_en
            if self._good_place_janet and self._say_rate_tgp is not None:
                return self._say_rate_tgp
            if self._lynda_business and self._say_rate_lynda is not None:
                return self._say_rate_lynda
        return self._say_rate

    def _speak_say(self, text: str, lang: str, voice_override: Optional[str] = None) -> bool:
        if voice_override and voice_override.strip():
            voice = voice_override.strip()
        elif lang == "hr":
            voice = self.voice_hr
        elif lang == "de_at":
            voice = self.voice_de_at
        elif lang == "ja":
            voice = self.voice_ja
        else:
            voice = self.voice_en
        rate = self._say_rate_for_lang(lang)
        try:
            subprocess.run(
                ["say", "-v", voice, "-r", str(rate), text],
                check=True,
                timeout=600,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"⚠️  say -v {voice} failed: {e}; trying fallbacks")
            # Avoid naked `say` for Croatian — system default is often male/non-hr.
            if lang == "hr" and voice.strip().lower() != "lana":
                try:
                    subprocess.run(
                        ["say", "-v", "Lana", "-r", str(rate), text],
                        check=True,
                        timeout=600,
                    )
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass
            if lang == "ja" and voice.strip() != "Kyoko":
                try:
                    subprocess.run(
                        ["say", "-v", "Kyoko", "-r", str(rate), text],
                        check=True,
                        timeout=600,
                    )
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass
            try:
                subprocess.run(["say", "-r", str(rate), text], check=True, timeout=600)
                return True
            except Exception as e2:
                print(f"⚠️  say fallback failed: {e2}")
                return False
        except subprocess.TimeoutExpired:
            print("⚠️  say timed out")
            return False

    def _want_piper(self, effective_lang: str, hr_mode: str, engine_override: Optional[str] = None) -> bool:
        eng = _normalize_engine(engine_override)
        if eng == "say":
            return False
        if effective_lang == "hr":
            if hr_mode == "off":
                return False
            model, _ = _piper_paths("hr")
            if not model:
                return False
            if hr_mode == "piper":
                return eng in ("piper", "auto")
            # hr_mode == "say": only use Piper when this request forces `engine=piper`
            return eng == "piper"
        if effective_lang == "de_at":
            model, _ = _piper_paths("de_at")
            if not model:
                return eng == "piper"
            return eng in ("piper", "auto")
        if effective_lang == "ja":
            model, _ = _piper_paths("ja")
            if not model:
                return False
            return eng in ("piper", "auto")
        # English
        model, _ = _piper_paths("en")
        if not model:
            return eng == "piper"  # will fail later without model
        return eng in ("piper", "auto")

    def _speak_pyttsx3(self, text: str, resolved: str) -> bool:
        if self.engine is None:
            return False
        if resolved == "hr":
            voices = self.engine.getProperty("voices") or []
            picked = None
            for v in voices:
                lid = (v.id or "").lower()
                nm = (v.name or "").lower()
                langs = getattr(v, "languages", None) or []
                flat = " ".join(langs).lower() if langs else ""
                if "hr" in lid or "hr" in flat or "lana" in nm or "croat" in nm:
                    picked = v.id
                    break
            if picked:
                self.engine.setProperty("voice", picked)
        elif resolved == "de_at":
            voices = self.engine.getProperty("voices") or []
            picked = None
            for v in voices:
                lid = (v.id or "").lower()
                nm = (v.name or "").lower()
                langs = getattr(v, "languages", None) or []
                flat = " ".join(langs).lower() if langs else ""
                if "de" in lid or "de" in flat or "german" in nm:
                    picked = v.id
                    break
            if picked:
                self.engine.setProperty("voice", picked)
        elif resolved == "ja":
            voices = self.engine.getProperty("voices") or []
            picked = None
            for v in voices:
                lid = (v.id or "").lower()
                nm = (v.name or "").lower()
                langs = getattr(v, "languages", None) or []
                flat = " ".join(langs).lower() if langs else ""
                if "ja" in lid or "ja" in flat or "japan" in nm or "kyoko" in nm:
                    picked = v.id
                    break
            if picked:
                self.engine.setProperty("voice", picked)
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            print(f"⚠️  TTS failed: {e}")
            return False

    def speak(
        self,
        text: str,
        remove_emojis: bool = True,
        lang: Optional[str] = None,
        voice: Optional[str] = None,
        engine: Optional[str] = None,
        piper_speaker: Optional[int] = None,
    ) -> SpeakOutcome:
        if remove_emojis:
            text = self._strip_emoji(text)
        if not text.strip():
            return SpeakOutcome(
                spoken=False, skipped=False, resolved_lang="en", reason="empty"
            )

        resolved = _resolve_lang(text, lang)
        hr_mode = _hr_mode()
        effective_lang = resolved

        if resolved == "hr" and hr_mode == "off":
            if _env_truthy("JANET_TTS_HR_FALLBACK_EN"):
                effective_lang = "en"
            else:
                return SpeakOutcome(
                    spoken=False,
                    skipped=True,
                    resolved_lang=resolved,
                    reason="hr_disabled",
                )

        if not self._can_synthesize(effective_lang):
            return SpeakOutcome(
                spoken=False,
                skipped=True,
                resolved_lang=resolved,
                reason="tts_unavailable",
                effective_lang=effective_lang,
            )

        want_piper = self._want_piper(effective_lang, hr_mode, engine)
        if want_piper:
            model, cfg = _piper_paths(effective_lang)
            if model:
                sid = (
                    piper_speaker
                    if piper_speaker is not None
                    else _piper_speaker_id(effective_lang)
                )
                if _speak_piper(text, model, cfg, sid):
                    vu = os.path.basename(model)
                    if sid is not None:
                        vu = f"{vu}#spk{sid}"
                    return SpeakOutcome(
                        spoken=True,
                        skipped=False,
                        resolved_lang=resolved,
                        effective_lang=effective_lang,
                        backend="piper",
                        voice_used=vu,
                    )
                print("⚠️  Piper failed; falling back to system TTS")
            elif _normalize_engine(engine) == "piper":
                return SpeakOutcome(
                    spoken=False,
                    skipped=True,
                    resolved_lang=resolved,
                    reason="piper_model_missing",
                    effective_lang=effective_lang,
                )

        if self._use_say:
            vname = voice.strip() if voice and str(voice).strip() else None
            ok = self._speak_say(text, effective_lang, voice_override=vname)
            used = vname or (
                self.voice_hr
                if effective_lang == "hr"
                else (
                    self.voice_de_at
                    if effective_lang == "de_at"
                    else (self.voice_ja if effective_lang == "ja" else self.voice_en)
                )
            )
            return SpeakOutcome(
                spoken=ok,
                skipped=False,
                resolved_lang=resolved,
                effective_lang=effective_lang,
                backend="say",
                voice_used=used,
            )

        if self.engine is not None:
            ok = self._speak_pyttsx3(text, effective_lang)
            return SpeakOutcome(
                spoken=ok,
                skipped=False,
                resolved_lang=resolved,
                effective_lang=effective_lang,
                backend="pyttsx3",
            )

        return SpeakOutcome(
            spoken=False,
            skipped=True,
            resolved_lang=resolved,
            reason="tts_unavailable",
            effective_lang=effective_lang,
        )

    def speak_async(self, text: str, remove_emojis: bool = True, lang: Optional[str] = None):
        if remove_emojis:
            text = self._strip_emoji(text)
        if not text.strip():
            return

        resolved = _resolve_lang(text, lang)
        hr_mode = _hr_mode()
        effective_lang = resolved
        speak_lang = lang

        if resolved == "hr" and hr_mode == "off":
            if not _env_truthy("JANET_TTS_HR_FALLBACK_EN"):
                return
            effective_lang = "en"
            speak_lang = "en"

        def _run():
            self.speak(text, remove_emojis=False, lang=speak_lang)

        if self._want_piper(effective_lang, hr_mode) and _piper_paths(effective_lang)[0]:
            threading.Thread(target=_run, daemon=True).start()
            return

        if self._use_say:
            if effective_lang == "hr":
                voice = self.voice_hr
            elif effective_lang == "de_at":
                voice = self.voice_de_at
            elif effective_lang == "ja":
                voice = self.voice_ja
            else:
                voice = self.voice_en
            r = self._say_rate_for_lang(effective_lang)
            subprocess.Popen(["say", "-v", voice, "-r", str(r), text])
            return
        if not self.is_available():
            return
        try:
            self.engine.say(text)
            self.engine.startLoop(False)
        except Exception as e:
            print(f"⚠️  TTS async failed: {e}")


def get_default_tts() -> Optional[TextToSpeech]:
    try:
        return TextToSpeech()
    except Exception:
        return None
