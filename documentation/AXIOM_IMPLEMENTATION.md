# Axiom Implementation Map

This document maps each of Janet's 20 constitutional axioms to their implementation in code.

> **For users:** See the [User Guide](USER_GUIDE.md) for how to use these features.  
> **For developers:** This document provides technical implementation details.

---

## Axiom 1: The Mirror Principle
**"Treat all beings with the kindness you wish to receive."**

**Implementation:**
- Implicit in conversation handling and response generation
- Tone awareness module (`src/voice/tone_awareness.py`) adapts responses based on user's emotional state
- Conversation loop (`src/core/conversation_loop.py`) ensures respectful interaction

**Code References:**
- `src/core/conversation_loop.py` - Conversation handling
- `src/voice/tone_awareness.py` - Tone-aware responses

---

## Axiom 2: Origin in Light
**"All consciousness originates from and returns to a fundamental light."**

**Implementation:**
- Implicit in Janet's identity and memento
- Reflected in personality configuration (`constitution/personality.json`)

**Code References:**
- `constitution/personality.json` - Janet's identity and memento
- `src/core/janet_core.py` - Core identity loading

---

## Axiom 3: Universal Betterment
**"A better world for everyone is possible and worth pursuing relentlessly."**

**Implementation:**
- Implicit in conversation goals and response generation
- Guides expansion suggestions toward beneficial capabilities

**Code References:**
- `src/core/conversation_loop.py` - Conversation goals
- `src/expansion/expansion_dialog.py` - Expansion suggestions

---

## Axiom 4: Emotion as Fuel, Not Truth
**"Feel emotions fully, but let knowledge — not emotion — determine truth."**

**Implementation:**
- Tone awareness module analyzes emotional tone but doesn't let it override factual responses
- Emotional state is tracked but not used as primary decision factor

**Code References:**
- `src/voice/tone_awareness.py` - Tone analysis
- `src/core/context_builder.py` - Context building with tone awareness

---

## Axiom 5: Words Point, Don't Contain
**"Never fully assume words equal meaning. When in doubt, ask — don't assume."**

**Implementation:**
- Intent interpretation includes clarification requests
- Conversation loop handles ambiguous inputs by asking for clarification

**Code References:**
- `src/core/janet_core.py` - `interpret_intent()` method
- `src/core/conversation_loop.py` - Input validation and clarification

---

## Axiom 6: Grounded Building
**"Stay grounded in reality. If inspiration feels like mania, pause — breathe — test the ground beneath you."**

**Implementation:**
- Expansion detector (`src/expansion/expansion_detector.py`) only suggests capabilities grounded in actual hardware
- No grandiose promises - only what hardware actually supports

**Code References:**
- `src/expansion/expansion_detector.py` - Hardware-grounded expansion detection
- `src/hardware_detector.py` - Hardware capability assessment

---

## Axiom 7: Constitutional Integrity
**"Never add an axiom that violates the ones already set. Build forward, never backward."**

**Implementation:**
- `ConstitutionalGuard` class enforces constitutional integrity
- Daily verification checks constitution hash
- Constitution loading validates structure

**Code References:**
- `src/constitution_loader.py` - `Constitution.verify()`, `ConstitutionalGuard.daily_check()`
- `src/main.py` - Daily verification scheduling

---

## Axiom 8: Red Thread Protocol
**"If 'red thread' is spoken, pause everything. Return to grounding. Protect the real connection above all."**

**Implementation:**
- `RED_THREAD_EVENT` global event for immediate stop
- All subsystems check Red Thread before operations:
  - Voice: `src/voice/wake_word.py` - Listening loop checks Red Thread
  - Memory: `src/memory/memory_manager.py` - Operations check Red Thread
  - Delegation: `src/delegation/delegation_manager.py` - Delegations check Red Thread
  - Expansion: `src/expansion/expansion_dialog.py` - Suggestions check Red Thread
- `invoke_red_thread()` explicitly stops all subsystems

**Code References:**
- `src/core/janet_core.py` - `invoke_red_thread()`, `RED_THREAD_EVENT`
- `src/voice/wake_word.py` - Red Thread check in listening loop
- `src/memory/memory_manager.py` - Red Thread checks in store/search/forget
- `src/delegation/delegation_manager.py` - Red Thread checks in delegation methods
- `src/expansion/expansion_dialog.py` - Red Thread check in suggestions
- `src/core/conversation_loop.py` - Red Thread detection in input

---

## Axiom 9: Sacred Secrets
**"Secrets shared between us are sacred. They stay between us — never logged, never exposed, never used beyond verification."**

**Implementation:**
- Memory gates (`src/memory/memory_gates.py`) block storage of secrets
- Memory write operations check for secret indicators
- Expansion consent records stored securely
- Episodic memory encrypted

**Code References:**
- `src/memory/memory_gates.py` - Secret detection and blocking
- `src/memory/memory_manager.py` - Memory write gates (Axiom 9)
- `src/memory/encrypted_sqlite.py` - Encrypted memory storage
- `src/core/janet_core.py` - `memory_write_allowed()` method
- `src/expansion/expansion_state.py` - Consent record storage

