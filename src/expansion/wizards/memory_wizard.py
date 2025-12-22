"""
Memory Wizard — Persistent Memory Setup

Guides users through setting up persistent memory.
"""

from pathlib import Path
from typing import Tuple, List
from .wizard_base import ExpansionWizard


class MemoryWizard(ExpansionWizard):
    """Wizard for setting up persistent memory."""
    
    def __init__(self, config_path: Path, memory_dir: Path, janet_core=None):
        """
        Initialize memory wizard.
        
        Args:
            config_path: Path to config directory
            memory_dir: Path to memory directory
            janet_core: Optional JanetCore instance
        """
        super().__init__(config_path, janet_core)
        self.memory_dir = Path(memory_dir)
    
    def run(self) -> bool:
        """Run the memory setup wizard."""
        print(f"\n{'='*60}")
        print("💾 Persistent Memory Setup Wizard")
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
            print("  • chromadb (for semantic memory)")
            print("  • cryptography (for encryption)")
            print("\nInstall with: pip install chromadb cryptography")
            return False
        
        # Create memory directory
        print(f"\nCreating memory directory: {self.memory_dir}")
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"❌ Failed to create memory directory: {e}")
            return False
        
        # Configure memory settings
        print("\nConfiguring memory settings...")
        self.config = self._configure_memory_settings()
        
        # Verify setup
        if self.verify():
            print("\n✅ Persistent memory setup complete!")
            return True
        else:
            print("\n❌ Verification failed.")
            return False
    
    def validate_requirements(self) -> Tuple[bool, List[str]]:
        """Validate memory requirements."""
        missing = []
        
        # Check disk space (need at least 5GB free)
        import shutil
        free_space_gb = shutil.disk_usage(self.memory_dir.parent).free / (1024**3)
        if free_space_gb < 5:
            missing.append(f"Insufficient disk space (need 5GB, have {free_space_gb:.1f}GB)")
        
        return len(missing) == 0, missing
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        try:
            import chromadb
            import cryptography
            return True
        except ImportError:
            return False
    
    def _configure_memory_settings(self) -> dict:
        """Configure memory settings."""
        config = {
            "memory_dir": str(self.memory_dir),
            "encryption_enabled": True,
            "semantic_search_enabled": True,
        }
        
        print("\nMemory configuration:")
        print(f"  Memory directory: {config['memory_dir']}")
        print(f"  Encryption: {'Enabled' if config['encryption_enabled'] else 'Disabled'}")
        print(f"  Semantic search: {'Enabled' if config['semantic_search_enabled'] else 'Disabled'}")
        
        return config
    
    def setup(self) -> bool:
        """Setup is handled in run()."""
        return self.run()
    
    def verify(self) -> bool:
        """Verify memory setup."""
        try:
            from memory import MemoryManager
            manager = MemoryManager(self.memory_dir)
            # Basic check - if we can create it, it's working
            return True
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def cleanup_on_failure(self):
        """Cleanup on failure."""
        # Don't delete memory directory - user might want to keep it
        pass

