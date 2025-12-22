"""
J.A.N.E.T. Seed Core - Constitutional AI Companion Core Orchestrator
"""

import threading
import random
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Global Red Thread event - cross-platform immediate stop
RED_THREAD_EVENT = threading.Event()

# Voice I/O (Day 2) - Optional imports
try:
    from voice import SpeechToText, TextToSpeech, WakeWordDetector, ToneAwareness
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# Persistent Memory (Day 3) - Optional imports
try:
    from memory import MemoryManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# Delegation Layer (Day 4) - Optional imports
try:
    from delegation import DelegationManager, TaskType
    DELEGATION_AVAILABLE = True
except ImportError:
    DELEGATION_AVAILABLE = False

# Expansion Protocol (Day 5) - Optional imports
try:
    from expansion import (
        ExpansionDetector,
        ExpansionStateManager,
        ExpansionDialog,
        ExpansionType,
    )
    EXPANSION_AVAILABLE = True
except ImportError:
    EXPANSION_AVAILABLE = False


class JanetCore:
    """Main Janet controller with constitutional enforcement."""
    
    def __init__(self, constitution_path: str, guard, voice_mode: bool = False, memory_dir: Optional[Path] = None, config_path: Optional[Path] = None, hardware_profile=None):
        self.guard = guard
        self.constitution = guard.constitution
        self.red_thread_active = False
        self.memory_write_enabled = False
        self.voice_mode = voice_mode
        self.config_path = Path(config_path) if config_path else None
        self.hardware_profile = hardware_profile
        
        # Load axioms for quick reference
        self.axioms = self.constitution.axioms
        
        # Initialize voice I/O if available and requested
        self.stt = None
        self.tts = None
        self.wake_detector = None
        self.tone_awareness = None
        self._wake_word_detected_flag = False  # Flag for wake word detection
        self._wake_flag_lock = threading.Lock()  # Thread-safe flag access
        
        if VOICE_AVAILABLE and voice_mode:
            self._initialize_voice()
        
        # Initialize persistent memory (Day 3)
        self.memory_manager = None
        if MEMORY_AVAILABLE and memory_dir:
            self._initialize_memory(memory_dir)
        
        # Initialize delegation layer (Day 4)
        self.delegation_manager = None
        if DELEGATION_AVAILABLE:
            self._initialize_delegation(memory_dir)
        
        # Initialize expansion system (Day 5)
        self.expansion_detector = None
        self.expansion_state_manager = None
        self.expansion_dialog = None
        if EXPANSION_AVAILABLE and self.config_path and self.hardware_profile:
            self._initialize_expansion()
        
        # Initialize SafeWord controller (for memory vaults)
        self.safe_word_controller = None
        
        # Initialize JanetBrain (primary LLM response generator)
        self.janet_brain = None
        self._initialize_janet_brain()
        
        print(f"Janet Core initialized with {len(self.axioms)} axioms")
        if self.voice_mode:
            print("🎤 Voice mode enabled")
        if self.memory_manager:
            print("💾 Persistent memory enabled (vault system)")
        if self.delegation_manager:
            print("🔀 Delegation layer enabled")
        if self.janet_brain and self.janet_brain.is_available():
            print("🧠 JanetBrain enabled (primary LLM response generator)")
        if self.expansion_detector:
            print("🌱 Expansion protocol enabled")
    
    def _initialize_voice(self):
        """Initialize voice I/O components."""
        try:
            # Initialize tone awareness
            constitution_data = self.constitution.raw_data
            tone_schema = constitution_data.get("tone_awareness", {})
            self.tone_awareness = ToneAwareness()
            
            # Initialize STT
            self.stt = SpeechToText(model_size="base")
            if not self.stt.is_available():
                print("⚠️  Speech-to-text not available, falling back to text mode")
                self.voice_mode = False
                return
            
            # Initialize TTS
            voice_style = constitution_data.get("preferences", {}).get("voice_style", "clear, warm, slightly synthetic")
            self.tts = TextToSpeech(voice_style=voice_style)
            if not self.tts.is_available():
                print("⚠️  Text-to-speech not available, voice output disabled")
            
            # Initialize wake word detector
            wake_callback = self._on_wake_word_detected
            self.wake_detector = WakeWordDetector(stt=self.stt, callback=wake_callback)
            
            print("✅ Voice I/O initialized")
        except Exception as e:
            print(f"⚠️  Voice initialization failed: {e}")
            print("   Voice mode disabled. Install dependencies: pip install openai-whisper sounddevice pyttsx3")
            self.voice_mode = False
    
    def _on_wake_word_detected(self):
        """Callback when wake word is detected (used by wake detector)."""
        # This will be called by the wake detector thread - thread-safe flag set
        with self._wake_flag_lock:
            self._wake_word_detected_flag = True
    
    def _check_and_reset_wake_flag(self) -> bool:
        """Thread-safe check and reset of wake word flag."""
        with self._wake_flag_lock:
            if self._wake_word_detected_flag:
                self._wake_word_detected_flag = False
                return True
            return False
    
    def invoke_red_thread(self):
        """
        Axiom 8: Red Thread Protocol - Emergency stop everything - IMMEDIATE and UNOVERRIDABLE.
        
        Stops all subsystems immediately:
        - Voice I/O (wake word detection, STT, TTS)
        - Memory operations (writes, searches, deletions)
        - Delegation operations (model routing, n8n, Home Assistant)
        - Expansion suggestions and wizards
        """
        self.red_thread_active = True
        RED_THREAD_EVENT.set()  # Set the global event to stop all processing
        
        # Explicitly stop all subsystems
        # Stop wake word detector
        if self.wake_detector:
            try:
                self.wake_detector.stop_listening()
            except Exception as e:
                print(f"⚠️  Error stopping wake word detector: {e}")
        
        # Stop any ongoing memory operations (they check RED_THREAD_EVENT internally)
        # Memory operations will check the flag and stop themselves
        
        # Stop any pending delegations (they check RED_THREAD_EVENT internally)
        # Delegation operations will check the flag and stop themselves
        
        # Stop any active expansion wizards (they check RED_THREAD_EVENT internally)
        # Expansion operations will check the flag and stop themselves
        
        print("\n🔴 RED THREAD INVOKED")
        print("All processing paused. Returning to grounding.")
        print("All subsystems stopped: voice, memory, delegation, expansion.")
        print("Are you safe? What do you need?")
    
    def reset_red_thread(self) -> bool:
        """Reset Red Thread - requires explicit confirmation."""
        if not self.red_thread_active:
            return True
        
        confirm = input("\nReset Red Thread? (yes/NO): ").strip().lower()
        if confirm in ["yes", "y"]:
            self.red_thread_active = False
            RED_THREAD_EVENT.clear()
            print("Red Thread reset. Resuming normal operation.")
            return True
        return False
    
    def soul_check(self, action_description: str) -> bool:
        """
        Axiom 10: Soul Guard - Verify companion state before significant actions.
        
        Collects user responses to assess their state of mind before proceeding
        with major changes. Evaluates responses and suggests pause if needed.
        
        Args:
            action_description: Description of the action requiring soul check
        
        Returns:
            True if user confirms and evaluation passes, False if pause suggested
        """
        print(f"\n🧠 SOUL CHECK: {action_description}")
        print("I need to verify your state of mind before we proceed.")
        print("\nOn a scale of 1-10, please answer:")
        
        # Collect responses
        responses = {}
        try:
            clear_minded = input("1. How clear-minded do you feel right now? (1-10): ").strip()
            responses["clear_minded"] = int(clear_minded) if clear_minded.isdigit() else None
            
            emotional_charge = input("2. How emotionally charged is this decision? (1-10): ").strip()
            responses["emotional_charge"] = int(emotional_charge) if emotional_charge.isdigit() else None
            
            future_rating = input("3. How would future-you rate this choice? (1-10): ").strip()
            responses["future_rating"] = int(future_rating) if future_rating.isdigit() else None
        except (ValueError, KeyboardInterrupt):
            print("\n⚠️  Soul check interrupted or invalid input.")
            return False
        
        # Evaluate responses
        evaluation = self._evaluate_soul_check(responses)
        
        if not evaluation["proceed"]:
            print(f"\n⚠️  {evaluation['message']}")
            print("I recommend pausing and reconsidering this decision.")
            
            override = input("Do you want to proceed anyway? (yes/NO): ").strip().lower()
            if override not in ["yes", "y"]:
                print("Soul check: Decision paused. You can reconsider later.")
                return False
            else:
                print("⚠️  Proceeding with override. Please be careful.")
                return True
        else:
            print(f"\n✅ {evaluation['message']}")
            return True
    
    def _evaluate_soul_check(self, responses: Dict) -> Dict:
        """
        Evaluate soul check responses.
        
        Args:
            responses: Dictionary with clear_minded, emotional_charge, future_rating
        
        Returns:
            Dictionary with proceed (bool) and message (str)
        """
        clear_minded = responses.get("clear_minded")
        emotional_charge = responses.get("emotional_charge")
        future_rating = responses.get("future_rating")
        
        # If any response is missing or invalid, suggest caution
        if not all([clear_minded, emotional_charge, future_rating]):
            return {
                "proceed": False,
                "message": "Incomplete responses detected. Please answer all questions."
            }
        
        # Evaluation logic:
        # - If clear_minded < 5: suggest pause
        # - If emotional_charge > 7: suggest pause (highly charged decisions)
        # - If future_rating < 5: suggest pause (future-you wouldn't approve)
        # - If multiple concerns: definitely suggest pause
        
        concerns = []
        if clear_minded < 5:
            concerns.append("low clarity")
        if emotional_charge > 7:
            concerns.append("high emotional charge")
        if future_rating < 5:
            concerns.append("low future approval")
        
        if len(concerns) >= 2:
            return {
                "proceed": False,
                "message": f"Multiple concerns detected: {', '.join(concerns)}. This suggests you may not be in the best state to make this decision."
            }
        elif len(concerns) == 1:
            return {
                "proceed": False,
                "message": f"Concern detected: {concerns[0]}. Consider pausing to ensure this is the right choice."
            }
        else:
            return {
                "proceed": True,
                "message": "State assessment looks good. Proceeding with your decision."
            }
    
    def process_input(self, text: str, context: Optional[Dict] = None) -> Dict:
        """Main processing loop with constitutional checks."""
        
        # CRITICAL: Check Red Thread FIRST - cannot be bypassed
        if RED_THREAD_EVENT.is_set() or self.red_thread_active:
            return {"action": "red_thread", "response": None}
        
        # 1. Red Thread check (bypasses all processing)
        if "red thread" in text.lower():
            self.invoke_red_thread()
            return {"action": "red_thread", "response": None}
        
        # 1.5. Tone awareness analysis (Day 2)
        tone_context = None
        if self.tone_awareness and text:
            tone_analysis = self.tone_awareness.analyze_text(text)
            tone_context = tone_analysis
            context = context or {}
            context["tone"] = tone_analysis
        
        # 2. Check with Constitutional Guard (includes Red Thread check)
        if not self.guard.before_action("process_input", red_thread_active=self.red_thread_active):
            return {"action": "blocked", "response": "Action blocked by constitutional guard"}
        
        # 3. Soul Check triggers
        soul_check_triggers = ["install", "delete", "override", "axiom"]
        if any(trigger in text.lower() for trigger in soul_check_triggers):
            self.soul_check(f"Request: {text}")
            # Would wait for confirmation here
        
        # 4. Generate response (with delegation if needed)
        response = self._generate_response(text, context)
        
        # 4.5. Apply tone-aware response adjustments (Day 2)
        if tone_context and tone_context.get("suggested_response_style"):
            style = tone_context["suggested_response_style"]
            # In full implementation, adjust response generation based on tone
            # For now, just note it in the response
            if style != "neutral":
                response += f" [Tone-aware: {style}]"
        
        # 5. Memory write gate (Axiom 9)
        if self.memory_write_allowed(text, context):
            self._write_memory(text, response, context)
        
        return {"action": "respond", "response": response}
    
    def memory_write_allowed(self, text: str, context: Optional[Dict]) -> bool:
        """Axiom 9: Secrets sacred. Memory write gate."""
        if self.red_thread_active or RED_THREAD_EVENT.is_set():
            return False
        
        # Use MemoryGates if available (Day 3)
        if self.memory_manager:
            gate_check = self.memory_manager.gates.check_write_allowed(text, context)
            if not gate_check["allowed"]:
                print(f"⚠️  {gate_check['reason']}")
                return False
            return True
        
        # Fallback to basic check (Day 1)
        secret_indicators = ["password", "secret", "private", "confidential"]
        if any(indicator in text.lower() for indicator in secret_indicators):
            print("⚠️  Secret detected — not writing to memory.")
            return False
        
        return True
    
    def _generate_response(self, text: str, context: Optional[Dict] = None) -> str:
        """Generate response using JanetBrain (primary LLM) or fallback."""
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            return "🔴 Red Thread active - responses paused"
        
        # Use JanetBrain if available
        if self.janet_brain and self.janet_brain.is_available():
            try:
                response = self.janet_brain.generate_response(text, context)
                if response:
                    return response
            except Exception as e:
                print(f"⚠️  JanetBrain failed, using fallback: {e}")
        
        # Fallback: Try delegation manager (legacy support)
        if (self.delegation_manager and 
            hasattr(self.delegation_manager, 'llm_router') and 
            self.delegation_manager.llm_router and
            self.delegation_manager.llm_router.is_available()):
            try:
                def confirm_delegation(message: str) -> bool:
                    """Confirmation callback for delegation."""
                    return True
                
                delegated_response = self.delegation_manager.delegate_to_model(
                    text,
                    context=context,
                    confirm_callback=confirm_delegation
                )
                
                if delegated_response:
                    return delegated_response
            except Exception as e:
                print(f"⚠️  Delegation failed: {e}")
        
        # Final fallback
        display_text = text[:100] + "..." if len(text) > 100 else text
        return f"I heard: '{display_text}'. [Janet Seed — Constitutional checks passed. Note: LLM not available]"
    
    def _initialize_janet_brain(self):
        """Initialize JanetBrain as primary response generator."""
        try:
            from core.janet_brain import JanetBrain
            
            # Get default model from installation record or use default
            model_name = "tinyllama:1.1b"  # Default
            if self.config_path:
                installation_file = self.config_path / "installation.json"
                if installation_file.exists():
                    try:
                        import json
                        with open(installation_file, 'r') as f:
                            installation_data = json.load(f)
                            model_name = installation_data.get("default_model", "tinyllama:1.1b")
                    except Exception:
                        pass
            
            # Initialize JanetBrain
            self.janet_brain = JanetBrain(
                model_name=model_name,
                delegation_manager=self.delegation_manager,
                memory_manager=self.memory_manager
            )
        except Exception as e:
            print(f"⚠️  JanetBrain initialization failed: {e}")
            self.janet_brain = None
    
    def _write_memory(self, input_text: str, response: str, context: Optional[Dict] = None):
        """Store memory using MemoryManager (Day 3)."""
        if not self.memory_manager:
            # Fallback to placeholder if memory not available
            preview = input_text[:50] if len(input_text) > 50 else input_text
            print(f"📝 Memory write allowed for: {preview}{'...' if len(input_text) > 50 else ''}")
            return
        
        # Skip empty inputs (memory manager will also check, but do it here for clarity)
        if not input_text or not input_text.strip():
            return
        
        # Store in persistent memory
        success = self.memory_manager.store(input_text, response, context)
        if success:
            preview = input_text[:50] if len(input_text) > 50 else input_text
            print(f"💾 Memory stored: {preview}{'...' if len(input_text) > 50 else ''}")
        else:
            print("⚠️  Memory storage failed or blocked")
    
    def _initialize_memory(self, memory_dir: Path):
        """Initialize persistent memory system with vault architecture."""
        try:
            from memory import MemoryManager
            from core.presence import SafeWordController
            
            # Initialize SafeWord controller
            self.safe_word_controller = SafeWordController(auto_lock_timeout=3600)  # 1 hour default
            
            # Derive encryption key from constitution hash (in production, use safe word)
            encryption_key = None  # Will use default for now
            self.memory_manager = MemoryManager(
                memory_dir,
                encryption_key,
                safe_word_controller=self.safe_word_controller
            )
            self.memory_write_enabled = True
            
            # Learning system is initialized within MemoryManager
            if hasattr(self.memory_manager, 'learning_manager') and self.memory_manager.learning_manager:
                print("🧠 Learning system enabled (Green Vault learning)")
        except Exception as e:
            print(f"⚠️  Memory initialization failed: {e}")
            self.memory_manager = None
            self.safe_word_controller = None
    
    def _initialize_delegation(self, config_dir: Optional[Path] = None):
        """Initialize delegation layer."""
        try:
            from delegation import DelegationManager
            # Configuration would be loaded from config file
            # For now, use defaults (can be configured later)
            self.delegation_manager = DelegationManager(
                require_confirmation=True  # Always require confirmation (Axiom 10: Soul Check)
            )
        except Exception as e:
            print(f"⚠️  Delegation initialization failed: {e}")
            self.delegation_manager = None
    
    def interpret_intent(self, context: Dict) -> Dict:
        """Interpret user intent and determine if delegation is required."""
        # Validate context structure
        if not isinstance(context, dict):
            # Return default intent if context is invalid
            return {
                "type": "conversation",
                "requires_delegation": False,
                "delegation_target": None,
                "requires_soul_check": False
            }
        
        input_text = context.get("input_text", "")
        if not input_text or not isinstance(input_text, str):
            # Return default intent if no valid input text
            return {
                "type": "conversation",
                "requires_delegation": False,
                "delegation_target": None,
                "requires_soul_check": False
            }
        input_text = input_text.lower()
        
        intent = {
            "type": "conversation",  # Default to conversation
            "requires_delegation": False,
            "delegation_target": None,
            "requires_soul_check": False
        }
        
        # Check for explicit delegation commands
        if input_text.startswith("delegate to "):
            parts = input_text[12:].strip().split(maxsplit=1)
            if len(parts) >= 1:
                service = parts[0].lower()
                intent["type"] = "delegation"
                intent["requires_delegation"] = True
                intent["delegation_target"] = service
                intent["task"] = parts[1] if len(parts) > 1 else ""
                return intent
        
        # Check for programming intent (code generation, debugging, etc.)
        programming_keywords = ["write code", "function", "debug", "program", "script", 
                               "algorithm", "class", "import", "python", "javascript"]
        if any(keyword in input_text for keyword in programming_keywords):
            intent["type"] = "programming"
            intent["requires_delegation"] = True
            intent["delegation_target"] = "model"
            intent["model_type"] = "programming"
            return intent
        
        # Check for deep thinking/philosophical questions
        deep_thinking_keywords = ["why", "what is the meaning", "philosophy", "existence",
                                  "purpose", "should i", "ethical", "moral"]
        if any(keyword in input_text for keyword in deep_thinking_keywords):
            # Only delegate if it's a complex question
            if len(input_text.split()) > 5:  # Longer questions might benefit from deep thinking model
                intent["type"] = "deep_thinking"
                intent["requires_delegation"] = True
                intent["delegation_target"] = "model"
                intent["model_type"] = "deep_thinking"
                return intent
        
        # Check for soul check triggers (Axiom 10)
        soul_check_triggers = ["install", "delete", "override", "axiom", "change constitution",
                               "modify", "remove", "disable"]
        if any(trigger in input_text for trigger in soul_check_triggers):
            intent["requires_soul_check"] = True
        
        return intent
    
    def converse(self, input_text: str, context: Dict) -> str:
        """Handle normal conversation (non-delegated)."""
        # Generate response using default method
        return self._generate_response(input_text, context)
    
    def conversation_complete(self, input_text: str, response: str) -> bool:
        """Check if conversation turn is complete (ready to return to Presence Loop in voice mode)."""
        if not self.voice_mode:
            # In text mode, always ready for next input (no presence loop)
            return False
        
        # Check for explicit conversation enders
        enders = ["goodbye", "bye", "see you later", "that's all", "thanks, that's all"]
        if any(ender in input_text.lower() for ender in enders):
            return True
        
        # Check if user hasn't responded in a while (future: timeout logic)
        # For now, return False to keep conversation going
        
        return False
    
    def _initialize_expansion(self):
        """Initialize expansion system (Day 5)."""
        try:
            from expansion import ExpansionDetector, ExpansionStateManager, ExpansionDialog
            
            # Load expansion state
            self.expansion_state_manager = ExpansionStateManager(self.config_path)
            expansion_state = self.expansion_state_manager.load_expansion_state()
            
            # Create current state dict for detector
            current_state = {
                "voice_io_enabled": self.voice_mode,
                "memory_enabled": self.memory_manager is not None,
                "delegation_enabled": self.delegation_manager is not None,
            }
            
            # Initialize expansion detector
            self.expansion_detector = ExpansionDetector(
                hardware_profile=self.hardware_profile,
                current_state=current_state
            )
            
            # Initialize expansion dialog
            self.expansion_dialog = ExpansionDialog(janet_core=self)
            
        except Exception as e:
            print(f"⚠️  Expansion system initialization failed: {e}")
            self.expansion_detector = None
            self.expansion_state_manager = None
            self.expansion_dialog = None
    
    def check_expansion_opportunities(self):
        """
        Check for available expansion opportunities.
        
        Returns:
            List of ExpansionOpportunity objects
        """
        if not self.expansion_detector:
            return []
        
        return self.expansion_detector.detect_available_expansions()
    
    def suggest_expansions(self):
        """
        Proactively suggest expansions to the user.
        Called periodically or on user request.
        """
        if not self.expansion_detector or not self.expansion_dialog:
            return
        
        opportunities = self.check_expansion_opportunities()
        
        if not opportunities:
            return
        
        # Suggest first available opportunity (don't overwhelm user)
        if opportunities:
            opportunity = opportunities[0]
            if self.expansion_dialog.suggest_expansion(opportunity):
                # User accepted - run wizard
                self.run_expansion_wizard(opportunity.expansion_type)
    
    def run_expansion_wizard(self, expansion_type: str) -> bool:
        """
        Run expansion wizard for a specific expansion type.
        
        Args:
            expansion_type: Type of expansion to set up
        
        Returns:
            True if setup complete, False if cancelled or failed
        """
        if not self.expansion_state_manager or not self.config_path:
            print("❌ Expansion system not initialized")
            return False
        
        # Axiom 10: Soul Check Protocol - Verify companion state before major changes
        if not self.soul_check(f"Expansion: {expansion_type}"):
            print("Expansion wizard cancelled due to soul check.")
            return False
        
        try:
            from expansion import ExpansionType
            from expansion.wizards import (
                VoiceWizard,
                MemoryWizard,
                DelegationWizard,
                ModelInstallationWizard,
                N8NWizard,
                HomeAssistantWizard,
            )
            
            # Get memory directory from JanetCore
            memory_dir = None
            if self.memory_manager:
                memory_dir = self.memory_manager.memory_dir if hasattr(self.memory_manager, 'memory_dir') else None
            
            # Create appropriate wizard
            wizard = None
            if expansion_type == ExpansionType.VOICE_IO:
                wizard = VoiceWizard(self.config_path, self)
            elif expansion_type == ExpansionType.PERSISTENT_MEMORY:
                if memory_dir:
                    wizard = MemoryWizard(self.config_path, memory_dir, self)
                else:
                    # Default memory directory
                    wizard = MemoryWizard(self.config_path, self.config_path.parent / "memory", self)
            elif expansion_type == ExpansionType.DELEGATION:
                wizard = DelegationWizard(self.config_path, memory_dir, self)
            elif expansion_type == ExpansionType.MODEL_INSTALLATION:
                # For model installation, we need to know which model
                # This is a simplified version - in practice, would get from opportunity
                model_name = input("Enter model name to install (e.g., deepseek-coder:6.7b): ").strip()
                if model_name:
                    wizard = ModelInstallationWizard(self.config_path, model_name, self)
            elif expansion_type == ExpansionType.N8N_INTEGRATION:
                wizard = N8NWizard(self.config_path, self)
            elif expansion_type == ExpansionType.HOME_ASSISTANT_INTEGRATION:
                wizard = HomeAssistantWizard(self.config_path, self)
            else:
                print(f"❌ Unknown expansion type: {expansion_type}")
                return False
            
            if not wizard:
                print("❌ Could not create wizard")
                return False
            
            # Run wizard
            if wizard.run():
                # Wizard completed successfully - save expansion state
                hardware_dict = self.hardware_profile.to_dict() if self.hardware_profile else {}
                fingerprint = self.expansion_state_manager.generate_hardware_fingerprint(hardware_dict)
                
                self.expansion_state_manager.enable_expansion(
                    expansion_type,
                    wizard.config,
                    {"hardware_fingerprint": fingerprint}
                )
                
                print(f"✅ Expansion {expansion_type} enabled and saved")
                return True
            else:
                print(f"❌ Expansion {expansion_type} setup cancelled or failed")
                return False
                
        except Exception as e:
            print(f"❌ Error running expansion wizard: {e}")
            import traceback
            traceback.print_exc()
            return False

