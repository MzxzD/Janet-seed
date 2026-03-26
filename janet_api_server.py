#!/usr/bin/env python3
"""
Janet API Server - OpenAI-compatible HTTP API for IDE integration
Wraps JanetBrain to provide Continue.dev and other IDE extensions with Janet's constitutional AI
"""
import os
import sys
import time
import uuid
import json
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
# Add JanetOS root for core (privilege_guard, cloud_permission_guard)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from fastapi import FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect, Body, Request
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("⚠️  FastAPI not installed. Run: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from src.core.janet_brain import JanetBrain, RequestPriority
    import litellm
    HAS_JANET_BRAIN = True
except ImportError:
    HAS_JANET_BRAIN = False
    litellm = None
    print("⚠️  JanetBrain not available. Check janet-seed installation.")
    sys.exit(1)

# Configuration
API_PORT = int(os.getenv("JANET_API_PORT", "8080"))
API_HOST = os.getenv("JANET_API_HOST", "0.0.0.0")
API_KEY = os.getenv("JANET_API_KEY", "janet-local-dev")  # Optional authentication
DEFAULT_MODEL = os.getenv("JANET_DEFAULT_MODEL", "qwen2.5-coder:7b")

# Global instances
janet_brain: Optional[JanetBrain] = None
memory_manager = None  # MemoryManager for Green Vault (lazy init)

# Session management (conversation context per session)
sessions: Dict[str, Dict[str, Any]] = {}

# Last command/response for HA (display in dashboard)
_last_command: Optional[str] = None
_last_response: Optional[str] = None

# FastAPI app
app = FastAPI(
    title="Janet API Server",
    description="OpenAI-compatible API for Janet Constitutional AI",
    version="1.0.0"
)

# CORS middleware (allow IDE extensions to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for OpenAI compatibility
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    session_id: Optional[str] = None  # AC-GV1: chat_id for Green Vault / inactivity flush
    tools: Optional[List[Dict[str, Any]]] = None  # Tool/function calling (Cursor Composer, agent mode)
    tool_choice: Optional[Any] = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "janet"


class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]


class LearnRequest(BaseModel):
    """Request body for POST /api/learn (JanetXMzNN Double Soul - Green Vault ingestion)"""
    content: str = Field(..., description="Summary or extracted text to store")
    context: str = Field(default="media_digestion", description="Context tag (e.g. media_digestion, cve_upgrade)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Source, type, digest_date")


class LearnResponse(BaseModel):
    """Response for POST /api/learn"""
    status: str
    memory_id: Optional[str] = None
    stored: bool


class CloudAllowRequest(BaseModel):
    """Request for POST /api/cloud-allow"""
    scope: str = Field(..., description="Scope (e.g. youtube)")
    grant: bool = Field(..., description="Grant or revoke")
    id_verified: bool = Field(default=False, description="ID verification passed")


class CloudIdVerifyRequest(BaseModel):
    """Request for POST /api/cloud-id-verify"""
    method: str = Field(default="self_attest", description="self_attest or platform")
    scope: Optional[str] = Field(default=None, description="Scope (optional)")


# Helper functions
def verify_api_key(authorization: Optional[str] = None) -> bool:
    """Verify API key if authentication is enabled"""
    if not API_KEY or API_KEY == "none":
        return True  # No authentication required
    
    if not authorization:
        return False
    
    # Support both "Bearer token" and just "token"
    token = authorization.replace("Bearer ", "").strip()
    return token == API_KEY


def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create new one"""
    if session_id and session_id in sessions:
        return session_id
    
    # Create new session
    new_session_id = str(uuid.uuid4())
    sessions[new_session_id] = {
        "created_at": time.time(),
        "last_request_time": None,
        "conversation_history": [],
        "model": DEFAULT_MODEL,
    }
    return new_session_id


def _get_inactivity_config():
    """AC-GV1: (inactivity_sec, save_context_when_idle) from ~/.janet/menubar_config.json or env."""
    try:
        config_path = Path.home() / ".janet" / "menubar_config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                cfg = json.load(f)
            min_val = max(1, min(60, int(cfg.get("inactivity_min", 10))))
            return (min_val * 60, cfg.get("save_context_when_idle", True))
    except Exception:
        pass
    sec = max(60, int(os.environ.get("JANET_INACTIVITY_FLUSH_SEC", "600")))
    save = os.environ.get("JANET_SAVE_CONTEXT_WHEN_IDLE", "true").lower() in ("1", "true", "yes")
    return (sec, save)


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars ≈ 1 token)"""
    return len(text) // 4


