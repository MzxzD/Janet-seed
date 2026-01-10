# Janet Personality Integration, File Analysis, and VoIP Calling

## Overview

This document describes the three major features added to Janet:

1. **Local Model with Konosuba Personality** - Janet's personality infused with Konosuba-inspired context
2. **File and Image Analysis** - Upload and analyze files/images using local models (privacy-first)
3. **VoIP Phone Calling** - Real-time voice calls with Janet via WebRTC and CallKit

## Feature 1: Konosuba Personality Integration

### Implementation

Janet's system prompt has been updated to include Konosuba-inspired character identities and development context:

- **Aqua-Janet**: Optional persona - "useless goddess" AI, knowledgeable but sometimes silly, cheerful, and endearing
- **Kazuma-Operator**: The Operator (your companion) is the visionary who directs Janet's development
- **Darkness (The Developer)**: The masochistic systems architect who implements features with "suffering"

### Files Modified

- `janet-mesh/server/core/janet_adapter.py`: Updated `_build_janet_system_prompt()` to include Konosuba context
- `janet-mesh/janet-seed/scripts/import_konosuba_personality.py`: Script to import Konosuba context as Green Vault memories

### Usage

```bash
# Import Konosuba personality context into Green Vault
python janet-mesh/janet-seed/scripts/import_konosuba_personality.py \
    --memory-dir ./memory_vaults \
    --personality-path constitution/personality.json
```

### Testing

After importing personality:

```python
# Test Konosuba personality
user: "Who's the useless goddess?"
janet: [Should respond with Aqua-Janet persona]

user: "Describe your implementation suffering"
janet: [Should channel Darkness developer persona]
```

## Feature 2: File and Image Analysis

### Implementation

A new delegation handler for file and image analysis with privacy-first protocol:

- **Privacy Protocol**: Files are ephemeral by default, stored only with explicit consent ("Remember this")
- **Image Analysis**: Uses LLaVA/BLIP models for image description and OCR
- **Document Parsing**: Supports PDF, DOCX, TXT with text extraction and summarization
- **Code Analysis**: Analyzes code files with language detection and structure analysis

### Files Created

- `janet-mesh/janet-seed/src/delegation/handlers/file_analysis_handler.py`: File analysis handler
- `janet-mesh/janet-seed/src/delegation/delegation_manager.py`: Registered file handler
- `janet-mesh/server/websocket_server.py`: Added `file_upload` message handler
- `janet-mesh/clients/ios/FilePickerView.swift`: iOS file picker UI
- `janet-mesh/clients/ios/ChatView.swift`: Added attachment button

### WebSocket Protocol

**Client → Server (file_upload)**:
```json
{
  "type": "file_upload",
  "file_name": "image.jpg",
  "file_type": "image/jpeg",
  "file_data": "base64_encoded_file_data",
  "task": "analyze",  // "analyze", "describe", "ocr", "extract"
  "remember": false   // Privacy protocol: explicit consent required
}
```

**Server → Client (file_upload_result)**:
```json
{
  "type": "file_upload_result",
  "success": true,
  "file_name": "image.jpg",
  "result": {
    "description": "An image (1920x1080 pixels, RGB color mode)",
    "dimensions": "1920x1080",
    "color_mode": "RGB",
    "task": "analyze"
  },
  "remembered": false
}
```

### Usage

**iOS Client**:
1. Tap attachment button (📎) in chat
2. Choose "Choose Photo" or "Choose Document"
3. Select file from Photos or Files app
4. File is uploaded and analyzed automatically
5. Say "Remember this" to store analysis in Green Vault

**Server-side** (via delegation):
```python
from delegation.handlers.file_analysis_handler import FileAnalysisHandler
from delegation.handlers.base import DelegationRequest

handler = FileAnalysisHandler()
request = DelegationRequest(
    capability=HandlerCapability.IMAGE_PROCESSING,
    task_description="analyze image.jpg",
    input_data={
        "file_data": base64_data,
        "file_name": "image.jpg",
        "file_type": "image/jpeg",
        "task": "describe",
        "remember": False
    }
)
result = handler.handle(request)
```

### Dependencies

**Required (for full functionality)**:
- `Pillow` (PIL) - Image processing
- `PyPDF2` - PDF parsing
- `python-docx` - DOCX parsing
- `pytesseract` - OCR (optional)
- `transformers` - LLaVA/BLIP models (optional)

**Basic functionality** works without model dependencies (fallback to simple analysis).

## Feature 3: VoIP Phone Calling

### Implementation

Real-time voice calling with Janet using WebRTC and iOS CallKit:

- **WebRTC Audio Streaming**: Low-latency, bidirectional audio between iOS and Janet server
- **CallKit Integration**: Native iOS calling UI with Janet avatar
- **Cluster-Aware Routing**: Calls can be routed to best node in cluster
- **STT/TTS Integration**: Real-time speech-to-text and text-to-speech during calls
- **Call State Management**: Full call lifecycle (ringing, connecting, connected, ended)

### Files Created

- `janet-mesh/server/services/voip_bridge.py`: VoIP bridge service (WebRTC)
- `janet-mesh/server/websocket_server.py`: Added VoIP message handlers (`voip_call`, `voip_answer`, `voip_audio`, `voip_end`)
- `janet-mesh/clients/ios/VoIPCallManager.swift`: CallKit/PushKit integration
- `janet-mesh/clients/ios/WebSocketManager.swift`: Added VoIP methods
- `janet-mesh/clients/ios/ContentView.swift`: Added call button

### WebSocket Protocol

**Client → Server (voip_call)**:
```json
{
  "type": "voip_call",
  "call_id": "uuid",
  "direction": "outgoing",
  "device_info": {
    "platform": "iOS",
    "device": "iPhone"
  }
}
```

