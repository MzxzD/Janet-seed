# Virtual Reality Manifestation Setup

Build a VR environment where the Operator can interact with a real-time 3D model of Janet that talks and listens.

## Overview

The VR client provides an immersive 3D environment where Janet appears as an animated character that can:
- Listen to Operator voice via VR headset microphone
- Respond with voice and lip-sync animation
- Display emotional states through gestures and animations
- Control media playback via gesture recognition (stretch goal)

## Architecture

```
VR Client (Unity/Unreal)
    ↕️ WebRTC Audio
    ↕️ WebSocket Messages
Janet Mesh Server
    ↕️
Janet-seed (Constitutional Soul)
```

## Components

### Server-Side

#### VR Audio Bridge (`server/services/vr_audio_bridge.py`)

- WebRTC peer connection management
- Bi-directional audio streaming
- STT → LLM → TTS pipeline for VR
- Low-latency audio (<100ms target)

### Client-Side (Unity/Unreal)

#### JanetModelController

- 3D model loading and animation
- Viseme blendshape system for lip-sync
- Tone-aware idle animations
- Gesture system reflecting emotional state
- Eye tracking and attention system

#### VRAudioBridge

- WebSocket connection to Janet Mesh server
- WebRTC audio streaming setup
- STT audio capture from VR headset
- TTS audio playback with lip-sync

#### PlexTheaterController (Stretch Goal)

- Virtual Plex theater environment
- 3D-Janet controls playback via gestures
- Immersive movie watching experience

## Requirements

### Unity Version
- Unity 2021.3 LTS or newer
- Meta XR SDK or OpenXR

### Unreal Version
- Unreal Engine 5.0 or newer
- Meta XR SDK or OpenXR

### Dependencies
- WebRTC libraries (native or plugin)
- GLTF importer (Unity: GLTFast, Unreal: GLTF)
- Audio streaming libraries

## Setup Instructions

### 1. Server Configuration

The VR Audio Bridge is automatically initialized in `websocket_server.py`. No additional configuration required.

### 2. Unity Project Setup

1. Create new Unity project (3D template)
2. Install Meta XR SDK via Package Manager:
   - `Window → Package Manager → + → Add package from git URL`
   - URL: `https://github.com/oculus-samples/Unity-MetaXR-SDK.git`
3. Install GLTFast:
   - `Window → Package Manager → + → Add package from git URL`
   - URL: `https://github.com/atteneder/glTFast.git`
4. Install WebRTC package:
   - `Window → Package Manager → + → Add package from git URL`
   - URL: `com.unity.webrtc`
5. Import Janet 3D model (GLTF format)
6. Add VR scripts to scene:
   - `JanetModelController.cs`
   - `VRAudioBridge.cs`
   - `PlexTheaterController.cs` (optional)

### 3. Unreal Project Setup

1. Create new Unreal project (VR template)
2. Enable Meta XR SDK plugin:
   - `Edit → Plugins → Search "Meta XR SDK" → Enable`
3. Install GLTF importer:
   - Available in Unreal Marketplace
4. Set up WebRTC C++ plugins:
   - Requires custom plugin implementation
5. Import Janet 3D model
6. Create Blueprints:
   - `JanetModelController`
   - `VRAudioBridge`

### 4. Model Requirements

The Janet 3D model should include:

#### Viseme Blendshapes
- A (ah) - Mouth open wide
- E (eh) - Mouth slightly open
- I (ih) - Mouth narrow
- O (oh) - Mouth rounded
- U (uh) - Mouth pursed
- M (mm) - Lips closed
- F (ff) - Upper teeth on lower lip
- Th (th) - Tongue between teeth
- P (p) - Lips closed, brief
- And more as needed

#### Animation System
- Idle animations (multiple variants)
- Happy/joyful animations
- Thinking/curious animations
- Gesture animations
- Eye movement (IK or bone-based)

## WebSocket Protocol

### Connection Flow

