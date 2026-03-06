"""
Home Assistant Dashboard Handler
Handles requests to open and interact with Home Assistant dashboard.
"""
import webbrowser
from typing import Dict, Optional, List
from .base import DelegationHandler, DelegationRequest, DelegationResult, HandlerCapability
from ..home_assistant import HomeAssistantClient


class HomeAssistantDashboardHandler(DelegationHandler):
    """Handler for Home Assistant dashboard interactions."""
    
    def __init__(self, ha_client: Optional[HomeAssistantClient] = None):
        """
        Initialize dashboard handler.
        
        Args:
            ha_client: HomeAssistantClient instance
        """
        super().__init__(
            handler_id="home_assistant_dashboard",
            name="Home Assistant Dashboard Handler"
        )
        self.ha_client = ha_client
    
    def get_capabilities(self) -> List[HandlerCapability]:
        """Return list of capabilities this handler provides."""
        return [HandlerCapability.HOME_AUTOMATION]
    
    def is_available(self) -> bool:
        """Check if handler is available and ready."""
        return self.ha_client is not None and self.ha_client.is_available()
    
    def can_handle(self, request: DelegationRequest) -> bool:
        """
        Check if this handler can handle the request.
        
        Args:
            request: DelegationRequest
            
        Returns:
            True if handler can handle this request
        """
        keywords = [
            "home assistant dashboard",
            "ha dashboard",
            "open home assistant",
            "show home assistant",
            "home automation dashboard",
            "smart home dashboard"
        ]
        
        task_lower = request.task_description.lower()
        return any(keyword in task_lower for keyword in keywords)
    
    def handle(self, request: DelegationRequest) -> DelegationResult:
        """
        Handle dashboard request.
        
        Args:
            request: DelegationRequest
            
        Returns:
            DelegationResult
        """
        if not self.ha_client or not self.ha_client.is_available():
            return DelegationResult(
                success=False,
                output_data={},
                message="Home Assistant is not configured. Please set up Home Assistant first.",
                error="HA not configured",
                metadata={"suggestion": "Configure Home Assistant URL and token in settings."}
            )
        
        # Get HA URL
        ha_url = self.ha_client.base_url
        
        # Check if we should open a specific page
        task_lower = request.task_description.lower()
        
        if "devices" in task_lower or "entities" in task_lower:
            url = f"{ha_url}/config/entities"
            page_name = "devices page"
        elif "automation" in task_lower or "automations" in task_lower:
            url = f"{ha_url}/config/automation/dashboard"
            page_name = "automations page"
        elif "scene" in task_lower or "scenes" in task_lower:
            url = f"{ha_url}/config/scene/dashboard"
            page_name = "scenes page"
        elif "settings" in task_lower or "config" in task_lower:
            url = f"{ha_url}/config/dashboard"
            page_name = "settings page"
        else:
            url = ha_url
            page_name = "main dashboard"
        
        # Open in browser
        try:
            webbrowser.open(url)
            return DelegationResult(
                success=True,
                output_data={"url": url, "page": page_name},
                message=f"Opening Home Assistant {page_name}",
                metadata={"suggestion": "The dashboard should open in your default browser."}
            )
        except Exception as e:
            return DelegationResult(
                success=False,
                output_data={"url": url},
                message=f"Failed to open dashboard: {str(e)}",
                error=str(e),
                metadata={"suggestion": f"You can manually open: {url}"}
            )
    
    def get_dashboard_url(self, page: Optional[str] = None) -> Optional[str]:
        """
        Get URL for specific dashboard page.
        
        Args:
            page: Page name (devices, automations, scenes, settings, or None for main)
            
        Returns:
            Dashboard URL or None if HA not configured
        """
        if not self.ha_client or not self.ha_client.is_available():
            return None
        
        base_url = self.ha_client.base_url
        
        if page == "devices":
            return f"{base_url}/config/entities"
        elif page == "automations":
            return f"{base_url}/config/automation/dashboard"
        elif page == "scenes":
            return f"{base_url}/config/scene/dashboard"
        elif page == "settings":
            return f"{base_url}/config/dashboard"
        else:
            return base_url
    
    def get_dashboard_info(self) -> Dict:
        """
        Get information about available dashboard pages.
        
        Returns:
            Dictionary with dashboard info
        """
        if not self.ha_client or not self.ha_client.is_available():
            return {
                "available": False,
                "message": "Home Assistant not configured"
            }
        
        base_url = self.ha_client.base_url
        
        return {
            "available": True,
            "base_url": base_url,
            "pages": {
                "main": base_url,
                "devices": f"{base_url}/config/entities",
                "automations": f"{base_url}/config/automation/dashboard",
                "scenes": f"{base_url}/config/scene/dashboard",
                "settings": f"{base_url}/config/dashboard",
                "history": f"{base_url}/history",
                "logbook": f"{base_url}/logbook",
                "map": f"{base_url}/map",
                "developer_tools": f"{base_url}/developer-tools"
            }
        }
