"""
Dynamic Shortcut Builder - Server Side
Janet learns user patterns and generates iOS shortcuts on-the-fly
"""

import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime


class DynamicShortcutBuilder:
    """Builds iOS shortcuts dynamically based on user intent"""
    
    def __init__(self, memory_manager, llm):
        self.memory = memory_manager
        self.llm = llm
        self.shortcut_templates = self._load_templates()
    
    def recognize_intent(self, text: str) -> Optional[Dict]:
        """
        Analyze user text and recognize intent
        
        Args:
            text: User's request text
        
        Returns:
            {
                "intent": "play_music",
                "parameters": {"app": "apple_music"},
                "confidence": 0.95
            }
        """
        prompt = f"""Analyze this user request and identify the intent.

User: "{text}"

Return ONLY valid JSON (no markdown, no explanation):
{{
    "intent": "action_name",
    "parameters": {{}},
    "confidence": 0.0
}}

Common intents:
- play_music: Play music on a specific app
- call_contact: Call someone
- send_message: Send a text message
- open_app: Open an application
- set_reminder: Create a reminder
- take_photo: Take a photo
- get_directions: Get directions to a place
- search_web: Search the web
- check_weather: Check weather
- read_news: Read news

Extract parameters from the user's text (e.g., app name, contact name, query).
Set confidence based on how clear the intent is (0.0-1.0).
"""
        
        try:
            # Get LLM response
            response = self.llm.generate(prompt, max_tokens=200)
            
            # Clean response (remove markdown if present)
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code blocks
                lines = response.split("\n")
                response = "\n".join([l for l in lines if not l.startswith("```")])
            
            # Parse JSON
            result = json.loads(response)
            
            print(f"🎯 Recognized intent: {result.get('intent')} (confidence: {result.get('confidence')})")
            
            return result
        except Exception as e:
            print(f"❌ Intent recognition failed: {e}")
            return None
    
    def find_existing_shortcut(self, intent: str) -> Optional[Dict]:
        """Check if shortcut already exists in Green Vault"""
        
        try:
            # Search Green Vault for shortcuts
            shortcuts = self.memory.search_memory(
                query=f"shortcut:{intent}",
                memory_type="green",
                limit=1
            )
            
            if shortcuts:
                print(f"✅ Found existing shortcut for: {intent}")
                return shortcuts[0]
            
            print(f"⚠️ No existing shortcut for: {intent}")
            return None
        except Exception as e:
            print(f"❌ Shortcut search failed: {e}")
            return None
    
    def create_shortcut_interactive(self, intent: str, parameters: Dict) -> Dict:
        """
        Guide user through shortcut creation with questions
        
        Args:
            intent: The action intent (e.g., "play_music")
            parameters: Already-known parameters
        
        Returns:
            {
                "questions": ["Which app?", "Any preferences?"],
                "session_id": "abc123"
            }
        """
        
        # Get template for this intent
        template = self.shortcut_templates.get(intent)
        
        if not template:
            return {"error": f"Unknown intent: {intent}"}
        
        # Generate clarifying questions
        questions = []
        
        for param in template["required_parameters"]:
            if param not in parameters:
                questions.append(template["questions"][param])
        
        # Store session
        session_id = self._create_session(intent, parameters)
        
        print(f"❓ Created session {session_id} with {len(questions)} questions")
        
        return {
            "questions": questions,
            "session_id": session_id
        }
    
    def build_shortcut(
        self,
        intent: str,
        parameters: Dict,
        answers: Dict
    ) -> Dict:
        """
        Build the actual iOS shortcut URL scheme
        
        Args:
            intent: The action intent
            parameters: Known parameters
            answers: Answers to clarifying questions
        
        Returns:
            {
                "url_scheme": "shortcuts://...",
                "name": "Play Music",
                "description": "Plays music on Apple Music"
            }
        """
        
        template = self.shortcut_templates.get(intent)
        
        if not template:
            return {"error": f"Unknown intent: {intent}"}
        
        # Merge parameters with answers
        all_params = {**parameters, **answers}
        
        # Use LLM to fill in missing parameters intelligently
        all_params = self._fill_missing_parameters(template, all_params)
        
        # Build URL scheme
        url_scheme = self._build_url_scheme(template, all_params)
        
        # Create shortcut definition
        shortcut = {
            "id": str(uuid.uuid4()),
            "intent": intent,
            "parameters": all_params,
            "url_scheme": url_scheme,
            "name": template["name"],
            "description": template["description"],
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "success_rate": 1.0
        }
        
        # Save to Green Vault
        self.memory.store_memory(
            content=f"shortcut:{intent}",
            metadata=shortcut,
            memory_type="green"
        )
        
        print(f"✅ Built shortcut: {shortcut['name']}")
        print(f"📱 URL: {url_scheme}")
        
        return shortcut
    
    def _build_url_scheme(self, template: Dict, parameters: Dict) -> str:
        """Build iOS Shortcuts URL scheme"""
        
        if template["type"] == "shortcuts_app":
            # Use Shortcuts app URL scheme
            shortcut_name = template["name"].replace(" ", "%20")
            
            # Build input text
            input_parts = []
            for key, value in parameters.items():
                input_parts.append(f"{key}={value}")
            
            input_text = "&".join(input_parts)
            
            return f"shortcuts://run-shortcut?name={shortcut_name}&input=text&text={input_text}"
        
        elif template["type"] == "url_scheme":
            # Direct URL scheme (e.g., music://, tel://)
            try:
                return template["url_pattern"].format(**parameters)
            except KeyError as e:
                print(f"⚠️ Missing parameter for URL scheme: {e}")
                # Return a safe default
                return template.get("fallback_url", "shortcuts://")
        
        return "shortcuts://"
    
    def _fill_missing_parameters(self, template: Dict, parameters: Dict) -> Dict:
        """Use LLM to intelligently fill missing parameters"""
        
        missing = []
        for param in template["required_parameters"]:
            if param not in parameters:
                missing.append(param)
        
        if not missing:
            return parameters
        
        # Use LLM to infer missing parameters
        prompt = f"""Given this shortcut template and existing parameters, infer the missing parameters.

Template: {template['name']}
Existing parameters: {json.dumps(parameters)}
Missing parameters: {missing}

Return ONLY valid JSON with the missing parameters filled in:
{{
    "param1": "value1",
    "param2": "value2"
}}

Use sensible defaults based on the context.
"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=100)
            
            # Clean and parse
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join([l for l in lines if not l.startswith("```")])
            
            inferred = json.loads(response)
            
            # Merge inferred parameters
            return {**parameters, **inferred}
        except Exception as e:
            print(f"⚠️ Failed to infer parameters: {e}")
            return parameters
    
    def _load_templates(self) -> Dict:
        """Load shortcut templates"""
        
        return {
            "play_music": {
                "name": "Play Music",
                "description": "Plays music on your preferred app",
                "type": "url_scheme",
                "url_pattern": "music://play?query={query}",
                "fallback_url": "music://",
                "required_parameters": ["query"],
                "questions": {
                    "app": "Which app? Apple Music, Spotify, or YouTube Music?",
                    "query": "What would you like to listen to?"
                }
            },
            "call_contact": {
                "name": "Call Contact",
                "description": "Calls a contact",
                "type": "url_scheme",
                "url_pattern": "tel://{phone}",
                "fallback_url": "tel://",
                "required_parameters": ["phone"],
                "questions": {
                    "contact_name": "Who would you like to call?",
                    "phone": "What's their phone number?"
                }
            },
            "send_message": {
                "name": "Send Message",
                "description": "Sends a text message",
                "type": "url_scheme",
                "url_pattern": "sms:{phone}&body={message}",
                "fallback_url": "sms:",
                "required_parameters": ["phone", "message"],
                "questions": {
                    "contact_name": "Who should I message?",
                    "phone": "What's their phone number?",
                    "message": "What's the message?"
                }
            },
            "open_app": {
                "name": "Open App",
                "description": "Opens an application",
                "type": "url_scheme",
                "url_pattern": "{app_scheme}://",
                "fallback_url": "shortcuts://",
                "required_parameters": ["app_scheme"],
                "questions": {
                    "app_name": "Which app should I open?",
                    "app_scheme": "What's the app's URL scheme?"
                }
            },
            "set_reminder": {
                "name": "Set Reminder",
                "description": "Creates a reminder",
                "type": "url_scheme",
                "url_pattern": "x-apple-reminderkit://REMCDReminder/{title}",
                "fallback_url": "x-apple-reminderkit://",
                "required_parameters": ["title"],
                "questions": {
                    "title": "What should I remind you about?",
                    "date": "When? (e.g., tomorrow at 2pm)",
                    "time": "What time?"
                }
            },
            "take_photo": {
                "name": "Take Photo",
                "description": "Opens camera to take a photo",
                "type": "url_scheme",
                "url_pattern": "camera://",
                "fallback_url": "camera://",
                "required_parameters": [],
                "questions": {}
            },
            "get_directions": {
                "name": "Get Directions",
                "description": "Opens Maps with directions",
                "type": "url_scheme",
                "url_pattern": "maps://?daddr={destination}",
                "fallback_url": "maps://",
                "required_parameters": ["destination"],
                "questions": {
                    "destination": "Where do you want to go?"
                }
            },
            "search_web": {
                "name": "Search Web",
                "description": "Searches the web",
                "type": "url_scheme",
                "url_pattern": "https://www.google.com/search?q={query}",
                "fallback_url": "https://www.google.com",
                "required_parameters": ["query"],
                "questions": {
                    "query": "What do you want to search for?",
                    "engine": "Which search engine? (Google, DuckDuckGo, Bing)"
                }
            },
            "check_weather": {
                "name": "Check Weather",
                "description": "Opens weather app",
                "type": "url_scheme",
                "url_pattern": "weather://",
                "fallback_url": "weather://",
                "required_parameters": [],
                "questions": {}
            }
        }
    
    def _create_session(self, intent: str, parameters: Dict) -> str:
        """Create a session for multi-turn shortcut creation"""
        
        session_id = str(uuid.uuid4())
        
        # Store in temporary memory
        self.memory.store_memory(
            content=f"shortcut_session:{session_id}",
            metadata={
                "intent": intent,
                "parameters": parameters,
                "created_at": datetime.now().isoformat()
            },
            memory_type="green"
        )
        
        return session_id
    
    def get_all_shortcuts(self) -> List[Dict]:
        """Get all shortcuts from Green Vault"""
        
        try:
            shortcuts = self.memory.search_memory(
                query="shortcut:",
                memory_type="green",
                limit=100
            )
            
            return shortcuts
        except Exception as e:
            print(f"❌ Failed to get shortcuts: {e}")
            return []
    
    def delete_shortcut(self, shortcut_id: str) -> bool:
        """Delete a shortcut from Green Vault"""
        
        try:
            # This would need to be implemented in the memory manager
            # For now, just log
            print(f"🗑️ Deleting shortcut: {shortcut_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete shortcut: {e}")
            return False
