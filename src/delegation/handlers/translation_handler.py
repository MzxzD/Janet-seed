"""
Translation delegation handler.
Handles "Hey Janet, translate X to Japanese" via LLM.
"""
from typing import Any, Dict, List, Optional
from .base import DelegationHandler, DelegationRequest, DelegationResult, HandlerCapability
from ..translate import translate_text


class TranslationHandler(DelegationHandler):
    """Handler for translation requests."""
    
    def __init__(self, handler_id: str = "translation", name: str = "Translation", llm_router=None):
        super().__init__(handler_id, name)
        self.llm_router = llm_router
    
    def get_capabilities(self) -> List[HandlerCapability]:
        return [HandlerCapability.MODEL_INFERENCE]
    
    def can_handle(self, request: DelegationRequest) -> bool:
        desc = (request.task_description or "").lower()
        inp = request.input_data or {}
        return "translate" in desc or inp.get("action") == "translate"
    
    def handle(self, request: DelegationRequest) -> DelegationResult:
        inp = request.input_data or {}
        text = inp.get("text", "")
        target = inp.get("target_lang", "Japanese")
        source = inp.get("source_lang")
        
        result = translate_text(
            text, target, source,
            self.llm_router if self.llm_router else None
        )
        
        return DelegationResult(
            success=True,
            output_data={"translated": result},
            message=result,
            metadata={"target_lang": target},
        )
    
    def is_available(self) -> bool:
        return True
