# Plex Media Server Integration

Grant Janet the ability to browse local Plex library, query metadata, and control playback on devices via voice—offline-first, respecting privacy.

## Overview

The Plex integration enables Janet to interact with your local Plex Media Server:
- Search library for movies, shows, music
- Get recommendations based on watch history (with consent)
- Control playback on Plex clients (TV, speakers, etc.)
- Query library statistics (unwatched episodes, recent additions)

## Architecture

```
iOS/Android Client
    ↕️ WebSocket
Janet Mesh Server
    ↕️ Plex Bridge
Plex Handler (Delegation)
    ↕️ plexapi
Plex Media Server
```

## Components

### Plex Handler (`janet-seed/src/delegation/handlers/plex_handler.py`)

Delegation handler that provides:
- `search_media`: Find movies/shows by title, genre, actor
- `get_recommendations`: Suggest based on watch history (with consent)
- `control_playback`: Play/pause/stop on Plex clients
- `fetch_library_stats`: Count unwatched episodes, recent additions

### Plex Wizard (`janet-seed/src/expansion/wizards/plex_wizard.py`)

Guided setup wizard that:
- Discovers Plex servers on local network
- Guides through token authentication
- Configures client device pairing
- Sets up privacy consent for watch history

### Plex Bridge (`server/core/plex_bridge.py`)

WebSocket-to-Plex bridge service that:
- Routes playback commands from mesh clients
- Handles media search requests
- Provides library statistics
- Manages connection to Plex server

## Setup

### 1. Prerequisites

- Local Plex Media Server running
- Plex server accessible on local network
- Plex authentication token

### 2. Get Plex Token

**Option A: From Plex Web**
1. Visit https://www.plex.tv/desktop
2. Sign in to your Plex account
3. Go to: Account → Settings → Network
4. Find your "Manual Port" or check Plex server's XML API token

**Option B: From Plex Server**
1. Log into Plex server web interface
2. Settings → Network → Manual Port
3. Check for API token in server logs or config

### 3. Run Plex Wizard

The Plex integration is discovered as an expansion opportunity:

1. Janet detects Plex integration is available
2. Suggests expansion: "Plex Media Server integration available. Would you like to set it up?"
3. User consents → Wizard launches
4. Follow wizard prompts:
   - Enter Plex server URL (e.g., `http://192.168.1.100:32400`)
   - Enter Plex token
   - Choose privacy settings (watch history tracking)
5. Wizard verifies connection
6. Configuration saved to `config/plex_config.json`

### 4. Manual Configuration

If wizard fails, configure manually:

```json
{
  "plex_server_url": "http://192.168.1.100:32400",
  "plex_token": "your-plex-token-here",
  "allow_history_tracking": false
}
```

Save to: `janet-seed/config/plex_config.json`

## Usage

### Search Media

**Via Voice/Text**:
- "Search for Blade Runner in Plex"
- "Find action movies in my library"
- "What TV shows do I have?"

**WebSocket Message**:
```json
{
  "type": "plex_search",
  "query": "Blade Runner",
  "type": "movie",
  "limit": 10
}
```

**Response**:
```json
{
  "type": "plex_search_result",
  "success": true,
  "results": [
    {
      "type": "movie",
      "title": "Blade Runner",
      "year": 1982,
      "rating": 8.1,
      "summary": "...",
      "thumb": "url"
    }
  ],
  "count": 1
}
```

### Control Playback

**Via Voice/Text**:
- "Play Blade Runner on living room TV"
- "Pause playback"
- "Stop the movie"

**WebSocket Message**:
```json
{
  "type": "plex_command",
  "command": "play",
  "title": "Blade Runner",
  "client": "Living Room TV"
}
```

**Response**:
```json
{
  "type": "plex_result",
  "success": true,
  "message": "Playing 'Blade Runner' on Living Room TV",
  "output_data": {
    "action": "play",
    "media": "Blade Runner",
    "client": "Living Room TV"
  }
}
```

### Get Recommendations

**Via Voice/Text**:
- "What should I watch next?"
- "Recommend something based on what I've watched"
- "Suggest a movie"

**Requirements**:
- Watch history tracking must be enabled (with consent)
- Requires explicit consent for privacy

### Library Statistics

**Via Voice/Text**:
- "How many unwatched episodes do I have?"
- "What's in my Plex library?"
- "Show me recent additions"

**Response**:
```json
{
  "stats": {
    "movies": {
      "total": 150,
      "unwatched": 23
    },
    "shows": {
      "total": 45,
      "unwatched_episodes": 127
    },
    "recent_additions": [
      {
        "title": "New Movie",
        "type": "movie",
        "addedAt": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

## Privacy Protocol

### Watch History Tracking

- **Default**: Disabled (ephemeral queries only)
- **With Consent**: Enabled → Green Vault storage (safe summaries only)
- **Never Stored**: Raw watch history, detailed playback data
- **Respects Axiom 9**: Consent-based memory storage

### Media Preferences

- **Stored**: Safe summaries in Green Vault (with consent)
- **Not Stored**: Detailed watch history, playback positions
- **Never**: Red/Blue Vault storage for media data

### Ephemeral Queries

By default, all Plex queries are ephemeral:
- Search results not stored
- Playback commands not logged
- Library stats not cached

Only with explicit Operator consent are safe summaries stored in Green Vault.

## Delegation Integration

The Plex handler is registered in `delegation_manager.py`:

```python
plex_handler = PlexDelegationHandler(
    plex_server_url=url,
    plex_token=token,
    allow_history_tracking=False  # Default: require explicit consent
)
delegation_manager.register_handler(plex_handler)
```

### Capability

The handler provides `MEDIA_CONTROL` capability:
- Added to `HandlerCapability` enum
- Routes media-related requests to Plex handler
- Integrates with Janet's delegation system

## Expansion Detection

The Plex integration is detected as an expansion opportunity:

```python
ExpansionType.PLEX_INTEGRATION
```

**Detected When**:
- Network is available (for Plex server discovery)
- `plexapi` library is available (or can be installed)

**Suggested Benefits**:
- Browse library via voice/text
- Control playback on Plex clients
- Get recommendations (with consent)
- Query library statistics

## Error Handling

### Common Issues

**Connection Failed**:
- Verify Plex server URL and port
- Check network connectivity
- Verify Plex server is running

**Authentication Failed**:
- Verify Plex token is correct
- Check token hasn't expired
- Regenerate token if needed

**No Clients Available**:
- Ensure Plex clients are on and connected
- Check client names match exactly
- List available clients via library stats

## Configuration File

Location: `janet-seed/config/plex_config.json`

```json
{
  "plex_server_url": "http://192.168.1.100:32400",
  "plex_token": "your-token-here",
  "allow_history_tracking": false,
  "configured_at": "2024-01-15T10:00:00Z"
}
```

## Integration with VR (Stretch Goal)

The Plex integration can be extended for VR Theater mode:

1. VR client requests media playback
2. Janet processes via Plex handler
3. Video streams to virtual theater screen
4. 3D-Janet controls playback via gestures
5. Immersive movie watching experience

## Future Enhancements

- Support for music libraries
- Photo library browsing
- Playlist management
- Multi-server support
- Cloud Plex server support (with privacy considerations)
- Advanced recommendation engine
