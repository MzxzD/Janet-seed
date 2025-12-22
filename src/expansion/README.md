# Expansion Protocol Architecture

The expansion protocol enables Janet to detect and suggest growth opportunities while maintaining strict constitutional boundaries. All expansions require explicit consent and work offline-first.

## Purpose

The expansion system provides:
- **Detection**: Identify available expansion opportunities based on hardware
- **Suggestion**: Proactively suggest expansions (never auto-install)
- **Wizards**: Step-by-step guided setup for each expansion type
- **State Management**: Track enabled expansions with consent records
- **Offline-First**: All expansions work without network connection

## Architecture

```mermaid
flowchart TB
    Hardware[Hardware Profile] --> Detector[Expansion Detector<br/>Check Capabilities]
    CurrentState[Current State<br/>Enabled Features] --> Detector
    
    Detector -->|Detects| Opportunities[Expansion Opportunities]
    Opportunities --> Dialog[Expansion Dialog<br/>Suggest to User]
    
    Dialog -->|User Consents| Wizard[Expansion Wizard<br/>Guided Setup]
    Dialog -->|User Declines| Respect[Respect Choice<br/>Don't Ask Again]
    
    Wizard -->|Completes| StateManager[Expansion State Manager<br/>Save Config + Consent]
    StateManager -->|Stores| Config[Config Files<br/>expansion_state.json]
    StateManager -->|Records| Consent[Consent Records<br/>expansion_consent.json]
    
    Config -->|Loads| JanetCore[JanetCore<br/>Initialize Features]
```

## Core Principles

1. **Never Auto-Install** - All expansion requires explicit human action
2. **Offline-First** - All expansions work without network
3. **Suggest, Don't Assume** - Janet can detect but only suggests
4. **Explain Benefits and Risks** - Clear information for each opportunity
5. **Step-by-Step Guidance** - Guided wizards for setup
6. **Reversible** - Users can disable expansions at any time

## Key Components

### ExpansionDetector

Detects available expansion opportunities:

```mermaid
flowchart LR
    Hardware[Hardware Profile] --> Check[Check Capabilities]
    CurrentState[Current State] --> Check
    Check --> Voice{Can Expand<br/>Voice I/O?}
    Check --> Memory{Can Expand<br/>Memory?}
    Check --> Delegation{Can Expand<br/>Delegation?}
    Check --> Models{Can Expand<br/>Models?}
    
    Voice -->|Yes| VoiceOpp[Voice I/O Opportunity]
    Memory -->|Yes| MemoryOpp[Memory Opportunity]
    Delegation -->|Yes| DelegationOpp[Delegation Opportunity]
    Models -->|Yes| ModelOpp[Model Opportunities]
    
    VoiceOpp --> List[Opportunity List]
    MemoryOpp --> List
    DelegationOpp --> List
    ModelOpp --> List
```

