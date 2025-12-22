"""
Delegation Wizard — Task Delegation Setup

Guides users through setting up task delegation capabilities.
"""

from pathlib import Path
from typing import Tuple, List
from .wizard_base import ExpansionWizard
from ..model_manager import ModelManager


class DelegationWizard(ExpansionWizard):
    """Wizard for setting up task delegation."""
    
    def __init__(self, config_path: Path, memory_dir: Path = None, janet_core=None):
        """
        Initialize delegation wizard.
        
        Args:
            config_path: Path to config directory
            memory_dir: Optional memory directory
            janet_core: Optional JanetCore instance
        """
        super().__init__(config_path, janet_core)
        self.memory_dir = Path(memory_dir) if memory_dir else None
        self.model_manager = ModelManager()
    
    def run(self) -> bool:
        """Run the delegation setup wizard."""
        print(f"\n{'='*60}")
        print("🔀 Task Delegation Setup Wizard")
        print(f"{'='*60}\n")
        
        # Validate requirements
        valid, missing = self.validate_requirements()
        if not valid:
            print("❌ Requirements not met:")
            for req in missing:
                print(f"  • {req}")
            return False
        
        # Check dependencies
        print("Checking dependencies...")
        deps_ok = self._check_dependencies()
        if not deps_ok:
            print("\n⚠️  Some dependencies are missing.")
            print("You'll need to install:")
            print("  • litellm (for model routing)")
            print("\nInstall with: pip install litellm")
            return False
        
        # Check for models
        print("\nChecking available models...")
        available_models = self.model_manager.list_available_models()
        if not available_models:
            print("⚠️  No Ollama models found.")
            print("You'll need at least one model for delegation to work.")
            print("Consider installing a model using the Model Installation wizard.")
            return False
        
        print(f"Found {len(available_models)} model(s): {', '.join(available_models)}")
        
        # Configure delegation settings
        print("\nConfiguring delegation settings...")
        self.config = self._configure_delegation_settings(available_models)
        
        # Verify setup
        if self.verify():
            print("\n✅ Task delegation setup complete!")
            return True
        else:
            print("\n❌ Verification failed.")
            return False
    
    def validate_requirements(self) -> Tuple[bool, List[str]]:
        """Validate delegation requirements."""
        missing = []
        
        if not self.model_manager.ollama_path:
            missing.append("Ollama not installed")
        
        return len(missing) == 0, missing
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        try:
            import litellm
            return True
        except ImportError:
            return False
    
    def _configure_delegation_settings(self, available_models: List[str]) -> dict:
        """Configure delegation settings."""
        config = {
            "model_routing_enabled": True,
            "available_models": available_models,
            "default_model": available_models[0] if available_models else None,
        }
        
        print("\nDelegation configuration:")
        print(f"  Model routing: {'Enabled' if config['model_routing_enabled'] else 'Disabled'}")
        print(f"  Available models: {', '.join(config['available_models'])}")
        print(f"  Default model: {config['default_model']}")
        
        return config
    
    def setup(self) -> bool:
        """Setup is handled in run()."""
        return self.run()
    
    def verify(self) -> bool:
        """Verify delegation setup."""
        try:
            from delegation import DelegationManager
            manager = DelegationManager(memory_dir=self.memory_dir)
            # Basic check - if we can create it, it's working
            return True
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def cleanup_on_failure(self):
        """Cleanup on failure."""
        pass