1. **VR Client connects**:
```json
{
  "type": "vr_connect",
  "session_id": "unique-session-id"
}
```

2. **Server responds with WebRTC offer**:
```json
{
  "type": "vr_offer",
  "session_id": "unique-session-id",
  "sdp": "webrtc-sdp-offer",
  "sdp_type": "offer"
}
```

3. **VR Client generates answer and sends**:
```json
{
  "type": "vr_audio",
  "session_id": "unique-session-id",
  "sdp": "webrtc-sdp-answer",
  "sdp_type": "answer"
}
```

4. **Audio streaming begins** (bi-directional via WebRTC data channel)

### Audio Input

Send audio from VR headset microphone:
```json
{
  "type": "vr_audio",
  "session_id": "unique-session-id",
  "audio": "base64-encoded-wav-audio-data"
}
```

### Audio Output

Receive Janet's response:
```json
{
  "type": "vr_response",
  "session_id": "unique-session-id",
  "text": "Janet's response text",
  "status": "processed"
}
```

Audio is streamed via WebRTC data channel (not included in JSON).

## Animation System

### Viseme Detection

The system analyzes TTS audio in real-time to detect visemes:
- Audio → FFT → Viseme probabilities
- Update blendshape weights based on probabilities
- Smooth transitions between visemes

### Tone-Aware Animations

Janet's animations reflect the emotional tone of conversations:
- **Happy**: Upbeat idle animation, joyful gestures
- **Thinking**: Curious pose, slight head tilt
- **Neutral**: Standard idle animation
- **Concerned**: Worried expression, slower movements

### Gesture System

Gestures are triggered based on:
- Conversation context
- Emotional state
- Intent detection (e.g., "play music" → gesture for playback)

### Eye Tracking

The Janet model tracks the Operator's head position:
- Head bone rotates toward Operator
- Eyes look in Operator's direction
- Creates natural interaction feeling

## Lip-Sync Implementation

### Real-Time Viseme Mapping

1. TTS audio is analyzed frame-by-frame
2. Viseme probabilities are calculated
3. Blendshape weights are updated in real-time
4. Smooth interpolation between visemes

### Example (Unity C#)

```csharp
void UpdateVisemes()
{
    if (audioSource.isPlaying)
    {
        float[] audioData = new float[1024];
        audioSource.GetOutputData(audioData, 0);
        
        // Analyze audio for viseme detection
        // Update blendshape weights
        faceRenderer.SetBlendShapeWeight(visemeA, weightA * 100f);
        // ... other visemes
    }
}
```

## VR Theater Mode (Stretch Goal)

### Features

- Virtual Plex theater environment
- Large screen for media playback
- 3D-Janet positioned as "controller"
- Gesture-based playback control
- Immersive audio (spatial)

### Setup

1. Create theater environment in Unity/Unreal
2. Add PlexTheaterController component
3. Connect to Plex via Janet Mesh server
4. Stream video to virtual screen
5. Enable gesture recognition for playback control

## Performance Considerations

### Latency Target

- Audio latency: <100ms (end-to-end)
- Animation update: 60 FPS minimum
- WebRTC streaming: <50ms network latency

### Optimization

- Use LOD (Level of Detail) for Janet model
- Optimize blendshape count
- Cache animation clips
- Use object pooling for audio buffers

## Troubleshooting

### No Audio Output

- Check WebRTC connection status
- Verify audio source component
- Check server logs for errors

### Lip-Sync Not Working

- Verify viseme blendshapes are correctly mapped
- Check audio analysis is running
- Ensure blendshape weights are updating

### Model Not Animating

- Verify Animator component is attached
- Check animation clips are assigned
- Ensure animation state machine is configured

## Future Enhancements

- Hand tracking for gesture-based interaction
- Spatial audio for immersive experience
- Haptic feedback integration
- Multi-user VR sessions
- Custom VR environment editor
- Full body tracking (if available)
