#!/usr/bin/env bash
# Download open-source Piper English voices from rhasspy/piper-voices (HuggingFace).
# Female US English: assistant (lessac), bright/youthful (amy), mature narrative (ljspeech, kristin),
# lessac-adjacent studio (hfc_female). No dataset promises a specific age — listen and pick.
# License: see https://huggingface.co/rhasspy/piper-voices and per-voice MODEL_CARD / metadata.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JANET_SEED="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT="${1:-$JANET_SEED/data/piper}"
HF="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US"
mkdir -p "$OUT"

download_pair() {
  local sub="$1" name="$2"
  local url_onnx="$HF/$sub/$name.onnx"
  local url_json="$HF/$sub/$name.onnx.json"
  echo "→ $name"
  curl -fL --progress-bar -o "$OUT/$name.onnx" "$url_onnx"
  curl -fL --progress-bar -o "$OUT/$name.onnx.json" "$url_json"
}

# Lessac: clear, natural US female — closest “helpful assistant” among stock Piper EN.
download_pair "lessac/medium" "en_US-lessac-medium"
# Amy: younger / brighter timbre — “anime-adjacent” but real neural TTS, not Vocaloid.
download_pair "amy/medium" "en_US-amy-medium"
# LJSpeech: single adult female narrator (classic “professional read”) — less “teen bright” than Amy.
download_pair "ljspeech/medium" "en_US-ljspeech-medium"
# Kristin: LibriVox US female — often reads older / storyteller than Amy (subjective).
download_pair "kristin/medium" "en_US-kristin-medium"
# HFC female: finetuned from lessac; different color, still mature-leaning vs Amy.
download_pair "hfc_female/medium" "en_US-hfc_female-medium"

echo "Done. Files in $OUT"
ls -la "$OUT"/en_US-*-medium.onnx 2>/dev/null || true
