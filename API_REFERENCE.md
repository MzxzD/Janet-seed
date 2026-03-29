# Janet API Server - API Reference

**OpenAI-Compatible HTTP API for Janet Constitutional AI**

This document provides detailed technical documentation for the Janet API Server, which provides IDE integration through an OpenAI-compatible HTTP API.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Request/Response Formats](#requestresponse-formats)
5. [Error Handling](#error-handling)
6. [Streaming](#streaming)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## Overview

### Base URL

```
http://localhost:8080
```

Default port is 8080, configurable via `JANET_API_PORT` environment variable.

### API Version

Current version: `v1`

All endpoints are prefixed with `/v1/` for versioning.

### Compatibility

The API implements the OpenAI Chat Completions API specification, making it compatible with:
- Continue.dev
- Any OpenAI-compatible client
- Custom integrations

---

## Authentication

### API Key Authentication

All requests (except root and health) require authentication via Bearer token.

**Header:**
```
Authorization: Bearer <api_key>
```

**Default API Key:** `janet-local-dev`

**Custom API Key:**
```bash
JANET_API_KEY=your-custom-key python3 janet_api_server.py
```

**Disable Authentication:**
```bash
JANET_API_KEY=none python3 janet_api_server.py
```

### Example Request

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer janet-local-dev" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tinyllama:1.1b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## Endpoints

### Root Endpoint

**GET /**

Returns API information and status.

**Response:**
```json
{
  "name": "Janet API Server",
  "version": "1.0.0",
  "description": "OpenAI-compatible API for Janet Constitutional AI",
  "status": "online",
  "endpoints": {
    "chat": "/v1/chat/completions",
    "models": "/v1/models",
    "health": "/health"
  }
}
```

**Status Codes:**
- `200 OK` - Always returns 200

---

### Health Check

**GET /health**

Check if the API server and Janet brain are operational.

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "brain_available": true,
  "current_model": "tinyllama:1.1b",
  "available_models": ["tinyllama:1.1b", "llama3:8b"],
  "active_sessions": 0
}
```

**Status Codes:**
- `200 OK` - Server is healthy
- `503 Service Unavailable` - Janet brain not available

**Example:**
```bash
curl http://localhost:8080/health
```

---

### Status (HTTP + WebSocket hints)

**GET /api/status**

Home Assistant / dashboard friendly. Includes **`websocket_chat`** (full `ws://` or `wss://` URL derived from the request `Host` header) and **`websocket_paths`** (`/ws`, `/ws/chat`).

**Example:**
```bash
curl http://janet-1.local:8080/api/status
```

---

### WebSocket chat (same port as HTTP API)

**WebSocket** `ws://<host>:8080/ws` — alias: **`/ws/chat`**

Real-time chat on **the same server** as `/api/status` (port **8080**), distinct from the CallJanet-style WebSocket on **8765** if you run `simple_websocket_server.py` separately.

**Authentication:** None on the socket (LAN/trust boundary — do not expose raw to the public internet without TLS and auth).

**Message formats (JSON text frames):**

1. **OpenAI-style** — object with `model` and `messages` (same shape as `POST /v1/chat/completions` body). Response: JSON with `choices[0].message.content`.

2. **Legacy** — `{"type":"user_message","text":"Hello","context_window":[]}` — response: `{"type":"janet_response","text":"...","timestamp":"..."}`.

3. **`{"type":"ping"}`** — response: `{"type":"pong",...}`.

4. **`{"type":"models"}`** — list models when brain is up.

**Postman:** New → WebSocket → `ws://janet-1.local:8080/ws` → Connect → send a JSON message.

---

### List Models

**GET /v1/models**

List all available Ollama models that Janet can use.

**Authentication:** Required

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "tinyllama:1.1b",
      "object": "model",
      "created": 1677652288,
      "owned_by": "janet"
    },
    {
      "id": "llama3:8b",
      "object": "model",
      "created": 1677652288,
      "owned_by": "janet"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Models retrieved successfully
- `401 Unauthorized` - Invalid API key
- `503 Service Unavailable` - Janet brain not available

**Example:**
```bash
curl http://localhost:8080/v1/models \
  -H "Authorization: Bearer janet-local-dev"
```

---

### Chat Completions

**POST /v1/chat/completions**

Generate a response to a conversation using Janet's AI.

**Authentication:** Required

**Request Body:**
```json
{
  "model": "tinyllama:1.1b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | Yes | - | Ollama model to use (e.g., "tinyllama:1.1b") |
| `messages` | array | Yes | - | Array of message objects |
| `temperature` | float | No | 0.7 | Sampling temperature (0.0-2.0) |
| `max_tokens` | integer | No | 2000 | Maximum tokens to generate |
| `stream` | boolean | No | false | Enable streaming responses |
| `top_p` | float | No | 1.0 | Nucleus sampling parameter |
| `frequency_penalty` | float | No | 0.0 | Frequency penalty (-2.0 to 2.0) |
| `presence_penalty` | float | No | 0.0 | Presence penalty (-2.0 to 2.0) |

**Message Object:**
```json
{
  "role": "user|assistant|system",
  "content": "Message content"
}
```

**Non-Streaming Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "tinyllama:1.1b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

**Status Codes:**
- `200 OK` - Response generated successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Invalid API key
- `503 Service Unavailable` - Janet brain not available

**Example:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer janet-local-dev" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tinyllama:1.1b",
    "messages": [
      {"role": "user", "content": "Write a Python function to reverse a string"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

---

### Performance Stats (Janet-Specific)

**GET /v1/performance**

Get Janet brain performance statistics.

**Authentication:** Required

**Response:**
```json
{
  "current_model": "tinyllama:1.1b",
  "available_models": ["tinyllama:1.1b", "llama3:8b"],
  "model_performance": {
    "tinyllama:1.1b": {
      "model_name": "tinyllama:1.1b",
      "total_requests": 42,
      "total_tokens": 8400,
      "total_duration": 21.5,
      "average_latency": 0.512,
      "success_rate": 0.976,
      "failures": 1
    }
  },
  "cache_stats": {
    "size": 15,
    "hits": 8,
    "misses": 34,
    "hit_rate": 0.190
  },
  "conversation_active": true,
  "conversation_length": 6,
  "best_model_latency": "tinyllama:1.1b",
  "best_model_success": "llama3:8b"
}
```

**Status Codes:**
- `200 OK` - Stats retrieved successfully
- `401 Unauthorized` - Invalid API key
- `503 Service Unavailable` - Janet brain not available

**Example:**
```bash
curl http://localhost:8080/v1/performance \
  -H "Authorization: Bearer janet-local-dev"
```

---

### Red Thread (Janet-Specific)

**POST /v1/red-thread**

Activate Janet's Red Thread emergency stop protocol.

**Authentication:** Required

**Response:**
```json
{
  "status": "acknowledged",
  "message": "Red Thread protocol activated - all operations paused"
}
```

**Status Codes:**
- `200 OK` - Red Thread activated
- `401 Unauthorized` - Invalid API key

**Example:**
```bash
curl -X POST http://localhost:8080/v1/red-thread \
  -H "Authorization: Bearer janet-local-dev"
```

---

## Request/Response Formats

### Message Roles

| Role | Description | Example |
|------|-------------|---------|
| `system` | System instructions for the model | "You are a helpful coding assistant." |
| `user` | User's input/question | "How do I reverse a string in Python?" |
| `assistant` | Model's previous responses | "You can use string slicing: `s[::-1]`" |

### Finish Reasons

| Reason | Description |
|--------|-------------|
| `stop` | Model completed the response naturally |
| `length` | Response truncated due to max_tokens limit |
| `error` | An error occurred during generation |

### Temperature Guidelines

| Temperature | Behavior | Use Case |
|-------------|----------|----------|
| 0.0 - 0.3 | Deterministic, focused | Code generation, factual answers |
| 0.4 - 0.7 | Balanced | General conversation, explanations |
| 0.8 - 1.0 | Creative | Brainstorming, creative writing |
| 1.1 - 2.0 | Very creative | Experimental, highly varied outputs |

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "message": "Error description",
    "type": "error_type",
    "code": "error_code"
  }
}
```

### Common Errors

| Status Code | Error Type | Description | Solution |
|-------------|------------|-------------|----------|
| 400 | `invalid_request` | Malformed request | Check request format |
| 401 | `authentication_error` | Invalid API key | Verify API key |
| 404 | `not_found` | Endpoint not found | Check URL |
| 503 | `service_unavailable` | Janet brain offline | Check Ollama, restart server |
| 500 | `internal_error` | Server error | Check server logs |

### Example Error Response

```json
{
  "error": {
    "message": "Model 'invalid-model' not found",
    "type": "invalid_request",
    "code": "model_not_found"
  }
}
```

---

## Streaming

### Enabling Streaming

Set `stream: true` in the request:

```json
{
  "model": "tinyllama:1.1b",
  "messages": [{"role": "user", "content": "Count to 10"}],
  "stream": true
}
```

### Streaming Response Format

Server-Sent Events (SSE) format:

```
data: {"id":"chatcmpl-abc","object":"chat.completion.chunk","created":1677652288,"model":"tinyllama:1.1b","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc","object":"chat.completion.chunk","created":1677652288,"model":"tinyllama:1.1b","choices":[{"index":0,"delta":{"content":" world"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc","object":"chat.completion.chunk","created":1677652288,"model":"tinyllama:1.1b","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

### Streaming Example (Python)

```python
import requests
import json

url = "http://localhost:8080/v1/chat/completions"
headers = {
    "Authorization": "Bearer janet-local-dev",
    "Content-Type": "application/json"
}
data = {
    "model": "tinyllama:1.1b",
    "messages": [{"role": "user", "content": "Write a haiku"}],
    "stream": True
}

response = requests.post(url, headers=headers, json=data, stream=True)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data_str = line_str[6:]  # Remove 'data: ' prefix
            if data_str == '[DONE]':
                break
            chunk = json.loads(data_str)
            content = chunk['choices'][0]['delta'].get('content', '')
            print(content, end='', flush=True)
```

### Streaming Example (curl)

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer janet-local-dev" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tinyllama:1.1b",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }' \
  --no-buffer
```

---

## Rate Limiting

Currently, no rate limiting is enforced. For production use, consider:

1. **Request queuing** - Built into JanetBrain
2. **Max concurrent requests** - Configure in performance settings
3. **External rate limiter** - Use nginx or similar

---

## Examples

### Example 1: Simple Question

**Request:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer janet-local-dev" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tinyllama:1.1b",
    "messages": [
      {"role": "user", "content": "What is a closure in JavaScript?"}
    ]
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-xyz789",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "tinyllama:1.1b",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "A closure in JavaScript is a function that has access to variables in its outer (enclosing) function's scope, even after the outer function has returned..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 85,
    "total_tokens": 100
  }
}
```

### Example 2: Code Generation

**Request:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer janet-local-dev" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "messages": [
      {
        "role": "system",
        "content": "You are an expert Python programmer."
      },
      {
        "role": "user",
        "content": "Write a function to find the longest palindrome in a string."
      }
    ],
    "temperature": 0.3,
    "max_tokens": 500
  }'
```

### Example 3: Conversation with Context

**Request:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer janet-local-dev" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "messages": [
      {"role": "user", "content": "What is recursion?"},
      {"role": "assistant", "content": "Recursion is when a function calls itself..."},
      {"role": "user", "content": "Can you show me an example in Python?"}
    ]
  }'
```

### Example 4: Streaming Response (JavaScript)

```javascript
const response = await fetch('http://localhost:8080/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer janet-local-dev',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'tinyllama:1.1b',
    messages: [{role: 'user', content: 'Write a poem about coding'}],
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      if (data === '[DONE]') break;
      
      const parsed = JSON.parse(data);
      const content = parsed.choices[0].delta.content;
      if (content) {
        process.stdout.write(content);
      }
    }
  }
}
```

---

## Integration Examples

### Continue.dev Configuration

```yaml
models:
  - name: Janet
    provider: openai
    model: tinyllama:1.1b
    apiBase: http://localhost:8080/v1
    apiKey: janet-local-dev
```

### Python Client

```python
import openai

openai.api_base = "http://localhost:8080/v1"
openai.api_key = "janet-local-dev"

response = openai.ChatCompletion.create(
    model="tinyllama:1.1b",
    messages=[
        {"role": "user", "content": "Hello, Janet!"}
    ]
)

print(response.choices[0].message.content)
```

### Node.js Client

```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  baseURL: 'http://localhost:8080/v1',
  apiKey: 'janet-local-dev'
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'tinyllama:1.1b',
    messages: [{role: 'user', content: 'Hello, Janet!'}]
  });
  
  console.log(response.choices[0].message.content);
}

chat();
```

---

## Performance Optimization

### Model Selection

Choose the right model for the task:

```python
# Fast autocomplete
{"model": "tinyllama:1.1b", "max_tokens": 50}

# Balanced coding
{"model": "llama3:8b", "max_tokens": 500}

# Complex reasoning
{"model": "llama3:70b", "max_tokens": 2000}
```

### Caching

Janet automatically caches responses. To bypass cache:

```python
# Add unique context to prevent cache hits
{"messages": [
    {"role": "user", "content": f"Question: {question}"},
    {"role": "system", "content": f"timestamp: {time.time()}"}
]}
```

### Concurrent Requests

Janet handles concurrent requests efficiently:

```python
import asyncio
import aiohttp

async def make_request(session, prompt):
    async with session.post(
        'http://localhost:8080/v1/chat/completions',
        json={
            'model': 'tinyllama:1.1b',
            'messages': [{'role': 'user', 'content': prompt}]
        },
        headers={'Authorization': 'Bearer janet-local-dev'}
    ) as response:
        return await response.json()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [
            make_request(session, f"Question {i}")
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)
        return results
```

---

## Monitoring and Debugging

### Check Server Logs

Server logs show all requests and responses:

```bash
# Start server with verbose logging
python3 janet_api_server.py
```

### Performance Monitoring

```bash
# Get performance stats
curl http://localhost:8080/v1/performance \
  -H "Authorization: Bearer janet-local-dev" | jq
```

### Health Monitoring

```bash
# Continuous health check
watch -n 5 'curl -s http://localhost:8080/health | jq'
```

---

## Security Considerations

1. **API Key Protection**
   - Use strong API keys in production
   - Rotate keys regularly
   - Never commit keys to version control

2. **Network Security**
   - Bind to localhost for local use only
   - Use firewall rules for remote access
   - Consider HTTPS for remote deployments

3. **Input Validation**
   - API validates all inputs
   - Max token limits prevent abuse
   - Rate limiting recommended for production

4. **Constitutional AI**
   - Janet follows 20 axioms
   - Privacy-first design
   - No external data transmission

---

## Support and Resources

- **Setup Guide:** See `JANET_IDE_SETUP.md`
- **Source Code:** `janet_api_server.py`
- **Test Suite:** `test_janet_api.py`
- **Configuration:** `~/.continue/config.yaml`

---

**API Version:** 1.0.0  
**Last Updated:** 2026-03-02  
**Compatibility:** OpenAI Chat Completions API v1
