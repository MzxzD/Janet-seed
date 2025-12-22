# Memory System Architecture

The memory system implements a three-vault architecture that protects secrets while enabling safe learning and context retrieval.

## Purpose

The memory system provides:
- **Green Vault**: Safe, distilled summaries for context and learning
- **Blue Vault**: Ephemeral secrets unlocked during session
- **Red Vault**: Encrypted secrets at rest
- **Classification**: Automatic routing to appropriate vault
- **Distillation**: Safe abstraction of conversations
- **Learning System**: Fine-tuning from Green Vault only

## Architecture

```mermaid
flowchart TB
    Input[User Input + Response] --> Classifier[Conversation Classifier]
    
    Classifier -->|discard| Discard[No Storage<br/>Ephemeral]
    Classifier -->|normal| Distiller[Conversation Distiller]
    Classifier -->|sensitive| BlueCheck{Blue Vault<br/>Unlocked?}
    Classifier -->|secret| SecretCheck{Explicit<br/>Declaration?}
    
    Distiller -->|Distilled Summary| GreenVault[Green Vault<br/>SQLite + ChromaDB<br/>Safe Summaries]
    
    BlueCheck -->|Yes| BlueVault[Blue Vault<br/>In-Memory<br/>Ephemeral Secrets]
    BlueCheck -->|No| Blocked1[Storage Blocked<br/>Requires Safe Word]
    
    SecretCheck -->|Yes + Safe Word| RedVault[Red Vault<br/>Encrypted at Rest<br/>Fernet Encryption]
    SecretCheck -->|No| Blocked2[Storage Blocked<br/>Requires Declaration]
    
    GreenVault -->|With Consent| Learning[Learning System<br/>Fine-tuning Data]
    BlueVault -.->|Never| Learning
    RedVault -.->|Never| Learning
```

## Vault System

### Green Vault (Safe Summaries)

**Purpose**: Store distilled, non-sensitive summaries for context retrieval and learning.

**Storage:**
- SQLite: Episodic memory (timestamps, summaries)
- ChromaDB: Semantic search (vector embeddings)

**Allowed:**
- Abstract summaries (no verbatim quotes)
- Topic tags and themes
- Emotional tone indicators
- Actionable insights
- Learning/training data (with explicit consent)

**Flow:**

```mermaid
sequenceDiagram
    participant Input
    participant Classifier
    participant Distiller
    participant GreenVault
    participant SQLite
    participant ChromaDB
    
    Input->>Classifier: User Input + Response
    Classifier->>Classifier: Classify as "normal"
    Classifier->>Distiller: Route for Distillation
    Distiller->>Distiller: Extract Topics, Tone, Insights
    Distiller->>Distiller: Remove Verbatim Quotes
    Distiller->>GreenVault: Distilled Summary
    GreenVault->>SQLite: Store Episodic Entry
    GreenVault->>ChromaDB: Store Semantic Embedding
```

### Blue Vault (Ephemeral Secrets)

**Purpose**: Store unlocked secrets during active session.

**Storage:**
- In-memory only
- Zeroized on lock
- Never persisted

**Flow:**

```mermaid
sequenceDiagram
    participant User
    participant SafeWord
    participant BlueVault
    participant RedVault
    
    User->>SafeWord: "safeword unlock" + Safe Word
    SafeWord->>SafeWord: Verify Safe Word
    SafeWord->>RedVault: Decrypt Secrets for Session
    RedVault->>BlueVault: Unlocked Secrets
    BlueVault->>BlueVault: Store in Memory
    
    Note over BlueVault: Secrets available during session
    
    User->>SafeWord: "safeword lock"
    SafeWord->>BlueVault: Zeroize All Data
    BlueVault->>BlueVault: Clear Memory
```

### Red Vault (Encrypted Secrets)

**Purpose**: Store persistent secrets encrypted at rest.

**Storage:**
- Encrypted with Fernet (symmetric encryption)
- Key derived from safe word (never stored)
- Explicit declaration required

**Flow:**

```mermaid
sequenceDiagram
    participant User
    participant Classifier
    participant RedVault
    participant Encryption
    
    User->>Classifier: "store secret: my_password"
    Classifier->>Classifier: Detect Explicit Declaration
    User->>RedVault: Provide Safe Word
    RedVault->>Encryption: Derive Key from Safe Word
    Encryption->>RedVault: Encrypt Secret
    RedVault->>RedVault: Store Encrypted
    
    Note over RedVault: Secret encrypted at rest
    
    User->>RedVault: Retrieve Secret + Safe Word
    RedVault->>Encryption: Derive Key from Safe Word
    Encryption->>RedVault: Decrypt Secret
    RedVault->>BlueVault: Unlocked Secret (Session Only)
```

## Classification System

Conversations are automatically classified into four categories:

```mermaid
flowchart TD
    Input[User Input] --> Rules[Rule-Based Classification]
    
    Rules --> Discard{Discard<br/>Patterns?}
    Rules --> Secret{Secret<br/>Indicators?}
    Rules --> Sensitive{Sensitive<br/>Keywords?}
    Rules --> Normal{Default}
    
    Discard -->|Yes| NoStorage[No Storage<br/>Ephemeral]
    Secret -->|Yes| Explicit{Explicit<br/>Declaration?}
    Sensitive -->|Yes| Unlocked{Blue Vault<br/>Unlocked?}
    Normal -->|Yes| GreenVault[Green Vault]
    
    Explicit -->|Yes| RedVault[Red Vault]
    Explicit -->|No| Blocked1[Blocked]
    Unlocked -->|Yes| BlueVault[Blue Vault]
    Unlocked -->|No| Blocked2[Blocked]
```