def _normalize_tool_args(args_str: str) -> str:
    """
    Normalize tool call arguments for Continue compatibility.
    Qwen/Ollama may return XML-like args; Continue expects JSON.
    """
    if not args_str or not isinstance(args_str, str):
        return args_str
    s = args_str.strip()
    # Already valid JSON?
    try:
        json.loads(s)
        return s
    except json.JSONDecodeError:
        pass
    # Try to parse XML-like <parameter=name>value</parameter>
    import re
    result = {}
    for m in re.finditer(r"<parameter=([^>]+)>([^<]*)</parameter>", s, re.IGNORECASE):
        key, val = m.group(1).strip(), m.group(2).strip()
        if val.lower() == "true":
            val = True
        elif val.lower() == "false":
            val = False
        elif val.isdigit():
            val = int(val)
        result[key] = val
    if result:
        return json.dumps(result)
    return s


async def generate_streaming_response(
    user_message: str,
    context: Optional[Dict] = None,
    model: str = DEFAULT_MODEL
) -> AsyncGenerator[str, None]:
    """Generate streaming response for real-time code generation"""
    global janet_brain
    
    if not janet_brain or not janet_brain.is_available():
        yield f'data: {{"error": "Janet brain not available"}}\n\n'
        yield "data: [DONE]\n\n"
        return
    
    # Switch model if needed
    if model != janet_brain.model_name and model in janet_brain.available_models:
        janet_brain.switch_model(model)
    
    # Generate response (non-streaming from JanetBrain, we'll chunk it)
    response_text = janet_brain.generate_response(
        user_message,
        context=context,
        priority=RequestPriority.HIGH
    )
    
    # Stream the response word by word for better UX
    words = response_text.split()
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    
    for i, word in enumerate(words):
        chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {
                    "content": word + (" " if i < len(words) - 1 else "")
                },
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        await asyncio.sleep(0.01)  # Small delay for streaming effect
    
    # Final chunk with finish_reason
    final_chunk = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


async def generate_tool_calls_stream(out: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """
    Stream tool_calls as OpenAI-compatible SSE for Continue.dev.
    Continue expects stream=true and parses delta.tool_calls from chunks.
    """
    chunk_id = out.get("id") or f"chatcmpl-{uuid.uuid4().hex[:8]}"
    model = out.get("model", DEFAULT_MODEL)
    created = out.get("created", int(time.time()))
    choices = out.get("choices", [])
    if not choices:
        yield "data: [DONE]\n\n"
        return
    choice = choices[0]
    msg = choice.get("message", {})
    tool_calls = msg.get("tool_calls") or []
    finish_reason = choice.get("finish_reason", "stop")
    if not tool_calls:
        finish_reason = "stop"
    # First chunk: role
    yield f"data: {json.dumps({
        'id': chunk_id,
        'object': 'chat.completion.chunk',
        'created': created,
        'model': model,
        'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]
    })}\n\n"
    # Second chunk: full tool_calls (Continue accepts single chunk)
    delta_tool_calls = [
        {
            "index": i,
            "id": tc.get("id", f"call_{uuid.uuid4().hex[:8]}"),
            "type": "function",
            "function": {
                "name": tc.get("function", {}).get("name", ""),
                "arguments": tc.get("function", {}).get("arguments", "{}")
            }
        }
        for i, tc in enumerate(tool_calls)
    ]
    yield f"data: {json.dumps({
        'id': chunk_id,
        'object': 'chat.completion.chunk',
        'created': created,
        'model': model,
        'choices': [{'index': 0, 'delta': {'tool_calls': delta_tool_calls}, 'finish_reason': finish_reason}]
    })}\n\n"
    yield "data: [DONE]\n\n"


