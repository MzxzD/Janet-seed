"""
Refactored Delegation Manager - Plugin-Based Architecture
Supports dynamic handler registration and capability-based routing.
"""
from typing import Dict, Optional, List, Callable, Any
from datetime import datetime
from enum import Enum
import threading

from .handlers.base import (
    DelegationHandler, DelegationRequest, DelegationResult, HandlerCapability
)
from .handlers.n8n_handler import N8NDelegationHandler
from .handlers.image_handler import ImageProcessingHandler
from .handlers.home_automation_handler import HomeAutomationHandler
from .litellm_router import LiteLLMRouter, TaskType
from .n8n_client import N8NClient
from .home_assistant import HomeAssistantClient

# Import Red Thread event for constitutional integration (Axiom 8)
try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    RED_THREAD_EVENT = None


class DelegationType(Enum):
    """Types of delegation (legacy compatibility)."""
    MODEL_ROUTING = "model_routing"
    N8N_WEBHOOK = "n8n_webhook"
    HOME_ASSISTANT = "home_assistant"
    EXTERNAL_API = "external_api"


class DelegationManager:
    """Manages task delegation with plugin-based architecture."""
    
    def __init__(
        self,
        litellm_config: Optional[Dict] = None,
        n8n_url: Optional[str] = None,
        n8n_api_key: Optional[str] = None,
        home_assistant_url: Optional[str] = None,
        home_assistant_token: Optional[str] = None,
        require_confirmation: bool = True
    ):
        """
        Initialize delegation manager.
        
        Args:
            litellm_config: LiteLLM router configuration
            n8n_url: n8n base URL
            n8n_api_key: n8n API key
            home_assistant_url: Home Assistant URL
            home_assistant_token: Home Assistant access token
            require_confirmation: Whether to require confirmation for delegations
        """
        self.require_confirmation = require_confirmation
        
        # Initialize clients
        self.llm_router = LiteLLMRouter(litellm_config) if litellm_config else LiteLLMRouter()
        self.n8n_client = N8NClient(n8n_url, n8n_api_key) if n8n_url else None
        
        # Handler registry
        self.handlers: Dict[str, DelegationHandler] = {}
        self.capability_map: Dict[HandlerCapability, List[DelegationHandler]] = {}
        
        # Initialize built-in handlers
        self._initialize_handlers(home_assistant_url, home_assistant_token)
        
        # Delegation history
        self.delegation_history: List[Dict] = []
    
    def _initialize_handlers(
        self,
        home_assistant_url: Optional[str],
        home_assistant_token: Optional[str]
    ):
        """Initialize built-in handlers."""
        # Initialize n8n handler with workflow mappings
        if self.n8n_client:
            n8n_workflow_map = {
                HandlerCapability.IMAGE_PROCESSING: "/webhook/image-processing",
                HandlerCapability.IMAGE_GENERATION: "/webhook/image-generation",
                HandlerCapability.HOME_AUTOMATION: "/webhook/home-automation",
                # Add more as needed
            }
            n8n_handler = N8NDelegationHandler(self.n8n_client, n8n_workflow_map)
            self.register_handler(n8n_handler)
        
        # Initialize image processing handler
        n8n_handler = self.handlers.get("n8n_handler")
        image_handler = ImageProcessingHandler(n8n_handler)
        self.register_handler(image_handler)
        
        # Initialize home automation handler
        home_assistant = (
            HomeAssistantClient(home_assistant_url, home_assistant_token)
            if home_assistant_url and home_assistant_token
            else None
        )
        ha_handler = HomeAutomationHandler(n8n_handler, home_assistant)
        self.register_handler(ha_handler)
    
    def register_handler(self, handler: DelegationHandler):
        """Register a delegation handler."""
        self.handlers[handler.handler_id] = handler
        
        # Update capability map
        for capability in handler.get_capabilities():
            if capability not in self.capability_map:
                self.capability_map[capability] = []
            if handler not in self.capability_map[capability]:
                self.capability_map[capability].append(handler)
    
    def unregister_handler(self, handler_id: str):
        """Unregister a handler."""
        if handler_id in self.handlers:
            handler = self.handlers[handler_id]
            # Remove from capability map
            for capability in handler.get_capabilities():
                if capability in self.capability_map:
                    self.capability_map[capability] = [
                        h for h in self.capability_map[capability]
                        if h.handler_id != handler_id
                    ]
            del self.handlers[handler_id]
    
    def delegate(
        self,
        capability: HandlerCapability,
        task_description: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        confirm_callback: Optional[Callable[[str], bool]] = None,
        async_callback: Optional[Callable[[DelegationResult], None]] = None,
        timeout: Optional[int] = None
    ) -> Optional[DelegationResult]:
        """
        Delegate a task to appropriate handler.
        
        Args:
            capability: Type of capability needed
            task_description: Human-readable task description
            input_data: Input data for the task
            context: Additional context
            confirm_callback: Function to call for confirmation
            async_callback: Optional callback for async results
            timeout: Optional timeout in seconds
        
        Returns:
            Delegation result, or None if declined/failed
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - delegation blocked")
            return None
        
        # Find handlers for this capability
        handlers = self.capability_map.get(capability, [])
        if not handlers:
            print(f"⚠️  No handlers available for {capability.value}")
            return None
        
        # Create request
        request = DelegationRequest(
            capability=capability,
            task_description=task_description,
            input_data=input_data,
            context=context,
            requires_confirmation=self.require_confirmation,
            async_callback=async_callback,
            timeout=timeout
        )
        
        # Require confirmation if enabled
        if self.require_confirmation and confirm_callback:
            confirmation_message = (
                f"Delegate {task_description} to {handlers[0].name}?"
            )
            if not confirm_callback(confirmation_message):
                return None
        
        # Try handlers in order (first available)
        for handler in handlers:
            if handler.enabled and handler.can_handle(request):
                result = handler.handle(request)
                
                # Log delegation
                self._log_delegation(capability, handler.handler_id, {
                    "task_description": task_description,
                    "success": result.success,
                    "error": result.error
                })
                
                return result
        
        # No handler could process
        return DelegationResult(
            success=False,
            output_data={},
            message=f"No available handler for {capability.value}",
            error="All handlers unavailable or cannot handle request"
        )
    
    def delegate_async(
        self,
        capability: HandlerCapability,
        task_description: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        confirm_callback: Optional[Callable[[str], bool]] = None,
        result_callback: Callable[[DelegationResult], None],
        timeout: Optional[int] = None
    ) -> bool:
        """
        Delegate task asynchronously.
        
        Returns:
            True if delegation started, False otherwise
        """
        def async_handler():
            result = self.delegate(
                capability=capability,
                task_description=task_description,
                input_data=input_data,
                context=context,
                confirm_callback=confirm_callback,
                timeout=timeout
            )
            if result:
                result_callback(result)
        
        thread = threading.Thread(target=async_handler, daemon=True)
        thread.start()
        return True
    
    def get_available_capabilities(self) -> List[HandlerCapability]:
        """Get list of available capabilities."""
        return [
            capability
            for capability, handlers in self.capability_map.items()
            if any(h.enabled and h.is_available() for h in handlers)
        ]
    
    def get_handlers_for_capability(
        self,
        capability: HandlerCapability
    ) -> List[DelegationHandler]:
        """Get all handlers that support a capability."""
        return [
            h for h in self.capability_map.get(capability, [])
            if h.enabled
        ]
    
    def _log_delegation(
        self,
        capability: HandlerCapability,
        handler_id: str,
        details: Dict
    ):
        """Log delegation event."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "capability": capability.value,
            "handler_id": handler_id,
            "details": details
        }
        self.delegation_history.append(log_entry)
    
    def get_delegation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent delegation history."""
        return self.delegation_history[-limit:]
    
    def get_capabilities(self) -> Dict:
        """Get available delegation capabilities."""
        return {
            "available_capabilities": [
                c.value for c in self.get_available_capabilities()
            ],
            "handlers": {
                handler_id: handler.get_metadata()
                for handler_id, handler in self.handlers.items()
            },
            "require_confirmation": self.require_confirmation
        }
    
    # Backward compatibility methods
    def delegate_to_model(
        self,
        query: str,
        task_type: Optional[TaskType] = None,
        context: Optional[Dict] = None,
        confirm_callback: Optional[Callable[[str], bool]] = None
    ) -> Optional[str]:
        """Legacy method - delegate to model."""
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - delegation blocked")
            return None
        
        if not self.llm_router.is_available():
            return None
        
        if task_type is None:
            task_type = self.llm_router.detect_task_type(query)
        
        response = self.llm_router.route(query, task_type, context)
        
        # Log delegation
        self._log_delegation(
            HandlerCapability.MODEL_INFERENCE,
            "llm_router",
            {
                "query": query[:50],
                "task_type": task_type.value,
                "success": response is not None
            }
        )
        
        return response
    
    def delegate_to_n8n(
        self,
        webhook_path: str,
        payload: Dict,
        confirm_callback: Optional[Callable[[str], bool]] = None
    ) -> Optional[Dict]:
        """Legacy method - delegate to n8n."""
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - delegation blocked")
            return None
        
        if not self.n8n_client:
            return None
        
        response = self.n8n_client.trigger_webhook(webhook_path, payload)
        
        # Log delegation
        self._log_delegation(
            HandlerCapability.CUSTOM,
            "n8n_legacy",
            {
                "webhook_path": webhook_path,
                "success": response is not None
            }
        )
        
        return response
    
    def delegate_to_home_assistant(
        self,
        service: str,
        domain: str,
        entity_id: Optional[str] = None,
        data: Optional[Dict] = None,
        confirm_callback: Optional[Callable[[str], bool]] = None
    ) -> Optional[Dict]:
        """Legacy method - delegate to Home Assistant."""
        # Use new capability-based system
        result = self.delegate(
            capability=HandlerCapability.HOME_AUTOMATION,
            task_description=f"Home Assistant {domain}.{service}",
            input_data={
                "domain": domain,
                "service": service,
                "entity_id": entity_id,
                "data": data or {}
            },
            confirm_callback=confirm_callback
        )
        
        if result and result.success:
            return result.output_data.get("result")
        return None
