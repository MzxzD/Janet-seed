"""
Delegation Layer for Janet - Plugin-Based Architecture
Supports dynamic handler registration and capability-based routing.
"""

from .delegation_manager import DelegationManager, DelegationType
from .handlers.base import (
    DelegationHandler, DelegationRequest, DelegationResult, HandlerCapability
)
from .handlers.n8n_handler import N8NDelegationHandler
from .handlers.image_handler import ImageProcessingHandler
from .handlers.home_automation_handler import HomeAutomationHandler
from .litellm_router import LiteLLMRouter
from .n8n_client import N8NClient
from .home_assistant import HomeAssistantClient

__all__ = [
    'DelegationManager',
    'DelegationType',
    'DelegationHandler',
    'DelegationRequest',
    'DelegationResult',
    'HandlerCapability',
    'N8NDelegationHandler',
    'ImageProcessingHandler',
    'HomeAutomationHandler',
    'LiteLLMRouter',
    'N8NClient',
    'HomeAssistantClient',
]

