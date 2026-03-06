#!/usr/bin/env python3
"""
Janet API Server - MOCK MODE (for testing when Ollama has issues)
This version returns mock responses without calling Ollama
"""
import json
import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configuration
API_PORT = 8080
API_HOST = "0.0.0.0"
API_KEY = "janet-local-dev"

app = FastAPI(title="Janet API Server (Mock Mode)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = False

def verify_api_key(authorization: Optional[str] = None) -> bool:
    if not authorization:
        return False
    token = authorization.replace("Bearer ", "").strip()
    return token == API_KEY

@app.get("/")
async def root():
    return {
        "name": "Janet API Server (Mock Mode)",
        "version": "1.0.0-mock",
        "status": "online"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "brain_available": True,
        "current_model": "janet-mock",
        "available_models": ["janet-mock"],
        "active_sessions": 0,
        "mode": "MOCK - Ollama bypass"
    }

@app.get("/v1/models")
async def list_models(authorization: Optional[str] = Header(None)):
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {
        "object": "list",
        "data": [{
            "id": "janet-mock",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "janet"
        }]
    }

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    user_message = request.messages[-1].content.lower()
    
    # Generate mock responses based on keywords
    if "hello" in user_message or "hi" in user_message:
        response_text = "Hello! I'm Janet, your constitutional AI coding assistant. I'm currently running in mock mode because Ollama is experiencing GPU issues. How can I help you code today?"
    elif "explain" in user_message or "what" in user_message:
        response_text = "I'd be happy to explain that! In mock mode, I can help you understand code concepts. Once Ollama is working, I'll provide full AI-powered explanations."
    elif "write" in user_message or "create" in user_message or "generate" in user_message:
        response_text = "I can help you write code! Here's a simple example:\n\n```python\ndef example_function(param):\n    \"\"\"Docstring here\"\"\"\n    return param\n```\n\nOnce Ollama is working, I'll generate custom code based on your specific needs."
    elif "error" in user_message or "fix" in user_message:
        response_text = "To fix the Ollama Metal GPU error, try:\n1. Restart your Mac\n2. Or use: OLLAMA_NUM_GPU=0 to force CPU mode\n3. Or reinstall Ollama: brew reinstall ollama"
    else:
        response_text = f"I received your message: '{request.messages[-1].content}'. I'm Janet, running in mock mode. Once Ollama is fixed, I'll provide full AI responses!"
    
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response_text
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(request.messages[-1].content) // 4,
            "completion_tokens": len(response_text) // 4,
            "total_tokens": (len(request.messages[-1].content) + len(response_text)) // 4
        }
    }

if __name__ == "__main__":
    print("=" * 60)
    print("JANET API SERVER - MOCK MODE")
    print("=" * 60)
    print("\n⚠️  Running in MOCK mode (Ollama bypass)")
    print("   This provides basic responses for testing Continue.dev")
    print(f"\n✅ Server starting on http://{API_HOST}:{API_PORT}")
    print("\nConfigure Continue.dev with:")
    print(f"  apiBase: http://localhost:{API_PORT}/v1")
    print(f"  apiKey: {API_KEY}")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")
