# 🌱 Expansion Guide — J.A.N.E.T. Seed

This guide explains how to expand Janet's capabilities using the consent-based expansion protocol.

> **New to J.A.N.E.T. Seed?** Start with the [User Guide](USER_GUIDE.md) for basic usage.

---

## 🧭 What is Expansion?

Expansion allows Janet to grow her capabilities based on your hardware and needs. All expansions require:

- **Explicit consent** — You must approve each expansion
- **Clear explanation** — Janet explains benefits, risks, and requirements
- **Step-by-step guidance** — Wizards guide you through setup
- **Reversibility** — You can disable expansions at any time

---

## 🔍 Discovering Expansions

### Ask Janet

Simply ask:
```
what can you do?
```

Janet will show you all available expansion opportunities based on your hardware.

### Automatic Suggestions

Janet may proactively suggest expansions when:
- Your hardware supports new capabilities
- You haven't enabled a feature that would be useful
- A new opportunity becomes available

You can always say "no" or "not now" — Janet will respect your choice.

---

## 🎯 Available Expansions

### Voice I/O

Enable voice interaction with speech-to-text and text-to-speech.

**Requirements:**
- Microphone
- Speaker
- 4GB RAM
- 2GB disk space

**Benefits:**
- Hands-free interaction
- Wake word detection ("Hey Janet")
- Tone-aware responses

### Persistent Memory

Enable long-term memory storage for conversations and learned patterns.

**Requirements:**
- 6GB RAM
- 5GB disk space

**Benefits:**
- Conversation continuity across sessions
- Learned preferences and patterns
- Semantic search through past conversations

### Task Delegation

Enable routing tasks to specialized models or automation tools.

**Requirements:**
- 8GB RAM
- 3GB disk space
- Ollama models (can be installed offline)

**Benefits:**
- Specialized model routing (programming, deep thinking)
- Integration with n8n for automation
- Home Assistant control

### Model Installation

Add additional Ollama models for specialized tasks.

**Requirements:**
- 8GB RAM
- 10GB disk space (varies by model)
- Ollama installed

**Benefits:**
- Specialized models for coding, deep thinking, etc.
- Better performance for specific tasks
- More capable task handling

### n8n Integration

Connect Janet to n8n for workflow automation.

**Requirements:**
- Network access
- n8n instance running

**Benefits:**
- Automate repetitive tasks
- Integrate with external services
- Create custom workflows

### Home Assistant Integration

Connect Janet to Home Assistant for smart home control.

**Requirements:**
- Network access
- Home Assistant instance running
- Long-lived access token

**Benefits:**
- Voice control of smart home devices
- Automated home management
- Integration with existing HA automations

---

## 🚀 Using Expansion Wizards

When you accept an expansion opportunity, Janet will guide you through setup using a wizard.

### Wizard Steps

1. **Requirements Check** — Janet verifies your hardware meets requirements
2. **Dependency Check** — Checks if required software is installed
3. **Configuration** — Guides you through configuration
4. **Verification** — Tests that everything works
5. **Completion** — Saves your expansion state

### Example: Voice I/O Setup

```
Janet: "I notice voice I/O could be enabled. Would you like to explore this?"

You: "yes"

Janet: [Runs Voice I/O Wizard]
  - Checks microphone availability
  - Tests audio devices
  - Configures voice settings
  - Verifies setup

Janet: "✅ Voice I/O setup complete!"
```

---

## 🔄 Managing Expansions

### Disable an Expansion

To disable an expansion, you can:

1. Ask Janet to disable it (future feature)
2. Manually edit `config/expansion_state.json`
3. Remove the expansion from the configuration

### Check Expansion Status

Ask Janet:
```
what can you do?
```

Or check `config/expansion_state.json` directly.

---

## 🛡️ Constitutional Guarantees

All expansions respect Janet's constitutional axioms:

- **Axiom 9 (Consent)**: Every expansion requires explicit consent
- **Axiom 10 (Soul Check)**: Major expansions trigger soul check
- **Axiom 6 (Grounding)**: Expansions are grounded in actual hardware capabilities
- **Red Thread**: Expansion processes can be interrupted

---

## 📋 Offline Installation

All expansions work offline. For model installation, see [OFFLINE_INSTALLATION.md](OFFLINE_INSTALLATION.md).

Janet provides step-by-step instructions for:
- Downloading models on a connected device
- Transferring files to your offline system
- Verifying installations

---

## ❓ Troubleshooting

### Expansion Wizard Fails

- Check that requirements are met
- Verify dependencies are installed
- Check file permissions
- Review error messages for guidance

### Expansion Not Working

- Verify expansion is enabled in `config/expansion_state.json`
- Check that dependencies are still installed
- Restart Janet to reload expansion state

### Can't Find Expansion

- Ask Janet: `what can you do?`
- Check hardware requirements
- Verify expansion is available for your system

---

## 🌱 Best Practices

1. **Start Small** — Enable expansions one at a time
2. **Test Thoroughly** — Verify each expansion works before adding more
3. **Read Requirements** — Understand what each expansion needs
4. **Keep Backups** — Backup your expansion state
5. **Review Regularly** — Check which expansions you're using

---

## 💡 Tips

- **Offline-First**: All expansions work without internet
- **Reversible**: You can disable expansions anytime
- **Consent-Based**: Nothing happens without your approval
- **Guided**: Wizards make setup easy

---

**Remember**: Expansion is about growing Janet's capabilities with your informed consent. Nothing happens automatically.

