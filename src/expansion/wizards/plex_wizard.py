"""
Plex Expansion Wizard - Guided setup for Plex Media Server integration
Consent-based wizard that guides Operator through Plex server discovery,
token authentication, client pairing, and privacy consent configuration.
"""
import logging
from typing import Tuple, List, Optional
from pathlib import Path
import json
import socket
from urllib.parse import urlparse

from .wizard_base import ExpansionWizard

logger = logging.getLogger(__name__)

try:
    from plexapi.server import PlexServer
    from plexapi.myplex import MyPlexAccount
    PLEXAPI_AVAILABLE = True
except ImportError:
    PLEXAPI_AVAILABLE = False
    PlexServer = None
    MyPlexAccount = None


class PlexWizard(ExpansionWizard):
    """
    Wizard for Plex Media Server integration.
    
    Guides Operator through:
    - Plex server discovery (local network scan)
    - Token authentication setup
    - Client device pairing
    - Privacy consent for watch history
    """
    
    def __init__(self, config_path: Path, janet_core=None):
        """Initialize Plex wizard."""
        super().__init__(config_path, janet_core)
        self.plex_server_url = None
        self.plex_token = None
        self.allow_history_tracking = False
        self.discovered_servers = []
    
    def run(self) -> bool:
        """
        Run the Plex wizard.
        
        Returns:
            True if setup complete, False if cancelled or failed
        """
        print("\n=== Plex Media Server Integration Wizard ===")
        print("This wizard will guide you through connecting Janet to your local Plex server.")
        print("All operations are offline-first - no cloud dependencies.")
        print()
        
        # Step 1: Validate requirements
        success, missing = self.validate_requirements()
        if not success:
            print(f"⚠️  Missing requirements: {', '.join(missing)}")
            print("Some features may be limited.")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False
        
        # Step 2: Discover Plex servers
        print("\n--- Step 1: Plex Server Discovery ---")
        if not self._discover_servers():
            print("⚠️  Could not automatically discover Plex servers.")
            print("You can manually enter server details.")
        
        # Step 3: Select or enter server
        print("\n--- Step 2: Server Configuration ---")
        if not self._configure_server():
            print("❌ Server configuration cancelled or failed.")
            return False
        
        # Step 4: Authenticate
        print("\n--- Step 3: Authentication ---")
        if not self._authenticate():
            print("❌ Authentication failed.")
            return False
        
        # Step 5: Privacy consent
        print("\n--- Step 4: Privacy Configuration ---")
        self._configure_privacy()
        
        # Step 6: Setup
        print("\n--- Step 5: Finalizing Setup ---")
        if not self.setup():
            print("❌ Setup failed.")
            self.cleanup_on_failure()
            return False
        
        # Step 7: Verify
        print("\n--- Step 6: Verification ---")
        if not self.verify():
            print("❌ Verification failed.")
            self.cleanup_on_failure()
            return False
        
        print("\n✅ Plex integration setup complete!")
        print(f"Server: {self.plex_server_url}")
        print(f"History tracking: {'Enabled' if self.allow_history_tracking else 'Disabled'}")
        return True
    
    def validate_requirements(self) -> Tuple[bool, List[str]]:
        """
        Validate that requirements are met.
        
        Returns:
            Tuple of (success: bool, missing_requirements: List[str])
        """
        missing = []
        
        if not PLEXAPI_AVAILABLE:
            missing.append("plexapi library (pip install plexapi)")
        
        # Plex server is optional (will be discovered)
        # Network is optional (offline-first)
        
        return len(missing) == 0, missing
    
    def _discover_servers(self) -> bool:
        """Discover Plex servers on local network."""
        if not self.check_network_available():
            print("⚠️  Network not available. Manual server entry will be required.")
            return False
        
        print("Scanning local network for Plex servers...")
        discovered = []
        
        try:
            # Try GDM (Plex Discovery Protocol) - broadcast on port 32414
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(2)
            
            # Broadcast Plex discovery message
            # GDM uses UDP broadcast - simplified discovery
            broadcast_address = "255.255.255.255"
            discovery_port = 32414
            
            # For now, provide manual entry option
            # Full GDM implementation would require more complex protocol
            print("Note: Automatic discovery requires GDM implementation.")
            print("You can manually enter your Plex server URL and token.")
            
            return False  # Discovery not fully implemented yet
        
        except Exception as e:
            logger.warning(f"Plex server discovery failed: {e}")
            return False
    
    def _configure_server(self) -> bool:
        """Configure Plex server URL."""
        # Show discovered servers if any
        if self.discovered_servers:
            print("Discovered servers:")
            for i, server in enumerate(self.discovered_servers, 1):
                print(f"  {i}. {server['name']} - {server['url']}")
            print()
            choice = input("Select server number, or 'm' for manual entry: ")
            
            if choice.isdigit() and 1 <= int(choice) <= len(self.discovered_servers):
                selected = self.discovered_servers[int(choice) - 1]
                self.plex_server_url = selected['url']
                return True
        
        # Manual entry
        print("Enter Plex server URL manually.")
        print("Format: http://IP_ADDRESS:32400 (e.g., http://192.168.1.100:32400)")
        server_url = input("Server URL (or 'skip' to cancel): ").strip()
        
        if server_url.lower() == 'skip':
            return False
        
        # Validate URL format
        try:
            parsed = urlparse(server_url)
            if not parsed.scheme or not parsed.hostname:
                print("❌ Invalid URL format.")
                return False
            self.plex_server_url = server_url
            return True
        except Exception as e:
            print(f"❌ Invalid URL: {e}")
            return False
    
    def _authenticate(self) -> bool:
        """Authenticate with Plex server."""
        print("Plex authentication requires a token.")
        print("You can get your token from:")
        print("  1. https://www.plex.tv/desktop (Account → Settings → Network)")
        print("  2. Or from your Plex server's config (Settings → Network → Manual Port)")
        print()
        
        token = input("Enter Plex token (or 'skip' to cancel): ").strip()
        if token.lower() == 'skip':
            return False
        
        if not token:
            print("❌ Token required.")
            return False
        
        self.plex_token = token
        
        # Test connection
        print("Testing connection...")
        if PLEXAPI_AVAILABLE:
            try:
                server = PlexServer(self.plex_server_url, self.plex_token)
                # Try to access library to verify token
                sections = server.library.sections()
                print(f"✅ Connected successfully! Found {len(sections)} library sections.")
                return True
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                print("Please verify your server URL and token.")
                return False
        else:
            # Without plexapi, we can't verify, but store config anyway
            print("⚠️  plexapi not available - cannot verify connection.")
            print("Config will be saved, but connection will be tested on first use.")
            return True
    
    def _configure_privacy(self):
        """Configure privacy settings (watch history tracking)."""
        print("\nPrivacy Configuration:")
        print("Watch history tracking allows Janet to provide recommendations based on what you've watched.")
        print("This data will be stored in Green Vault (safe summaries) with your consent.")
        print("You can enable/disable this at any time.")
        print()
        
        response = input("Enable watch history tracking? (y/n, default: n): ").strip().lower()
        self.allow_history_tracking = response == 'y'
        
        if self.allow_history_tracking:
            print("✅ Watch history tracking enabled (with consent).")
        else:
            print("ℹ️  Watch history tracking disabled. Recommendations will not be available.")
    
    def setup(self) -> bool:
        """
        Perform the setup.
        
        Returns:
            True if setup successful
        """
        if not self.plex_server_url or not self.plex_token:
            logger.error("Plex server URL or token missing")
            return False
        
        try:
            # Save configuration
            config_file = self.config_path / "plex_config.json"
            config = {
                "plex_server_url": self.plex_server_url,
                "plex_token": self.plex_token,
                "allow_history_tracking": self.allow_history_tracking,
                "configured_at": str(Path(__file__).stat().st_mtime)  # Placeholder timestamp
            }
            
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Plex configuration saved to {config_file}")
            self.config = config
            return True
        
        except Exception as e:
            logger.error(f"Failed to save Plex configuration: {e}")
            return False
    
    def verify(self) -> bool:
        """
        Verify that setup was successful.
        
        Returns:
            True if verification passes
        """
        if not PLEXAPI_AVAILABLE:
            print("⚠️  Cannot verify - plexapi not available.")
            return True  # Don't fail if library missing
        
        try:
            server = PlexServer(self.plex_server_url, self.plex_token)
            
            # Verify connection
            sections = server.library.sections()
            clients = server.clients()
            
            print(f"✅ Verification successful!")
            print(f"   Library sections: {len(sections)}")
            print(f"   Available clients: {len(clients)}")
            
            if clients:
                print("   Clients:")
                for client in clients[:5]:  # Show first 5
                    print(f"     - {client.name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            print(f"❌ Verification failed: {e}")
            return False
    
    def cleanup_on_failure(self):
        """Clean up on failure (revert changes)."""
        config_file = self.config_path / "plex_config.json"
        if config_file.exists():
            try:
                config_file.unlink()
                logger.info(f"Cleaned up Plex configuration: {config_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup Plex config: {e}")
    
    def generate_offline_instructions(self) -> str:
        """
        Generate offline installation instructions.
        
        Returns:
            Instruction string
        """
        return """
Plex Media Server Integration - Offline Setup Instructions

1. Get Plex Token:
   - Visit https://www.plex.tv/desktop in a browser (on a connected device)
   - Sign in to your Plex account
   - Go to: Account → Settings → Network
   - Find your "Manual Port" or check your Plex server's XML API token
   - Copy the token

2. Find Your Plex Server IP:
   - Check your router's admin panel for connected devices
   - Or run: arp -a | grep -i plex (on Linux/Mac)
   - Or check Plex server's network settings

3. Configure Janet:
   - When prompted, enter: http://YOUR_IP:32400
   - Enter the token from step 1
   - Choose privacy settings (watch history tracking)

4. Transfer Token (Sneakernet):
   - If Janet is on a device without network:
   - Copy token to a text file
   - Transfer file to Janet's device
   - Enter token when wizard prompts

5. Verify:
   - Wizard will test connection
   - If successful, Plex integration is ready!
"""
