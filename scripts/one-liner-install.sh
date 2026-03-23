#!/usr/bin/env bash
# One-liner (install only):
#   curl -sSL https://raw.githubusercontent.com/MzxzD/Janet-Projects/main/JanetOS/janet-seed/scripts/one-liner-install.sh | bash
# One-liner (install + run all tests including edge cases):
#   curl -sSL https://raw.githubusercontent.com/MzxzD/Janet-Projects/main/JanetOS/janet-seed/scripts/one-liner-install.sh | bash -s -- --test
# One-liner (install + start server + smoke "talk to Janet"):
#   curl -sSL https://raw.githubusercontent.com/MzxzD/Janet-Projects/main/JanetOS/janet-seed/scripts/one-liner-install.sh | bash -s -- --run
set -e

# Resolve JANET_SEED_DIR: env > script's repo > clone
SCRIPT_DIR=""
if [[ -n "$BASH_SOURCE" ]] && [[ -f "$BASH_SOURCE" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "$BASH_SOURCE")" && pwd)"
fi
if [[ -n "$JANET_SEED_DIR" ]]; then
  JANET_SEED_DIR="$(cd "$JANET_SEED_DIR" && pwd)"
elif [[ -n "$SCRIPT_DIR" ]] && [[ -f "$SCRIPT_DIR/../requirements.txt" ]]; then
  JANET_SEED_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  # Piped from curl or no repo: clone
  CLONE_DIR="${JANET_CLONE_DIR:-$HOME/Janet-Projects}"
  if [[ ! -f "$CLONE_DIR/JanetOS/janet-seed/requirements.txt" ]]; then
    echo "Cloning Janet-Projects to $CLONE_DIR..."
    git clone --depth 1 https://github.com/MzxzD/Janet-Projects.git "$CLONE_DIR"
  fi
  JANET_SEED_DIR="$CLONE_DIR/JanetOS/janet-seed"
fi
export JANET_SEED_DIR
echo "Janet AI one-liner install (janet-seed + deps)"
echo "Install dir: $JANET_SEED_DIR"

# Parse flags (after install we'll run --test or --run)
DO_TEST=false
DO_RUN=false
for arg in "$@"; do
  case "$arg" in
    --test) DO_TEST=true ;;
    --run)  DO_RUN=true ;;
  esac
done

# Homebrew (skip if dry-run for CI)
if [[ "$JANET_ONE_LINER_DRY_RUN" == "1" ]]; then
  echo "Dry run: skipping Homebrew and pip install."
  PYTHON="${PYTHON:-python3}"
  VENV="$JANET_SEED_DIR/.venv"
else
  if ! command -v brew &>/dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    PATH="$(brew --prefix)/bin:$(brew --prefix)/sbin:$PATH"
  fi

  # Python 3 + Ollama (recommended)
  brew list python@3.12 &>/dev/null || brew install python@3.12
  brew list ollama &>/dev/null || brew install ollama || true

  PYTHON="${PYTHON:-$(brew --prefix python@3.12)/bin/python3.12}"
  if ! command -v "$PYTHON" &>/dev/null; then
    PYTHON=python3
  fi
  echo "Using: $PYTHON"

  # Venv and deps
  VENV="$JANET_SEED_DIR/.venv"
  if [[ ! -d "$VENV" ]]; then
    "$PYTHON" -m venv "$VENV"
  fi
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -r "$JANET_SEED_DIR/requirements.txt"
  "$VENV/bin/pip" install -q rumps 2>/dev/null || true

  # Stubs
  mkdir -p "$JANET_SEED_DIR/bin"
  cat > "$JANET_SEED_DIR/bin/janet-server" << EOF
#!/bin/bash
cd "$JANET_SEED_DIR" && "$VENV/bin/python3" janet_api_server.py "\$@"
EOF
  cat > "$JANET_SEED_DIR/bin/janet-menubar" << EOF
#!/bin/bash
cd "$JANET_SEED_DIR" && "$VENV/bin/python3" janet_menubar.py "\$@"
EOF
  chmod +x "$JANET_SEED_DIR/bin/janet-server" "$JANET_SEED_DIR/bin/janet-menubar"
fi

VENV="${VENV:-$JANET_SEED_DIR/.venv}"
PYTHON="${PYTHON:-python3}"

echo ""
echo "Done. To talk to Janet:"
echo "  1. Start server:  $JANET_SEED_DIR/bin/janet-server"
echo "  2. Menu bar:      $JANET_SEED_DIR/bin/janet-menubar  (macOS)"
echo "  3. Test:          curl http://localhost:8080/health"
echo "  Or use Cursor/Continue with apiBase http://localhost:8080/v1"

# --test: run full test suite (including edge-case tests)
if [[ "$DO_TEST" == "true" ]] && [[ -d "$VENV" ]]; then
  echo ""
  echo "Running full test suite (including edge cases)..."
  "$VENV/bin/python" -m pytest "$JANET_SEED_DIR/tests" -v --tb=short -x 2>/dev/null || \
  "$VENV/bin/python" -m pytest "$JANET_SEED_DIR/tests" -v --tb=short || true
fi

# --run: start server in background, smoke test, then stop
if [[ "$DO_RUN" == "true" ]] && [[ -d "$VENV" ]]; then
  echo ""
  echo "Starting Janet API server in background..."
  export JANET_DEFAULT_MODEL="${JANET_DEFAULT_MODEL:-qwen2.5-coder:7b}"
  "$VENV/bin/python" "$JANET_SEED_DIR/janet_api_server.py" &
  PID=$!
  sleep 3
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health | grep -q 200; then
    echo "Janet is up. You can talk to Janet at http://localhost:8080"
  else
    echo "Server started (PID $PID). Check: curl http://localhost:8080/health"
  fi
  echo "To stop: kill $PID"
fi
