"""
Model Manager — Offline-First Model Detection and Installation Guidance

Handles detection, verification, and offline installation guidance for Ollama models.
Never auto-downloads - only provides instructions.
"""

import subprocess
import sys
import platform
import shutil
import socket
from pathlib import Path
from typing import List, Tuple, Optional


class ModelManager:
    """Manages Ollama model detection, verification, and offline installation."""
    
    def __init__(self):
        """Initialize model manager."""
        self.ollama_path = self._find_ollama_path()
    
    def _find_ollama_path(self) -> Optional[Path]:
        """Find Ollama executable path."""
        if shutil.which("ollama"):
            return Path(shutil.which("ollama"))
        return None
    
    def verify_ollama_model(self, model_name: str) -> bool:
        """
        Check if an Ollama model exists locally.
        
        Args:
            model_name: Model name (e.g., "tinyllama:1.1b", "deepseek-coder:6.7b")
        
        Returns:
            True if model is available locally
        """
        if not self.ollama_path:
            return False
        
        try:
            result = subprocess.run(
                [str(self.ollama_path), "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Check if model name appears in output
                return model_name in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        return False
    
    def list_available_models(self) -> List[str]:
        """
        List all locally available Ollama models.
        
        Returns:
            List of model names (e.g., ["tinyllama:1.1b", "deepseek-coder:6.7b"])
        """
        if not self.ollama_path:
            return []
        
        try:
            result = subprocess.run(
                [str(self.ollama_path), "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                models = []
                lines = result.stdout.strip().split('\n')
                # Skip header line
                for line in lines[1:]:
                    if line.strip():
                        # Extract model name (first column)
                        parts = line.split()
                        if parts:
                            models.append(parts[0])
                return models
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        return []
    
    def detect_missing_models(self, required: List[str]) -> List[str]:
        """
        Compare required models vs available, return missing ones.
        
        Args:
            required: List of required model names
        
        Returns:
            List of missing model names
        """
        available = self.list_available_models()
        missing = []
        
        for model in required:
            # Check exact match or partial match (e.g., "deepseek-coder" matches "deepseek-coder:6.7b")
            found = False
            for avail in available:
                if model == avail or model in avail or avail in model:
                    found = True
                    break
            if not found:
                missing.append(model)
        
        return missing
    
    def get_ollama_model_path(self) -> Path:
        """
        Get platform-specific Ollama model directory.
        
        Returns:
            Path to Ollama models directory
        """
        system = platform.system()
        home = Path.home()
        
        if system == "Darwin":  # macOS
            return home / ".ollama" / "models"
        elif system == "Linux":
            return home / ".ollama" / "models"
        elif system == "Windows":
            return home / ".ollama" / "models"
        else:
            # Fallback
            return home / ".ollama" / "models"
    
    def check_network_available(self) -> bool:
        """
        Check if network connection is available (with consent).
        This is a simple check - doesn't guarantee internet access.
        
        Returns:
            True if network interface appears active
        """
        try:
            # Try to connect to a well-known DNS server (non-blocking check)
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except (OSError, socket.timeout, socket.error):
            return False
    
    def generate_offline_installation_instructions(self, model_name: str) -> str:
        """
        Generate step-by-step offline installation instructions.
        
        Args:
            model_name: Model name to install (e.g., "deepseek-coder:6.7b")
        
        Returns:
            Formatted instruction string
        """
        model_path = self.get_ollama_model_path()
        system = platform.system()
        
        instructions = f"""
📋 Offline Installation Guide for {model_name}

Since we're working offline, here's how to add this model manually:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: Download on a Connected Device
────────────────────────────────────────
On a device with internet access, run:
  ollama pull {model_name}

This will download the model files to the Ollama models directory.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2: Find the Model Files
─────────────────────────────
The model files will be located at:
"""
        
        if system == "Darwin":  # macOS
            instructions += f"  macOS: ~/.ollama/models/\n"
            instructions += f"  Full path: {model_path}\n"
        elif system == "Linux":
            instructions += f"  Linux: ~/.ollama/models/\n"
            instructions += f"  Full path: {model_path}\n"
        elif system == "Windows":
            instructions += f"  Windows: C:\\Users\\YourName\\.ollama\\models\\\n"
            instructions += f"  Full path: {model_path}\n"
        else:
            instructions += f"  Path: {model_path}\n"
        
        instructions += f"""
Look for a directory or files related to: {model_name.split(':')[0]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3: Transfer Files to This Device
──────────────────────────────────────
Copy the model files to this device using one of these methods:

  • USB drive: Copy files to USB, then copy to target location
  • Network share: If devices are on same network, use file sharing
  • Local network: Use scp, rsync, or file sharing protocol
  • External drive: Copy via external storage device

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4: Place Files in Correct Location
────────────────────────────────────────
On THIS device, place the files at:
  {model_path}

Make sure the directory structure matches what Ollama expects.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 5: Verify Installation
───────────────────────────
When ready, I'll verify the installation by running:
  ollama list

This should show {model_name} in the list.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TROUBLESHOOTING
───────────────
• If model doesn't appear: Check file permissions and directory structure
• If Ollama can't find model: Ensure files are in the correct location
• If verification fails: Try running 'ollama list' manually to check

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When you've completed these steps, let me know and I'll verify the installation.
"""
        
        return instructions
    
    def verify_model_installation(self, model_name: str) -> Tuple[bool, str]:
        """
        Verify that a model is properly installed and accessible.
        
        Args:
            model_name: Model name to verify
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.ollama_path:
            return False, "Ollama not found. Please install Ollama first."
        
        # Check if model exists
        if not self.verify_ollama_model(model_name):
            return False, f"Model {model_name} not found. Please complete installation steps."
        
        # Try to verify model is actually usable (lightweight check)
        try:
            # Just check if model appears in list - full test would require running it
            result = subprocess.run(
                [str(self.ollama_path), "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and model_name in result.stdout:
                return True, f"Model {model_name} verified and ready to use."
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            return False, f"Verification failed: {e}"
        
        return False, f"Model {model_name} not found in Ollama list."
    
    def get_learning_capable_models(self) -> List[str]:
        """
        Get list of models suitable for learning/fine-tuning.
        
        These are small models that can be fine-tuned efficiently.
        
        Returns:
            List of recommended model names for learning
        """
        return [
            "tinyllama:1.1b",
            "phi-2:2.7b",
            "qwen2.5:0.5b",
            "llama3.2:1b"
        ]
    
    def suggest_learning_model(self) -> Optional[str]:
        """
        Suggest a learning-capable model based on available models.
        
        Returns:
            Model name to use for learning, or None if none available
        """
        available = self.list_available_models()
        recommended = self.get_learning_capable_models()
        
        # Check if any recommended models are available
        for model in recommended:
            for avail in available:
                if model in avail or avail in model:
                    return avail
        
        # If none available, suggest the smallest one
        if recommended:
            return recommended[0]
        
        return None
    
    def verify_fine_tuning_support(self, model_name: str) -> Tuple[bool, str]:
        """
        Verify if a model supports fine-tuning.
        
        Note: This is a basic check. Full verification would require
        checking model architecture and available libraries.
        
        Args:
            model_name: Model name to check
            
        Returns:
            Tuple of (supports_finetuning: bool, message: str)
        """
        # Check if model is available
        if not self.verify_ollama_model(model_name):
            return False, f"Model {model_name} not available"
        
        # Check if fine-tuning dependencies are available
        try:
            import transformers
            import peft
            import torch
            deps_available = True
        except ImportError:
            deps_available = False
        
        if not deps_available:
            return False, "Fine-tuning dependencies not installed. Install with: pip install transformers peft accelerate torch"
        
        # Small models are generally fine-tunable
        small_models = ["tinyllama", "phi-2", "qwen2.5", "llama3.2"]
        model_base = model_name.split(":")[0].lower()
        
        if any(small in model_base for small in small_models):
            return True, f"Model {model_name} appears suitable for fine-tuning"
        else:
            return True, f"Model {model_name} may be fine-tunable, but larger models require more resources"
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a model.
        
        Args:
            model_name: Model name
            
        Returns:
            Dictionary with model information
        """
        is_available = self.verify_ollama_model(model_name)
        supports_finetuning, finetuning_msg = self.verify_fine_tuning_support(model_name)
        
        return {
            "name": model_name,
            "available": is_available,
            "supports_finetuning": supports_finetuning,
            "finetuning_message": finetuning_msg,
            "recommended_for_learning": model_name in self.get_learning_capable_models()
        }

