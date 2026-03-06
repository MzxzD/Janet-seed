"""
API module for Janet.
Provides REST API endpoints for external integrations.
"""
from .home_assistant_api import start_api_server, set_janet_core, app

__all__ = ['start_api_server', 'set_janet_core', 'app']