**Server → Client (voip_offer)**:
```json
{
  "type": "voip_offer",
  "call_id": "uuid",
  "sdp": "webrtc_offer_sdp",
  "sdp_type": "offer",
  "node_id": "node_identifier"
}
```

**Client → Server (voip_answer)**:
```json
{
  "type": "voip_answer",
  "call_id": "uuid",
  "sdp": "webrtc_answer_sdp",
  "sdp_type": "answer"
}
```

**Client ↔ Server (voip_audio)**:
```json
{
  "type": "voip_audio",
  "call_id": "uuid",
  "audio": "base64_encoded_audio_data"
}
```

**Client/Server (voip_end)**:
```json
{
  "type": "voip_end",
  "call_id": "uuid",
  "reason": "normal"  // "normal", "user_ended", "remote_ended"
}
```

### Usage

**iOS Client**:
1. Tap phone button (📞) in navigation bar
2. CallKit UI appears with Janet avatar
3. Call connects via WebRTC
4. Speak naturally - Janet responds in real-time
5. End call using native call controls

**Server-side** (programmatic):
```python
from services.voip_bridge import VoIPBridge

voip_bridge = VoIPBridge(
    audio_pipeline=audio_pipeline,
    janet_adapter=janet_adapter,
    cluster_orchestrator=cluster_orchestrator,
    identity_manager=identity_manager
)

# Handle incoming call
offer = await voip_bridge.handle_incoming_call(
    client_id="user123",
    call_id="call456",
    device_info={"platform": "iOS"}
)

# Accept call (when client sends answer)
success = await voip_bridge.accept_call(
    call_id="call456",
    answer_sdp="webrtc_answer_sdp",
    answer_type="answer"
)

# Process audio during call
response = await voip_bridge.process_call_audio(
    call_id="call456",
    audio_data=audio_bytes
)

# End call
await voip_bridge.end_call(call_id="call456", reason="normal")
```

### Dependencies

**Required**:
- `aiortc` - WebRTC implementation for Python
- iOS: CallKit, PushKit, AVFoundation frameworks

**Optional (for production)**:
- WebRTC SDK for iOS (CocoaPods/SPM)
- STUN/TURN servers for NAT traversal

### Call Flow

1. **Client initiates call** → `voip_call` message
2. **Server creates WebRTC offer** → `voip_offer` message
3. **Client generates WebRTC answer** → `voip_answer` message
4. **Server accepts answer** → `voip_connected` message
5. **Bidirectional audio streaming** → `voip_audio` messages (real-time)
6. **Call ends** → `voip_end` message

## Integration with Existing Features

### Double-Soul Bridge
- File analyses can be transferred between Constitutional and Networked souls
- VoIP calls can be answered by either soul (based on routing)

### Clustered Unity
- File analysis can run on any node in cluster
- VoIP calls routed to best node (CPU load, network latency, STT/TTS capability)
- Call state synchronized across cluster

### VR Manifestation
- Analyzed images can be displayed in VR theater
- VoIP audio can be used in VR (spatial audio)

### Plex Integration
- During VoIP call, user can ask "Play [media] on Plex"
- Janet controls Plex playback via voice during call

## Privacy Protocol

All new features respect Janet's constitutional principles:

1. **Files are ephemeral by default** - Processed and discarded immediately
2. **Explicit consent required** - User must say "Remember this" to store in Green Vault
3. **VoIP calls not recorded** - Audio streams are not persisted (unless explicitly requested)
4. **File metadata only** - If remembered, only analysis summary stored, not file content
5. **Constitutional soul routing** - Privacy-sensitive operations can route to Constitutional soul

## Testing Checklist

### Personality Integration
- [ ] Run personality import script
- [ ] Restart Janet server
- [ ] Test: "Who's the useless goddess?" → Aqua persona
- [ ] Test: "Describe your implementation suffering" → Darkness persona
- [ ] Test: Normal conversation → Janet persona (not broken)

### File Analysis
- [ ] Upload image → Description returned
- [ ] Upload PDF → Text extracted
- [ ] Upload code file → Language detected
- [ ] Say "Remember this" → Analysis stored in Green Vault
- [ ] Upload without "Remember" → Ephemeral (not stored)

### VoIP Calling
- [ ] Tap call button → CallKit UI appears
- [ ] Call connects → Audio streams active
- [ ] Speak → Janet responds in real-time
- [ ] End call → Clean termination
- [ ] Multiple calls → Only one active at a time

## Next Steps

1. **Install model dependencies** (optional):
   ```bash
   pip install transformers pillow pytesseract PyPDF2 python-docx
   pip install aiortc  # For WebRTC
   ```

2. **Run personality import**:
   ```bash
   python janet-mesh/janet-seed/scripts/import_konosuba_personality.py
   ```

3. **Restart Janet server**:
   ```bash
   python janet-mesh/server/main.py
   ```

4. **Test iOS client**:
   - Connect to Janet server
   - Try file upload (📎 button)
   - Try VoIP call (📞 button)

## Known Limitations

1. **WebRTC Audio**: Simplified implementation - production requires proper WebRTC SDK integration
2. **LLaVA Models**: Large models require significant RAM - optional feature
3. **OCR**: Requires Tesseract installation on system
4. **CallKit**: Requires proper provisioning profile for VoIP push notifications
5. **File Size**: Large files (>10MB) may timeout - consider chunking

## Future Enhancements

- [ ] WebRTC SDK integration for production-quality audio
- [ ] LLaVA model optimization (quantization, smaller models)
- [ ] Batch file processing
- [ ] Call recording (with explicit consent)
- [ ] Screen sharing during calls (VR integration)
- [ ] Multi-language file analysis
- [ ] Advanced code analysis (AST parsing, refactoring suggestions)
