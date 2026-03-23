#!/usr/bin/env python3
"""
Janet Menu Bar Controller
A macOS menu bar app to control Janet's AI model
"""
import os
import sys

# --test mode: health poll only, no rumps needed
if "--test" in sys.argv:
    import requests
    try:
        r = requests.get("http://localhost:8080/health", timeout=5)
        if r.status_code == 200:
            print("OK: Janet API healthy", r.json())
            sys.exit(0)
        print("WARN: API returned", r.status_code)
        sys.exit(1)
    except Exception as e:
        print("FAIL: Janet API unreachable:", e)
        sys.exit(1)

# --ctl: scriptable control surface for E2E (no rumps). Usage: --ctl <cmd> [args...]
if "--ctl" in sys.argv:
    idx = sys.argv.index("--ctl")
    args = sys.argv[idx + 1:] if idx + 1 < len(sys.argv) else []
    import json as _json
    import subprocess as _subprocess
    from pathlib import Path as _Path
    _JANET_DIR = _Path(__file__).resolve().parent
    _CONFIG_PATH = _Path.home() / ".janet" / "menubar_config.json"
    _DEFAULT_API = "http://localhost:8080"
    _SERVER_LOG = os.environ.get("JANET_SERVER_LOG", "/tmp/janet_server.log")

    def _load_cfg():
        if not _CONFIG_PATH.exists():
            return {}
        with open(_CONFIG_PATH, "r") as f:
            return _json.load(f)

    def _save_cfg(cfg):
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_PATH, "w") as f:
            _json.dump(cfg, f, indent=2)

    def _api_url():
        c = _load_cfg()
        return c.get("api_url") or os.environ.get("JANET_API_URL", _DEFAULT_API)

    cmd = args[0] if args else ""
    out = {}
    if cmd == "status":
        import requests as _req
        url = _api_url()
        try:
            r = _req.get(f"{url}/health", timeout=5)
            out = {"ok": r.status_code == 200, "status_code": r.status_code, "data": r.json() if r.status_code == 200 else None}
        except Exception as e:
            out = {"ok": False, "error": str(e)}
        print(_json.dumps(out))
    elif cmd == "config-get":
        print(_json.dumps(_load_cfg()))
    elif cmd == "config-set":
        if len(args) < 2:
            print(_json.dumps({"ok": False, "error": "config-set requires JSON string or path"}))
            sys.exit(1)
        arg = args[1]
        if arg.startswith("{") or arg.startswith("["):
            cfg = _json.loads(arg)
        else:
            with open(arg, "r") as f:
                cfg = _json.load(f)
        _save_cfg(cfg)
        print(_json.dumps({"ok": True, "config": _load_cfg()}))
    elif cmd == "start-server":
        model = args[1] if len(args) > 1 else "qwen2.5-coder:7b"
        _subprocess.run(
            f"cd {_JANET_DIR} && OLLAMA_NUM_GPU=0 JANET_DEFAULT_MODEL={model!r} python3 -u janet_api_server.py > {_SERVER_LOG!r} 2>&1 &",
            shell=True,
        )
        print(_json.dumps({"ok": True, "model": model, "log": _SERVER_LOG}))
    else:
        print(_json.dumps({"ok": False, "error": f"unknown command: {cmd}", "usage": "status|config-get|config-set <json_or_path>|start-server [model]"}))
        sys.exit(1)
    sys.exit(0 if out.get("ok", True) else 1)

import atexit
import rumps
import subprocess
import requests
import json
import time
import threading
import shutil
from pathlib import Path

# Unload LaunchAgent on any exit (Cmd+Q, system Quit, etc.) so launchd won't restart us.
# Sync unload: launchd will SIGTERM us, so we exit cleanly without a restart loop.
def _unload_launch_agent_on_exit():
    plist = Path.home() / "Library/LaunchAgents/com.janet.plist"
    if plist.exists():
        subprocess.run(
            ["launchctl", "unload", str(plist)],
            capture_output=True,
            timeout=5,
        )
atexit.register(_unload_launch_agent_on_exit)

JANET_API_KEY = "janet-local-dev"
JANET_DIR = Path(__file__).parent
CONFIG_PATH = Path.home() / ".continue/config.json"
SERVER_LOG = os.environ.get("JANET_SERVER_LOG", "/tmp/janet_server.log")
MENUBAR_CONFIG_PATH = Path.home() / ".janet" / "menubar_config.json"
DEFAULT_API_URL = "http://localhost:8080"
INACTIVITY_OPTIONS = [5, 10, 15, 30]


