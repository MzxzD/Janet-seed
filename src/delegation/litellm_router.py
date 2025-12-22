"""
LiteLLM Router for Model Delegation
Routes tasks to specialized models: conversation, programming, deep_thinking
"""
from typing import Dict, Optional, List
from enum import Enum

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False


class TaskType(Enum):
    """Task types for model routing."""
    CONVERSATION = "conversation"
    PROGRAMMING = "programming"
    DEEP_THINKING = "deep_thinking"
    GENERAL = "general"


class LiteLLMRouter:
    """Routes tasks to appropriate models using LiteLLM."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize LiteLLM router.
        
        Args:
            config: Configuration dictionary with model mappings
        """
        self.config = config or self._default_config()
        self.available = HAS_LITELLM
        
        if not HAS_LITELLM:
            print("⚠️  LiteLLM not available. Install with: pip install litellm")
    
    def _default_config(self) -> Dict:
        """Default model configuration."""
        return {
            "conversation": {
                "model": "ollama/llama3",  # Default conversation model
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "programming": {
                "model": "ollama/deepseek-coder:6.7b",  # Programming model
                "temperature": 0.3,
                "max_tokens": 2000
            },
            "deep_thinking": {
                "model": "ollama/llama3:70b",  # Deep thinking model (if available)
                "temperature": 0.5,
                "max_tokens": 3000
            },
            "general": {
                "model": "ollama/llama3",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
    
    def is_available(self) -> bool:
        """Check if LiteLLM is available."""
        return self.available
    
    def detect_task_type(self, query: str) -> TaskType:
        """
        Detect task type from query.
        
        Args:
            query: User query
        
        Returns:
            TaskType enum
        """
        query_lower = query.lower()
        
        # Programming indicators
        programming_keywords = [
            "code", "program", "function", "class", "debug", "syntax",
            "algorithm", "python", "javascript", "api", "library",
            "import", "def ", "function", "variable", "loop", "recursion"
        ]
        if any(keyword in query_lower for keyword in programming_keywords):
            return TaskType.PROGRAMMING
        
        # Deep thinking indicators
        deep_thinking_keywords = [
            "philosophy", "meaning", "why", "existential", "ethics",
            "reflect", "analyze deeply", "think about", "contemplate",
            "what does it mean", "explore", "examine", "consider"
        ]
        if any(keyword in query_lower for keyword in deep_thinking_keywords):
            return TaskType.DEEP_THINKING
        
        # Default to conversation
        return TaskType.CONVERSATION
    
    def route(self, query: str, task_type: Optional[TaskType] = None, context: Optional[Dict] = None) -> Optional[str]:
        """
        Route query to appropriate model.
        
        Args:
            query: User query
            task_type: Explicit task type, or None for auto-detection
            context: Additional context
        
        Returns:
            Model response, or None if unavailable
        """
        if not self.is_available():
            return None
        
        # Detect task type if not provided
        if task_type is None:
            task_type = self.detect_task_type(query)
        
        # Get model config
        task_name = task_type.value
        model_config = self.config.get(task_name, self.config["general"])
        
        try:
            # Prepare messages
            messages = []
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Context: {context}"
                })
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Call model via LiteLLM
            response = litellm.completion(
                model=model_config["model"],
                messages=messages,
                temperature=model_config.get("temperature", 0.7),
                max_tokens=model_config.get("max_tokens", 1000)
            )
            
            # Extract response text
            if response and response.choices:
                return response.choices[0].message.content
            
            return None
        except Exception as e:
            print(f"⚠️  LiteLLM routing failed: {e}")
            return None
    
    def list_available_models(self) -> List[str]:
        """List available models."""
        if not self.is_available():
            return []
        
        try:
            # List models from config
            models = set()
            for config in self.config.values():
                if "model" in config:
                    models.add(config["model"])
            return list(models)
        except Exception:
            return []

