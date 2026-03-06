"""
Home Assistant API endpoints for Janet.
Provides REST API for Home Assistant integration.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import Dict, Any
import logging
import os
import sys

_LOGGER = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Global reference to JanetCore (will be set when server starts)
janet_core = None


def set_janet_core(core):
    """Set the JanetCore instance for API endpoints."""
    global janet_core
    janet_core = core
    _LOGGER.info("JanetCore instance connected to API server")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "janet-seed",
        "version": "1.0.0"
    }), 200


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get Janet's current status."""
    try:
        if janet_core is None:
            return jsonify({
                "state": "initializing",
                "uptime": 0,
                "model": "unknown",
                "voice_enabled": False,
                "in_conversation": False,
                "memory_usage": 0,
                "green_vault_entries": 0,
                "blue_vault_active": False,
                "red_vault_entries": 0,
            }), 200
        
        # Get actual status from JanetCore
        status = {
            "state": "idle",  # idle, listening, thinking, speaking
            "uptime": 0,  # TODO: Track actual uptime
            "model": "qwen2.5-coder:7b",  # TODO: Get from janet_core
            "voice_enabled": True,
            "in_conversation": False,  # TODO: Get from janet_core
            "memory_usage": 1024 * 1024 * 50,  # 50 MB - TODO: Get actual
            "green_vault_entries": 0,  # TODO: Get from memory manager
            "blue_vault_active": False,
            "red_vault_entries": 0,
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        _LOGGER.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/speak', methods=['POST'])
def speak():
    """Make Janet speak a message."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get('text', '')
        voice = data.get('voice')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        _LOGGER.info(f"Speak request: {message} (voice: {voice})")
        
        # TODO: Integrate with Janet's TTS system
        # For now, just log it
        if janet_core:
            # Try to use TTS if available
            try:
                from src.voice.tts import TextToSpeech
                tts = TextToSpeech()
                if tts.is_available():
                    tts.speak(message)
                else:
                    _LOGGER.warning("TTS not available, message logged only")
            except Exception as e:
                _LOGGER.warning(f"TTS error: {e}, message logged only")
        
        return jsonify({
            "status": "success",
            "message": message,
            "voice": voice
        }), 200
        
    except Exception as e:
        _LOGGER.error(f"Error in speak endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/command', methods=['POST'])
def command():
    """Send a voice command to Janet."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        command_text = data.get('command', '')
        
        if not command_text:
            return jsonify({"error": "No command provided"}), 400
        
        _LOGGER.info(f"Command request: {command_text}")
        
        # TODO: Integrate with Janet's conversation system
        # For now, just acknowledge
        response = f"Received command: {command_text}"
        
        if janet_core:
            # Try to process with janet_core
            try:
                # This would integrate with the actual conversation system
                _LOGGER.info(f"Processing command with JanetCore: {command_text}")
                response = "Command processed by Janet"
            except Exception as e:
                _LOGGER.warning(f"JanetCore processing error: {e}")
        
        return jsonify({
            "status": "success",
            "command": command_text,
            "response": response
        }), 200
        
    except Exception as e:
        _LOGGER.error(f"Error in command endpoint: {e}")
        return jsonify({"error": str(e)}), 500


def start_api_server(host='0.0.0.0', port=8080, janet_core_instance=None):
    """
    Start the Home Assistant API server.
    
    Args:
        host: Host to bind to (default: 0.0.0.0 for all interfaces)
        port: Port to bind to (default: 8080)
        janet_core_instance: Optional JanetCore instance for integration
    """
    if janet_core_instance:
        set_janet_core(janet_core_instance)
    
    _LOGGER.info(f"Starting Home Assistant API server on {host}:{port}")
    _LOGGER.info("Available endpoints:")
    _LOGGER.info(f"  GET  http://{host}:{port}/health")
    _LOGGER.info(f"  GET  http://{host}:{port}/api/status")
    _LOGGER.info(f"  POST http://{host}:{port}/api/speak")
    _LOGGER.info(f"  POST http://{host}:{port}/api/command")
    
    try:
        app.run(host=host, port=port, debug=False, threaded=True)
    except Exception as e:
        _LOGGER.error(f"Failed to start API server: {e}")
        raise


if __name__ == "__main__":
    # For standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Starting Janet Home Assistant API Server (Standalone Mode)")
    print("=" * 60)
    
    start_api_server(host='0.0.0.0', port=8080)
