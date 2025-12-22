"""
Home Assistant REST API Client
Integrates with Home Assistant for smart home control.
"""
import json
from typing import Dict, Optional, List
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class HomeAssistantClient:
    """Client for Home Assistant REST API."""
    
    def __init__(self, base_url: str = "http://homeassistant.local:8123", access_token: Optional[str] = None):
        """
        Initialize Home Assistant client.
        
        Args:
            base_url: Home Assistant base URL
            access_token: Long-lived access token
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.available = HAS_REQUESTS
        
        if not HAS_REQUESTS:
            print("⚠️  requests not available. Install with: pip install requests")
    
    def is_available(self) -> bool:
        """Check if Home Assistant client is available."""
        return self.available and self.access_token is not None
    
    def _headers(self) -> Dict:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json"
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def get_state(self, entity_id: str) -> Optional[Dict]:
        """
        Get entity state.
        
        Args:
            entity_id: Entity ID (e.g., "light.living_room")
        
        Returns:
            Entity state dictionary
        """
        if not self.is_available():
            return None
        
        url = f"{self.base_url}/api/states/{entity_id}"
        
        try:
            response = requests.get(url, headers=self._headers(), timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Home Assistant get_state failed: {e}")
            return None
    
    def call_service(self, domain: str, service: str, entity_id: Optional[str] = None, **kwargs) -> Optional[Dict]:
        """
        Call Home Assistant service.
        
        Args:
            domain: Service domain (e.g., "light")
            service: Service name (e.g., "turn_on")
            entity_id: Entity ID (optional)
            **kwargs: Additional service data
        
        Returns:
            Service call result
        """
        if not self.is_available():
            return None
        
        url = f"{self.base_url}/api/services/{domain}/{service}"
        
        data = kwargs.copy()
        if entity_id:
            data["entity_id"] = entity_id
        
        try:
            response = requests.post(url, json=data, headers=self._headers(), timeout=10)
            response.raise_for_status()
            
            # Home Assistant returns a list of state changes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Home Assistant service call failed: {e}")
            return None
    
    def turn_on_light(self, entity_id: str, brightness: Optional[int] = None, color: Optional[List[int]] = None) -> bool:
        """Turn on a light."""
        data = {}
        if brightness:
            data["brightness"] = brightness
        if color:
            data["rgb_color"] = color
        
        result = self.call_service("light", "turn_on", entity_id=entity_id, **data)
        return result is not None
    
    def turn_off_light(self, entity_id: str) -> bool:
        """Turn off a light."""
        result = self.call_service("light", "turn_off", entity_id=entity_id)
        return result is not None
    
    def set_temperature(self, entity_id: str, temperature: float) -> bool:
        """Set thermostat temperature."""
        result = self.call_service("climate", "set_temperature", entity_id=entity_id, temperature=temperature)
        return result is not None
    
    def get_all_entities(self) -> List[Dict]:
        """Get all entities."""
        if not self.is_available():
            return []
        
        url = f"{self.base_url}/api/states"
        
        try:
            response = requests.get(url, headers=self._headers(), timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Home Assistant get_all_entities failed: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test Home Assistant connection."""
        if not self.is_available():
            return False
        
        try:
            url = f"{self.base_url}/api/"
            response = requests.get(url, headers=self._headers(), timeout=5)
            return response.status_code == 200
        except Exception:
            return False

