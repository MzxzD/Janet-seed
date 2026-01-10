# Double-Soul Conversation Transfer

Enables seamless, consent-based transfer of conversation context between Janet-seed (Constitutional Soul) and Janet Mesh (Networked Soul).

## Overview

The Soul Bridge service allows conversation context and memories to be transferred between the two "souls" of Janet:
- **Constitutional Soul** (Janet-seed): The core constitutional AI system with vault-based memory
- **Networked Soul** (Janet Mesh): The mesh network server with SQLite-based memory

## Architecture

```
Constitutional Soul (Janet-seed)
    ↕️ [Soul Bridge]
Networked Soul (Janet Mesh)
```

## Key Components

### Soul Bridge (`janet-seed/src/bridge/soul_bridge.py`)

- Manages conversation UUID generation and tracking
- Handles transfer requests with consent gates
- Routes to Memory Transfer for actual data transfer

### Memory Transfer (`janet-seed/src/bridge/memory_transfer.py`)

- Exports conversation context respecting vault rules:
  - **Green Vault**: Safe summaries transferable with consent
  - **Blue Vault**: Never transferred (ephemeral, session-only)
  - **Red Vault**: Encrypted secrets require explicit Operator approval + safe word
- Imports context into target soul's memory system

### State Reconciliation (`janet-seed/src/bridge/state_reconciliation.py`)

- Resolves conflicts for concurrent edits
- Implements last-write-wins with timestamp validation
- Merges conversation histories intelligently

## Vault Transfer Rules

### Green Vault (Safe Summaries)
✅ **Transferable** with consent
- Distilled conversation summaries
- Topic tags and themes
- Safe for semantic search

### Blue Vault (Ephemeral)
❌ **Never Transferred**
- Session-only sensitive context
- Zeroized on session end
- Not meant for persistence

### Red Vault (Encrypted Secrets)
🔒 **Requires Safe Word Unlock**
- Explicit Operator approval required
- Safe word must be provided for decryption
- Re-encrypted on target soul with new safe word

## Usage

### WebSocket Message Format

**Request Transfer**:
```json
{
  "type": "transfer_context",
  "source_soul": "networked",
  "target_soul": "constitutional",
  "conversation_uuid": "optional-existing-uuid",
  "include_vaults": ["green", "red"],
  "auto_consent": false
}
```

**Consent Request** (sent to client):
```json
{
  "type": "consent_request",
  "conversation_uuid": "uuid",
  "prompt": "Soul sync requested. Proceed?",
  "prompt_audio": "base64-audio",
  "requires_response": true
}
```

**Transfer Result**:
```json
{
  "type": "transfer_result",
  "conversation_uuid": "uuid",
  "success": true,
  "messages_transferred": 42,
  "vaults_transferred": ["green"],
  "error": null
}
```

## Consent Gate

Before any transfer occurs, the system:
1. Generates a TTS prompt: "Soul sync requested. Proceed?"
2. Sends consent request to the Operator (via client)
3. Waits for explicit consent
4. Proceeds only if consent granted

## Implementation Details

### Export Process

1. Generate or retrieve conversation UUID
2. Export Green Vault summaries (if included)
3. Export Red Vault secrets (if included and unlocked)
4. Export conversation messages
5. Package into transfer format

### Import Process

1. Validate exported context
2. Import conversation messages
3. Import Green Vault summaries (safe)
4. Import Red Vault secrets (if safe word provided)
5. Skip Blue Vault (never imported)

### Conflict Resolution

- **Last-write-wins**: Messages with later timestamps take precedence
- **Merge strategy**: Combines unique messages from both sources
- **Timestamp validation**: Strict ordering for concurrent edits

## Constitutional Compliance

- **Axiom 8 (Red Thread)**: Transfer blocked during Red Thread activation
- **Axiom 9 (Consent-Based Memory)**: All transfers require explicit consent
- **Axiom 10 (Soul Check)**: Major transfers trigger verification prompts

## Error Handling

- Invalid conversation UUID → Error returned
- Missing consent → Transfer denied
- Red Vault locked → Secrets skipped with warning
- Import failures → Partial success reported

## Example Flow

1. Operator requests transfer: "Sync conversation to constitutional soul"
2. System generates conversation UUID
3. Consent gate: "Soul sync requested. Proceed?" (TTS)
4. Operator confirms: "Yes"
5. Export: Green Vault summaries + messages
6. Import: Context added to Constitutional Soul
7. Result: "Transfer complete: 42 messages, 15 summaries"

## Future Enhancements

- Full vault reconciliation
- Incremental transfer (only new messages)
- Transfer history and audit logs
- Multi-soul clustering support
