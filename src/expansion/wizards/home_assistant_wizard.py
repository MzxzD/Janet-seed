"""
Home Assistant Wizard — Home Assistant Integration Setup

Guides users through setting up Home Assistant integration.
"""

from pathlib import Path
from typing import Tuple, List
from .wizard_base import ExpansionWizard


class HomeAssistantWizard(ExpansionWizard):
    """Wizard for setting up Home Assistant integration."""
    
    def run(self) -> bool:
        """Run the Home Assistant setup wizard."""
        print(f"\n{'='*60}")
        print("🏠 Home Assistant Integration Setup Wizard")
        print(f"{'='*60}\n")
        
        # Validate requirements
        valid, missing = self.validate_requirements()
        if not valid:
            print("❌ Requirements not met:")
            for req in missing:
                print(f"  • {req}")
            return False
        
        # Get Home Assistant URL
        print("Please provide your Home Assistant instance details:")
        ha_url = input("Home Assistant URL (e.g., http://homeassistant.local:8123): ").strip()
        if not ha_url:
            print("❌ Home Assistant URL is required.")
            return False
        
        # Get API token
        api_token = input("Long-Lived Access Token: ").strip()
        if not api_token:
            print("❌ API token is required.")
            print("Generate one at: Home Assistant → Profile → Long-Lived Access Tokens")
            return False
        
        # Test connection
        print(f"\nTesting connection to {ha_url}...")
        if not self._test_connection(ha_url, api_token):
            print("❌ Could not connect to Home Assistant instance.")
            print("Please verify:")
            print("  • Home Assistant is running")
            print("  • URL is correct")
            print("  • API token is valid")
            print("  • Network access is available")
            return False
        
        # Configure Home Assistant settings
        self.config = {
            "ha_url": ha_url,
            "api_token": api_token,
        }
        
        # Verify setup
        if self.verify():
            print("\n✅ Home Assistant integration setup complete!")
            return True
        else:
            print("\n❌ Verification failed.")
            return False
    
    def validate_requirements(self) -> Tuple[bool, List[str]]:
        """Validate Home Assistant requirements."""
        missing = []
        
        if not self.check_network_available():
            missing.append("Network connection required")
        
        return len(missing) == 0, missing
    
    def _test_connection(self, url: str, api_token: str) -> bool:
        """Test connection to Home Assistant instance."""
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            }
            response = requests.get(f"{url}/api/", headers=headers, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def setup(self) -> bool:
        """Setup is handled in run()."""
        return self.run()
    
    def verify(self) -> bool:
        """Verify Home Assistant integration."""
        try:
            from delegation.home_assistant import HomeAssistantClient
            client = HomeAssistantClient(
                base_url=self.config["ha_url"],
                api_token=self.config["api_token"]
            )
            # Basic check - if we can create it, it's working
            return True
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def cleanup_on_failure(self):
        """Cleanup on failure."""
        pass

