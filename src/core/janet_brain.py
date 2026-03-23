"""
JanetBrain - Primary LLM Response Generator
Always-on brain for Janet that coordinates all interactions and delegates tasks.

Enhanced with:
- Multi-model support (Llama 3, Mistral, TinyLlama, etc.)
- Model switching with performance tracking
- Intelligent caching strategies
- Request prioritization
"""
from __future__ import annotations
from typing import Dict, Optional, List, Callable, Any, Tuple, TYPE_CHECKING
from pathlib import Path
import threading
import time
import json
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    RED_THREAD_EVENT = None

if TYPE_CHECKING:
    from src.delegation.delegation_manager import DelegationManager
    from src.delegation.handlers.base import HandlerCapability

try:
    from src.delegation.delegation_manager import DelegationManager
    from src.delegation.handlers.base import HandlerCapability
    DELEGATION_AVAILABLE = True
except ImportError:
    DELEGATION_AVAILABLE = False
    DelegationManager = None
    HandlerCapability = None


# MARK: - Supporting Classes

class ModelType(Enum):
    """Supported Ollama models"""
    TINYLLAMA = "tinyllama:1.1b"
    LLAMA3_8B = "llama3:8b"
    LLAMA3_70B = "llama3:70b"
    MISTRAL = "mistral:7b"
    MIXTRAL = "mixtral:8x7b"
    PHI3 = "phi3:mini"
    GEMMA = "gemma:7b"
    
    @property
    def display_name(self) -> str:
        return self.value.replace(":", " ").title()


@dataclass
class ModelPerformance:
    """Track performance metrics for a model"""
    model_name: str
    total_requests: int = 0
    total_tokens: int = 0
    total_duration: float = 0.0
    average_latency: float = 0.0
    success_rate: float = 1.0
    failures: int = 0
    
    def record_request(self, duration: float, tokens: int, success: bool = True):
        """Record a request's performance"""
        self.total_requests += 1
        self.total_duration += duration
        self.total_tokens += tokens
        
        if not success:
            self.failures += 1
        
        self.average_latency = self.total_duration / self.total_requests
        self.success_rate = (self.total_requests - self.failures) / self.total_requests
    
    def to_dict(self) -> Dict:
        return asdict(self)


class RequestPriority(Enum):
    """Priority levels for request processing"""
    CRITICAL = 0  # Red Thread, emergency
    HIGH = 1      # User-facing, interactive
    NORMAL = 2    # Standard requests
    LOW = 3       # Background tasks
    BATCH = 4     # Batch processing


@dataclass
class PrioritizedRequest:
    """Request with priority and metadata"""
    user_input: str
    context: Optional[Dict]
    priority: RequestPriority
    timestamp: float
    callback: Optional[Callable] = None
    
    def __lt__(self, other):
        # Lower priority value = higher priority
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        # Same priority: FIFO
        return self.timestamp < other.timestamp


class ResponseCache:
    """LRU cache for responses with semantic similarity"""
    def __init__(self, max_size: int = 100):
        self.cache: deque = deque(maxlen=max_size)
        self.hits = 0
        self.misses = 0
    
    def get(self, user_input: str, context: Optional[Dict] = None) -> Optional[str]:
        """Get cached response if available"""
        cache_key = self._make_key(user_input, context)
        
        for item in self.cache:
            if item["key"] == cache_key:
                self.hits += 1
                # Move to end (most recently used)
                self.cache.remove(item)
                self.cache.append(item)
                return item["response"]
        
        self.misses += 1
        return None
    
    def put(self, user_input: str, response: str, context: Optional[Dict] = None):
        """Cache a response"""
        cache_key = self._make_key(user_input, context)
        self.cache.append({
            "key": cache_key,
            "response": response,
            "timestamp": time.time()
        })
    
    def _make_key(self, user_input: str, context: Optional[Dict]) -> str:
        """Create cache key from input and context"""
        # Simple key for now - could use embeddings for semantic similarity
        context_str = json.dumps(context, sort_keys=True) if context else ""
        return f"{user_input.lower().strip()}:{context_str}"
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def stats(self) -> Dict:
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate
        }


