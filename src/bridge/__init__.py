"""
Soul Bridge - Transfer conversation context between Constitutional and Networked Souls
"""
from .soul_bridge import SoulBridge, TransferRequest, TransferResult
from .memory_transfer import MemoryTransfer
from .state_reconciliation import StateReconciliation, Conflict, ReconciliationResult

# New ritual components
try:
    from .soulspeak_codec import SoulspeakCodec
    from .soulspeak_protocol import SoulspeakProtocol, TransferMode, TransferProgress
    from .soul_relationship import SoulRelationship, SyncRecord
    from .ritual_orchestrator import RitualOrchestrator, RitualPhase
    RITUAL_COMPONENTS_AVAILABLE = True
except ImportError:
    # Ritual components not available
    RITUAL_COMPONENTS_AVAILABLE = False
    # Define placeholders to avoid import errors
    SoulspeakCodec = None
    SoulspeakProtocol = None
    TransferMode = None
    TransferProgress = None
    SoulRelationship = None
    SyncRecord = None
    RitualOrchestrator = None
    RitualPhase = None

__all__ = [
    'SoulBridge',
    'TransferRequest',
    'TransferResult',
    'MemoryTransfer',
    'StateReconciliation',
    'Conflict',
    'ReconciliationResult',
]

# Add ritual components to __all__ if available
if RITUAL_COMPONENTS_AVAILABLE:
    __all__.extend([
        'SoulspeakCodec',
        'SoulspeakProtocol',
        'TransferMode',
        'TransferProgress',
        'SoulRelationship',
        'SyncRecord',
        'RitualOrchestrator',
        'RitualPhase',
    ])
