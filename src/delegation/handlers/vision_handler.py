"""
Vision handler - screenshot / screen content analysis.
Fallback: screenshot → janet-seed → Ollama vision model.
Used when user invokes "search screen" or "what's on this screen" from Janet.
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
from .base import DelegationHandler, DelegationRequest, DelegationResult, HandlerCapability


class VisionHandler(DelegationHandler):
    """Handler for vision/screenshot analysis."""
    
    def __init__(self, handler_id: str = "vision", name: str = "Vision", llm_router=None):
        super().__init__(handler_id, name)
        self.llm_router = llm_router
    
    def get_capabilities(self) -> List[HandlerCapability]:
        return [HandlerCapability.IMAGE_PROCESSING]
    
    def can_handle(self, request: DelegationRequest) -> bool:
        inp = request.input_data or {}
        return "image_path" in inp or "screenshot" in inp or "image" in inp
    
    def handle(self, request: DelegationRequest) -> DelegationResult:
        inp = request.input_data or {}
        image_path = inp.get("image_path") or inp.get("screenshot") or inp.get("image")
        query = inp.get("query", "Describe what you see in this image.")
        
        if not image_path or not Path(image_path).exists():
            return DelegationResult(
                success=False,
                output_data={},
                message="No valid image provided",
                error="Missing or invalid image_path"
            )
        
        # Use LLM vision model if available (Ollama with vision)
        if self.llm_router and hasattr(self.llm_router, "route_vision"):
            try:
                result = self.llm_router.route_vision(image_path, query)
                return DelegationResult(
                    success=True,
                    output_data={"description": result},
                    message=result or "Could not analyze image.",
                )
            except Exception as e:
                return DelegationResult(
                    success=False,
                    output_data={},
                    message=str(e),
                    error=str(e),
                )
        
        return DelegationResult(
            success=False,
            output_data={},
            message="Vision model not configured. Add Ollama vision model.",
            error="No vision capability",
        )
    
    def is_available(self) -> bool:
        return self.llm_router is not None
