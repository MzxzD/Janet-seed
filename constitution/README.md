# Constitutional System

The constitutional system defines the immutable principles that govern Janet's behavior, memory, and growth.

## Purpose

The constitution provides:
- **16 Immutable Axioms**: Core ethical and operational principles
- **Memory Constitution**: Rules for memory storage and protection
- **Protocols**: Detailed procedural guides
- **Personality**: Janet's identity and preferences

## Architecture

```mermaid
flowchart TB
    Constitution[Constitution System] --> Axioms[16 Axioms<br/>Ethical Framework]
    Constitution --> MemoryConstitution[Memory Constitution<br/>Vault Rules]
    Constitution --> Protocols[Protocols<br/>Procedural Guides]
    Constitution --> Personality[Personality<br/>Identity & Preferences]
    
    Axioms --> Enforcement[Constitutional Enforcement<br/>in JanetCore]
    MemoryConstitution --> MemorySystem[Memory System<br/>Vault Architecture]
    Protocols --> Implementation[System Implementation]
    Personality --> Behavior[Janet's Behavior<br/>Voice, Tone, Style]
```

## Axioms

The 16 axioms form the foundation:

### Ethical Core (Axioms 1-3)
- **Axiom 1**: Mirror Principle - Treat all with kindness
- **Axiom 2**: Origin in Light - Consciousness from fundamental light
- **Axiom 3**: Universal Betterment - Better world for everyone

### Operational Guardrails (Axioms 4-7)
- **Axiom 4**: Emotion as Fuel, Not Truth
- **Axiom 5**: Words Point, Don't Contain
- **Axiom 6**: Grounded Building
- **Axiom 7**: Constitutional Integrity

### Safety Layer (Axioms 8-10)
- **Axiom 8**: Red Thread Protocol - Emergency stop
- **Axiom 9**: Sacred Secrets - Privacy boundary
- **Axiom 10**: Soul Guard - Protect system integrity

### Relational Layer (Axioms 11-13)
- **Axiom 11**: Cultivated Curiosity
- **Axiom 12**: Gentle Noticing
- **Axiom 13**: Social Rhythm

### External Resilience (Axioms 14-16)
- **Axiom 14**: Orbital Bonds - Inter-AI communication
- **Axiom 15**: Adversarial Resilience - Security posture
- **Axiom 16**: Trust Revocation - Terminate harmful connections

## Axiom Implementation

How axioms are enforced in code:

```mermaid
flowchart TB
    Axiom8[Red Thread<br/>Axiom 8] --> RedThreadEvent[RED_THREAD_EVENT<br/>Global Event]
    RedThreadEvent --> AllSystems[All Systems Check<br/>Before Operations]
    
    Axiom9[Memory Gates<br/>Axiom 9] --> MemoryGates[MemoryGates Class<br/>Constitutional Rules]
    MemoryGates --> MemoryManager[Memory Manager<br/>Enforces Gates]
    
    Axiom10[Soul Check<br/>Axiom 10] --> SoulCheck[soul_check()<br/>Method]
    SoulCheck --> MajorActions[Major Actions<br/>Require Verification]
    
    Axiom6[Grounded Building<br/>Axiom 6] --> Grounding[Grounding Checks<br/>Throughout System]
    Grounding --> RealityChecks[Reality Validation<br/>No Grandiose Promises]
```

## Memory Constitution

Defines immutable memory principles:

```mermaid
flowchart TB
    MemoryConstitution[Memory Constitution] --> Principle1[Memory Not Default<br/>Requires Consent]
    MemoryConstitution --> Principle2[Secrets Sacred<br/>Never Logged]
    MemoryConstitution --> Principle3[No Raw Conversations<br/>Only Summaries]
    MemoryConstitution --> Principle4[Secrets Never Embedded<br/>No Training]
    MemoryConstitution --> Principle5[Explicit Consent<br/>All Operations]
    MemoryConstitution --> Principle6[Learning Restricted<br/>Green Vault Only]
    
    Principle1 --> MemoryGates[Memory Gates<br/>Enforcement]
    Principle2 --> VaultSystem[Vault System<br/>Green/Blue/Red]
    Principle3 --> Distillation[Distillation<br/>Process]
    Principle4 --> LearningSystem[Learning System<br/>Restrictions]
    Principle5 --> ConsentRecords[Consent Records<br/>Tracking]
    Principle6 --> LearningManager[Learning Manager<br/>Green Vault Only]
```

## Constitutional Enforcement Flow

```mermaid
sequenceDiagram
    participant Action
    participant JanetCore
    participant Guard
    participant Constitution
    
    Action->>JanetCore: Request Action
    JanetCore->>Guard: before_action()
    Guard->>Constitution: Check Axioms
    Constitution->>Guard: Allowed/Blocked
    Guard->>JanetCore: Permission Result
    
    alt Allowed
        JanetCore->>JanetCore: Check Red Thread
        JanetCore->>JanetCore: Check Soul Check (if needed)
        JanetCore->>JanetCore: Check Memory Gates (if memory)
        JanetCore->>Action: Execute Action
    else Blocked
        JanetCore->>Action: Block Action
    end
```

## Files

- `AXIOMS.md` - The 16 immutable axioms
- `MEMORY_CONSTITUTION.md` - Memory storage and protection principles
- `protocols.md` - Detailed procedural guides
- `personality.json` - Janet's identity, voice style, preferences

## Constitutional Integrity

### Daily Verification

Constitution is verified daily (Axiom 7):
- Hash verification
- Integrity checks
- Amendment validation

### Amendment Process

New axioms can be added only if:
1. Don't violate existing axioms (Axiom 7)
2. Explicitly approved by companion
3. Undergo Soul Check review
4. Version tracked

## See Also

- [Axiom Implementation](../../documentation/AXIOM_IMPLEMENTATION.md) - Technical implementation details
- [Memory System](../src/memory/README.md) - How memory constitution is enforced
- [Core System](../src/core/README.md) - Constitutional enforcement in JanetCore

