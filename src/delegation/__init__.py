"""
Delegation Layer for Janet - Plugin-Based Architecture
Supports dynamic handler registration and capability-based routing.
"""

from .delegation_manager import DelegationManager, DelegationType
from .handlers.base import (
    DelegationHandler, DelegationRequest, DelegationResult, HandlerCapability
)

# Optional handler imports (may fail if dependencies not available)
try:
    from .handlers.n8n_handler import N8NDelegationHandler
except ImportError:
    N8NDelegationHandler = None

try:
    from .handlers.image_handler import ImageProcessingHandler
except ImportError:
    ImageProcessingHandler = None

try:
    from .handlers.home_automation_handler import HomeAutomationHandler
except ImportError:
    HomeAutomationHandler = None

try:
    from .litellm_router import LiteLLMRouter
except ImportError:
    LiteLLMRouter = None

try:
    from .n8n_client import N8NClient
except ImportError:
    N8NClient = None

try:
    from .home_assistant import HomeAssistantClient
except ImportError:
    HomeAssistantClient = None

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