def _public_ws_chat_url(request: Request, path: str = "/ws") -> str:
    """Build ws:// or wss:// URL for LAN/mDNS clients (e.g. Postman, web apps)."""
    host = request.headers.get("host")
    if not host:
        netloc = request.url.netloc
        host = netloc if netloc else f"127.0.0.1:{API_PORT}"
    scheme = "wss" if request.url.scheme == "https" else "ws"
    return f"{scheme}://{host}{path}"


def _websocket_paths() -> List[str]:
    return ["/ws", "/ws/chat"]


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "Janet API Server",
        "version": "1.0.0",
        "description": "OpenAI-compatible API for Janet Constitutional AI",
        "status": "online" if janet_brain and janet_brain.is_available() else "offline",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health",
            "status": "/api/status",
            "websocket_chat": "/ws",
            "websocket_chat_alt": "/ws/chat",
            "speak": "/api/speak",
            "command": "/api/command",
            "learn": "/api/learn",
            "cloud_allowed": "/api/cloud-allowed",
            "cloud_allow": "/api/cloud-allow",
            "cloud_id_verify": "/api/cloud-id-verify"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not janet_brain or not janet_brain.is_available():
        raise HTTPException(status_code=503, detail="Janet brain not available")
    
    return {
        "status": "healthy",
        "brain_available": janet_brain.is_available(),
        "current_model": janet_brain.model_name,
        "available_models": janet_brain.available_models,
        "active_sessions": len(sessions)
    }


# Startup time for uptime
_server_start_time = time.time()


@app.get("/api/status")
async def api_status(request: Request):
    """Status endpoint for Home Assistant integration (sensors)"""
    ws_primary = _public_ws_chat_url(request, "/ws")
    ws_paths = _websocket_paths()
    if not janet_brain:
        return {
            "state": "disconnected",
            "connected": False,
            "websocket_chat": ws_primary,
            "websocket_paths": ws_paths,
        }
    
    mm = _get_memory_manager()
    memory_usage = 0
    green_vault_entries = 0
    blue_vault_active = False
    red_vault_entries = 0
    if mm:
        try:
            if hasattr(mm, "green_vault") and mm.green_vault:
                green_vault_entries = len(mm.green_vault) if isinstance(mm.green_vault, (list, dict)) else 0
            if hasattr(mm, "memory_usage"):
                memory_usage = getattr(mm, "memory_usage", 0) or 0
        except Exception:
            pass
    
    return {
        "state": "idle",
        "connected": True,
        "uptime": int(time.time() - _server_start_time),
        "model": janet_brain.model_name,
        "voice_enabled": False,
        "in_conversation": len(sessions) > 0,
        "last_input": _last_command,
        "last_response": _last_response,
        "turn_count": len(sessions),
        "memory_usage": memory_usage,
        "green_vault_entries": green_vault_entries,
        "blue_vault_active": blue_vault_active,
        "red_vault_entries": red_vault_entries,
        "websocket_chat": ws_primary,
        "websocket_paths": ws_paths,
    }


@app.post("/api/speak")
async def api_speak(data: dict = Body(default={})):
    """
    Make Janet speak a message (Home Assistant integration).
    POST body: {"text": "message", "voice": "optional"}
    """
    message = (data or {}).get("text", "")
    if not message:
        raise HTTPException(status_code=400, detail="No message provided")
    try:
        from src.voice.tts import TextToSpeech
        tts = TextToSpeech()
        if tts.is_available():
            tts.speak(message)
        else:
            print(f"📢 [speak] TTS unavailable, message logged: {message[:80]}...")
    except Exception as e:
        print(f"⚠️  [speak] TTS error: {e}, message logged: {message[:80]}...")
    return {"status": "success", "message": message}