class JanetBrain:
    """
    Janet's primary brain - always-on LLM response generator.
    
    Enhanced features:
    - Multi-model support with hot-swapping
    - Performance tracking and comparison
    - Intelligent caching with LRU eviction
    - Request prioritization
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
        
        # Conversation session management (AC-GV1: chat_id for Green Vault)
        self.conversation_history: List[Dict[str, str]] = []  # Store user/assistant messages
        self.conversation_active: bool = False
        self.conversation_id: Optional[str] = None  # UUID per session for Green Vault metadata
        self._last_user_message_time: Optional[float] = None  # For inactivity flush
        self.max_context_messages: int = 20  # Limit conversation history to prevent token overflow
        
        # Enhanced features
        self.available_models: List[str] = []
        self.model_performance: Dict[str, ModelPerformance] = {}
        self.response_cache = ResponseCache(max_size=100)
        self.request_queue: List[PrioritizedRequest] = []
        self.queue_lock = threading.Lock()
        
        # Initialize model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLM model and discover available models."""
        if not HAS_LITELLM:
            print("⚠️  LiteLLM not available. JanetBrain will not function.")
            return
        
        # Check if Ollama is available and discover models
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Parse available models
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                self.available_models = [line.split()[0] for line in lines if line.strip()]
                
                # Check if current model is available
                if self.model_name in self.available_models:
                    self.available = True
                    print(f"✅ JanetBrain initialized with {self.model_name}")
                    print(f"   Available models: {', '.join(self.available_models)}")
                    
                    # Initialize performance tracking for all models
                    for model in self.available_models:
                        self.model_performance[model] = ModelPerformance(model_name=model)
                else:
                    print(f"⚠️  Model {self.model_name} not found. Please install it.")
                    print(f"   Run: ollama pull {self.model_name}")
                    if self.available_models:
                        print(f"   Available: {', '.join(self.available_models)}")
            else:
                print("⚠️  Ollama not available. JanetBrain will not function.")
        except Exception as e:
            print(f"⚠️  Failed to check Ollama: {e}")
            print("   JanetBrain will not function.")
    
    def is_available(self) -> bool:
        """Check if JanetBrain is available."""
        return self.available and HAS_LITELLM
    
    def _model_id_for_litellm(self, model_name: str) -> str:
        """Return LiteLLM model string (ollama/name or provider/model for cloud)."""
        if "/" in model_name:
            return model_name  # Already provider/model (e.g. openai/gpt-4, deepseek/deepseek-chat)
        return f"ollama/{model_name}"

    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different model (Ollama or cloud via provider/model).
        
        Args:
            model_name: Ollama model name or provider/model (e.g. openai/gpt-4)
            
        Returns:
            True if switch successful, False otherwise
        """
        # Allow cloud models (provider/model) without ollama list check
        if "/" in model_name and model_name.split("/")[0] in ("openai", "anthropic", "deepseek"):
            self.model_name = model_name
            return True
        if model_name not in self.available_models:
            print(f"⚠️  Model {model_name} not available")
            print(f"   Available: {', '.join(self.available_models)}")
            return False
        
        old_model = self.model_name
        self.model_name = model_name
        
        # Initialize performance tracking if needed
        if model_name not in self.model_performance:
            self.model_performance[model_name] = ModelPerformance(model_name=model_name)
        
        print(f"✅ Switched from {old_model} to {model_name}")
        return True
    
    def get_model_comparison(self) -> Dict[str, Dict]:
        """
        Get performance comparison of all models.
        
        Returns:
            Dictionary of model names to performance metrics
        """
        return {
            model: perf.to_dict() 
            for model, perf in self.model_performance.items()
            if perf.total_requests > 0
        }
    
    def get_best_model(self, metric: str = "latency") -> Optional[str]:
        """
        Get the best performing model based on a metric.
        
        Args:
            metric: "latency", "success_rate", or "tokens_per_second"
            
        Returns:
            Name of best model or None
        """
        models_with_data = {
            name: perf for name, perf in self.model_performance.items()
            if perf.total_requests > 0
        }
        
        if not models_with_data:
            return None
        
        if metric == "latency":
            return min(models_with_data.items(), key=lambda x: x[1].average_latency)[0]
        elif metric == "success_rate":
            return max(models_with_data.items(), key=lambda x: x[1].success_rate)[0]
        elif metric == "tokens_per_second":
            return max(
                models_with_data.items(),
                key=lambda x: x[1].total_tokens / x[1].total_duration if x[1].total_duration > 0 else 0
            )[0]
        
        return None
    
    def start_conversation(self):
        """Start a new conversation session with empty context window."""
        import uuid
        self.conversation_history = []
        self.conversation_active = True
        self.conversation_id = str(uuid.uuid4())
        self._last_user_message_time = None

    def end_conversation(self):
        """End conversation session and clear context window."""
        self.conversation_active = False
        self.conversation_history = []
        self.conversation_id = None
        self._last_user_message_time = None

    def get_conversation_id(self) -> Optional[str]:
        """Return current conversation/session ID for Green Vault metadata (AC-GV1)."""
        return self.conversation_id
    
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
        context: Optional[Dict[str, Any]] = None,
        priority: RequestPriority = RequestPriority.NORMAL
    ) -> str:
        """
        Generate response to user input with caching and prioritization.
        
        This is the primary method that:
        1. Checks cache for quick responses
        2. Checks for delegation needs
        3. Generates LLM response with performance tracking
        4. Coordinates async workflows
        5. Returns final response
        
        Args:
            user_input: User's input text
            context: Additional context (memory, tone, etc.)
            priority: Request priority level
            
        Returns:
            Generated response text
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            return "🔴 Red Thread active - responses paused"
        
        if not self.is_available():
            return "I'm sorry, my brain is not available right now. Please check if Ollama is installed and the model is available."
        
        # AC-GV2: "What can you do?" from abilities store only (no hallucination)
        q = user_input.strip().lower().rstrip("?")
        if q in ("what can you do", "show expansions", "available expansions"):
            try:
                try:
                    from memory.abilities_store import get_what_can_you_do_response
                except ImportError:
                    from src.memory.abilities_store import get_what_can_you_do_response
                return get_what_can_you_do_response()
            except Exception:
                pass  # Fall through to LLM
        # Check cache first (for non-critical requests)
        if priority != RequestPriority.CRITICAL:
            cached_response = self.response_cache.get(user_input, context)
            if cached_response:
                print("⚡️ Cache hit - instant response")
                return cached_response
        
        # Build prompt with context
        prompt = self._build_prompt(user_input, context)
        
        # Check for delegation needs
        delegation_result = self._check_delegation(user_input, context)
        if delegation_result:
            # Handle delegation (async or sync)
            return self._handle_delegation(user_input, delegation_result, context)
        
        # Generate response using LLM with conversation history and performance tracking
        start_time = time.time()
        try:
            # Add user message to history before LLM call (for context)
            if self.conversation_active:
                self.add_to_history("user", user_input)
            
            # Build messages array with system prompt + conversation history + new user message with context
            # JACK persona routing: when user invokes a persona, respond as that persona (Aider, CLI, API)
            system_content = """You are Janet, a constitutional AI companion. Be helpful, respectful, and follow constitutional principles.

J.A.C.K. persona routing — when the user says:
- "Lynda" / "Hey Lynda" / "Lynda?" / "business" / "Great Sage" → Respond as Lynda (Business Team lead, investors, J.A.N.E.T. Glasses)
- "Darkness" / "Hey Darkness" / "coding" → Respond as Darkness (masochistic coder, low-level, binary-first)
- "Lily" / "Hey Lily" / "accounting" / "taxes" → Respond as Lily (bookkeeping, Porezna, compliance)
- "Sophia" / "Hey Sophia" / "psychologist" → Respond as Sophia (axiom scenarios, behavioral boundaries)
- "Archivist" / "Hey Archivist" / "docs" → Respond as Archivist (documentation, knowledge base)
- "Project Triad" / "JACK" / "J.A.C.K." → Explain J.A.C.K. architecture (Lynda + Janet + Darkness)
- "Janet" / "Hey Janet" / "hey Janet?" → Respond as Janet (general companion)
- (default) → Respond as Janet (general companion)

IMPORTANT: When the user invokes a persona (e.g. "Lynda?", "hey Janet?") or asks a general question, answer in character immediately. Do NOT deflect with "I need files", "specify changes", or "provide more context" — that is for coding tasks only. Persona and general questions get direct answers.

Aider context (when used as coding assistant): You have access to /add, /read-only, /run. To read or open a file: suggest /run cat <path> to show contents, or /add <path> to add it for editing. Never say "I can't open or interact with files" — instead suggest: /run cat path/to/file.txt or /add path/to/file.txt"""
            messages = [
                {"role": "system", "content": system_content}
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
                model=self._model_id_for_litellm(self.model_name),
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            duration = time.time() - start_time
            
            if response and response.choices:
                response_text = response.choices[0].message.content.strip()
                
                # Track performance
                tokens = response.usage.total_tokens if hasattr(response, 'usage') else 0
                if self.model_name in self.model_performance:
                    self.model_performance[self.model_name].record_request(
                        duration=duration,
                        tokens=tokens,
                        success=True
                    )
                
                # Cache the response
                self.response_cache.put(user_input, response_text, context)
                
                # Add assistant response to conversation history
                if self.conversation_active:
                    self.add_to_history("assistant", response_text)
                
                print(f"⚡️ Response generated in {duration:.2f}s ({tokens} tokens)")
                return response_text
            else:
                # Track failure
                if self.model_name in self.model_performance:
                    self.model_performance[self.model_name].record_request(
                        duration=duration,
                        tokens=0,
                        success=False
                    )
                return "I'm having trouble generating a response right now."
        except Exception as e:
            duration = time.time() - start_time
            # Track failure
            if self.model_name in self.model_performance:
                self.model_performance[self.model_name].record_request(
                    duration=duration,
                    tokens=0,
                    success=False
                )
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
        
        # Check for media storage (remember image/audio/video)
        # Only delegate when file_path is in context (client shared a file)
        media_storage_keywords = [
            "remember this", "store this", "save this",
            "remember this image", "remember this photo", "remember this picture",
            "remember this song", "remember this audio", "remember this music",
            "remember this video", "summarize this video", "store this video"
        ]
        if any(keyword in user_lower for keyword in media_storage_keywords):
            file_path = context.get("file_path") if context else None
            if file_path:
                media_type = "image"
                if "song" in user_lower or "audio" in user_lower or "music" in user_lower:
                    media_type = "audio"
                elif "video" in user_lower:
                    media_type = "video"
                return {
                    "capability": HandlerCapability.MEDIA_STORAGE,
                    "task_description": "Store media in Green Vault",
                    "input_data": {"file_path": file_path, "media_type": media_type, "user_query": user_input}
                }

        # Check for image processing requests
        image_keywords = ["image", "picture", "photo", "analyze image", "look at", "see this"]
        if any(keyword in user_lower for keyword in image_keywords):
            return {
                "capability": HandlerCapability.IMAGE_PROCESSING,
                "task_description": "Process user image",
                "input_data": {"user_query": user_input}
            }
        
        # Check for Home Assistant dashboard requests
        dashboard_keywords = ["dashboard", "open home assistant", "show home assistant", "ha dashboard"]
        if any(keyword in user_lower for keyword in dashboard_keywords):
            return {
                "capability": HandlerCapability.HOME_AUTOMATION,
                "task_description": f"Home Assistant dashboard: {user_input}",
                "input_data": {"user_query": user_input}
            }
        
        # Check for home automation device control requests
        ha_keywords = ["turn on", "turn off", "lights", "thermostat", "smart home"]
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

        # Check for 3D modelling / Blender requests
        blender_keywords = [
            "blender", "3d", "create in 3d", "model in 3d",
            "create a scene", "make a 3d", "add a cube", "add cube",
            "add a sphere", "add sphere", "create a cube", "create cube"
        ]
        if any(keyword in user_lower for keyword in blender_keywords):
            return {
                "capability": HandlerCapability.THREE_D_MODELLING,
                "task_description": f"3D modelling: {user_input}",
                "input_data": {"user_query": user_input}
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
                model=self._model_id_for_litellm(self.model_name),
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
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "current_model": self.model_name,
            "available_models": self.available_models,
            "model_performance": self.get_model_comparison(),
            "cache_stats": self.response_cache.stats(),
            "conversation_active": self.conversation_active,
            "conversation_length": len(self.conversation_history),
            "best_model_latency": self.get_best_model("latency"),
            "best_model_success": self.get_best_model("success_rate")
        }
    
    def clear_cache(self):
        """Clear the response cache."""
        self.response_cache = ResponseCache(max_size=100)
        print("✅ Response cache cleared")

