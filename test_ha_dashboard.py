#!/usr/bin/env python3
"""
Test Home Assistant Dashboard Handler
Quick test to verify dashboard integration works.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from delegation.home_assistant import HomeAssistantClient
from delegation.handlers.home_assistant_dashboard_handler import HomeAssistantDashboardHandler
from delegation.handlers.base import DelegationRequest, HandlerCapability


def test_dashboard_handler():
    """Test the dashboard handler."""
    print("=" * 60)
    print("Home Assistant Dashboard Handler Test")
    print("=" * 60)
    print()
    
    # Get HA configuration from environment
    ha_url = os.getenv("HOME_ASSISTANT_URL", "http://homeassistant.local:8123")
    ha_token = os.getenv("HOME_ASSISTANT_TOKEN", "")
    
    if not ha_token:
        print("⚠️  HOME_ASSISTANT_TOKEN not set")
        print("   Set it with: export HOME_ASSISTANT_TOKEN=your_token")
        print()
        print("Testing with mock configuration...")
        ha_url = "http://homeassistant.local:8123"
        ha_token = "test_token"
    
    # Initialize client and handler
    print(f"1️⃣  Initializing Home Assistant client...")
    print(f"   URL: {ha_url}")
    ha_client = HomeAssistantClient(base_url=ha_url, access_token=ha_token)
    
    print(f"2️⃣  Creating dashboard handler...")
    handler = HomeAssistantDashboardHandler(ha_client)
    print(f"   Handler ID: {handler.handler_id}")
    print(f"   Handler Name: {handler.name}")
    print(f"   Capabilities: {[c.value for c in handler.get_capabilities()]}")
    print()
    
    # Test cases
    test_cases = [
        "open home assistant dashboard",
        "show home assistant devices",
        "open home assistant automations",
        "show home assistant scenes",
        "not a dashboard request"
    ]
    
    print("3️⃣  Testing dashboard requests...")
    print()
    
    for i, task in enumerate(test_cases, 1):
        print(f"Test {i}: \"{task}\"")
        
        # Create request
        request = DelegationRequest(
            capability=HandlerCapability.HOME_AUTOMATION,
            task_description=task,
            input_data={"user_query": task}
        )
        
        # Check if handler can handle it
        can_handle = handler.can_handle(request)
        print(f"   Can handle: {can_handle}")
        
        if can_handle:
            # Handle the request (but don't actually open browser in test)
            print(f"   ✅ Handler would process this request")
            
            # Show what URL would be opened
            if "devices" in task.lower():
                page = "devices"
            elif "automation" in task.lower():
                page = "automations"
            elif "scene" in task.lower():
                page = "scenes"
            else:
                page = "main"
            
            url = handler.get_dashboard_url(page)
            print(f"   Would open: {url}")
        else:
            print(f"   ❌ Handler would not process this request")
        
        print()
    
    # Test dashboard info
    print("4️⃣  Getting dashboard info...")
    info = handler.get_dashboard_info()
    
    if info.get("available"):
        print(f"   ✅ Dashboard available")
        print(f"   Base URL: {info['base_url']}")
        print(f"   Available pages:")
        for page_name, page_url in info['pages'].items():
            print(f"      • {page_name}: {page_url}")
    else:
        print(f"   ❌ Dashboard not available: {info.get('message')}")
    
    print()
    print("=" * 60)
    print("✅ Test complete!")
    print()
    print("To actually test opening the dashboard:")
    print("1. Make sure Home Assistant is running")
    print("2. Set HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN")
    print("3. Say: 'Hey Janet, open Home Assistant dashboard'")
    print("=" * 60)


if __name__ == "__main__":
    test_dashboard_handler()
