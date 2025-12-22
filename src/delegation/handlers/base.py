"""
Base Delegation Handler Interface
All delegation handlers must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Callable, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class HandlerCapability(Enum):
    """Capabilities a handler can provide."""
    IMAGE_PROCESSING = "image_processing"
    IMAGE_GENERATION = "image_generation"
    VIDEO_PROCESSING = "video_processing"
    AUDIO_PROCESSING = "audio_processing"
    HOME_AUTOMATION = "home_automation"
    WEATHER = "weather"
    CALENDAR = "calendar"
    EMAIL = "email"
    MODEL_INFERENCE = "model_inference"
    DATA_ANALYSIS = "data_analysis"
    WEB_SEARCH = "web_search"
    CUSTOM = "custom"


@dataclass
class DelegationRequest:
    """Request for delegation."""
    capability: HandlerCapability
    task_description: str
    input_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = True
    async_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    timeout: Optional[int] = None  # seconds


@dataclass
class DelegationResult:
    """Result from delegation."""
    success: bool
    output_data: Dict[str, Any]
    message: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DelegationHandler(ABC):
    """Base class for all delegation handlers."""
    
    def __init__(self, handler_id: str, name: str):
        """
        Initialize handler.
        
        Args:
            handler_id: Unique identifier for this handler
            name: Human-readable name
        """
        self.handler_id = handler_id
        self.name = name
        self.enabled = True
    
    @abstractmethod
    def get_capabilities(self) -> List[HandlerCapability]:
        """Return list of capabilities this handler provides."""
        pass
    
    @abstractmethod
    def can_handle(self, request: DelegationRequest) -> bool:
        """Check if this handler can handle the request."""
        pass
    
    @abstractmethod
    def handle(self, request: DelegationRequest) -> DelegationResult:
        """
        Handle the delegation request.
        
        Args:
            request: Delegation request
            
        Returns:
            Delegation result
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if handler is available and ready."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get handler metadata (optional override)."""
        return {
            "handler_id": self.handler_id,
            "name": self.name,
            "capabilities": [c.value for c in self.get_capabilities()],
            "enabled": self.enabled,
            "available": self.is_available()
        }

