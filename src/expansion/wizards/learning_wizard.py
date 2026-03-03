"""
Learning Wizard — Guided Setup for Green Vault Learning
Guides users through selecting summaries, providing consent, choosing model, and initiating learning.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
from .wizard_base import ExpansionWizard
from memory.learning_manager import LearningManager
from memory.llm_learner import LLMLearner
from expansion.model_manager import ModelManager


class LearningWizard(ExpansionWizard):
    """Wizard for setting up learning from Green Vault."""
    
    def __init__(
        self,
        config_path: Path,
        learning_manager: LearningManager,
        janet_core=None
    ):
        """
        Initialize learning wizard.
        
        Args:
            config_path: Path to config directory
            learning_manager: LearningManager instance
            janet_core: Optional JanetCore instance
        """
        super().__init__(config_path, janet_core)
        self.learning_manager = learning_manager
        self.model_manager = ModelManager()
        self.selected_summaries: List[str] = []
        self.selected_model: Optional[str] = None
    
    def run(self) -> bool:
        """
        Run the learning wizard.
        
        Returns:
            True if learning setup complete
        """
        print(f"\n{'='*60}")
        print("🧠 Learning Wizard - Green Vault Learning Setup")
        print(f"{'='*60}\n")
        
        # Step 1: Review available summaries
        if not self._review_summaries():
            return False
        
        # Step 2: Select summaries for learning
        if not self._select_summaries():
            return False
        
        # Step 3: Choose model
        if not self._choose_model():
            return False
        
        # Step 4: Review and confirm
        if not self._review_and_confirm():
            return False
        
        # Step 5: Initiate learning
        return self._initiate_learning()
    
    def _review_summaries(self) -> bool:
        """Review available summaries for learning."""
        print("Step 1: Review Available Summaries")
        print("-" * 60)
        
        stats = self.learning_manager.get_learning_statistics()
        
        print(f"\n📊 Learning Data Statistics:")
        print(f"  Total summaries: {stats['total_summaries']}")
        print(f"  With consent: {stats['with_consent']}")
        print(f"  Opted out: {stats['opted_out']}")
        print(f"  Available for learning: {stats['available_for_learning']}")
        print(f"  Pending consent: {stats['pending_consent']}")
        
        if stats['available_for_learning'] == 0:
            print("\n⚠️  No summaries available for learning.")
            print("   You need to grant consent for summaries first.")
            print("   Use: learning consent <summary_id>")
            return False
        
        return True
    
    def _select_summaries(self) -> bool:
        """Select summaries for learning."""
        print("\nStep 2: Select Summaries for Learning")
        print("-" * 60)
        
        # Get available summaries
        available = self.learning_manager.get_training_data(limit=50)
        
        if not available:
            print("⚠️  No summaries available with consent.")
            return False
        
        print(f"\nFound {len(available)} summaries with consent.")
        print("\nOptions:")
        print("  1. Use all available summaries")
        print("  2. Select specific summaries")
        
        choice = input("\nChoose option (1/2): ").strip()
        
        if choice == "1":
            self.selected_summaries = [s.get("id") for s in available]
            print(f"✅ Selected all {len(self.selected_summaries)} summaries")
        elif choice == "2":
            # Show summaries for selection
            print("\nAvailable summaries:")
            for i, summary in enumerate(available[:20], 1):  # Show first 20
                preview = summary.get("summary", "")[:60]
                print(f"  {i}. [{summary.get('id', 'unknown')}] {preview}...")
            
            selected = input("\nEnter summary IDs (comma-separated): ").strip()
            self.selected_summaries = [s.strip() for s in selected.split(",") if s.strip()]
            
            if not self.selected_summaries:
                print("⚠️  No summaries selected")
                return False
            
            print(f"✅ Selected {len(self.selected_summaries)} summaries")
        else:
            print("Invalid choice")
            return False
        
        return True
    
    def _choose_model(self) -> bool:
        """Choose model for learning."""
        print("\nStep 3: Choose Model")
        print("-" * 60)
        
        # Get recommended models
        recommended = self.model_manager.get_learning_capable_models()
        available = self.model_manager.list_available_models()
        
        print("\nRecommended models for learning:")
        for i, model in enumerate(recommended, 1):
            is_available = any(model in avail for avail in available)
            status = "✅ Available" if is_available else "❌ Not installed"
            print(f"  {i}. {model} - {status}")
        
        # Suggest model
        suggested = self.model_manager.suggest_learning_model()
        if suggested:
            print(f"\n💡 Suggested: {suggested}")
        
        model_input = input("\nEnter model name (or press Enter for suggested): ").strip()
        
        if model_input:
            self.selected_model = model_input
        elif suggested:
            self.selected_model = suggested
        else:
            print("⚠️  No model selected")
            return False
        
        # Verify model
        supports, message = self.model_manager.verify_fine_tuning_support(self.selected_model)
        print(f"\n{message}")
        
        if not supports:
            print("⚠️  Model may not be suitable for fine-tuning")
            proceed = input("Continue anyway? (yes/NO): ").strip().lower()
            if proceed not in ["yes", "y"]:
                return False
        
        return True
    
    def _review_and_confirm(self) -> bool:
        """Review selections and confirm."""
        print("\nStep 4: Review and Confirm")
        print("-" * 60)
        
        print(f"\n📋 Learning Configuration:")
        print(f"  Model: {self.selected_model}")
        print(f"  Summaries: {len(self.selected_summaries)} selected")
        print(f"  Estimated training examples: {len(self.selected_summaries)}")
        
        print("\n⚠️  This will:")
        print("  - Use selected Green Vault summaries for training")
        print("  - Fine-tune the model (may take time)")
        print("  - Save fine-tuned model for use as Janet's brain")
        
        response = input("\nProceed with learning? (yes/NO): ").strip().lower()
        return response in ["yes", "y"]
    
    def _initiate_learning(self) -> bool:
        """Initiate the learning process."""
        print("\nStep 5: Initiating Learning")
        print("-" * 60)
        
        try:
            # Get training data
            training_data = self.learning_manager.get_training_data(
                limit=None,
                exclude_ids=None
            )
            
            # Filter to selected summaries
            if self.selected_summaries:
                training_data = [
                    t for t in training_data
                    if t.get("id") in self.selected_summaries
                ]
            
            if not training_data:
                print("⚠️  No training data available")
                return False
            
            # Initialize LLM learner
            models_dir = self.config_path.parent / "models"
            learner = LLMLearner(
                model_name=self.selected_model,
                learning_manager=self.learning_manager,
                models_dir=models_dir
            )
            
            # Format training data
            formatted_data = learner.format_training_data(training_data)
            
            print(f"\n📚 Starting fine-tuning...")
            print(f"   Model: {self.selected_model}")
            print(f"   Training examples: {len(formatted_data)}")
            print("   This may take a while...")
            
            # Fine-tune
            result = learner.fine_tune(
                training_data=formatted_data,
                output_model_name=f"{self.selected_model}_finetuned"
            )
            
            if result:
                print(f"\n✅ Learning complete!")
                print(f"   Fine-tuned model saved")
                
                # Audit the operation
                summary_ids = [t.get("id") for t in training_data]
                self.learning_manager.audit_learning_operation(
                    operation_type="fine-tuning",
                    data_used=summary_ids,
                    results={"model_path": result}
                )
                
                return True
            else:
                print("\n⚠️  Learning failed")
                return False
                
        except Exception as e:
            print(f"\n❌ Learning error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def setup(self) -> bool:
        """Perform the setup (called by base class)."""
        return self.run()
    
    def verify(self) -> bool:
        """Verify that setup was successful."""
        # Check if fine-tuned model exists
        models_dir = self.config_path.parent / "models"
        if self.selected_model:
            model_file = models_dir / f"{self.selected_model}_finetuned_training_data.json"
            return model_file.exists()
        return False
    
    def validate_requirements(self) -> Tuple[bool, List[str]]:
        """Validate learning requirements."""
        missing = []
        
        # Check for fine-tuning dependencies
        try:
            import transformers
        except ImportError:
            missing.append("transformers")
        
        try:
            import peft
        except ImportError:
            missing.append("peft")
        
        try:
            import torch
        except ImportError:
            missing.append("torch")
        
        # Check for Ollama
        if not self.model_manager.ollama_path:
            missing.append("ollama")
        
        # Check for available summaries
        stats = self.learning_manager.get_learning_statistics()
        if stats['available_for_learning'] == 0:
            missing.append("summaries with consent")
        
        return len(missing) == 0, missing

