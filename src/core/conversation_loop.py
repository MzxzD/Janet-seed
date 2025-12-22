"""
Conversation Loop for J.A.N.E.T. Seed
Handles the structured conversation flow with Red Thread, intent interpretation, and delegation.
"""

import random
from typing import TYPE_CHECKING, Union

# Import VOICE_AVAILABLE if needed
try:
    from voice import SpeechToText, TextToSpeech, WakeWordDetector, ToneAwareness
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

from .context_builder import build_context
from .janet_core import RED_THREAD_EVENT

if TYPE_CHECKING:
    from .janet_core import JanetCore


def run_conversation_loop(janet: 'JanetCore', input_device: str, voice_mode: bool) -> Union[bool, str]:
    """
    Run conversation loop: listen, build context, interpret intent, delegate/converse, output.
    
    Args:
        janet: JanetCore instance
        input_device: Current input device ("voice" or "text")
        voice_mode: Whether voice mode is enabled
        
    Returns:
        bool: True if conversation complete (should return to presence loop), False if continuing
        Special return: "quit" if user wants to exit entirely
    """
    while True:  # Conversation loop (exits back to Presence Loop when complete)
        
        # Check Red Thread FIRST (bypasses all processing)
        if RED_THREAD_EVENT.is_set() or janet.red_thread_active:
            if not janet.red_thread_active:
                janet.invoke_red_thread()
            
            # Wait for reset
            if janet.reset_red_thread():
                continue
            else:
                return True  # Exit conversation loop, return to Presence Loop
        
        # Listen for input
        user_input = None
        if input_device == "voice" and janet.stt and janet.stt.is_available():
            print("\n🎤 Listening... (or type 'text' to switch to text mode)")
            user_input = janet.stt.listen_and_transcribe(duration=5.0)
            if not user_input:
                # Fallback to text input if voice fails
                user_input = input("\nYou (text): ").strip()
        else:
            # Text input mode
            user_input = input("\nYou: ").strip()
        
        # Validate input
        if not user_input:
            continue
        
        # Limit input length to prevent DoS and token limit issues (10K characters = ~2500 tokens)
        MAX_INPUT_LENGTH = 10000
        if len(user_input) > MAX_INPUT_LENGTH:
            print(f"⚠️  Input too long ({len(user_input)} characters, max {MAX_INPUT_LENGTH}). Please shorten your message.")
            continue
        
        # Detect "Hi Janet" as conversation starter
        greeting_patterns = ["hi janet", "hello janet", "hey janet", "hi, janet", "hello, janet", "hey, janet"]
        user_input_lower = user_input.lower().strip()
        is_greeting = any(pattern in user_input_lower for pattern in greeting_patterns)
        
        if is_greeting:
            # Start new conversation session
            if janet.janet_brain:
                janet.janet_brain.start_conversation()
            
            # Return hardcoded greeting (TTS) without LLM
            greeting_phrases = janet.constitution.raw_data.get("wake_word", {}).get("response", 
                                                                                   ["Hi there!", "Yes?", "I'm here."])
            greeting = random.choice(greeting_phrases)
            
            print(f"\nJanet: {greeting}")
            if input_device == "voice" and janet.tts and janet.tts.is_available():
                try:
                    avoid_emojis = janet.constitution.raw_data.get("preferences", {}).get("avoid_emojis_in_voice_mode", True)
                    janet.tts.speak(greeting, remove_emojis=avoid_emojis)
                except Exception as e:
                    print(f"⚠️  TTS failed: {e}")
            
            # Continue to next input (which will use LLM with fresh context)
            continue
        
        # Check for Red Thread in input
        if "red thread" in user_input.lower():
            janet.invoke_red_thread()
            if janet.reset_red_thread():
                continue
            else:
                return True  # Exit conversation loop
        
        # Handle special commands (quit, mode switching, memory, delegation stats, expansion, safeword)
        if user_input.lower() in ["quit", "exit"]:
            return "quit"  # Signal to exit entire program
        
        # SafeWord commands (Memory Constitution)
        if user_input.lower().startswith("safeword unlock") or user_input.lower().startswith("unlock safeword"):
            if janet.safe_word_controller and janet.memory_manager:
                safe_word = input("Enter safe word: ").strip()
                if safe_word:
                    if janet.safe_word_controller.unlock(safe_word, janet.memory_manager.blue_vault):
                        print("\n🔓 Safe word unlocked. Blue Vault is now accessible.")
                        # Load secrets from Red Vault into Blue Vault
                        if janet.memory_manager.red_vault:
                            secret_ids = janet.memory_manager.red_vault.list_secrets()
                            for secret_id in secret_ids:
                                decrypted = janet.memory_manager.red_vault.decrypt_for_session(secret_id, safe_word)
                                if decrypted:
                                    janet.memory_manager.blue_vault.store_unlocked_secret(secret_id, decrypted)
                        print(f"   Status: {janet.safe_word_controller.get_status()}")
                    else:
                        print("\n❌ Safe word unlock failed.")
                else:
                    print("\n⚠️  No safe word provided.")
            else:
                print("\n⚠️  SafeWord controller not available.")
            continue
        
        if user_input.lower() == "safeword lock" or user_input.lower() == "lock safeword":
            if janet.safe_word_controller and janet.memory_manager:
                janet.safe_word_controller.lock(janet.memory_manager.blue_vault)
                print("\n🔒 Safe word locked. Blue Vault zeroized.")
            else:
                print("\n⚠️  SafeWord controller not available.")
            continue
        
        if user_input.lower() == "safeword status" or user_input.lower() == "safeword":
            if janet.safe_word_controller:
                status = janet.safe_word_controller.get_status()
                print(f"\n🔐 SafeWord Status:")
                print(f"   State: {status['state']}")
                if status['unlocked_since']:
                    print(f"   Unlocked since: {status['unlocked_since']}")
                    if 'auto_lock_remaining' in status:
                        print(f"   Auto-lock in: {int(status['auto_lock_remaining'])} seconds")
                print(f"   Auto-lock timeout: {status['auto_lock_timeout']} seconds")
            else:
                print("\n⚠️  SafeWord controller not available.")
            continue
        
        # Vault inspection commands
        if user_input.lower() == "vault status" or user_input.lower() == "vaults":
            if janet.memory_manager:
                print("\n🏛️  Vault Status:")
                # Green Vault stats (from legacy stats)
                stats = janet.memory_manager.get_stats()
                print(f"   Green Vault: {stats.get('episodic_count', 0)} summaries")
                # Blue Vault
                if janet.memory_manager.blue_vault:
                    has_secrets = janet.memory_manager.blue_vault.has_secrets()
                    print(f"   Blue Vault: {'Has unlocked secrets' if has_secrets else 'Empty (locked)'}")
                # Red Vault
                if janet.memory_manager.red_vault:
                    secret_ids = janet.memory_manager.red_vault.list_secrets()
                    print(f"   Red Vault: {len(secret_ids)} encrypted secrets")
            else:
                print("\n⚠️  Memory vaults not available.")
            continue
        
        # Expansion commands (Day 5)
        if user_input.lower() in ["what can you do", "show expansions", "available expansions"]:
                if janet.expansion_detector:
                    opportunities = janet.check_expansion_opportunities()
                    if opportunities:
                        print(f"\n🌱 Available Expansions ({len(opportunities)}):")
                        for i, opp in enumerate(opportunities, 1):
                            print(f"\n  {i}. {opp.name}")
                            print(f"     {opp.description}")
                            print(f"     Setup time: {opp.estimated_setup_time}")
                        print("\nWould you like to explore any of these? (say the number or name)")
                    else:
                        print("\nNo new expansion opportunities available at this time.")
                else:
                    print("\nExpansion system not available.")
                continue
        
        if user_input.lower().startswith("expand ") or user_input.lower().startswith("enable "):
                # User wants to enable an expansion
                expansion_name = user_input[6:].strip() if user_input.lower().startswith("expand ") else user_input[7:].strip()
                if janet.expansion_detector:
                    opportunities = janet.check_expansion_opportunities()
                    # Find matching opportunity
                    for opp in opportunities:
                        if expansion_name.lower() in opp.name.lower() or expansion_name.lower() in opp.expansion_type.lower():
                            if janet.expansion_dialog.suggest_expansion(opp):
                                janet.run_expansion_wizard(opp.expansion_type)
                            break
                    else:
                        print(f"Expansion '{expansion_name}' not found or not available.")
                continue
        
        # Mode switching
        if user_input.lower() == "text" and input_device == "voice":
            print("Switching to text mode. Type 'voice' to switch back.")
            input_device = "text"
            if janet.wake_detector:
                janet.wake_detector.stop_listening()
            continue
        if user_input.lower() == "voice" and input_device == "text" and VOICE_AVAILABLE:
            print("Switching to voice mode...")
            try:
                janet._initialize_voice()
                # Only set voice_mode to True if initialization succeeded
                if janet.stt and janet.stt.is_available():
                    input_device = "voice"
                    janet.voice_mode = True
                    if janet.wake_detector and janet.wake_detector.is_available():
                        janet.wake_detector.start_listening()
                else:
                    print("⚠️  Voice mode initialization failed, staying in text mode")
            except Exception as e:
                print(f"⚠️  Failed to initialize voice mode: {e}")
            continue
        
        # Learning commands (Green Vault Learning)
        if user_input.lower().startswith("learning consent") and janet.memory_manager:
            parts = user_input.lower().split()
            if len(parts) >= 3:
                summary_id = parts[2]
                if hasattr(janet.memory_manager, 'learning_manager') and janet.memory_manager.learning_manager:
                    if janet.memory_manager.learning_manager.grant_consent(summary_id):
                        print(f"\nJanet: ✅ Consent granted for summary {summary_id}")
                    else:
                        print(f"\nJanet: ❌ Failed to grant consent for summary {summary_id}")
                else:
                    print("\nJanet: Learning system not available")
            else:
                print("\nJanet: Usage: 'learning consent <summary_id>'")
            continue
        
        if user_input.lower().startswith("learning opt-out") and janet.memory_manager:
            parts = user_input.lower().split()
            if len(parts) >= 3:
                summary_id = parts[2]
                if hasattr(janet.memory_manager, 'learning_manager') and janet.memory_manager.learning_manager:
                    if janet.memory_manager.learning_manager.opt_out_summary(summary_id):
                        print(f"\nJanet: ✅ Summary {summary_id} opted out from learning")
                    else:
                        print(f"\nJanet: ❌ Failed to opt out summary {summary_id}")
                else:
                    print("\nJanet: Learning system not available")
            else:
                print("\nJanet: Usage: 'learning opt-out <summary_id>'")
            continue
        
        if user_input.lower() == "learning status" and janet.memory_manager:
            if hasattr(janet.memory_manager, 'learning_manager') and janet.memory_manager.learning_manager:
                stats = janet.memory_manager.learning_manager.get_learning_statistics()
                print(f"\nJanet: Learning Statistics:")
                print(f"  Total summaries: {stats['total_summaries']}")
                print(f"  With consent: {stats['with_consent']}")
                print(f"  Opted out: {stats['opted_out']}")
                print(f"  Available for learning: {stats['available_for_learning']}")
                print(f"  Pending consent: {stats['pending_consent']}")
            else:
                print("\nJanet: Learning system not available")
            continue
        
        if user_input.lower() == "learning review" and janet.memory_manager:
            if hasattr(janet.memory_manager, 'learning_manager') and janet.memory_manager.learning_manager:
                training_data = janet.memory_manager.learning_manager.get_training_data(limit=10)
                if training_data:
                    print(f"\nJanet: Found {len(training_data)} summaries available for learning:")
                    for i, summary in enumerate(training_data[:10], 1):
                        preview = summary.get("summary", "")[:60]
                        print(f"  {i}. [{summary.get('id', 'unknown')}] {preview}...")
                else:
                    print("\nJanet: No summaries available for learning (need consent)")
            else:
                print("\nJanet: Learning system not available")
            continue
        
        if user_input.lower() == "learn from green vault" and janet.memory_manager:
            if hasattr(janet.memory_manager, 'learning_manager') and janet.memory_manager.learning_manager:
                try:
                    from expansion.wizards import LearningWizard
                    wizard = LearningWizard(
                        config_path=janet.config_path,
                        learning_manager=janet.memory_manager.learning_manager,
                        janet_core=janet
                    )
                    wizard.run()
                except Exception as e:
                    print(f"\nJanet: Learning wizard failed: {e}")
            else:
                print("\nJanet: Learning system not available")
            continue
        
        if user_input.lower() == "learning audit" and janet.memory_manager:
            if hasattr(janet.memory_manager, 'learning_audit') and janet.memory_manager.learning_audit:
                history = janet.memory_manager.learning_audit.get_audit_history(limit=10)
                if history:
                    print(f"\nJanet: Learning Audit History (last {len(history)} operations):")
                    for i, entry in enumerate(history, 1):
                        print(f"\n  {i}. {entry.get('operation_type', 'unknown')}")
                        print(f"     Timestamp: {entry.get('timestamp', 'unknown')}")
                        print(f"     Data used: {entry.get('data_used', {}).get('count', 0)} summaries")
                else:
                    print("\nJanet: No learning operations recorded yet")
            else:
                print("\nJanet: Learning audit not available")
            continue
        
        if user_input.lower() == "learning stats" and janet.memory_manager:
            if hasattr(janet.memory_manager, 'learning_manager') and janet.memory_manager.learning_manager:
                stats = janet.memory_manager.learning_manager.get_learning_statistics()
                print(f"\nJanet: Learning Statistics:")
                print(f"  Total summaries: {stats['total_summaries']}")
                print(f"  With consent: {stats['with_consent']}")
                print(f"  Opted out: {stats['opted_out']}")
                print(f"  Available for learning: {stats['available_for_learning']}")
                print(f"  Pending consent: {stats['pending_consent']}")
                
                # Also show audit stats if available
                if hasattr(janet.memory_manager, 'learning_audit') and janet.memory_manager.learning_audit:
                    audit_stats = janet.memory_manager.learning_audit.get_statistics()
                    print(f"\n  Learning Operations:")
                    print(f"    Total operations: {audit_stats['total_operations']}")
                    print(f"    Unique summaries used: {audit_stats['unique_summaries_used']}")
            else:
                print("\nJanet: Learning system not available")
            continue
        
        # Memory management commands (Day 3)
        if user_input.lower().startswith("forget"):
                if janet.memory_manager:
                    parts = user_input.lower().split()
                    if len(parts) > 1 and parts[1] == "all":
                        # Axiom 10: Soul Check before major memory deletion
                        if not janet.soul_check("Memory deletion: forget all memories"):
                            print("\nJanet: Memory deletion cancelled due to soul check.")
                            continue
                        # Forget all memories
                        result = janet.memory_manager.forget()
                        print(f"\nJanet: {result['message']}")
                    elif len(parts) > 1 and parts[1].isdigit():
                        # Forget specific memory ID (less critical, no soul check needed)
                        memory_id = int(parts[1])
                        result = janet.memory_manager.forget(memory_id)
                        print(f"\nJanet: {result['message']}")
                    else:
                        print("\nJanet: Usage: 'forget all' or 'forget <memory_id>'")
                else:
                    print("\nJanet: Persistent memory not available")
                continue
        
        if user_input.lower() == "memory stats" and janet.memory_manager:
            stats = janet.memory_manager.get_stats()
            print(f"\nJanet: Memory Statistics:")
            print(f"  Episodic memories: {stats['episodic_count']}")
            print(f"  Semantic memories: {stats['semantic_count']}")
            if stats['last_summary']:
                print(f"  Last summary: {stats['last_summary']}")
            continue
        
        if user_input.lower().startswith("search memory") and janet.memory_manager:
            query = user_input[13:].strip()  # Remove "search memory"
            if query:
                results = janet.memory_manager.search(query, n_results=3)
                if results:
                    print(f"\nJanet: Found {len(results)} related memories:")
                    for i, result in enumerate(results, 1):
                        print(f"  {i}. {result['text'][:100]}...")
                else:
                    print("\nJanet: No related memories found")
            else:
                print("\nJanet: Usage: 'search memory <query>'")
            continue
        
        # Delegation commands (Day 4)
        if user_input.lower() == "delegation stats" and janet.delegation_manager:
            caps = janet.delegation_manager.get_capabilities()
            print(f"\nJanet: Delegation Capabilities:")
            print(f"  Model routing: {'Available' if caps['model_routing'] else 'Not available'}")
            print(f"  n8n: {'Available' if caps['n8n'] else 'Not available'}")
            print(f"  Home Assistant: {'Available' if caps['home_assistant'] else 'Not available'}")
            continue
        
        if user_input.lower().startswith("delegate to ") and janet.delegation_manager:
            # Parse delegation command: "delegate to <service> <action>"
            parts = user_input[12:].strip().split(maxsplit=1)
            if len(parts) >= 1:
                service = parts[0].lower()
                action = parts[1] if len(parts) > 1 else ""
                
                # Handle different delegation types
                if service == "model" and action:
                    # Delegate to model: "delegate to model <query>"
                    def confirm(message: str) -> bool:
                        response = input(f"{message} (yes/NO): ").strip().lower()
                        return response in ["yes", "y"]
                    
                    result = janet.delegation_manager.delegate_to_model(
                        action,
                        confirm_callback=confirm
                    )
                    if result:
                        print(f"\nJanet (delegated): {result}")
                    else:
                        print("\nJanet: Delegation declined or failed")
                else:
                    print("\nJanet: Usage: 'delegate to model <query>'")
            continue
        
        # ========== CONVERSATION PROCESSING (matching pseudo-code) ==========
        
        try:
            # Build context (tone, memory, delegation capabilities)
            context = build_context(janet, user_input, input_device)
            
            # Interpret intent (check if delegation is required)
            try:
                intent = janet.interpret_intent(context)
            except Exception as e:
                print(f"⚠️  Intent interpretation failed: {e}")
                # Default to conversation intent
                intent = {"type": "conversation", "requires_delegation": False, "requires_soul_check": False}
            
            # Soul Check if required (Axiom 10)
            if intent.get("requires_soul_check"):
                janet.soul_check(f"Request: {user_input}")
                # Wait for confirmation in full implementation
            
            # Generate response (delegate or converse)
            try:
                if intent.get("requires_delegation") and janet.delegation_manager:
                    # Delegate task
                    delegation_target = intent.get("delegation_target")
                    if delegation_target == "model":
                        model_type = intent.get("model_type", "conversation")
                        def confirm(message: str) -> bool:
                            response = input(f"{message} (yes/NO): ").strip().lower()
                            return response in ["yes", "y"]
                        
                        result = janet.delegation_manager.delegate_to_model(
                            user_input,
                            context=context,
                            confirm_callback=confirm
                        )
                        # delegate_to_model returns Optional[str]
                        if result:
                            response_text = str(result).strip()
                            if not response_text:
                                response_text = "Delegation returned empty response"
                        else:
                            response_text = "Delegation declined or failed"
                    else:
                        # Other delegation types (n8n, Home Assistant) would go here
                        response_text = janet.converse(user_input, context)
                else:
                    # Normal conversation
                    response_text = janet.converse(user_input, context)
            except Exception as e:
                print(f"⚠️  Response generation failed: {e}")
                response_text = "I'm sorry, I encountered an error processing your request. Please try again."
            
            # Validate response before output
            if not response_text:
                response_text = "I'm sorry, I couldn't generate a response. Please try again."
            response_text = str(response_text).strip()
            if not response_text:
                response_text = "I'm sorry, I couldn't generate a response. Please try again."
            
            # Output response
            print(f"\nJanet: {response_text}")
            if input_device == "voice" and janet.tts and janet.tts.is_available():
                try:
                    avoid_emojis = janet.constitution.raw_data.get("preferences", {}).get("avoid_emojis_in_voice_mode", True)
                    janet.tts.speak(response_text, remove_emojis=avoid_emojis)
                except Exception as e:
                    print(f"⚠️  TTS failed: {e}")
            
            # Check if conversation is complete (return to Presence Loop in voice mode)
            if janet.conversation_complete(user_input, response_text):
                # Store entire conversation on goodbye (if applicable)
                if janet.janet_brain and janet.memory_manager:
                    conversation_history = janet.janet_brain.get_conversation_history()
                    if conversation_history:
                        # Check if conversation should be stored (classification)
                        # Use first user message as classification sample
                        first_user_msg = None
                        for msg in conversation_history:
                            if msg.get("role") == "user":
                                first_user_msg = msg.get("content", "")
                                break
                        
                        if first_user_msg and janet.memory_write_allowed(first_user_msg, context):
                            try:
                                janet.memory_manager.store_conversation(conversation_history)
                            except Exception as e:
                                print(f"⚠️  Conversation storage failed: {e}")
                
                # Clear context window and end conversation session
                if janet.janet_brain:
                    janet.janet_brain.end_conversation()
                
                return True  # Exit conversation loop, return to Presence Loop
                
        except Exception as e:
            print(f"⚠️  Conversation processing error: {e}")
            print("Continuing conversation loop...")
            # Continue loop instead of crashing

