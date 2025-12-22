"""
Home Automation Handler
Delegates home automation tasks via n8n or direct Home Assistant.
"""
from typing import Dict, Optional, List, Any
from .base import DelegationHandler, DelegationRequest, DelegationResult, HandlerCapability
from .n8n_handler import N8NDelegationHandler
from ..home_assistant import HomeAssistantClient


class HomeAutomationHandler(DelegationHandler):
    """Handler for home automation tasks."""
    
    def __init__(
        self,
        n8n_handler: Optional[N8NDelegationHandler] = None,
        home_assistant: Optional[HomeAssistantClient] = None
    ):
        """Initialize home automation handler."""
        super().__init__("home_automation", "Home Automation Handler")
        self.n8n_handler = n8n_handler
        self.home_assistant = home_assistant
        # Prefer n8n if available, fallback to direct HA
        self.prefer_n8n = n8n_handler is not None
    
    def get_capabilities(self) -> List[HandlerCapability]:
        """Return home automation capability."""
        return [HandlerCapability.HOME_AUTOMATION]
    
    def can_handle(self, request: DelegationRequest) -> bool:
        """Check if we can handle home automation."""
        return (
            request.capability == HandlerCapability.HOME_AUTOMATION and
            self.is_available()
        )
    
    def handle(self, request: DelegationRequest) -> DelegationResult:
        """Handle home automation via n8n or direct HA."""
        # Try n8n first if preferred and available
        if self.prefer_n8n and self.n8n_handler and self.n8n_handler.can_handle(request):
            return self.n8n_handler.handle(request)
        
        # Fallback to direct Home Assistant
        if self.home_assistant and self.home_assistant.is_available():
            return self._handle_direct_ha(request)
        
        return DelegationResult(
            success=False,
            output_data={},
            message="Home automation not available",
            error="No n8n workflow or Home Assistant connection"
        )
    
    def _handle_direct_ha(self, request: DelegationRequest) -> DelegationResult:
        """Handle directly via Home Assistant API."""
        input_data = request.input_data
        
        # Parse common patterns
        domain = input_data.get("domain", "light")
        service = input_data.get("service", "turn_on")
        entity_id = input_data.get("entity_id")
        data = input_data.get("data", {})
        
        result = self.home_assistant.call_service(
            domain, service, entity_id, **data
        )
        
        if result:
            return DelegationResult(
                success=True,
                output_data={"result": result},
                message=f"Home Assistant {domain}.{service} executed",
                metadata={"entity_id": entity_id}
            )
        else:
            return DelegationResult(
                success=False,
                output_data={},
                message="Home Assistant call failed",
                error="Service call returned no result"
            )
    
    def is_available(self) -> bool:
        """Check if handler is available."""
        return (
            (self.n8n_handler and self.n8n_handler.is_available()) or
            (self.home_assistant and self.home_assistant.is_available())
        )

