"""
JanetBrain - Primary LLM Response Generator
Always-on brain for Janet that coordinates all interactions and delegates tasks.
"""
from typing import Dict, Optional, List, Callable, Any
from pathlib import Path
import threading
import time

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    RED_THREAD_EVENT = None

try:
    from delegation import DelegationManager, HandlerCapability
    DELEGATION_AVAILABLE = True
except ImportError:
    DELEGATION_AVAILABLE = False


class JanetBrain:
    """
    Janet's primary brain - always-on LLM response generator.
    
    This is the core intelligence that:
    - Generates all conversational responses
    - Detects when delegation is needed
    - Coordinates async workflows
    - Integrates with voice I/O
    """
    
    def __init__(
        self,
        model_name: str = "tinyllama:1.1b",
        delegation_manager: Optional[DelegationManager] = None,
        memory_manager=None
    ):
        """
        Initialize JanetBrain.
        
        Args:
            model_name: Ollama model name to use (default: tinyllama:1.1b)
            delegation_manager: DelegationManager instance for task delegation
            memory_manager: MemoryManager instance for context retrieval
        """
        self.model_name = model_name
        self.delegation_manager = delegation_manager
        self.memory_manager = memory_manager
        self.available = False
        self.pending_delegations: Dict[str, Dict] = {}  # Track async delegations
        
        # Conversation session management
        self.conversation_history: List[Dict[str, str]] = []  # Store user/assistant messages
        self.conversation_active: bool = False
        self.max_context_messages: int = 20  # Limit conversation history to prevent token overflow
        
        # Initialize model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLM model."""
        if not HAS_LITELLM:
            print("⚠️  LiteLLM not available. JanetBrain will not function.")
            return
        
        # Check if Ollama is available
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Check if model is available
                if self.model_name in result.stdout:
                    self.available = True
                    print(f"✅ JanetBrain initialized with {self.model_name}")
                else:
                    print(f"⚠️  Model {self.model_name} not found. Please install it.")
                    print(f"   Run: ollama pull {self.model_name}")
            else:
                print("⚠️  Ollama not available. JanetBrain will not function.")
        except Exception as e:
            print(f"⚠️  Failed to check Ollama: {e}")
            print("   JanetBrain will not function.")
    
    def is_available(self) -> bool:
        """Check if JanetBrain is available."""
        return self.available and HAS_LITELLM
    
    def start_conversation(self):
        """Start a new conversation session with empty context window."""
        self.conversation_history = []
        self.conversation_active = True
    
    def end_conversation(self):
        """End conversation session and clear context window."""
        self.conversation_active = False
        self.conversation_history = []
    
    def add_to_history(self, role: str, content: str):
        """
        Add message to conversation history.
        
        Args:
            role: "user" or "assistant"
            content: Message content
        """
        if not self.conversation_active:
            return
        
        self.conversation_history.append({"role": role, "content": content})
        
        # Implement sliding window - keep most recent N messages
        if len(self.conversation_history) > self.max_context_messages:
            # Keep system prompt equivalent + most recent messages
            # Remove oldest user/assistant pairs
            excess = len(self.conversation_history) - self.max_context_messages
            self.conversation_history = self.conversation_history[excess:]
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get current conversation history."""
        return self.conversation_history.copy()
    
    def generate_response(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate response to user input.
        
        This is the primary method that:
        1. Checks for delegation needs
        2. Generates LLM response
        3. Coordinates async workflows
        4. Returns final response
        
        Args:
            user_input: User's input text
            context: Additional context (memory, tone, etc.)
            
        Returns:
            Generated response text
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            return "🔴 Red Thread active - responses paused"
        
        if not self.is_available():
            return "I'm sorry, my brain is not available right now. Please check if Ollama is installed and the model is available."
        
        # Build prompt with context
        prompt = self._build_prompt(user_input, context)
        
        # Check for delegation needs
        delegation_result = self._check_delegation(user_input, context)
        if delegation_result:
            # Handle delegation (async or sync)
            return self._handle_delegation(user_input, delegation_result, context)
        
        # Generate response using LLM with conversation history
        try:
            # Add user message to history before LLM call (for context)
            if self.conversation_active:
                self.add_to_history("user", user_input)
            
            # Build messages array with system prompt + conversation history + new user message with context
            messages = [
                {
                    "role": "system",
                    "content": "You are Janet, a constitutional AI companion. Be helpful, respectful, and follow constitutional principles."
                }
            ]
            
            # Add conversation history (excluding the just-added user message, we'll add it with context)
            if self.conversation_active and len(self.conversation_history) > 1:
                # Get history without the last message (which is the current user input)
                history_without_current = self.conversation_history[:-1]
                messages.extend(history_without_current)
            
            # Add new user message with context (prompt includes user_input + context)
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = litellm.completion(
                model=f"ollama/{self.model_name}",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            if response and response.choices:
                response_text = response.choices[0].message.content.strip()
                
                # Add assistant response to conversation history
                if self.conversation_active:
                    self.add_to_history("assistant", response_text)
                
                return response_text
            else:
                return "I'm having trouble generating a response right now."
        except Exception as e:
            print(f"⚠️  LLM generation failed: {e}")
            return "I'm sorry, I encountered an error generating a response."
    
    def _build_prompt(self, user_input: str, context: Optional[Dict]) -> str:
        """Build prompt with context."""
        prompt_parts = [user_input]
        
        if context:
            # Add memory context
            if "relevant_memories" in context:
                memories = context["relevant_memories"]
                if memories:
                    prompt_parts.append("\n\nRelevant context from past conversations:")
                    for mem in memories[:3]:  # Limit to 3 most relevant
                        prompt_parts.append(f"- {mem.get('text', '')[:100]}")
            
            # Add tone context
            if "tone" in context:
                tone = context["tone"]
                if tone.get("emotion"):
                    prompt_parts.append(f"\n\nUser's emotional tone: {tone.get('emotion')}")
        
        return "\n".join(prompt_parts)
    
    def _check_delegation(self, user_input: str, context: Optional[Dict]) -> Optional[Dict]:
        """
        Check if user input requires delegation.
        
        Returns:
            Dict with delegation info if needed, None otherwise
        """
        if not DELEGATION_AVAILABLE or not self.delegation_manager:
            return None
        
        user_lower = user_input.lower()
        
        # Check for image processing requests
        image_keywords = ["image", "picture", "photo", "analyze image", "look at", "see this"]
        if any(keyword in user_lower for keyword in image_keywords):
            return {
                "capability": HandlerCapability.IMAGE_PROCESSING,
                "task_description": "Process user image",
                "input_data": {"user_query": user_input}
            }
        
        # Check for home automation requests
        ha_keywords = ["turn on", "turn off", "lights", "thermostat", "home assistant", "smart home"]
        if any(keyword in user_lower for keyword in ha_keywords):
            # Parse home automation command
            domain = "light"  # Default
            service = "turn_on"
            entity_id = None
            
            if "light" in user_lower:
                domain = "light"
                if "off" in user_lower or "turn off" in user_lower:
                    service = "turn_off"
                else:
                    service = "turn_on"
                # Try to extract entity ID (simplified)
                if "living room" in user_lower:
                    entity_id = "light.living_room"
                elif "bedroom" in user_lower:
                    entity_id = "light.bedroom"
            
            return {
                "capability": HandlerCapability.HOME_AUTOMATION,
                "task_description": f"Home automation: {domain}.{service}",
                "input_data": {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id
                }
            }
        
        return None
    
    def _handle_delegation(
        self,
        user_input: str,
        delegation_info: Dict,
        context: Optional[Dict]
    ) -> str:
        """
        Handle delegation request.
        
        Args:
            user_input: Original user input
            delegation_info: Delegation information
            context: Additional context
            
        Returns:
            Response text (may be initial acknowledgment if async)
        """
        capability = delegation_info["capability"]
        task_description = delegation_info["task_description"]
        input_data = delegation_info["input_data"]
        
        # For now, handle synchronously
        # TODO: Implement async delegation with callbacks
        result = self.delegation_manager.delegate(
            capability=capability,
            task_description=task_description,
            input_data=input_data,
            context=context,
            confirm_callback=lambda msg: True  # Auto-confirm for now
        )
        
        if result and result.success:
            # Generate response incorporating delegation result
            return self._generate_response_with_delegation_result(
                user_input,
                result,
                context
            )
        else:
            return "I tried to handle that, but encountered an issue. Let me try a different approach."
    
    def _generate_response_with_delegation_result(
        self,
        user_input: str,
        delegation_result: Any,
        context: Optional[Dict]
    ) -> str:
        """Generate final response incorporating delegation results."""
        # Get summary from delegation result
        output_data = delegation_result.output_data if hasattr(delegation_result, 'output_data') else {}
        summary = output_data.get("summary", output_data.get("result", "Task completed"))
        
        # Build prompt for final response
        prompt = f"""User asked: {user_input}

The task has been completed. Result: {summary}

Generate a natural, conversational response acknowledging the completion."""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are Janet, a constitutional AI companion. Be helpful and natural."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = litellm.completion(
                model=f"ollama/{self.model_name}",
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                return f"Done! {summary}"
        except Exception as e:
            print(f"⚠️  Failed to generate response with delegation result: {e}")
            return f"Done! {summary}"
    
    def delegate_async(
        self,
        capability: HandlerCapability,
        task_description: str,
        input_data: Dict[str, Any],
        context: Optional[Dict] = None,
        result_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Delegate task asynchronously.
        
        Args:
            capability: Capability needed
            task_description: Task description
            input_data: Input data
            context: Additional context
            result_callback: Callback when result is ready
            
        Returns:
            True if delegation started, False otherwise
        """
        if not self.delegation_manager:
            return False
        
        def handle_result(result):
            if result and result.success:
                summary = result.output_data.get("summary", "Task completed")
                if result_callback:
                    result_callback(summary)
        
        return self.delegation_manager.delegate_async(
            capability=capability,
            task_description=task_description,
            input_data=input_data,
            context=context,
            result_callback=handle_result
        )