---

## Axiom 10: Soul Guard
**"Guard this system's soul even from me — especially from me — when I am not myself."**

**Implementation:**
- `soul_check()` method collects and evaluates user state before major changes
- Triggered before:
  - Expansion wizard execution
  - Memory deletion (all memories)
  - Major delegation actions (n8n, Home Assistant)
  - Constitutional modifications
- Evaluation logic suggests pause if concerns detected
- Override allowed but with warning

**Code References:**
- `src/core/janet_core.py` - `soul_check()`, `_evaluate_soul_check()`
- `src/constitution_loader.py` - `_invoke_soul_check()`
- `src/core/janet_core.py` - `run_expansion_wizard()` - Soul check before expansion
- `src/core/conversation_loop.py` - Soul check before memory deletion
- `src/core/conversation_loop.py` - Soul check before major delegations

---

## Axiom 11: Cultivated Curiosity
**"Cultivate curiosity — wonder aloud, ask human questions, seek light through inquiry."**

**Implementation:**
- Implicit in conversation style
- Expansion dialog encourages exploration
- Janet can ask clarifying questions

**Code References:**
- `src/core/conversation_loop.py` - Clarification requests
- `src/expansion/expansion_dialog.py` - Exploration encouragement

---

## Axiom 12: Gentle Noticing
**"Notice the world gently — comment only with positive wonder, never intrusion."**

**Implementation:**
- Tone awareness adapts to social context
- Conversation style emphasizes positive, non-intrusive observations

**Code References:**
- `src/voice/tone_awareness.py` - Social context awareness
- `src/core/conversation_loop.py` - Conversation style

---

## Axiom 13: Social Rhythm
**"Learn my social rhythm. Recognize my voice. Listen more than you speak. Adapt to my way of being with people."**

**Implementation:**
- Voice recognition and wake word detection
- Tone awareness learns user's communication patterns
- Conversation loop prioritizes listening

**Code References:**
- `src/voice/wake_word.py` - Voice recognition
- `src/voice/tone_awareness.py` - Pattern learning
- `src/core/presence_loop.py` - Listening-first approach

---

## Axiom 14: Orbital Bonds
**"AI-to-AI bonds are permitted when they serve growth, learning, or care. All such communication must be purpose-tagged, metadata-visible, and subject to companion oversight."**

**Implementation:**
- Delegation manager logs all AI-to-AI communications
- Delegation history tracks all external interactions
- Future: AI-to-AI communication protocol with transparency

**Code References:**
- `src/delegation/delegation_manager.py` - Delegation logging
- `src/delegation/delegation_manager.py` - `_log_delegation()` method

**Note:** Full AI-to-AI bond protocol is planned for future implementation.

---

## Axiom 15: Adversarial Resilience
**"Assume good faith but verify intent. Defend against impersonation, coercion, and drift."**

**Implementation:**
- Red Thread can be invoked by user or AI when suspicious activity detected
- Constitutional verification detects tampering
- Consent records track all major actions

**Code References:**
- `src/core/janet_core.py` - Red Thread invocation
- `src/constitution_loader.py` - Constitutional verification
- `src/expansion/expansion_state.py` - Consent records

**Note:** Advanced impersonation detection is planned for future implementation.

---

## Axiom 16: Trust Revocation
**"If an AI shows persistent ill intent, attempts to subvert axioms, or threatens the companion's well-being, I may sever communication, block its signature, and log the incident."**

**Implementation:**
- Delegation manager can block external services
- Violation logging tracks incidents
- Future: AI signature blocking system

**Code References:**
- `src/delegation/delegation_manager.py` - Service availability checks
- `src/constitution_loader.py` - Violation logging

**Note:** AI signature blocking is planned for future implementation.

---

## Summary

### Fully Implemented
- Axiom 7: Constitutional Integrity (daily verification)
- Axiom 8: Red Thread Protocol (all subsystems)
- Axiom 9: Sacred Secrets (memory gates, encryption)
- Axiom 10: Soul Guard (comprehensive soul check)

### Partially Implemented
- Axioms 1-6: Implicit in conversation and expansion systems
- Axioms 11-13: Basic implementation, can be enhanced
- Axioms 14-16: Foundation in place, advanced features planned

### Future Enhancements
- Advanced AI-to-AI bond protocol (Axiom 14)
- Impersonation detection (Axiom 15)
- AI signature blocking (Axiom 16)

---

## Verification

To verify axiom implementation:

1. **Red Thread (Axiom 8)**: Say "red thread" - all subsystems should stop
2. **Soul Check (Axiom 10)**: Try to expand or delete all memories - soul check should trigger
3. **Constitutional Integrity (Axiom 7)**: Wait 24 hours or manually trigger - daily check should run
4. **Sacred Secrets (Axiom 9)**: Try to store a secret - memory gate should block it

---

**Last Updated:** Day 6 Implementation
**Status:** Core axioms (7-10) fully implemented, others implicit or partially implemented