def load_menubar_config():
    """Load menu bar config from ~/.janet/menubar_config.json."""
    if not MENUBAR_CONFIG_PATH.exists():
        return {}
    try:
        with open(MENUBAR_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_menubar_config(config):
    """Save menu bar config to ~/.janet/menubar_config.json."""
    MENUBAR_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MENUBAR_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_api_url():
    """API URL from config file or env (for health checks and menu)."""
    config = load_menubar_config()
    return config.get("api_url") or os.environ.get("JANET_API_URL", DEFAULT_API_URL)

# Base models; dynamic models from ollama list (and API available_models) are merged in
MODELS = {
    "qwen2.5-coder:7b": "🔧 Qwen2.5 Coder (Best for Code)",
    "qwen2:latest": "🤖 Qwen2 (General Purpose)",
    "llama3.2:latest": "⚡ Llama 3.2 (Fast)",
    "llama3.2-vision:11b": "👁️ Llama Vision (Images)",
    "llama2:latest": "🦙 Llama 2 (Classic)",
}
# Presets for "Pull model" submenu (offline/online via ollama pull)
PULL_PRESETS = list(MODELS.keys())


def get_ollama_models():
    """Fetch available models from ollama list"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return {}
        models = {}
        lines = result.stdout.strip().split("\n")[1:]  # Skip header
        for line in lines:
            parts = line.split()
            if parts:
                name = parts[0]  # NAME column
                if name not in MODELS:
                    models[name] = f"📦 {name}"
        return models
    except Exception:
        return {}


def get_health_models():
    """Fetch available_models from API when server is up (includes cloud models)."""
    try:
        r = requests.get(f"{get_api_url()}/health", timeout=2)
        if r.status_code != 200:
            return {}
        data = r.json()
        models = {}
        for name in data.get("available_models", []):
            if name not in MODELS and name not in models:
                models[name] = f"☁️ {name}" if "/" in name else f"📦 {name}"
        return models
    except Exception:
        return {}


def get_all_models():
    """Merge base MODELS with ollama list and API available_models (cloud)."""
    combined = dict(MODELS)
    for k, v in get_ollama_models().items():
        if k not in combined:
            combined[k] = v
    for k, v in get_health_models().items():
        if k not in combined:
            combined[k] = v
    return combined


def start_server(model="qwen2.5-coder:7b"):
    """Start janet_api_server with given model (python -u for unbuffered logs)."""
    log_path = SERVER_LOG
    cmd = f"""
    cd {JANET_DIR} && \
    OLLAMA_NUM_GPU=0 \
    JANET_DEFAULT_MODEL={model!r} \
    python3 -u janet_api_server.py > {log_path!r} 2>&1 &
    """
    subprocess.run(cmd, shell=True)


class JanetMenuBar(rumps.App):
    def __init__(self):
        icon_path = Path(__file__).parent / "janet_icon_small.png"
        if icon_path.exists():
            super(JanetMenuBar, self).__init__("Janet", icon=str(icon_path), quit_button=None)
        else:
            super(JanetMenuBar, self).__init__("🌱", quit_button=None)
        self.current_model = None
        self.update_menu()

    def update_menu(self):
        """Update menu with current status"""
        self.menu.clear()

        # Get current status
        try:
            response = requests.get(f"{get_api_url()}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.current_model = data.get("current_model", "Unknown")
                status = "🟢 Online"
                is_online = True
            else:
                status = "🔴 Offline"
                self.current_model = None
                is_online = False
        except Exception:
            status = "🔴 Offline"
            self.current_model = None
            is_online = False

        # Status section
        self.menu.add(rumps.MenuItem(f"Janet Status: {status}", callback=None))
        models_all = get_all_models()
        if self.current_model:
            model_display = models_all.get(self.current_model, self.current_model)
            self.menu.add(rumps.MenuItem(f"Current: {model_display}", callback=None))
        self.menu.add(rumps.separator)

        # Model selection
        self.menu.add(rumps.MenuItem("Switch Model:", callback=None))
        for model_id, model_name in models_all.items():
            is_current = model_id == self.current_model
            prefix = "✓ " if is_current else "   "
            menu_item = rumps.MenuItem(f"{prefix}{model_name}", callback=self.switch_model)
            menu_item.model_id = model_id
            self.menu.add(menu_item)

        self.menu.add(rumps.separator)

        # Actions: Start Server when offline, Restart when online
        if is_online:
            self.menu.add(rumps.MenuItem("🔄 Restart Server", callback=self.restart_server))
        else:
            self.menu.add(rumps.MenuItem("▶️ Start Server", callback=self.start_server))
        self.menu.add(rumps.MenuItem("📊 View Logs", callback=self.view_logs))
        self.menu.add(rumps.MenuItem("🔧 Open Config", callback=self.open_config))
        self.menu.add(rumps.MenuItem("💬 New chat with Janet (Aider)", callback=self.quick_aider))
        self.menu.add(rumps.MenuItem("🔄 Restart menu bar", callback=self.restart_menubar))

        # Settings submenu
        settings_menu = rumps.MenuItem("⚙️ Settings", callback=None)
        settings_menu.add(rumps.MenuItem("API URL…", callback=self.settings_api_url))
        mem_menu = rumps.MenuItem("Memory", callback=None)
        config = load_menubar_config()
        inactivity = config.get("inactivity_min", 10)
        for mins in INACTIVITY_OPTIONS:
            item = rumps.MenuItem(f"{'✓ ' if inactivity == mins else '   '} {mins} min", callback=self.settings_inactivity)
            item.inactivity_min = mins
            mem_menu.add(item)
        save_idle = config.get("save_context_when_idle", True)
        mem_menu.add(rumps.separator)
        mem_menu.add(rumps.MenuItem("Remember conversations after idle: " + ("On" if save_idle else "Off"), callback=self.settings_toggle_save_idle))
        settings_menu.add(mem_menu)
        self.menu.add(settings_menu)

        # Quick actions
        quick_menu = rumps.MenuItem("Quick actions", callback=None)
        quick_menu.add(rumps.MenuItem("What can you do?", callback=self.quick_what_can_you_do))
        quick_menu.add(rumps.MenuItem("Open Janet docs", callback=self.quick_open_docs))
        self.menu.add(quick_menu)

        # Pull model submenu (offline/online via ollama pull)
        if shutil.which("ollama"):
            pull_menu = rumps.MenuItem("📥 Pull model", callback=None)
            for mid in PULL_PRESETS:
                label = MODELS.get(mid, mid)
                item = rumps.MenuItem(f"Pull {label}", callback=self.pull_model)
                item.model_id = mid
                pull_menu.add(item)
            pull_menu.add(rumps.MenuItem("Other…", callback=self.pull_model_other))
            self.menu.add(pull_menu)
        else:
            self.menu.add(rumps.MenuItem("📥 Pull model (Ollama required)", callback=None))

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("❌ Quit", callback=self.quit_app))

    def start_server_action(self, model="qwen2.5-coder:7b"):
        """Start server (used when offline or for model switch)"""
        rumps.notification(
            title="Janet",
            subtitle="Starting Server...",
            message=f"Model: {get_all_models().get(model, model)}",
            sound=False,
        )
        subprocess.run(["pkill", "-f", "janet_api_server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start_server(model)
        config = load_menubar_config()
        config["last_model"] = model
        save_menubar_config(config)
        time.sleep(3)
        self.update_menu()
        rumps.notification(
            title="Janet",
            subtitle="Server Started!",
            message=f"Running on {get_all_models().get(model, model)}",
            sound=True,
        )

    def start_server(self, _):
        """Start Janet server when offline (use last model from config)."""
        config = load_menubar_config()
        model = config.get("last_model") or self.current_model or "qwen2.5-coder:7b"
        self.start_server_action(model)

    def switch_model(self, sender):
        """Switch to a different model"""
        model_id = sender.model_id
        models_all = get_all_models()
        rumps.notification(
            title="Janet",
            subtitle="Switching Model...",
            message=f"Switching to {models_all.get(model_id, model_id)}",
            sound=False,
        )
        subprocess.run(["pkill", "-f", "janet_api_server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start_server(model_id)
        config = load_menubar_config()
        config["last_model"] = model_id
        save_menubar_config(config)
        time.sleep(3)
        self.update_menu()
        rumps.notification(
            title="Janet",
            subtitle="Model Switched!",
            message=f"Now using {models_all.get(model_id, model_id)}",
            sound=True,
        )

    def restart_server(self, _):
        """Restart Janet server with current model"""
        model = self.current_model or "qwen2.5-coder:7b"
        models_all = get_all_models()
        rumps.notification(
            title="Janet",
            subtitle="Restarting Server...",
            message="Please wait...",
            sound=False,
        )
        subprocess.run(["pkill", "-f", "janet_api_server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start_server(model)
        time.sleep(3)
        self.update_menu()
        rumps.notification(
            title="Janet",
            subtitle="Server Restarted!",
            message=f"Running on {models_all.get(model, model)}",
            sound=True,
        )

    def _refresh_menu_after_pull(self):
        """Called on main thread after a pull completes to refresh model list."""
        self.update_menu()

    def _run_pull_and_notify(self, model_name):
        """Background thread: run ollama pull, then notify and refresh menu on main thread."""
        rumps.notification(
            title="Janet",
            subtitle="Pulling model...",
            message=model_name,
            sound=False,
        )
        try:
            proc = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=3600,
            )
            success = proc.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            success = False
            model_name = f"{model_name} ({e!s})"
        if success:
            rumps.notification(
                title="Janet",
                subtitle="Pulled model",
                message=model_name,
                sound=True,
            )
        else:
            rumps.notification(
                title="Janet",
                subtitle="Pull failed",
                message=str(model_name),
                sound=False,
            )
        try:
            from Foundation import NSObject
            from PyObjC import objc
            sel = objc.selector(JanetMenuBar._refresh_menu_after_pull, signature=b"v@:")
            self.performSelectorOnMainThread_withObject_waitUntilDone_(sel, None, False)
        except Exception:
            pass

    def pull_model(self, sender):
        """Pull a preset model via ollama pull (background)."""
        if not hasattr(sender, "model_id"):
            return
        model_id = sender.model_id
        if not shutil.which("ollama"):
            rumps.notification(
                title="Janet",
                subtitle="Ollama required",
                message="Install Ollama (e.g. brew install ollama) or run setup.",
                sound=False,
            )
            return
        t = threading.Thread(target=self._run_pull_and_notify, args=(model_id,), daemon=True)
        t.start()

    def pull_model_other(self, _):
        """Ask for model name via osascript then pull (macOS)."""
        if not shutil.which("ollama"):
            rumps.notification(
                title="Janet",
                subtitle="Ollama required",
                message="Install Ollama (e.g. brew install ollama) or run setup.",
                sound=False,
            )
            return
        try:
            out = subprocess.run(
                [
                    "osascript", "-e",
                    'text returned of (display dialog "Model name (e.g. llama3.2:latest):" default answer "llama3.2:latest")',
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            name = (out.stdout or "").strip() if out.returncode == 0 else ""
            if not name:
                return
        except Exception:
            return
        t = threading.Thread(target=self._run_pull_and_notify, args=(name,), daemon=True)
        t.start()

    def view_logs(self, _):
        """Open logs in Console.app"""
        log_path = SERVER_LOG
        if Path(log_path).exists():
            subprocess.run(["open", "-a", "Console", log_path])
        else:
            rumps.notification(
                title="Janet",
                subtitle="No logs yet",
                message="Start the server first",
                sound=False,
            )

    def settings_api_url(self, _):
        """Edit API URL via dialog and save to config."""
        config = load_menubar_config()
        current = config.get("api_url") or os.environ.get("JANET_API_URL", DEFAULT_API_URL)
        try:
            out = subprocess.run(
                [
                    "osascript", "-e",
                    f'text returned of (display dialog "Janet API URL:" default answer "{current}")',
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            url = (out.stdout or "").strip() if out.returncode == 0 else ""
            if url:
                config["api_url"] = url
                save_menubar_config(config)
                self.update_menu()
                rumps.notification(title="Janet", subtitle="API URL saved", message=url, sound=False)
        except Exception as e:
            rumps.notification(title="Janet", subtitle="Could not save", message=str(e), sound=False)

    def settings_inactivity(self, sender):
        """Set inactivity flush (minutes) and refresh menu."""
        mins = getattr(sender, "inactivity_min", 10)
        config = load_menubar_config()
        config["inactivity_min"] = mins
        save_menubar_config(config)
        self.update_menu()
        rumps.notification(title="Janet", subtitle="Memory", message=f"Inactivity flush: {mins} min", sound=False)

    def settings_toggle_save_idle(self, _):
        """Toggle 'Remember conversations after idle'."""
        config = load_menubar_config()
        config["save_context_when_idle"] = not config.get("save_context_when_idle", True)
        save_menubar_config(config)
        self.update_menu()
        on_off = "On" if config["save_context_when_idle"] else "Off"
        rumps.notification(title="Janet", subtitle="Remember after idle", message=on_off, sound=False)

    def quick_aider(self, _):
        """Open new Terminal and run Aider (chat with Janet). Uses Documents/.aider.conf.yml if present."""
        if not shutil.which("aider"):
            rumps.notification(
                title="Janet",
                subtitle="Aider not found",
                message="Install: curl -LsSf https://aider.chat/install.sh | sh",
                sound=False,
            )
            return
        # Open Terminal and run aider from Documents (picks up .aider.conf.yml)
        cmd = "cd ~/Documents && aider"
        try:
            subprocess.run(
                ["osascript", "-e", f'tell application "Terminal" to do script "{cmd}"'],
                check=True,
                timeout=5,
            )
        except Exception as e:
            rumps.notification(
                title="Janet",
                subtitle="Could not launch Aider",
                message=str(e),
                sound=False,
            )

    def quick_what_can_you_do(self, _):
        """Open abilities/capabilities doc (ABILITIES_MAP or Superpowers)."""
        for path in [
            JANET_DIR.parent.parent / "Janet-Superpowers" / "docs" / "agent" / "ABILITIES_MAP.md",
            JANET_DIR.parent.parent / "Janet-Superpowers" / "ABILITIES_MAP.md",
            Path.home() / "Documents" / "Janet-Projects" / "Janet-Superpowers" / "docs" / "agent" / "ABILITIES_MAP.md",
        ]:
            if path.exists():
                subprocess.run(["open", str(path)])
                return
        rumps.notification(title="Janet", subtitle="What can you do?", message="ABILITIES_MAP.md not found", sound=False)

    def quick_open_docs(self, _):
        """Open Janet docs (QUICK_START or INDEX)."""
        for path in [
            JANET_DIR.parent.parent / "Janet-Awakening" / "QUICK_START.md",
            JANET_DIR.parent.parent / "Janet-Awakening" / "INDEX.md",
            Path.home() / "Documents" / "Janet-Projects" / "Janet-Awakening" / "QUICK_START.md",
        ]:
            if path.exists():
                subprocess.run(["open", str(path)])
                return
        rumps.notification(title="Janet", subtitle="Docs", message="QUICK_START not found", sound=False)

    def open_config(self, _):
        """Open Continue.dev config with editor-agnostic app"""
        config_path = CONFIG_PATH
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.touch()
        editor = os.environ.get("CONTINUE_EDITOR")
        if editor:
            # Known editors: Cursor, Visual Studio Code, Zed
            app_map = {
                "cursor": "Cursor",
                "vscode": "Visual Studio Code",
                "code": "Visual Studio Code",
                "zed": "Zed",
            }
            app_name = app_map.get(editor.lower(), editor)
            subprocess.run(["open", "-a", app_name, str(config_path)])
        else:
            # Fallback: open with default app for .json
            subprocess.run(["open", str(config_path)])

    def restart_menubar(self, _):
        """Restart menu bar via LaunchAgent unload/reload (avoids KeepAlive restart loop)."""
        plist = Path.home() / "Library/LaunchAgents/com.janet.plist"
        if not plist.exists():
            rumps.notification(
                title="Janet",
                subtitle="Not running as LaunchAgent",
                message="Restart manually: python3 janet_menubar.py",
                sound=False,
            )
            return
        # Run in detached process so it survives when we get killed by unload
        script = f'sleep 1; launchctl unload "{plist}"; sleep 2; launchctl load "{plist}"'
        subprocess.Popen(
            ["bash", "-c", script],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        rumps.notification(
            title="Janet",
            subtitle="Restarting menu bar…",
            message="Will reload in a few seconds",
            sound=False,
        )

    def quit_app(self, _):
        """Quit the app. atexit handler unloads LaunchAgent so launchd won't restart us."""
        rumps.quit_application()


if __name__ == "__main__":
    app = JanetMenuBar()
    app.run()
