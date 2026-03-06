"""
Media Storage Handler - Process and store images, audio, video in Green Vault.
Calls janet-media binary (JanetMedia) for summarization, stores in Green Vault (JBJanet).
"""
import os
from pathlib import Path
from typing import Dict, Optional, List, Any

import requests

from .base import (
    DelegationHandler,
    DelegationRequest,
    DelegationResult,
    HandlerCapability,
)


class MediaStorageHandler(DelegationHandler):
    """Handler for remembering media (images, audio, video) in Green Vault."""

    def __init__(
        self,
        media_url: str = "http://localhost:9872",
        memory_manager=None,
    ):
        """
        Initialize MediaStorageHandler.

        Args:
            media_url: janet-media binary base URL (default: http://localhost:9872)
            memory_manager: MemoryManager instance for Green Vault storage
        """
        super().__init__("media_storage", "Media Storage Handler")
        self.media_url = media_url.rstrip("/")
        self.memory_manager = memory_manager

    def get_capabilities(self) -> List[HandlerCapability]:
        """Return media storage capability."""
        return [HandlerCapability.MEDIA_STORAGE]

    def can_handle(self, request: DelegationRequest) -> bool:
        """Check if we can handle media storage."""
        if request.capability != HandlerCapability.MEDIA_STORAGE:
            return False
        if not self.is_available():
            return False
        file_path = request.input_data.get("file_path")
        return file_path and Path(file_path).exists()

    def handle(self, request: DelegationRequest) -> DelegationResult:
        """Process media via janet-media, store summary in Green Vault."""
        file_path = request.input_data.get("file_path")
        media_type = request.input_data.get("media_type", "image")

        if not file_path or not Path(file_path).exists():
            return DelegationResult(
                success=False,
                output_data={},
                message="File not found",
                error="file_path missing or file does not exist",
            )

        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f)}
                data = {"media_type": media_type}
                resp = requests.post(
                    f"{self.media_url}/process",
                    files=files,
                    data=data,
                    timeout=120,
                )
            resp.raise_for_status()
            result = resp.json()
        except requests.RequestException as e:
            return DelegationResult(
                success=False,
                output_data={},
                message="janet-media request failed",
                error=str(e),
            )
        except ValueError as e:
            return DelegationResult(
                success=False,
                output_data={},
                message="Invalid response from janet-media",
                error=str(e),
            )

        summary = result.get("summary", "")
        tags = result.get("tags", [])
        confidence = result.get("confidence", 0.85)

        if not self.memory_manager or not summary:
            return DelegationResult(
                success=True,
                output_data={
                    "summary": summary,
                    "tags": tags,
                    "confidence": confidence,
                    "stored": False,
                },
                message=f"Summarized: {summary[:80]}...",
            )

        try:
            entry_id = self.memory_manager.green_vault.add_summary(
                summary=summary,
                tags=tags,
                confidence=confidence,
                expiry=None,
            )
            stored = entry_id != ""
        except Exception as e:
            return DelegationResult(
                success=False,
                output_data={"summary": summary},
                message="Failed to store in Green Vault",
                error=str(e),
            )

        return DelegationResult(
            success=True,
            output_data={
                "summary": summary,
                "tags": tags,
                "entry_id": entry_id,
                "stored": stored,
            },
            message=f"Remembered: {summary[:80]}..." if stored else f"Summarized: {summary[:80]}...",
        )

    def is_available(self) -> bool:
        """Check if janet-media is reachable."""
        try:
            resp = requests.get(f"{self.media_url}/health", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False
