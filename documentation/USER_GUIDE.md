# 📖 User Guide — J.A.N.E.T. Seed

Welcome to J.A.N.E.T. Seed! This guide will help you get started and make the most of your constitutional AI companion.

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Installation & Setup](#installation--setup)
3. [Getting Started](#getting-started)
4. [Using J.A.N.E.T. Seed](#using-janet-seed)
5. [Constitutional Features](#constitutional-features)
6. [Modes of Operation](#modes-of-operation)
7. [Expansion Protocol](#expansion-protocol)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)
10. [Privacy & Security](#privacy--security)
11. [Getting Help](#getting-help)

---

## Introduction

### What is J.A.N.E.T. Seed?

**J.A.N.E.T. Seed** (Just A Neat Evolving Thinker — Seed Edition) is a constitutional, offline-first AI companion designed to think *with* you, not *over* you.

Janet is:
- 🧠 **Constitutional** — Guided by 16 immutable axioms that ensure safety, privacy, and respect
- 🔐 **Offline-first** — Works entirely locally, no cloud required
- 🌱 **Consent-driven** — Never expands capabilities without your explicit approval
- 🧭 **Grounded** — Stays rooted in reality, interruptible at any time

### Core Principles

- **Constitution first** — All behavior is guided by Janet's constitutional axioms
- **Presence before cognition** — Janet listens only when invited
- **Consent over capability** — Nothing expands unless you say yes
- **Memory with restraint** — Secrets are sacred and never stored

### What J.A.N.E.T. Seed Is Not

- ❌ Not a cloud service
- ❌ Not autonomous without oversight
- ❌ Not self-expanding
- ❌ Not a general-purpose AGI

---

## Installation & Setup

### System Requirements

**Minimum:**
- Python 3.10 or higher
- 4GB RAM
- 2GB free disk space
- macOS, Linux, or Windows (WSL2)

**Recommended:**
- 8GB+ RAM
- 10GB+ free disk space
- Ollama installed (for AI model support)

### Installation Steps

1. **Clone or download the repository:**
   ```bash
   git clone <repository-url>
   cd janet-seed
   ```

2. **Run the installer:**
   ```bash
   python3 src/main.py
   ```

   On first run, Janet will:
   - Detect your hardware capabilities
   - Present the constitutional briefing
   - Ask for your explicit consent
   - Install dependencies (Python virtual environment, packages)
   - Set up Ollama (if needed)
   - Create configuration directories

3. **Follow the installation prompts:**
   - Read the constitutional briefing carefully
   - Provide consent when ready
   - Wait for installation to complete

### First-Time Setup

On your first run, Janet will:

1. **Hardware Detection** — Automatically detects your system capabilities
2. **Constitutional Briefing** — Presents Janet's 16 axioms
3. **Consent Gate** — Requires explicit consent before proceeding
4. **Installation** — Sets up virtual environment and dependencies
5. **Constitution Loading** — Loads and verifies constitutional integrity

### Verifying Installation

To verify your installation:

```bash
python3 src/main.py --verify
```

This checks that:
- The constitution file is valid
- Constitutional integrity is maintained
- All required files are present

---

## Getting Started

### Basic Commands

Once Janet is running, you can interact in two ways:

**Text Mode (Default):**
- Simply type your message and press Enter
- Janet will respond in text

**Voice Mode:**
- Say "Hey Janet" to activate (wake word)
- Speak your message
- Janet will respond with voice

### Your First Conversation

1. Start Janet:
   ```bash
   python3 src/main.py
   ```

2. After the constitutional briefing and consent, you'll see:
   ```
   Janet: Hello! I'm Janet. How can I help you today?
   ```

3. Try a simple greeting:
   ```
   You: Hello, Janet!
   Janet: Hello! It's nice to meet you. How can I assist you?
   ```

4. Ask questions or have a conversation naturally.

### Understanding Janet's Responses

Janet's responses are:
- **Constitutional** — Guided by her axioms
- **Contextual** — Aware of your conversation history (if memory is enabled)
- **Respectful** — Never intrusive or pushy
- **Honest** — Will tell you if she doesn't know something

---

## Using J.A.N.E.T. Seed

### Core Commands

#### Exit Janet
```
quit
exit
```
Exits Janet cleanly and returns to your terminal.

#### Emergency Stop (Red Thread)
```
red thread
```
**Axiom 8: Red Thread Protocol** — Immediately stops all processing and returns to grounding. Use this if you need Janet to stop everything immediately.

After invoking Red Thread:
- All subsystems stop (voice, memory, delegation)
- Janet returns to a safe state
- You'll be asked if you want to reset and continue

#### Switch Input Modes
```
text
```
Switches to text input mode (if currently in voice mode).

```
voice
```
Switches to voice input mode (requires voice I/O expansion).

### Memory Commands

*Note: These commands require the Persistent Memory expansion to be enabled.*

#### View Memory Statistics
```
memory stats
```
Shows:
- Number of episodic memories stored
- Number of semantic memories stored
- Last weekly summary date

#### Search Past Conversations
```
search memory <query>
```
Searches through past conversations for relevant memories.

Example:
```
search memory favorite color
```

#### Delete Memories

**Delete all memories:**
```
forget all
```
⚠️ **Warning:** This triggers a Soul Check (Axiom 10) to verify you're in the right state of mind before deleting all memories.

**Delete specific memory:**
```
forget <memory_id>
```
Deletes a specific memory by ID (shown in memory stats or search results).

### Delegation Commands

*Note: These commands require the Delegation Layer expansion to be enabled.*

#### View Delegation Capabilities
```
delegation stats
```
Shows which delegation services are available:
- Model routing (specialized AI models)
- n8n (workflow automation)
- Home Assistant (smart home control)

#### Delegate to AI Model
```
delegate to model <query>
```
Routes your query to a specialized AI model (e.g., for programming tasks, deep thinking).

Example:
```
delegate to model write a Python function to sort a list
```

#### Delegate to n8n
```
delegate to n8n <action>
```
Triggers an n8n workflow (requires n8n integration setup).

#### Delegate to Home Assistant
```
delegate to home_assistant <action>
```
Controls smart home devices via Home Assistant (requires Home Assistant integration setup).

⚠️ **Note:** Major delegation actions (n8n, Home Assistant) trigger a Soul Check to verify your intent.

### Expansion Commands

#### View Available Expansions
```
what can you do?
show expansions
available expansions
```
Shows all expansion opportunities based on your hardware.

#### Start Expansion Wizard
```
expand <type>
```
Starts the expansion wizard for a specific type:
- `expand voice` — Voice I/O
- `expand memory` — Persistent Memory
- `expand delegation` — Delegation Layer
- `expand model` — Model Installation
- `expand n8n` — n8n Integration
- `expand home_assistant` — Home Assistant Integration

For detailed expansion information, see [EXPANSION_GUIDE.md](EXPANSION_GUIDE.md).

---

## Constitutional Features

J.A.N.E.T. Seed is built on constitutional guarantees that ensure safety, privacy, and respect.

### Red Thread Protocol (Axiom 8)

**Emergency Stop** — Say "red thread" at any time to immediately stop all processing.

When Red Thread is invoked:
- All subsystems stop immediately
- Voice detection stops
- Memory operations stop
- Delegation operations stop
- Expansion wizards stop
- Janet returns to a safe, grounded state

**Use cases:**
- You need to stop everything immediately
- Something feels wrong or unsafe
- You want to pause and reconsider

### Soul Check (Axiom 10)

**Verification Before Major Changes** — Janet verifies your state of mind before significant actions.

Soul Check is automatically triggered before:
- Deleting all memories
- Major delegation actions (n8n, Home Assistant)
- Expansion wizard execution
- Constitutional modifications

**Soul Check Process:**
1. Janet asks three questions (1-10 scale):
   - How clear-minded do you feel?
   - How emotionally charged is this decision?
   - How would future-you rate this choice?
2. Janet evaluates your responses
3. If concerns are detected, Janet suggests pausing
4. You can override, but with a warning

### Memory Gates (Axiom 9)

**Sacred Secrets** — Secrets are never stored in memory.

Janet automatically detects and blocks storage of:
- Passwords
- Secrets
- Private/confidential information
- Sensitive personal data

If you share a secret, Janet will:
- Acknowledge it
- **Not** store it in memory
- Keep it only in the current conversation
- Forget it when the conversation ends

### Daily Constitutional Verification

**Automatic Integrity Checks** — Janet verifies her constitution hasn't been tampered with.

Every 24 hours, Janet:
- Verifies the constitution file hash
- Checks for tampering or modifications
- Logs verification results
- Warns if integrity is compromised

This ensures Janet's core principles remain intact.

---

## Modes of Operation

### Text Mode (Default)

**How to use:**
```bash
python3 src/main.py
```

- Type your messages
- Press Enter to send
- Janet responds in text
- Simple and straightforward

**Best for:**
- Quick questions
- Detailed conversations
- When you prefer typing
- Low-resource environments

### Voice Mode

**How to use:**
```bash
python3 src/main.py --voice
```

**Features:**
- **Wake Word Detection** — Say "Hey Janet" to activate
- **Speech-to-Text** — Speaks your input
- **Text-to-Speech** — Janet responds with voice
- **Tone Awareness** — Janet adapts to your emotional tone

**Wake Word Phrases:**
- "Hey Janet"
- "Janet"
- "Hey Jan"
- "Janet wake up"

**After wake word:**
- Janet acknowledges with a sound
- Greets you
- Listens for your input
- Responds with voice

**Best for:**
- Hands-free interaction
- Natural conversation flow
- When typing is inconvenient

### Tone Awareness

Janet can detect emotional tone in your voice or text:
- Stress patterns
- Sarcasm
- Emotional state
- Social context

Janet adapts her responses accordingly while staying grounded in facts (Axiom 4: Emotion as Fuel, Not Truth).

---

## Expansion Protocol

J.A.N.E.T. Seed can grow, but only with your explicit consent.

### How Expansion Works

1. **Discovery** — Janet detects available expansions based on your hardware
2. **Suggestion** — Janet suggests expansions (never auto-installs)
3. **Consent** — You must explicitly approve each expansion
4. **Wizard** — Step-by-step guided setup
5. **Verification** — Janet verifies the expansion works

### Discovering Expansions

**Ask Janet:**
```
what can you do?
```

Janet will show:
- Available expansions
- Requirements (hardware, disk space)
- Benefits and considerations
- Estimated setup time

**Automatic Suggestions:**
Janet may proactively suggest expansions when:
- Your hardware supports new capabilities
- A useful feature isn't enabled
- A new opportunity becomes available

You can always say "no" or "not now" — Janet respects your choice.

### Available Expansions

- **Voice I/O** — Speech-to-text and text-to-speech
- **Persistent Memory** — Long-term conversation storage
- **Task Delegation** — Specialized models and automation
- **Model Installation** — Additional AI models
- **n8n Integration** — Workflow automation
- **Home Assistant Integration** — Smart home control

For detailed information, see [EXPANSION_GUIDE.md](EXPANSION_GUIDE.md).

### Offline-First Installation

All expansions work offline-first:
- Models can be installed manually (sneakernet)
- No automatic downloads without consent
- Step-by-step offline installation guides
- Network only used with explicit permission

See [OFFLINE_INSTALLATION.md](OFFLINE_INSTALLATION.md) for offline model installation.

---

## Troubleshooting

### Common Issues

#### Installation Problems

**Issue:** Installation fails or dependencies don't install

**Solutions:**
- Ensure Python 3.10+ is installed: `python3 --version`
- Check internet connection (for initial dependency download)
- Try manual installation: `pip install -r requirements.txt`
- Check file permissions in Janet home directory

**Issue:** Ollama not found

**Solutions:**
- Install Ollama from https://ollama.com
- Ensure Ollama is in your PATH
- Verify with: `ollama --version`

#### Voice Mode Issues

**Issue:** "Voice I/O not available"

**Solutions:**
- Install voice dependencies: `pip install openai-whisper sounddevice pyttsx3`
- On macOS: `brew install portaudio`
- On Linux: `sudo apt-get install portaudio19-dev`
- Check microphone permissions in system settings

**Issue:** Wake word not detected

**Solutions:**
- Speak clearly: "Hey Janet"
- Check microphone is working
- Increase microphone volume
- Try different wake phrases: "Janet", "Hey Jan"

**Issue:** No audio output

**Solutions:**
- Check speaker/headphone connection
- Verify system audio settings
- Try text mode to verify Janet is working

#### Memory/Delegation Not Working

**Issue:** "Persistent memory not available"

**Solutions:**
- Enable memory expansion: `expand memory`
- Check disk space (requires 5GB free)
- Verify ChromaDB and SQLite are installed
- Check memory directory permissions

**Issue:** "Delegation not available"

**Solutions:**
- Enable delegation expansion: `expand delegation`
- Ensure Ollama is installed and running
- Check model availability: `ollama list`
- Verify LiteLLM dependencies are installed

#### Constitutional Verification Failures

**Issue:** "Constitutional integrity compromised"

**Solutions:**
- **Do not ignore this warning**
- Check if constitution file was modified
- Restore from backup if available
- Re-download or re-clone the repository
- Report the issue if constitution wasn't intentionally modified

**Issue:** Daily verification warnings

**Solutions:**
- Check system clock is correct
- Verify constitution file hasn't been modified
- Check file permissions on constitution file
- Review verification logs in `~/.janet/logs/`

### Getting More Help

If you encounter issues not covered here:

1. **Check the logs:**
   - Location: `~/.janet/logs/`
   - Look for error messages
   - Check verification logs

2. **Review documentation:**
   - [EXPANSION_GUIDE.md](EXPANSION_GUIDE.md)
   - [OFFLINE_INSTALLATION.md](OFFLINE_INSTALLATION.md)
   - [AXIOM_IMPLEMENTATION.md](AXIOM_IMPLEMENTATION.md)

3. **Report issues:**
   - Open an issue on GitHub
   - Include error messages and logs
   - Describe what you were trying to do

---

## Advanced Usage

### Command-Line Flags

```bash
python3 src/main.py [options]
```

**Available flags:**
- `--voice` — Enable voice mode
- `--detect-only` — Only run hardware detection, don't start Janet
- `--verify` — Verify constitution integrity and exit

**Examples:**
```bash
# Voice mode
python3 src/main.py --voice

# Hardware detection only
python3 src/main.py --detect-only

# Verify constitution
python3 src/main.py --verify
```

### Configuration Files

Janet stores configuration in `~/.janet/`:

- `~/.janet/config/` — Configuration files
- `~/.janet/constitution/` — Constitution files
- `~/.janet/memory/` — Memory storage (if enabled)
- `~/.janet/logs/` — Log files

**Important files:**
- `config/consent.json` — Your consent record
- `config/expansion_state.json` — Expansion state
- `config/hardware_report.json` — Hardware detection results

### Hardware Detection

To see what Janet detects about your hardware:

```bash
python3 src/main.py --detect-only
```

This shows:
- CPU information
- Memory (RAM)
- Disk space
- Available capabilities
- Expansion opportunities

### Constitution Verification

To verify the constitution without starting Janet:

```bash
python3 src/main.py --verify
```

This checks:
- Constitution file exists
- Constitution structure is valid
- Constitutional integrity (hash verification)
- All axioms are present

---

## Privacy & Security

### Offline-First Design

J.A.N.E.T. Seed is designed to work entirely offline:
- No cloud services required
- No internet connection needed after installation
- All processing happens locally
- No data leaves your device

### Memory Encryption

If Persistent Memory is enabled:
- Episodic memories are encrypted in SQLite
- Encryption keys are derived locally
- No keys are transmitted or stored remotely
- You control all data

### Secret Protection (Axiom 9)

Janet never stores secrets:
- Passwords are detected and blocked
- Secrets are not written to memory
- Confidential information stays in conversation only
- Memory gates prevent secret storage

### No Telemetry or Data Collection

Janet does not:
- Collect usage statistics
- Send data to external servers
- Track your behavior
- Phone home
- Collect telemetry

Everything stays on your device.

### Constitutional Integrity

Janet's constitution is protected:
- Daily verification checks for tampering
- Hash verification ensures integrity
- Modifications are detected and reported
- Core principles cannot be silently changed

---

## Getting Help

### Documentation

- **[README.md](../README.md)** — Project overview
- **[EXPANSION_GUIDE.md](EXPANSION_GUIDE.md)** — Expansion protocol details
- **[OFFLINE_INSTALLATION.md](OFFLINE_INSTALLATION.md)** — Offline model installation
- **[AXIOM_IMPLEMENTATION.md](AXIOM_IMPLEMENTATION.md)** — Technical axiom implementation
- **[CAPABILITIES.md](../CAPABILITIES.md)** — Capability scaling and consent

### Issue Reporting

If you find a bug or have a question:

1. **Check existing issues** — Your issue might already be reported
2. **Create a new issue** — Include:
   - What you were trying to do
   - What happened (error messages, logs)
   - Your system information (OS, Python version)
   - Steps to reproduce

### Community Resources

- **Code of Conduct** — See [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
- **Contributing** — See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Security** — See [SECURITY.md](../SECURITY.md)

### Constitutional Questions

If you have questions about Janet's constitution or axioms:
- Review [constitution/AXIOMS.md](../constitution/AXIOMS.md)
- Check [AXIOM_IMPLEMENTATION.md](AXIOM_IMPLEMENTATION.md) for technical details
- Open a discussion issue for philosophical questions

---

## Final Notes

J.A.N.E.T. Seed is designed to be:
- **Quiet** — Doesn't demand attention
- **Respectful** — Honors your boundaries
- **Honest** — Tells you what she can and can't do
- **Grounded** — Stays rooted in reality

Remember:
> "This is what I can be here.  
> This is what I could become elsewhere.  
> Nothing happens unless you say yes."

Thank you for choosing J.A.N.E.T. Seed. We hope Janet becomes a helpful, respectful companion in your journey.

---

**Last Updated:** Day 7 Implementation  
**Version:** v0.1-seed

