"""
N8N Webhook Client for Task Automation
Integrates with n8n workflows for task delegation.
"""
import json
from typing import Dict, Optional
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class N8NClient:
    """Client for n8n webhook integration."""
    
    def __init__(self, base_url: str = "http://localhost:5678", api_key: Optional[str] = None):
        """
        Initialize n8n client.
        
        Args:
            base_url: n8n base URL (default: http://localhost:5678)
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.available = HAS_REQUESTS
        
        if not HAS_REQUESTS:
            print("⚠️  requests not available. Install with: pip install requests")
    
    def is_available(self) -> bool:
        """Check if n8n client is available."""
        return self.available
    
    def trigger_webhook(self, webhook_path: str, payload: Dict, method: str = "POST") -> Optional[Dict]:
        """
        Trigger n8n webhook.
        
        Args:
            webhook_path: Webhook path (e.g., "/webhook/task")
            payload: Payload to send
            method: HTTP method (POST, GET, etc.)
        
        Returns:
            Response dictionary, or None if failed
        """
        if not self.is_available():
            return None
        
        url = f"{self.base_url}{webhook_path}"
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            elif method.upper() == "GET":
                response = requests.get(url, params=payload, headers=headers, timeout=10)
            else:
                print(f"⚠️  Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                return response.json()
            except ValueError:
                return {"status": "success", "message": response.text}
        
        except requests.exceptions.RequestException as e:
            print(f"⚠️  n8n webhook failed: {e}")
            return None
    
    def execute_workflow(self, workflow_id: str, data: Dict) -> Optional[Dict]:
        """
        Execute n8n workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            data: Input data
        
        Returns:
            Workflow execution result
        """
        if not self.is_available():
            return None
        
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/execute"
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        
        payload = {
            "data": data
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️  n8n workflow execution failed: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test n8n connection."""
        if not self.is_available():
            return False
        
        try:
            # Try to access n8n health endpoint
            response = requests.get(f"{self.base_url}/healthz", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

