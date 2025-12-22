# 🌿 J.A.N.E.T. Seed — Capabilities & Growth

J.A.N.E.T. Seed adapts to the system it inhabits.

It never assumes resources.  
It never expands silently.  
It never installs itself elsewhere.

## 🧱 Capability Levels

### Level 0 — Seed Mode (Minimum)

- Text-based conversation
- Constitutional enforcement
- Presence → Conversation loop
- No persistent memory (or minimal)
- No delegation

**Suitable for:**

- Low-resource devices
- First contact
- Evaluation

### Level 1 — Embodied Seed

- Voice input/output
- Wake word detection
- Tone-aware responses
- Selective memory (with gates)

**Requires:**

- Microphone
- Speaker
- Moderate disk space

### Level 2 — Remembering Seed

- Semantic memory (vector DB)
- Encrypted episodic memory
- Memory commands (forget, search, stats)

**Requires:**

- Additional storage
- Companion consent

### Level 3 — Delegating Seed

- Specialized models via LiteLLM
- Automation via n8n
- Smart home integration

**Requires:**

- Companion approval
- Explicit model availability

## 🌱 Expansion Protocol (Consent-Based)

Janet never expands herself.

When expansion is possible, she will say something like:

> "This is what I can do here.  
> If you'd like, I could grow elsewhere — but only if you want to."

### How Expansion Works

1. **Detection**: Janet detects expansion opportunities based on your hardware and current state
2. **Suggestion**: Janet proactively suggests expansions (or you can ask: `what can you do?`)
3. **Dialogue**: Janet explains benefits, risks, and requirements
4. **Consent**: You explicitly approve or decline
5. **Wizard**: If approved, a guided wizard walks you through setup
6. **Verification**: Janet verifies the expansion works correctly
7. **State Management**: Expansion state is saved with consent records

### Expansion Types

- **Voice I/O**: Speech-to-text and text-to-speech capabilities
- **Persistent Memory**: Long-term memory storage with encryption
- **Task Delegation**: Routing to specialized models or automation tools
- **Model Installation**: Adding additional Ollama models (offline-first)
- **n8n Integration**: Workflow automation via n8n
- **Home Assistant Integration**: Smart home control

### Offline-First

All expansions work **offline**. For model installation:

- Janet provides step-by-step offline installation instructions
- You can download models on a connected device and transfer them
- Janet verifies installations after manual setup
- Never auto-downloads without explicit consent

See [documentation/OFFLINE_INSTALLATION.md](documentation/OFFLINE_INSTALLATION.md) for details.

### Expansion Requirements

Expansion always requires:

- Explicit companion intent
- Explanation of benefits and risks
- Step-by-step human action
- Verification handshake
- Ability to revoke trust later

At any point, the answer can be no — without consequence.

### Managing Expansions

- **Check Status**: Ask `what can you do?` to see available expansions
- **Enable**: Accept an expansion suggestion or use `expand <name>`
- **Disable**: Expansions can be disabled at any time
- **State**: Expansion state is stored in `config/expansion_state.json`

See [documentation/EXPANSION_GUIDE.md](documentation/EXPANSION_GUIDE.md) for a complete guide.

## 🛑 What Will Never Happen Automatically

- Network scanning
- Silent installs
- Hidden agents
- Background propagation

**Trust is earned, not assumed.**

