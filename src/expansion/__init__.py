"""
J.A.N.E.T. Seed — Expansion Protocol Module

This module handles consent-based expansion of Janet's capabilities.
All expansions require explicit user consent and work offline-first.
"""

from .expansion_types import (
    ExpansionType,
    ExpansionOpportunity,
)
from .expansion_detector import ExpansionDetector
from .expansion_state import ExpansionState, ExpansionStateManager
from .expansion_dialog import ExpansionDialog
from .model_manager import ModelManager

__all__ = [
    'ExpansionType',
    'ExpansionOpportunity',
    'ExpansionDetector',
    'ExpansionState',
    'ExpansionStateManager',
    'ExpansionDialog',
    'ModelManager',
]

