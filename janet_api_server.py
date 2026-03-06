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

try:
    from fastapi import FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect
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
    HAS_JANET_BRAIN = True
except ImportError:
    HAS_JANET_BRAIN = False
    print("⚠️  JanetBrain not available. Check janet-seed installation.")
    sys.exit(1)

# Configuration
API_PORT = int(os.getenv("JANET_API_PORT", "8080"))
API_HOST = os.getenv("JANET_API_HOST", "0.0.0.0")
API_KEY = os.getenv("JANET_API_KEY", "janet-local-dev")  # Optional authentication
DEFAULT_MODEL = os.getenv("JANET_DEFAULT_MODEL", "tinyllama:1.1b")

# Global JanetBrain instance (shared across requests)
janet_brain: Optional[JanetBrain] = None

# Session management (conversation context per session)
sessions: Dict[str, Dict[str, Any]] = {}

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
        "conversation_history": [],
        "model": DEFAULT_MODEL
    }
    return new_session_id


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars ≈ 1 token)"""
    return len(text) // 4


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
            "health": "/health"
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Janet CLI and other real-time clients"""
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


def initialize_janet_brain():
    """Initialize the global JanetBrain instance"""
    global janet_brain
    
    print("🌱 Initializing Janet Brain...")
    janet_brain = JanetBrain(model_name=DEFAULT_MODEL)
    
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
