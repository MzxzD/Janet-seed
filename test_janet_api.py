#!/usr/bin/env python3
"""
Test script for Janet API Server
Verifies OpenAI-compatible endpoints work correctly
"""
import requests
import json
import time
import sys

API_BASE = "http://localhost:8080"
API_KEY = "janet-local-dev"

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Brain available: {data.get('brain_available')}")
            print(f"   Current model: {data.get('current_model')}")
            print(f"   Available models: {data.get('available_models')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Make sure janet_api_server.py is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_list_models():
    """Test models endpoint"""
    print("\nTesting /v1/models endpoint...")
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{API_BASE}/v1/models", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            print(f"✅ Models endpoint passed")
            print(f"   Found {len(models)} models:")
            for model in models:
                print(f"   - {model.get('id')}")
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat_completion():
    """Test chat completions endpoint (non-streaming)"""
    print("\nTesting /v1/chat/completions endpoint (non-streaming)...")
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        # Use first available model (llama3.2 or qwen2.5-coder typically available)
        model = "llama3.2:latest"  # Fallback; prefer qwen2.5-coder:7b if installed
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Say 'Hello from Janet!' and nothing else."}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False
        }
        
        print("   Sending request...")
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']
            usage = data.get('usage', {})
            
            print(f"✅ Chat completion passed ({duration:.2f}s)")
            print(f"   Response: {message[:100]}...")
            print(f"   Tokens: {usage.get('total_tokens', 'N/A')}")
            return True
        else:
            print(f"❌ Chat completion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_streaming_completion():
    """Test chat completions endpoint (streaming)"""
    print("\nTesting /v1/chat/completions endpoint (streaming)...")
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3.2:latest",
            "messages": [
                {"role": "user", "content": "Count from 1 to 5."}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": True
        }
        
        print("   Sending streaming request...")
        response = requests.post(
            f"{API_BASE}/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Streaming started")
            print("   Received chunks: ", end="", flush=True)
            
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        chunk_count += 1
                        print(".", end="", flush=True)
                        if line_str == 'data: [DONE]':
                            break
            
            print(f"\n   Total chunks: {chunk_count}")
            print("✅ Streaming completion passed")
            return True
        else:
            print(f"❌ Streaming failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_performance_endpoint():
    """Test Janet-specific performance endpoint"""
    print("\nTesting /v1/performance endpoint (Janet-specific)...")
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{API_BASE}/v1/performance", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Performance endpoint passed")
            print(f"   Current model: {data.get('current_model')}")
            print(f"   Cache hit rate: {data.get('cache_stats', {}).get('hit_rate', 0):.2%}")
            return True
        else:
            print(f"❌ Performance endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("JANET API SERVER TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("Health Check", test_health),
        ("List Models", test_list_models),
        ("Chat Completion", test_chat_completion),
        ("Streaming Completion", test_streaming_completion),
        ("Performance Stats", test_performance_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Janet API server is working correctly.")
        print("\nNext steps:")
        print("1. Install Continue.dev extension in VSCode")
        print("2. The config file is already at ~/.continue/config.yaml")
        print("3. Restart VSCode or reload the Continue.dev extension")
        print("4. Use Cmd+L (Mac) or Ctrl+L (Windows/Linux) to start chatting with Janet")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
