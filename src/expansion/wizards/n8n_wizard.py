"""
n8n Wizard — n8n Integration Setup

Guides users through setting up n8n integration.
"""

from pathlib import Path
from typing import Tuple, List
from .wizard_base import ExpansionWizard


class N8NWizard(ExpansionWizard):
    """Wizard for setting up n8n integration."""
    
    def run(self) -> bool:
        """Run the n8n setup wizard."""
        print(f"\n{'='*60}")
        print("🔗 n8n Integration Setup Wizard")
        print(f"{'='*60}\n")
        
        # Validate requirements
        valid, missing = self.validate_requirements()
        if not valid:
            print("❌ Requirements not met:")
            for req in missing:
                print(f"  • {req}")
            return False
        
        # Get n8n URL
        print("Please provide your n8n instance details:")
        n8n_url = input("n8n URL (e.g., http://localhost:5678): ").strip()
        if not n8n_url:
            print("❌ n8n URL is required.")
            return False
        
        # Get API key (optional)
        api_key = input("API Key (optional, press Enter to skip): ").strip()
        
        # Test connection
        print(f"\nTesting connection to {n8n_url}...")
        if not self._test_connection(n8n_url, api_key):
            print("❌ Could not connect to n8n instance.")
            print("Please verify:")
            print("  • n8n is running")
            print("  • URL is correct")
            print("  • Network access is available")
            return False
        
        # Configure n8n settings
        self.config = {
            "n8n_url": n8n_url,
            "api_key": api_key if api_key else None,
        }
        
        # Verify setup
        if self.verify():
            print("\n✅ n8n integration setup complete!")
            return True
        else:
            print("\n❌ Verification failed.")
            return False
    
    def validate_requirements(self) -> Tuple[bool, List[str]]:
        """Validate n8n requirements."""
        missing = []
        
        if not self.check_network_available():
            missing.append("Network connection required")
        
        return len(missing) == 0, missing
    
    def _test_connection(self, url: str, api_key: str = None) -> bool:
        """Test connection to n8n instance."""
        try:
            import requests
            headers = {}
            if api_key:
                headers["X-N8N-API-KEY"] = api_key
            
            response = requests.get(f"{url}/healthz", headers=headers, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def setup(self) -> bool:
        """Setup is handled in run()."""
        return self.run()
    
    def verify(self) -> bool:
        """Verify n8n integration."""
        try:
            from delegation.n8n_client import N8NClient
            client = N8NClient(
                base_url=self.config["n8n_url"],
                api_key=self.config.get("api_key")
            )
            # Basic check - if we can create it, it's working
            return True
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def cleanup_on_failure(self):
        """Cleanup on failure."""
        pass

