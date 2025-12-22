"""
LLM Learner - Fine-tuning interface for Green Vault learning
Integrates with LiteLLM/Ollama for model fine-tuning using Green Vault summaries.
"""
from typing import Dict, Optional, List, Any
from pathlib import Path
import json

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
    from datasets import Dataset
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    RED_THREAD_EVENT = None


class LLMLearner:
    """
    Handles LLM fine-tuning using Green Vault summaries.
    
    Supports:
    - Formatting training data from Green Vault
    - Fine-tuning via Ollama (if supported)
    - LoRA adaptation (if transformers available)
    - Saving and loading fine-tuned models
    """
    
    def __init__(
        self,
        model_name: str = "tinyllama:1.1b",
        learning_manager=None,
        models_dir: Optional[Path] = None
    ):
        """
        Initialize LLM learner.
        
        Args:
            model_name: Base model name for fine-tuning
            learning_manager: LearningManager instance
            models_dir: Directory for storing fine-tuned models
        """
        self.model_name = model_name
        self.learning_manager = learning_manager
        self.models_dir = Path(models_dir) if models_dir else Path.home() / ".janet" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def format_training_data(self, summaries: List[Dict]) -> List[Dict]:
        """
        Format Green Vault summaries as training data.
        
        Args:
            summaries: List of summary dictionaries from Green Vault
            
        Returns:
            List of formatted training examples
        """
        training_examples = []
        
        for summary in summaries:
            summary_text = summary.get("summary", "")
            tags = summary.get("tags", [])
            
            # Format as conversation example
            # Simple format: summary as both input and output (for now)
            # In practice, would format as Q&A or instruction-following
            example = {
                "input": f"Context: {', '.join(tags)}\nSummary: {summary_text}",
                "output": summary_text
            }
            training_examples.append(example)
        
        return training_examples
    
    def fine_tune(
        self,
        training_data: List[Dict],
        output_model_name: Optional[str] = None,
        epochs: int = 3,
        learning_rate: float = 2e-5
    ) -> Optional[str]:
        """
        Fine-tune model using training data.
        
        Args:
            training_data: Formatted training data
            output_model_name: Name for fine-tuned model
            epochs: Number of training epochs
            learning_rate: Learning rate
            
        Returns:
            Path to fine-tuned model or None if failed
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - fine-tuning blocked")
            return None
        
        if not training_data:
            print("⚠️  No training data provided")
            return None
        
        if output_model_name is None:
            output_model_name = f"{self.model_name}_finetuned"
        
        # Check if transformers available for LoRA
        if HAS_TRANSFORMERS:
            return self._fine_tune_with_transformers(
                training_data,
                output_model_name,
                epochs,
                learning_rate
            )
        else:
            # Fallback: Use Ollama fine-tuning (if supported)
            print("⚠️  Transformers not available. Fine-tuning requires transformers, peft, and accelerate.")
            print("   Install with: pip install transformers peft accelerate torch")
            return None
    
    def _fine_tune_with_transformers(
        self,
        training_data: List[Dict],
        output_model_name: str,
        epochs: int,
        learning_rate: float
    ) -> Optional[str]:
        """Fine-tune using transformers library."""
        try:
            # This is a simplified implementation
            # Full implementation would:
            # 1. Load base model
            # 2. Apply LoRA adapters
            # 3. Prepare dataset
            # 4. Train
            # 5. Save adapters
            
            print(f"📚 Fine-tuning {self.model_name} with {len(training_data)} examples...")
            print("   This is a placeholder - full implementation requires model loading and training setup")
            print("   For now, saving training data for manual fine-tuning")
            
            # Save training data
            training_file = self.models_dir / f"{output_model_name}_training_data.json"
            with open(training_file, 'w') as f:
                json.dump(training_data, f, indent=2)
            
            print(f"✅ Training data saved to {training_file}")
            print("   Full fine-tuning implementation coming soon")
            
            return str(training_file)
        except Exception as e:
            print(f"⚠️  Fine-tuning failed: {e}")
            return None
    
    def load_fine_tuned_model(self, model_path: str) -> bool:
        """
        Load a fine-tuned model.
        
        Args:
            model_path: Path to fine-tuned model
            
        Returns:
            True if loaded successfully, False otherwise
        """
        # Placeholder - would load model adapters
        print(f"📥 Loading fine-tuned model from {model_path}...")
        print("   Full model loading implementation coming soon")
        return False
    
    def get_training_data_from_green_vault(
        self,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get training data from Green Vault via LearningManager.
        
        Args:
            limit: Maximum number of summaries to use
            
        Returns:
            Formatted training data
        """
        if not self.learning_manager:
            return []
        
        # Get summaries with consent
        summaries = self.learning_manager.get_training_data(limit=limit)
        
        # Format for training
        return self.format_training_data(summaries)