**Classification Categories:**

1. **discard**: Ephemeral conversations (greetings, simple responses)
2. **normal**: Safe for Green Vault (general conversations)
3. **sensitive**: Requires Blue Vault unlock (personal, emotional, health)
4. **secret**: Requires explicit declaration (passwords, API keys, credentials)

## Distillation Process

Converts raw conversations into safe summaries:

```mermaid
flowchart LR
    Raw[Raw Conversation<br/>User + Janet] --> Extract[Extract Topics]
    Extract --> Abstract[Abstract Details]
    Abstract --> Remove[Remove Verbatim]
    Remove --> Tag[Add Tags]
    Tag --> Summary[Distilled Summary]
    Summary --> Store[Store in Green Vault]
```

**Distillation Steps:**
1. Extract topics and themes
2. Identify emotional tone (if relevant)
3. Extract actionable insights
4. Remove verbatim quotes
5. Create abstract summary
6. Add topic tags
7. Calculate confidence score

## Learning System

Only Green Vault summaries can be used for learning:

```mermaid
flowchart TB
    GreenVault[Green Vault<br/>Summaries] --> Consent{Consent<br/>Given?}
    Consent -->|Yes| OptOut{Opt-Out<br/>Flag?}
    Consent -->|No| Blocked[Blocked]
    
    OptOut -->|No| LearningManager[Learning Manager]
    OptOut -->|Yes| Blocked
    
    LearningManager --> Request[Request Consent<br/>Show Summary]
    Request --> User{User<br/>Consents?}
    User -->|Yes| Audit[Audit Logger<br/>Record Operation]
    User -->|No| Blocked
    
    Audit --> LLMLearner[LLM Learner<br/>Fine-tuning]
    LLMLearner --> Model[Fine-tuned Model]
    
    BlueVault -.->|Never| LearningManager
    RedVault -.->|Never| LearningManager
```

**Learning Safeguards:**
- Explicit consent required for each summary
- Opt-out available at any time
- Full audit trail of all operations
- Blue/Red Vaults explicitly forbidden

## SafeWord Controller

Manages Blue Vault access:

```mermaid
stateDiagram-v2
    [*] --> LOCKED: Initial State
    LOCKED --> UNLOCKED: unlock(safe_word)
    UNLOCKED --> LOCKED: lock() or timeout
    UNLOCKED --> UNLOCKED: Activity (reset timeout)
    LOCKED --> [*]: Zeroized
```

**Features:**
- Auto-lock timeout (configurable)
- Zeroization on lock
- Thread-safe operations
- Red Vault key derivation

## Memory Storage Flow

Complete storage flow from input to vault:

```mermaid
sequenceDiagram
    participant User
    participant JanetCore
    participant MemoryManager
    participant Classifier
    participant Distiller
    participant GreenVault
    
    User->>JanetCore: Input + Response
    JanetCore->>MemoryManager: store_conversation(history)
    MemoryManager->>Classifier: classify(first_user_message)
    Classifier->>MemoryManager: "normal"
    MemoryManager->>Distiller: distill(conversation)
    Distiller->>Distiller: Extract Topics, Tone, Insights
    Distiller->>MemoryManager: Distilled Summary
    MemoryManager->>GreenVault: add_summary(summary)
    GreenVault->>GreenVault: Store in SQLite + ChromaDB
```

## Constitutional Integration

### Memory Gates (Axiom 9)

Controls when memory writes are allowed:
- Checks Red Thread status
- Validates constitutional rules
- Respects "don't remember" requests
- Requires explicit consent for secrets

### Red Thread Protocol (Axiom 8)

All memory operations check Red Thread:
- Storage blocked when active
- Search blocked when active
- Deletion blocked when active
- Immediate stop on invocation

### Secrets Sacred (Memory Constitution)

Secrets are never:
- Embedded or used for training
- Summarized or abstracted
- Stored without explicit declaration
- Exposed without safe word

## Usage

### Storing Conversations

```python
from memory import MemoryManager
from pathlib import Path

memory_dir = Path("/path/to/memory")
memory_manager = MemoryManager(memory_dir)

# Store conversation (automatic classification)
memory_manager.store_conversation(conversation_history, context)
```

### Searching Memories

```python
# Search Green Vault (semantic search)
results = memory_manager.search("python programming", n_results=5)
for result in results:
    print(result['text'])
```

### SafeWord Operations

```python
from core.presence.safeword import SafeWordController

safe_word = SafeWordController()
blue_vault = memory_manager.blue_vault

# Unlock Blue Vault
safe_word.unlock("my_safe_word", blue_vault)

# Lock and zeroize
safe_word.lock(blue_vault)
```

## Dependencies

- `chromadb` - Semantic search and embeddings
- `cryptography` - Fernet encryption for Red Vault
- `sqlite3` - Episodic memory storage

## Files

- `memory_manager.py` - Unified memory interface
- `green_vault.py` - Safe summary storage
- `blue_vault.py` - Ephemeral secret storage
- `red_vault.py` - Encrypted secret storage
- `classification.py` - Conversation classification
- `distillation.py` - Summary distillation
- `memory_gates.py` - Constitutional memory gates
- `learning_manager.py` - Learning system manager
- `learning_audit.py` - Learning operation audit
- `llm_learner.py` - LLM fine-tuning integration

## See Also

- [Memory Constitution](../../constitution/MEMORY_CONSTITUTION.md) - Immutable memory principles
- [Core System](../core/README.md) - How memory integrates with JanetCore
- [SafeWord Controller](../core/presence/safeword.py) - Blue Vault access control