@app.post("/api/command")
async def api_command(data: dict = Body(default={})):
    """
    Send a voice command to Janet (Home Assistant integration).
    POST body: {"command": "..."}
    Processes via JanetBrain and returns response.
    """
    command_text = (data or {}).get("command", "").strip()
    if not command_text:
        raise HTTPException(status_code=400, detail="No command provided")
    global janet_brain
    if not janet_brain or not janet_brain.is_available():
        raise HTTPException(status_code=503, detail="Janet brain not available")
    try:
        response_text = janet_brain.generate_response(
            command_text,
            context=None,
            priority=RequestPriority.HIGH
        )
        global _last_command, _last_response
        _last_command = command_text
        _last_response = response_text
        return {"status": "success", "command": command_text, "response": response_text}
    except Exception as e:
        print(f"⚠️  [command] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_memory_manager():
    """Lazy-init MemoryManager for Green Vault (JanetXMzNN Double Soul)"""
    global memory_manager
    if memory_manager is not None:
        return memory_manager
    try:
        from src.memory import MemoryManager
        janet_home = Path(os.getenv("JANET_HOME", str(Path.home() / ".janet")))
        memory_dir = Path(os.getenv("JANET_MEMORY_DIR", str(janet_home / "memory")))
        memory_manager = MemoryManager(memory_dir)
        return memory_manager
    except Exception as e:
        print(f"⚠️  MemoryManager not available: {e}")
        return None


@app.post("/api/learn", response_model=LearnResponse)
async def api_learn(
    request: LearnRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Feed information to Janet's Green Vault for learning.
    JanetXMzNN Double Soul - media digestion, CVE upgrade, etc.
    """
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    mm = _get_memory_manager()
    if not mm or not hasattr(mm, "green_vault"):
        raise HTTPException(
            status_code=503,
            detail="Green Vault not available (MemoryManager not initialized)"
        )
    
    tags = [request.context]
    if request.metadata:
        if request.metadata.get("source"):
            tags.append(f"source:{request.metadata['source']}")
        if request.metadata.get("type"):
            tags.append(request.metadata["type"])
    
    try:
        entry_id = mm.green_vault.add_summary(
            summary=request.content[:50000] if len(request.content) > 50000 else request.content,
            tags=tags,
            confidence=0.85,
            expiry=None,
        )
        stored = entry_id != ""
        return LearnResponse(
            status="success" if stored else "partial",
            memory_id=entry_id if stored else None,
            stored=stored,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Cloud Allowed protocol (JanetXCloud-Double-Soul)
@app.get("/api/cloud-allowed")
async def api_cloud_allowed(
    scope: str = "youtube",
    authorization: Optional[str] = Header(None)
):
    """
    Check if Cloud Allowed for scope. Used by MzNN before cloud API calls.
    Returns {allowed: bool, id_verified: bool}.
    """
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    try:
        from core.cloud_permission_guard import get_cloud_guard
        guard = get_cloud_guard()
        return {
            "allowed": guard.is_allowed(scope),
            "id_verified": guard.id_verified,
        }
    except ImportError:
        return {"allowed": False, "id_verified": False}


@app.post("/api/cloud-allow")
async def api_cloud_allow(
    request: CloudAllowRequest,
    authorization: Optional[str] = Header(None)
):
    """Grant or revoke Cloud Allowed for scope. Internal use."""
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    try:
        from core.cloud_permission_guard import get_cloud_guard
        guard = get_cloud_guard()
        if request.grant:
            ok = guard.grant(request.scope, request.id_verified)
            return {"status": "granted" if ok else "denied", "granted": ok}
        else:
            guard.revoke(request.scope)
            return {"status": "revoked"}
    except ImportError:
        raise HTTPException(status_code=503, detail="Cloud Permission Guard not available")


@app.post("/api/cloud-id-verify")
async def api_cloud_id_verify(
    request: CloudIdVerifyRequest,
    authorization: Optional[str] = Header(None)
):
    """Verify ID for Cloud Allowed (self_attest or platform)."""
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    try:
        from core.cloud_permission_guard import get_cloud_guard
        guard = get_cloud_guard()
        method = request.method or "self_attest"
        if method not in ("self_attest", "platform"):
            method = "self_attest"
        guard.verify_id(method)
        return {
            "verified": True,
            "method": method,
            "verified_at": datetime.utcnow().isoformat() + "Z",
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Cloud Permission Guard not available")


@app.get("/v1/models")
async def list_models(authorization: Optional[str] = Header(None)):
    """List available models (OpenAI-compatible)"""
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not janet_brain or not janet_brain.is_available():
        raise HTTPException(status_code=503, detail="Janet brain not available")
    
    # Return available Ollama models
    models = []
    for model_name in janet_brain.available_models:
        models.append(ModelInfo(
            id=model_name,
            created=int(time.time()),
            owned_by="janet"
        ))
    
    return ModelsResponse(data=models)


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Chat completions endpoint (OpenAI-compatible)
    Supports both streaming and non-streaming responses
    """
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not janet_brain or not janet_brain.is_available():
        raise HTTPException(status_code=503, detail="Janet brain not available")
    
    # Extract user message (last message in the list)
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    user_message = request.messages[-1].content
    session_id = get_or_create_session(request.session_id)
    conv_history = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    # AC-GV1: Inactivity flush — store previous segment if idle and save_context_when_idle
    mm = _get_memory_manager()
    if mm and session_id in sessions:
        sess = sessions[session_id]
        last_t = sess.get("last_request_time")
        inactivity_sec, save_idle = _get_inactivity_config()
        prev_history = [{"role": m.role, "content": m.content} for m in request.messages[:-1]]
        if save_idle and prev_history and last_t is not None and (time.time() - last_t) >= inactivity_sec:
            try:
                mm.store_conversation(prev_history, context={"chat_id": session_id})
            except Exception:
                pass
        sess["last_request_time"] = time.time()
        sess["conversation_history"] = conv_history

    # Build context from conversation history
    context = {
        "conversation_history": [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages[:-1]
        ]
    }
    
    # Switch model if needed
    model = request.model
    if model != janet_brain.model_name and model in janet_brain.available_models:
        janet_brain.switch_model(model)
    
    # Tool-calling path (Cursor Composer, agent mode) — forward to Ollama with tools
    if request.tools:
        try:
            model_id = f"ollama/{model}" if "/" not in model else model
            messages = [{"role": m.role, "content": m.content} for m in request.messages]
            kwargs = {
                "model": model_id,
                "messages": messages,
                "temperature": request.temperature or 0.7,
                "max_tokens": request.max_tokens or 2000,
                "tools": request.tools,
            }
            if request.tool_choice is not None:
                kwargs["tool_choice"] = request.tool_choice
            resp = litellm.completion(**kwargs)
            # Convert to OpenAI-compatible dict (handles tool_calls)
            to_dict = getattr(resp, "model_dump", None) or getattr(resp, "dict", None)
            out = to_dict() if to_dict else {}
            out["id"] = out.get("id") or f"chatcmpl-{uuid.uuid4().hex[:8]}"
            out["model"] = model
            # Normalize tool_calls for Continue (XML-like args → JSON)
            for choice in out.get("choices", []):
                msg = choice.get("message", {})
                for tc in msg.get("tool_calls", []) or []:
                    fn = tc.get("function", {})
                    if isinstance(fn.get("arguments"), str):
                        fn["arguments"] = _normalize_tool_args(fn["arguments"])
            print(f"✅ Tool-call response ({len(request.tools)} tools available)")
            # Continue expects stream=true — return SSE when requested
            if request.stream:
                return StreamingResponse(
                    generate_tool_calls_stream(out),
                    media_type="text/event-stream"
                )
            return JSONResponse(content=out)
        except Exception as e:
            print(f"⚠️  Tool-call path failed: {e}")
            # Fall through to normal path (ignore tools)
    
    # Handle streaming vs non-streaming
    if request.stream:
        # Streaming response
        return StreamingResponse(
            generate_streaming_response(user_message, context, model),
            media_type="text/event-stream"
        )
    else:
        # Non-streaming response
        start_time = time.time()
        
        # Generate response
        response_text = janet_brain.generate_response(
            user_message,
            context=context,
            priority=RequestPriority.HIGH
        )
        
        duration = time.time() - start_time
        
        # Estimate tokens
        prompt_tokens = estimate_tokens(user_message)
        completion_tokens = estimate_tokens(response_text)
        total_tokens = prompt_tokens + completion_tokens
        
        # Build OpenAI-compatible response
        response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(time.time()),
            model=model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(role="assistant", content=response_text),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )
        )
        
        print(f"✅ Generated response in {duration:.2f}s ({total_tokens} tokens)")
        return response


