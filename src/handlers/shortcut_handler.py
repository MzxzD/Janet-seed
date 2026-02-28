"""
Shortcut Handler - WebSocket message handler for dynamic shortcuts
Integrates DynamicShortcutBuilder with Janet's WebSocket server
"""

from typing import Dict, Any
from src.abilities.dynamic_shortcuts import DynamicShortcutBuilder


class ShortcutHandler:
    """Handles shortcut-related WebSocket messages"""
    
    def __init__(self, memory_manager, llm):
        self.shortcut_builder = DynamicShortcutBuilder(memory_manager, llm)
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route shortcut messages to appropriate handlers
        
        Args:
            message: WebSocket message from iPhone client
        
        Returns:
            Response message to send back to client
        """
        
        message_type = message.get("type")
        
        if message_type == "recognize_intent":
            return await self._handle_recognize_intent(message)
        
        elif message_type == "create_shortcut":
            return await self._handle_create_shortcut(message)
        
        elif message_type == "build_shortcut":
            return await self._handle_build_shortcut(message)
        
        elif message_type == "get_shortcuts":
            return await self._handle_get_shortcuts(message)
        
        elif message_type == "save_shortcut":
            return await self._handle_save_shortcut(message)
        
        elif message_type == "delete_shortcut":
            return await self._handle_delete_shortcut(message)
        
        else:
            return {"error": f"Unknown message type: {message_type}"}
    
    async def _handle_recognize_intent(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize user intent from text"""
        
        text = message.get("text", "")
        
        if not text:
            return {"error": "No text provided"}
        
        print(f"🎯 Recognizing intent for: {text}")
        
        result = self.shortcut_builder.recognize_intent(text)
        
        if result:
            return {
                "intent": result.get("intent"),
                "parameters": result.get("parameters", {}),
                "confidence": result.get("confidence", 0.0)
            }
        else:
            return {
                "error": "Failed to recognize intent",
                "intent": "unknown",
                "parameters": {},
                "confidence": 0.0
            }
    
    async def _handle_create_shortcut(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Start interactive shortcut creation"""
        
        intent = message.get("intent")
        parameters = message.get("parameters", {})
        
        if not intent:
            return {"error": "No intent provided"}
        
        print(f"🔨 Creating shortcut for intent: {intent}")
        
        result = self.shortcut_builder.create_shortcut_interactive(intent, parameters)
        
        return result
    
    async def _handle_build_shortcut(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Build the actual shortcut URL scheme"""
        
        intent = message.get("intent")
        parameters = message.get("parameters", {})
        answers = message.get("answers", {})
        
        if not intent:
            return {"error": "No intent provided"}
        
        print(f"🏗️ Building shortcut for: {intent}")
        
        result = self.shortcut_builder.build_shortcut(intent, parameters, answers)
        
        if "error" in result:
            return result
        
        return {
            "url_scheme": result.get("url_scheme"),
            "name": result.get("name"),
            "description": result.get("description"),
            "shortcut_id": result.get("id")
        }
    
    async def _handle_get_shortcuts(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Get all shortcuts from Green Vault"""
        
        print("📥 Getting all shortcuts")
        
        shortcuts = self.shortcut_builder.get_all_shortcuts()
        
        return {
            "shortcuts": shortcuts,
            "count": len(shortcuts)
        }
    
    async def _handle_save_shortcut(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Save a shortcut to Green Vault"""
        
        shortcut = message.get("shortcut")
        
        if not shortcut:
            return {"error": "No shortcut provided"}
        
        print(f"💾 Saving shortcut: {shortcut.get('name', 'unknown')}")
        
        # The shortcut is already saved by build_shortcut
        # This is just for explicit saves from the client
        
        return {
            "success": True,
            "message": "Shortcut saved"
        }
    
    async def _handle_delete_shortcut(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a shortcut from Green Vault"""
        
        shortcut_id = message.get("shortcut_id")
        
        if not shortcut_id:
            return {"error": "No shortcut_id provided"}
        
        print(f"🗑️ Deleting shortcut: {shortcut_id}")
        
        success = self.shortcut_builder.delete_shortcut(shortcut_id)
        
        return {
            "success": success,
            "message": "Shortcut deleted" if success else "Failed to delete shortcut"
        }
