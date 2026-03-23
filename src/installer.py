"""
Janet Seed Installation Module
Handles offline-first installation of Janet core components.
"""
import os
import sys
import subprocess
import shutil
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

class Installer:
    """Handles installation of Janet Seed."""
    
    def __init__(self, janet_home: str, source_dir: str):
        self.janet_home = Path(janet_home).expanduser().resolve()
        self.source_dir = Path(source_dir).resolve()
        self.venv_path = self.janet_home / "venv"
        self.config_path = self.janet_home / "config"
        self.constitution_path = self.janet_home / "constitution"
        self.logs_path = self.janet_home / "logs"
        
    def is_installed(self) -> bool:
        """Check if Janet is already installed."""
        return (self.janet_home.exists() and 
                (self.janet_home / "config" / "installation.json").exists())
    
    def install(self, hardware_profile: Dict, constitution_hash: str) -> bool:
        """Perform complete installation."""
        try:
            print("\n🛠️  Installing Janet Seed...")
            
            # Create directory structure
            self._create_directories()
            
            # Set up Python virtual environment
            self._setup_venv()
            
            # Install dependencies
            self._install_dependencies()
            
            # Install Ollama (if needed)
            self._ensure_ollama()
            
            # Download model
            self._download_model()
            
            # Install Janet Core files
            self._install_core_files()
            
            # Create launch scripts
            self._create_launch_scripts()
            
            # Create installation record
            self._create_installation_record(hardware_profile, constitution_hash)
            
            print("\n✅ Installation complete!")
            return True
            
        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            return False
    
    def _create_directories(self):
        """Create Janet directory structure."""
        print("Creating directory structure...")
        for path in [self.janet_home, self.config_path, self.constitution_path, 
                     self.logs_path, self.janet_home / "models"]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _setup_venv(self):
        """Create Python virtual environment."""
        print("Setting up Python virtual environment...")
        if self.venv_path.exists():
            print("  Virtual environment already exists, skipping...")
            return
        
        subprocess.run(
            [sys.executable, "-m", "venv", str(self.venv_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    def _install_dependencies(self):
        """Install Python dependencies."""
        print("Installing dependencies...")
        requirements_file = self.source_dir / "requirements.txt"

        if not requirements_file.exists():
            print("  ⚠️  requirements.txt not found, skipping dependency installation")
            return
        
        # Determine pip path based on platform
        if sys.platform == "win32":
            pip_path = self.venv_path / "Scripts" / "pip"
        else:
            pip_path = self.venv_path / "bin" / "pip"
        
        # Upgrade pip first
        print("  Upgrading pip...")
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Install core dependencies first (Seed Mode essentials)
        core_deps = ["psutil>=5.9.0"]
        print("  Installing core dependencies...")
        for dep in core_deps:
            try:
                result = subprocess.run(
                    [str(pip_path), "install", dep],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"    ✅ {dep}")
            except subprocess.CalledProcessError as e:
                print(f"    ❌ Failed to install {dep}: {e.stderr}")
                raise
        
        # Try to install remaining dependencies, but allow failures for optional packages (voice, memory, delegation, learning)
        print("  Installing additional dependencies (some may be optional for Seed Mode)...")
        try:
            result = subprocess.run(
                [str(pip_path), "install", "-r", str(requirements_file)],
                check=False,  # Don't fail if some packages can't be installed
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("  ✅ All dependencies installed successfully")
            else:
                print("  ⚠️  Some optional dependencies failed to install (this is OK for Seed Mode)")
                print("      You can install them later when needed for advanced features (voice, memory, delegation, learning)")
                # Show which packages failed
                if "error" in result.stderr.lower() or "failed" in result.stderr.lower():
                    # Extract package names that failed
                    lines = result.stderr.split('\n')
                    for line in lines:
                        if "error" in line.lower() or "failed" in line.lower():
                            print(f"      {line.strip()}")
        except Exception as e:
            print(f"  ⚠️  Dependency installation encountered issues: {e}")
            print("      Installation will continue - Seed Mode core functionality should still work")
            print("      Note: Fine-tuning dependencies (transformers, torch, etc.) are large and optional")
            print("            They can be installed later when you're ready to use learning features")
    
    def _ensure_ollama(self):
        """Ensure Ollama is installed (with consent)."""
        print("Checking for Ollama...")
        if shutil.which("ollama"):
            print("  ✅ Ollama found")
            # Verify it's working
            try:
                result = subprocess.run(
                    ["ollama", "version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"  ✅ Ollama version: {result.stdout.strip()}")
                    return
            except Exception:
                pass
            print("  ⚠️  Ollama found but may not be working correctly")
        
        # Ollama not found - ask for consent to install (or use JANET_AUTO_INSTALL_OLLAMA=1)
        print("  ⚠️  Ollama not found.")
        print("  ℹ️  Ollama is required for Janet's LLM brain to function.")
        print("      Without it, Janet will not be able to generate responses.")
        
        if os.environ.get("JANET_AUTO_INSTALL_OLLAMA") != "1":
            response = input("  Install Ollama now? (yes/NO): ").strip().lower()
            if response not in ["yes", "y"]:
                print("  ⏭️  Ollama installation skipped.")
                print("  📋 You can install Ollama manually from https://ollama.com")
                print("      Or use the expansion protocol after startup to set it up.")
                return
        else:
            print("  📥 JANET_AUTO_INSTALL_OLLAMA=1: installing without prompt.")
        
        # User consented (or auto-install) - proceed with installation
        print("  📥 Installing Ollama...")
        
        if sys.platform == "win32":
            # Windows installation
            self._install_ollama_windows()
        elif sys.platform == "darwin":
            # macOS installation
            self._install_ollama_macos()
        elif sys.platform.startswith("linux"):
            # Linux installation
            self._install_ollama_linux()
        else:
            print(f"  ⚠️  Automatic Ollama installation not supported on {sys.platform}")
            print("  📋 Please install Ollama manually from https://ollama.com")
            return
        
        # Verify installation
        if shutil.which("ollama"):
            print("  ✅ Ollama installed successfully")
            # Verify it works
            try:
                result = subprocess.run(
                    ["ollama", "version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"  ✅ Ollama version: {result.stdout.strip()}")
            except Exception as e:
                print(f"  ⚠️  Ollama installed but verification failed: {e}")
        else:
            print("  ⚠️  Ollama installation may have failed")
            print("  📋 Please verify installation manually: https://ollama.com")
    
    def _install_ollama_windows(self):
        """Install Ollama on Windows."""
        print("  Installing Ollama for Windows...")
        
        # Try winget first (Windows 10/11)
        try:
            result = subprocess.run(
                ["winget", "install", "--id", "Ollama.Ollama", "--source", "winget", "--accept-package-agreements", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print("  ✅ Ollama installed via winget")
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback: Direct download
        print("  ⚠️  winget not available, attempting direct download...")
        print("  📋 For best results, install Ollama manually from:")
        print("      https://ollama.com/download/windows")
        print("  Or install winget and run: winget install Ollama.Ollama")
    
    def _install_ollama_macos(self):
        """Install Ollama on macOS."""
        print("  Installing Ollama for macOS...")
        
        # Check for Homebrew
        if shutil.which("brew"):
            try:
                print("  Using Homebrew to install Ollama...")
                result = subprocess.run(
                    ["brew", "install", "ollama"],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if result.returncode == 0:
                    print("  ✅ Ollama installed via Homebrew")
                    return
            except subprocess.TimeoutExpired:
                print("  ⚠️  Homebrew installation timed out")
            except Exception as e:
                print(f"  ⚠️  Homebrew installation failed: {e}")
        
        # Fallback: Official installer script
        print("  Using official Ollama installer...")
        try:
            result = subprocess.run(
                ["curl", "-fsSL", "https://ollama.com/install.sh"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Execute the installer script
                install_script = subprocess.Popen(
                    ["sh"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = install_script.communicate(input=result.stdout, timeout=300)
                if install_script.returncode == 0:
                    print("  ✅ Ollama installed via official installer")
                    return
                else:
                    print(f"  ⚠️  Installation script failed: {stderr}")
        except subprocess.TimeoutExpired:
            print("  ⚠️  Installation timed out")
        except Exception as e:
            print(f"  ⚠️  Installation failed: {e}")
        
        print("  📋 Please install Ollama manually:")
        print("      brew install ollama")
        print("      Or visit: https://ollama.com/download/mac")
    
    def _install_ollama_linux(self):
        """Install Ollama on Linux."""
        print("  Installing Ollama for Linux...")
        
        try:
            # Use official installer script
            result = subprocess.run(
                ["curl", "-fsSL", "https://ollama.com/install.sh"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Execute the installer script
                install_script = subprocess.Popen(
                    ["sh"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = install_script.communicate(input=result.stdout, timeout=300)
                if install_script.returncode == 0:
                    print("  ✅ Ollama installed successfully")
                    return
                else:
                    print(f"  ⚠️  Installation script failed: {stderr}")
        except subprocess.TimeoutExpired:
            print("  ⚠️  Installation timed out")
        except FileNotFoundError:
            print("  ⚠️  curl not found. Please install curl first:")
            print("      sudo apt-get install curl  # Debian/Ubuntu")
            print("      sudo yum install curl      # RHEL/CentOS")
        except Exception as e:
            print(f"  ⚠️  Installation failed: {e}")
        
        print("  📋 Please install Ollama manually:")
        print("      curl -fsSL https://ollama.com/install.sh | sh")
        print("      Or visit: https://ollama.com/download/linux")
    
    def _download_model(self):
        """Handle model download with offline-first support."""
        try:
            from expansion.model_manager import ModelManager
        except ImportError:
            # Fallback if expansion module not available
            print("  ⚠️  Expansion module not available, using basic model check")
            if not shutil.which("ollama"):
                print("  ⚠️  Skipping model download (Ollama not available)")
                return
            # Basic check - don't auto-download
            print("  ℹ️  Model installation available via expansion protocol after startup")
            return
        
        model_manager = ModelManager()
        
        # Check if model already exists
        if model_manager.verify_ollama_model("tinyllama:1.1b"):
            print("  ✅ Model tinyllama:1.1b already installed")
            return
        
        # Check network availability (optional, with consent)
        has_network = model_manager.check_network_available()
        
        if not has_network:
            print("  ℹ️  No network connection detected.")
            print("  📋 To install models offline:")
            instructions = model_manager.generate_offline_installation_instructions("tinyllama:1.1b")
            print(instructions)
            print("\n  Installation will continue without model.")
            print("  You can add models later using the expansion protocol.")
            return
        
        # Network available - ask for explicit consent
        print("  🌐 Network connection detected.")
        print("  ⚠️  Model download requires internet access.")
        response = input("  Download tinyllama:1.1b now? (yes/NO): ").strip().lower()
        if response not in ["yes", "y"]:
            print("  ⏭️  Skipping model download. You can add it later using the expansion protocol.")
            print("  📋 For offline installation instructions, say 'what can you do?' to Janet after startup.")
            return
        
        # Proceed with download (with explicit consent)
        print("  📥 Downloading model (this may take a while)...")
        if not model_manager.ollama_path:
            print("  ⚠️  Skipping model download (Ollama not available)")
            print("  📋 Please install Ollama first, then use the expansion protocol to add models.")
            return
        
        try:
            subprocess.run(
                [str(model_manager.ollama_path), "pull", "tinyllama:1.1b"],
                check=True,
                timeout=600  # 10 minute timeout
            )
            print("  ✅ Model downloaded")
            
            # Verify installation
            if model_manager.verify_ollama_model("tinyllama:1.1b"):
                print("  ✅ Model verified and ready to use")
            else:
                print("  ⚠️  Model downloaded but verification failed")
        except subprocess.TimeoutExpired:
            print("  ⚠️  Model download timed out")
            print("  📋 You can install the model offline later using the expansion protocol.")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Model download failed: {e}")
            print("  📋 You can install the model offline later using the expansion protocol.")
        except FileNotFoundError:
            print("  ⚠️  Ollama not found")
            print("  📋 Please install Ollama first, then use the expansion protocol to add models.")
    
    def _install_core_files(self):
        """Install Janet Core source files."""
        print("Installing Janet Core files...")
        src_dir = self.source_dir / "src"
        dest_dir = self.janet_home / "src"
        
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(src_dir, dest_dir)
        
        # Copy constitution
        constitution_src = self.source_dir / "constitution"
        if constitution_src.exists():
            if self.constitution_path.exists():
                shutil.rmtree(self.constitution_path)
            shutil.copytree(constitution_src, self.constitution_path)
    
    def _create_launch_scripts(self):
        """Create platform-appropriate launch scripts."""
        print("Creating launch scripts...")
        
        if sys.platform == "win32":
            self._create_windows_scripts()
        else:
            self._create_unix_scripts()
    
    def _create_unix_scripts(self):
        """Create Unix (macOS/Linux) launch scripts."""
        # janet-start script
        start_script = self.janet_home / "janet-start"
        start_script.write_text(f"""#!/bin/bash
JANET_HOME="{self.janet_home}"
cd "$JANET_HOME"
source "$JANET_HOME/venv/bin/activate"
python -m src.main "$@"
""")
        start_script.chmod(0o755)
        
        # uninstall script
        uninstall_script = self.janet_home / "janet-uninstall"
        uninstall_script.write_text(f"""#!/bin/bash
echo "Uninstalling Janet..."
read -p "Are you sure? This will remove ALL Janet data. (yes/NO): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    JANET_HOME="{self.janet_home}"
    echo "Removing $JANET_HOME..."
    rm -rf "$JANET_HOME"
    echo "Janet has been uninstalled."
else
    echo "Uninstall cancelled."
fi
""")
        uninstall_script.chmod(0o755)
    
    def _create_windows_scripts(self):
        """Create Windows (PowerShell) launch scripts."""
        # Use forward slashes or escaped backslashes for PowerShell
        janet_home_ps = str(self.janet_home).replace("\\", "/")
        janet_home_escaped = str(self.janet_home).replace("\\", "\\\\")
        
        # janet-start.ps1 script
        start_script = self.janet_home / "janet-start.ps1"
        start_script.write_text(f"""$JANET_HOME = "{janet_home_ps}"
Set-Location $JANET_HOME
& "$JANET_HOME/venv/Scripts/Activate.ps1"
python -m src.main $args
""")
        
        # janet-start.bat wrapper  
        start_bat = self.janet_home / "janet-start.bat"
        start_script_bat = str(start_script).replace("/", "\\")
        start_bat.write_text(f"""@echo off
powershell.exe -ExecutionPolicy Bypass -File "{start_script_bat}" %*
""")
        
        # uninstall script
        uninstall_script = self.janet_home / "janet-uninstall.ps1"
        uninstall_script.write_text(f"""$JANET_HOME = "{janet_home_ps}"
Write-Host "Uninstalling Janet..."
$confirm = Read-Host "Are you sure? This will remove ALL Janet data. (yes/NO)"
if ($confirm -match "^[Yy]") {{
    Write-Host "Removing $JANET_HOME..."
    Remove-Item -Recurse -Force $JANET_HOME
    Write-Host "Janet has been uninstalled."
}} else {{
    Write-Host "Uninstall cancelled."
}}
""")
    
    def _create_installation_record(self, hardware_profile: Dict, constitution_hash: str):
        """Create installation metadata file."""
        installation_data = {
            "installed_at": datetime.utcnow().isoformat() + "Z",
            "platform": hardware_profile.get("platform", "unknown"),
            "version": "v0.1-seed",
            "constitution_hash": constitution_hash,
            "hardware": hardware_profile,
            "default_model": "tinyllama:1.1b"  # Default model for JanetBrain
        }
        
        installation_file = self.config_path / "installation.json"
        with open(installation_file, 'w') as f:
            json.dump(installation_data, f, indent=2)