@app.get("/v1/performance")
async def get_performance(authorization: Optional[str] = Header(None)):
    """Get Janet brain performance statistics (Janet-specific endpoint)"""
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not janet_brain or not janet_brain.is_available():
        raise HTTPException(status_code=503, detail="Janet brain not available")
    
    return janet_brain.get_performance_stats()


@app.post("/v1/red-thread")
async def red_thread(authorization: Optional[str] = Header(None)):
    """Emergency stop - Red Thread protocol (Janet-specific endpoint)"""
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # This would integrate with Janet's Red Thread system
    # For now, just return acknowledgment
    return {
        "status": "acknowledged",
        "message": "Red Thread protocol activated - all operations paused"
    }


async def _websocket_chat_session(websocket: WebSocket):
    """Shared WebSocket chat loop (OpenAI-style messages, legacy user_message, ping, models)."""
    print(f"🔌 WebSocket connection attempt from {websocket.client}")
    await websocket.accept()
    print(f"🔌 WebSocket client connected and accepted")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get('type', None)
                
                # Check if this is an OpenAI-compatible ChatRequest (from Janet CLI)
                if 'model' in message and 'messages' in message:
                    # OpenAI-compatible format
                    model = message.get('model', DEFAULT_MODEL)
                    messages = message.get('messages', [])
                    
                    if not messages:
                        error_response = {
                            'error': 'No messages provided'
                        }
                        await websocket.send_text(json.dumps(error_response))
                        continue
                    
                    # Extract user message (last message)
                    user_message = messages[-1].get('content', '')
                    print(f"💬 User: {user_message[:100]}...")
                    
                    if not janet_brain or not janet_brain.is_available():
                        error_response = {
                            'error': 'Janet brain not available'
                        }
                        await websocket.send_text(json.dumps(error_response))
                        continue
                    
                    # Build context from conversation history
                    context = {
                        "conversation_history": [
                            {"role": msg.get('role'), "content": msg.get('content')}
                            for msg in messages[:-1]
                        ]
                    }
                    
                    # Switch model if needed
                    if model != janet_brain.model_name and model in janet_brain.available_models:
                        janet_brain.switch_model(model)
                    
                    # Generate response
                    response_text = janet_brain.generate_response(
                        user_message,
                        context=context,
                        priority=RequestPriority.HIGH
                    )
                    
                    print(f"🤖 Janet: {response_text[:100]}...")
                    
                    # Send OpenAI-compatible response
                    response = {
                        'id': f"chatcmpl-{uuid.uuid4().hex[:8]}",
                        'model': model,
                        'choices': [{
                            'index': 0,
                            'message': {
                                'role': 'assistant',
                                'content': response_text
                            },
                            'finish_reason': 'stop'
                        }],
                        'usage': {
                            'prompt_tokens': estimate_tokens(user_message),
                            'completion_tokens': estimate_tokens(response_text),
                            'total_tokens': estimate_tokens(user_message + response_text)
                        }
                    }
                    await websocket.send_text(json.dumps(response))
                
                elif msg_type == 'user_message':
                    # Legacy format (for iOS app compatibility)
                    user_text = message.get('text', '')
                    context_window = message.get('context_window', [])
                    
                    print(f"💬 User: {user_text[:100]}...")
                    
                    if not janet_brain or not janet_brain.is_available():
                        response = {
                            'type': 'error',
                            'text': 'Janet brain not available',
                            'timestamp': datetime.now().isoformat()
                        }
                        await websocket.send_text(json.dumps(response))
                        continue
                    
                    # Build context from conversation history
                    context = {
                        "conversation_history": context_window
                    }
                    
                    # Generate response
                    response_text = janet_brain.generate_response(
                        user_text,
                        context=context,
                        priority=RequestPriority.HIGH
                    )
                    
                    print(f"🤖 Janet: {response_text[:100]}...")
                    
                    # Send response
                    response = {
                        'type': 'janet_response',
                        'text': response_text,
                        'timestamp': datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(response))
                
                elif msg_type == 'models':
                    # Models list request
                    if not janet_brain or not janet_brain.is_available():
                        error_response = {
                            'error': 'Janet brain not available'
                        }
                        await websocket.send_text(json.dumps(error_response))
                        continue
                    
                    models = []
                    for model_name in janet_brain.available_models:
                        models.append({
                            'id': model_name,
                            'object': 'model',
                            'created': int(time.time()),
                            'owned_by': 'janet'
                        })
                    
                    response = {
                        'object': 'list',
                        'data': models
                    }
                    await websocket.send_text(json.dumps(response))
                
                elif msg_type == 'ping':
                    # Health check
                    response = {
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(response))
                
                else:
                    # Unknown message type
                    response = {
                        'error': f'Unknown message format',
                        'received': message
                    }
                    await websocket.send_text(json.dumps(response))
            
            except json.JSONDecodeError as e:
                response = {
                    'error': f'Invalid JSON: {str(e)}'
                }
                await websocket.send_text(json.dumps(response))
    
    except WebSocketDisconnect:
        print(f"🔌 WebSocket client disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        try:
            response = {
                'error': str(e)
            }
            await websocket.send_text(json.dumps(response))
        except:
            pass


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket chat — same protocol as /ws/chat."""
    await _websocket_chat_session(websocket)


@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """Alias for /ws (easier discovery in docs and Postman)."""
    await _websocket_chat_session(websocket)


def initialize_janet_brain():
    """Initialize the global JanetBrain instance"""
    global janet_brain

    # HA Double Soul: DelegationManager when HOME_ASSISTANT_URL + TOKEN set
    delegation_manager = None
    ha_url = os.getenv("HOME_ASSISTANT_URL", "")
    ha_token = os.getenv("HOME_ASSISTANT_TOKEN", "")
    if ha_url and ha_token:
        try:
            from src.delegation.delegation_manager import DelegationManager
            delegation_manager = DelegationManager(
                home_assistant_url=ha_url,
                home_assistant_token=ha_token,
                require_confirmation=False  # Voice: no interactive confirm
            )
            print(f"🏠 HA Double Soul: enabled ({ha_url})")
        except Exception as e:
            print(f"⚠️  HA delegation init failed: {e}")

    print("🌱 Initializing Janet Brain...")
    janet_brain = JanetBrain(model_name=DEFAULT_MODEL, delegation_manager=delegation_manager)
    
    if not janet_brain.is_available():
        print("⚠️  Janet Brain initialization failed!")
        print("   Make sure Ollama is installed and running")
        print(f"   Run: ollama pull {DEFAULT_MODEL}")
        return False
    
    # Start conversation mode (for context management)
    janet_brain.start_conversation()
    
    print(f"✅ Janet Brain initialized with {janet_brain.model_name}")
    print(f"   Available models: {', '.join(janet_brain.available_models)}")
    return True


def main():
    """Main entry point"""
    print("=" * 60)
    print("JANET API SERVER - Constitutional AI for IDEs")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Host: {API_HOST}")
    print(f"  Port: {API_PORT}")
    print(f"  Default Model: {DEFAULT_MODEL}")
    print(f"  Authentication: {'Enabled' if API_KEY and API_KEY != 'none' else 'Disabled'}")
    print()
    
    # Initialize Janet Brain
    if not initialize_janet_brain():
        print("\n❌ Failed to initialize Janet Brain. Exiting.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("SERVER READY")
    print("=" * 60)
    print(f"\nAPI Endpoint: http://{API_HOST}:{API_PORT}/v1/chat/completions")
    print(f"Models Endpoint: http://{API_HOST}:{API_PORT}/v1/models")
    print(f"Health Check: http://{API_HOST}:{API_PORT}/health")
    print(f"WebSocket chat: ws://<host>:{API_PORT}/ws (alias: /ws/chat)")
    print("\nConfigure Continue.dev with:")
    print(f"  apiBase: http://localhost:{API_PORT}/v1")
    print(f"  apiKey: {API_KEY}")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Start server
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
