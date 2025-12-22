"""
Model Installation Wizard — Offline-First Model Setup

Guides users through installing Ollama models offline or online.
"""

from pathlib import Path
from typing import Optional
from .wizard_base import ExpansionWizard
from ..model_manager import ModelManager


class ModelInstallationWizard(ExpansionWizard):
    """Wizard for installing Ollama models offline-first."""
    
    def __init__(self, config_path: Path, model_name: str, janet_core=None):
        """
        Initialize model installation wizard.
        
        Args:
            config_path: Path to config directory
            model_name: Name of model to install (e.g., "deepseek-coder:6.7b")
            janet_core: Optional JanetCore instance
        """
        super().__init__(config_path, janet_core)
        self.model_name = model_name
        self.model_manager = ModelManager()
    
    def run(self) -> bool:
        """
        Run the model installation wizard.
        
        Returns:
            True if installation complete
        """
        print(f"\n{'='*60}")
        print(f"🔧 Model Installation Wizard: {self.model_name}")
        print(f"{'='*60}\n")
        
        # Step 1: Check if model already exists
        if self.model_manager.verify_ollama_model(self.model_name):
            print(f"✅ Model {self.model_name} is already installed!")
            return True
        
        # Step 2: Check network availability (optional, with consent)
        has_network = self.check_network_available()
        
        # Step 3: Present installation options
        if has_network:
            print("🌐 Network connection detected.")
            print("\nYou have two options:")
            print("  1. Download now (requires internet)")
            print("  2. Install offline (manual transfer)")
            
            while True:
                choice = input("\nChoose option (1/2): ").strip()
                if choice == "1":
                    return self._install_online()
                elif choice == "2":
                    return self._install_offline()
                else:
                    print("Please enter 1 or 2")
        else:
            print("📴 No network connection detected.")
            return self._install_offline()
    
    def _install_online(self) -> bool:
        """Install model using online download (with consent)."""
        print(f"\n📥 Downloading {self.model_name}...")
        print("This may take a while depending on model size and connection speed.")
        
        # Get explicit consent
        response = input("Proceed with download? (yes/NO): ").strip().lower()
        if response not in ["yes", "y"]:
            print("Download cancelled. You can install offline later.")
            return False
        
        # Check if Ollama is available
        if not self.model_manager.ollama_path:
            print("❌ Ollama not found. Please install Ollama first.")
            return False
        
        # Download model
        try:
            import subprocess
            result = subprocess.run(
                [str(self.model_manager.ollama_path), "pull", self.model_name],
                check=True,
                timeout=1800  # 30 minute timeout
            )
            print(f"✅ Model {self.model_name} downloaded successfully!")
            
            # Verify installation
            return self.verify()
        except subprocess.TimeoutExpired:
            print("❌ Download timed out. You can try again or install offline.")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Download failed: {e}")
            print("You can try installing offline instead.")
            return False
        except FileNotFoundError:
            print("❌ Ollama not found. Please install Ollama first.")
            return False
    
    def _install_offline(self) -> bool:
        """Guide user through offline installation."""
        print("\n📋 Offline Installation Guide")
        print("="*60)
        
        # Generate and display instructions
        instructions = self.model_manager.generate_offline_installation_instructions(self.model_name)
        print(instructions)
        
        # Wait for user to complete steps
        print("\n" + "="*60)
        while True:
            response = input("\nHave you completed the installation steps? (yes/no/verify): ").strip().lower()
            
            if response in ["yes", "y"]:
                # Verify installation
                if self.verify():
                    print(f"✅ Model {self.model_name} verified and ready to use!")
                    return True
                else:
                    print("❌ Verification failed. Please check the installation steps.")
                    retry = input("Try verifying again? (yes/no): ").strip().lower()
                    if retry not in ["yes", "y"]:
                        return False
            elif response == "verify":
                if self.verify():
                    print(f"✅ Model {self.model_name} verified and ready to use!")
                    return True
                else:
                    print("❌ Verification failed. Please check the installation steps.")
            elif response in ["no", "n"]:
                print("You can complete the installation later and verify it then.")
                return False
            else:
                print("Please respond with: yes, no, or verify")
    
    def validate_requirements(self) -> Tuple[bool, List[str]]:
        """Validate that requirements are met."""
        missing = []
        
        if not self.model_manager.ollama_path:
            missing.append("Ollama not installed")
        
        return len(missing) == 0, missing
    
    def setup(self) -> bool:
        """Setup is handled in run() method."""
        return self.run()
    
    def verify(self) -> bool:
        """Verify that model is installed correctly."""
        success, message = self.model_manager.verify_model_installation(self.model_name)
        if not success:
            print(f"❌ {message}")
        else:
            print(f"✅ {message}")
        return success
    
    def cleanup_on_failure(self):
        """Cleanup on failure (nothing to clean up for model installation)."""
        pass
    
    def generate_offline_instructions(self) -> str:
        """Generate offline installation instructions."""
        return self.model_manager.generate_offline_installation_instructions(self.model_name)

