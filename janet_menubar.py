#!/usr/bin/env python3
"""
Janet Menu Bar Controller
A macOS menu bar app to control Janet's AI model
"""
import rumps
import subprocess
import requests
import json
from pathlib import Path

JANET_API_URL = "http://localhost:8080"
JANET_API_KEY = "janet-local-dev"
JANET_DIR = Path(__file__).parent

MODELS = {
    "qwen2.5-coder:7b": "🔧 Qwen2.5 Coder (Best for Code)",
    "qwen2:latest": "🤖 Qwen2 (General Purpose)",
    "llama3.2:latest": "⚡ Llama 3.2 (Fast)",
    "llama3.2-vision:11b": "👁️ Llama Vision (Images)",
    "llama2:latest": "🦙 Llama 2 (Classic)"
}


class JanetMenuBar(rumps.App):
    def __init__(self):
        # Try to use custom icon, fallback to emoji
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
            response = requests.get(f"{JANET_API_URL}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.current_model = data.get("current_model", "Unknown")
                status = "🟢 Online"
            else:
                status = "🔴 Offline"
                self.current_model = None
        except:
            status = "🔴 Offline"
            self.current_model = None
        
        # Status section
        self.menu.add(rumps.MenuItem(f"Janet Status: {status}", callback=None))
        if self.current_model:
            model_display = MODELS.get(self.current_model, self.current_model)
            self.menu.add(rumps.MenuItem(f"Current: {model_display}", callback=None))
        self.menu.add(rumps.separator)
        
        # Model selection
        self.menu.add(rumps.MenuItem("Switch Model:", callback=None))
        for model_id, model_name in MODELS.items():
            is_current = (model_id == self.current_model)
            prefix = "✓ " if is_current else "   "
            menu_item = rumps.MenuItem(f"{prefix}{model_name}", callback=self.switch_model)
            menu_item.model_id = model_id
            self.menu.add(menu_item)
        
        self.menu.add(rumps.separator)
        
        # Actions
        self.menu.add(rumps.MenuItem("🔄 Restart Server", callback=self.restart_server))
        self.menu.add(rumps.MenuItem("📊 View Logs", callback=self.view_logs))
        self.menu.add(rumps.MenuItem("🔧 Open Config", callback=self.open_config))
        
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("❌ Quit", callback=self.quit_app))
    
    def switch_model(self, sender):
        """Switch to a different model"""
        model_id = sender.model_id
        
        # Show notification
        rumps.notification(
            title="Janet",
            subtitle="Switching Model...",
            message=f"Switching to {MODELS[model_id]}",
            sound=False
        )
        
        # Stop current server
        subprocess.run(["pkill", "-f", "janet_api_server"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        
        # Start with new model
        cmd = f"""
        cd {JANET_DIR} && \
        OLLAMA_NUM_GPU=0 \
        JANET_DEFAULT_MODEL={model_id} \
        python3 janet_api_server.py > /tmp/janet_server.log 2>&1 &
        """
        subprocess.run(cmd, shell=True)
        
        # Wait and update
        import time
        time.sleep(3)
        self.update_menu()
        
        rumps.notification(
            title="Janet",
            subtitle="Model Switched!",
            message=f"Now using {MODELS[model_id]}",
            sound=True
        )
    
    def restart_server(self, _):
        """Restart Janet server with current model"""
        model = self.current_model or "qwen2.5-coder:7b"
        
        rumps.notification(
            title="Janet",
            subtitle="Restarting Server...",
            message="Please wait...",
            sound=False
        )
        
        # Stop and restart
        subprocess.run(["pkill", "-f", "janet_api_server"],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
        
        cmd = f"""
        cd {JANET_DIR} && \
        OLLAMA_NUM_GPU=0 \
        JANET_DEFAULT_MODEL={model} \
        python3 janet_api_server.py > /tmp/janet_server.log 2>&1 &
        """
        subprocess.run(cmd, shell=True)
        
        import time
        time.sleep(3)
        self.update_menu()
        
        rumps.notification(
            title="Janet",
            subtitle="Server Restarted!",
            message=f"Running on {MODELS.get(model, model)}",
            sound=True
        )
    
    def view_logs(self, _):
        """Open logs in Console.app"""
        subprocess.run(["open", "-a", "Console", "/tmp/janet_server.log"])
    
    def open_config(self, _):
        """Open Continue.dev config"""
        subprocess.run(["open", "-a", "Cursor", 
                       str(Path.home() / ".continue/config.json")])
    
    def quit_app(self, _):
        """Quit the app"""
        rumps.quit_application()


if __name__ == "__main__":
    app = JanetMenuBar()
    app.run()
