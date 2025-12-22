"""
Image Processing Handler
Delegates image processing tasks to n8n workflows or direct model calls.
"""
from typing import Dict, Optional, List, Any
from .base import DelegationHandler, DelegationRequest, DelegationResult, HandlerCapability
from .n8n_handler import N8NDelegationHandler


class ImageProcessingHandler(DelegationHandler):
    """Handler for image processing tasks."""
    
    def __init__(self, n8n_handler: Optional[N8NDelegationHandler] = None):
        """Initialize image processing handler."""
        super().__init__("image_processor", "Image Processing Handler")
        self.n8n_handler = n8n_handler
    
    def get_capabilities(self) -> List[HandlerCapability]:
        """Return image-related capabilities."""
        return [
            HandlerCapability.IMAGE_PROCESSING,
            HandlerCapability.IMAGE_GENERATION
        ]
    
    def can_handle(self, request: DelegationRequest) -> bool:
        """Check if we can handle image tasks."""
        return (
            request.capability in [
                HandlerCapability.IMAGE_PROCESSING,
                HandlerCapability.IMAGE_GENERATION
            ] and
            self.is_available()
        )
    
    def handle(self, request: DelegationRequest) -> DelegationResult:
        """Process image task via n8n or direct model."""
        # If n8n handler is available and configured, use it
        if self.n8n_handler and self.n8n_handler.can_handle(request):
            return self.n8n_handler.handle(request)
        
        # Fallback: direct model call (if implemented)
        # This could call an image model directly via LiteLLM
        return DelegationResult(
            success=False,
            output_data={},
            message="Image processing not configured",
            error="No n8n workflow or direct model available"
        )
    
    def is_available(self) -> bool:
        """Check if handler is available."""
        return (
            self.n8n_handler is not None and
            self.n8n_handler.is_available()
        )

