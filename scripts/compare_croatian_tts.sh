#!/usr/bin/env bash
# A/B the same Croatian line on macOS say (Lana) vs Piper HR model (each speaker slot).
# Requires Janet API running (default http://127.0.0.1:8080). Restart API after code changes.
set -euo pipefail
API="${JANET_API:-http://127.0.0.1:8080}"
TEXT="${1:-Možemo pričati hrvatski. Janet sada koristi Lanu kao zadani ženski glas, a Piper ostaje za usporedbu.}"

post() {
  local json="$1"
  echo "---"
  curl -sS -m 120 -X POST "${API}/api/speak" \
    -H "Content-Type: application/json" \
    -d "$json"
  echo
}

JSON_BASE=$(python3 -c "import json,sys; print(json.dumps({'text': sys.argv[1], 'lang': 'hr'}, ensure_ascii=False))" "$TEXT")

echo "Using API=$API"
echo "Phrase length: ${#TEXT} chars"

post "$(echo "$JSON_BASE" | python3 -c "import json,sys; d=json.load(sys.stdin); d.update({'engine':'say','voice':'Lana'}); print(json.dumps(d, ensure_ascii=False))")"
sleep 2

post "$(echo "$JSON_BASE" | python3 -c "import json,sys; d=json.load(sys.stdin); d.update({'engine':'piper','piper_speaker':0}); print(json.dumps(d, ensure_ascii=False))")"
sleep 2

post "$(echo "$JSON_BASE" | python3 -c "import json,sys; d=json.load(sys.stdin); d.update({'engine':'piper','piper_speaker':1}); print(json.dumps(d, ensure_ascii=False))")"

echo "---"
echo "Pick the row you prefer (fluidity, timbre). Set LaunchAgent JANET_PIPER_HR_SPEAKER or use POST piper_speaker; use engine=say for native hr_HR."