**Detection Logic:**
- Checks hardware capabilities (RAM, disk, CPU, GPU)
- Checks current state (what's already enabled)
- Compares requirements vs available resources
- Returns list of possible expansions

### ExpansionDialog

Proactive suggestion system:

```mermaid
sequenceDiagram
    participant Detector
    participant Dialog
    participant User
    participant Wizard
    
    Detector->>Dialog: Expansion Opportunity
    Dialog->>Dialog: Check Recently Declined
    Dialog->>User: Present Opportunity<br/>Benefits, Risks, Requirements
    User->>Dialog: "tell me more"
    Dialog->>User: Detailed Explanation<br/>Offline Instructions
    User->>Dialog: "yes"
    Dialog->>Wizard: Launch Wizard
    Wizard->>User: Guided Setup
    User->>Wizard: Complete Setup
    Wizard->>StateManager: Save Expansion
```

**Dialogue Flow:**

```mermaid
flowchart TD
    Opportunity[Expansion Opportunity] --> Present[Present to User]
    Present --> Response{User Response}
    
    Response -->|yes| Launch[Launch Wizard]
    Response -->|no| Decline[Mark as Declined<br/>Don't Ask Again Soon]
    Response -->|tell me more| Explain[Explain Benefits/Risks<br/>Show Offline Instructions]
    Response -->|not now| Respect[Respect Choice<br/>Ask Later]
    
    Explain --> Response
    Launch --> Setup[Wizard Setup]
    Setup --> Verify[Verify Installation]
    Verify --> Enable[Enable Expansion]
```

### ExpansionStateManager

Manages expansion state and consent:

```mermaid
flowchart TB
    Enable[Enable Expansion] --> StateManager[Expansion State Manager]
    StateManager --> SaveConfig[Save Configuration<br/>expansion_state.json]
    StateManager --> RecordConsent[Record Consent<br/>expansion_consent.json]
    
    RecordConsent --> ConsentData[Consent Data<br/>Timestamp, Fingerprint, Action]
    
    Load[Load Expansion State] --> StateManager
    StateManager --> CheckEnabled{Is Enabled?}
    CheckEnabled -->|Yes| LoadConfig[Load Configuration]
    CheckEnabled -->|No| Skip[Skip Initialization]
```

**Consent Records:**
- Timestamp of consent
- Hardware fingerprint
- Action (enabled/disabled)
- Expansion type
- Configuration snapshot

### ModelManager

Offline-first model detection and installation guidance:

```mermaid
flowchart TD
    Request[Model Installation Request] --> Check[Check if Model Exists]
    Check -->|Exists| Verified[Model Verified]
    Check -->|Missing| Network{Network<br/>Available?}
    
    Network -->|Yes| Options[Present Options<br/>Online or Offline]
    Network -->|No| Offline[Show Offline Instructions]
    
    Options -->|Online| Consent{User Consents<br/>to Download?}
    Options -->|Offline| Offline
    
    Consent -->|Yes| Download[Download Model<br/>ollama pull]
    Consent -->|No| Offline
    
    Offline --> Instructions[Generate Instructions<br/>Step-by-Step Guide]
    Instructions --> Wait[Wait for User<br/>Complete Steps]
    Wait --> Verify[Verify Installation]
    
    Download --> Verify
    Verify -->|Success| Ready[Model Ready]
    Verify -->|Failed| Retry[Retry or Manual]
```

**Offline Installation Guide:**
1. Download on connected device: `ollama pull <model>`
2. Find model files (platform-specific path)
3. Transfer files (USB, network share, etc.)
4. Place files in correct location
5. Verify installation: `ollama list`

## Expansion Flow

Complete expansion lifecycle:

```mermaid
sequenceDiagram
    participant Hardware
    participant Detector
    participant Dialog
    participant User
    participant Wizard
    participant StateManager
    participant JanetCore
    
    Hardware->>Detector: Hardware Profile
    Detector->>Detector: Detect Opportunities
    Detector->>Dialog: Expansion Opportunity
    Dialog->>User: Suggest Expansion
    User->>Dialog: "yes"
    Dialog->>Wizard: Launch Wizard
    Wizard->>User: Guide Setup
    User->>Wizard: Complete Setup
    Wizard->>StateManager: Save Expansion + Consent
    StateManager->>StateManager: Store Config & Consent
    StateManager->>JanetCore: Expansion Enabled
    JanetCore->>JanetCore: Initialize Feature
```

## Expansion Types

### Voice I/O
- Speech-to-text and text-to-speech
- Wake word detection
- Tone awareness

### Persistent Memory
- Memory vault system
- Encrypted storage
- Semantic search

### Task Delegation
- Specialized model routing
- n8n integration
- Home Assistant control

### Model Installation
- Additional Ollama models
- Offline-first installation
- Model verification

### n8n Integration
- Workflow automation
- Webhook routing
- Custom integrations

### Home Assistant Integration
- Smart home control
- Device management
- Automation triggers

## Wizard System

All expansions use guided wizards:

```mermaid
flowchart TD
    Start[Wizard Start] --> Validate[Validate Requirements]
    Validate -->|Pass| Setup[Setup Process]
    Validate -->|Fail| ShowRequirements[Show Requirements<br/>What's Missing]
    
    Setup --> Online{Network<br/>Available?}
    Online -->|Yes| Choice{User Choice}
    Online -->|No| Offline[Offline Instructions]
    
    Choice -->|Online| OnlineSetup[Online Setup<br/>With Consent]
    Choice -->|Offline| Offline
    
    OnlineSetup --> Verify[Verify Setup]
    Offline --> Wait[Wait for User<br/>Complete Steps]
    Wait --> Verify
    
    Verify -->|Success| Save[Save Configuration]
    Verify -->|Failed| Cleanup[Cleanup on Failure]
    Save --> Complete[Wizard Complete]
    Cleanup --> Fail[Wizard Failed]
```

## Constitutional Integration

### Consent (Axiom 9, Expansion Protocol)

Every expansion requires:
- Explicit consent before any action
- Consent stored with timestamp and fingerprint
- User can revoke consent at any time
- No silent or automatic expansions

### Soul Check (Axiom 10)

Triggered before major expansions:
- Delegation setup
- Integration setup
- Model installation (large models)

### Grounding (Axiom 6)

Expansion suggestions are grounded:
- Based on actual hardware capabilities
- No grandiose promises
- Only what hardware actually supports

### Red Thread (Axiom 8)

Expansion processes respect Red Thread:
- Suggestions blocked when active
- Wizards can be interrupted
- Failed expansions clean up safely

## Usage

### Detecting Opportunities

```python
from expansion import ExpansionDetector
from hardware_detector import HardwareProfile

hardware = HardwareProfile(...)
current_state = {"voice_io_enabled": False}
detector = ExpansionDetector(hardware, current_state)

opportunities = detector.detect_available_expansions()
for opp in opportunities:
    print(f"{opp.name}: {opp.description}")
```

### Suggesting Expansions

```python
from expansion import ExpansionDialog

dialog = ExpansionDialog(janet_core=janet)
if dialog.suggest_expansion(opportunity):
    # User accepted, launch wizard
    janet.run_expansion_wizard(opportunity.expansion_type)
```

### Managing State

```python
from expansion import ExpansionStateManager
from pathlib import Path

state_manager = ExpansionStateManager(Path("/path/to/config"))
state = state_manager.load_expansion_state()

if state.is_enabled("voice_io"):
    config = state.get_config("voice_io")
    # Initialize voice I/O with config
```

## Dependencies

- `hardware_detector` - Hardware capability detection
- `constitution_loader` - Constitutional integration
- `ollama` - Model detection (for model installation)

## Files

- `expansion_detector.py` - Opportunity detection
- `expansion_dialog.py` - Suggestion dialogues
- `expansion_state.py` - State management
- `expansion_types.py` - Data structures
- `model_manager.py` - Model detection and offline guidance
- `wizards/` - Expansion wizards (see [Wizards README](wizards/README.md))

## See Also

- [Expansion Wizards](wizards/README.md) - Wizard system documentation
- [Core System](../core/README.md) - How expansion integrates with JanetCore
- [User Guide](../../documentation/EXPANSION_GUIDE.md) - User-facing expansion guide
- [Offline Installation](../../documentation/OFFLINE_INSTALLATION.md) - Offline model installation

