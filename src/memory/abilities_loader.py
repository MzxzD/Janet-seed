"""
Abilities Loader - Load and provide Janet's discovered abilities
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class AbilitiesLoader:
    """
    Loads and manages Janet's discovered abilities.
    
    Abilities are capabilities Janet has learned or been granted,
    stored in abilities_knowledge.json for persistent access.
    """
    
    def __init__(self, abilities_file: Optional[Path] = None):
        """
        Initialize abilities loader.
        
        Args:
            abilities_file: Path to abilities JSON file
        """
        if abilities_file is None:
            abilities_file = Path(__file__).parent / "abilities_knowledge.json"
        
        self.abilities_file = Path(abilities_file)
        self.abilities: Dict[str, Dict] = {}
        self.load_abilities()
    
    def load_abilities(self) -> None:
        """Load abilities from JSON file."""
        if not self.abilities_file.exists():
            print(f"⚠️  Abilities file not found: {self.abilities_file}")
            return
        
        try:
            with open(self.abilities_file, 'r') as f:
                data = json.load(f)
                abilities_list = data.get('abilities', [])
                
                for ability in abilities_list:
                    ability_id = ability.get('id')
                    if ability_id:
                        self.abilities[ability_id] = ability
                
                print(f"✅ Loaded {len(self.abilities)} abilities")
        except Exception as e:
            print(f"❌ Error loading abilities: {e}")
    
    def get_ability(self, ability_id: str) -> Optional[Dict]:
        """
        Get a specific ability by ID.
        
        Args:
            ability_id: Ability identifier
            
        Returns:
            Ability dictionary or None
        """
        return self.abilities.get(ability_id)
    
    def list_abilities(self, category: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """
        List abilities, optionally filtered by category or status.
        
        Args:
            category: Filter by category (e.g., 'platform_expansion')
            status: Filter by status (e.g., 'active')
            
        Returns:
            List of ability dictionaries
        """
        abilities = list(self.abilities.values())
        
        if category:
            abilities = [a for a in abilities if a.get('category') == category]
        
        if status:
            abilities = [a for a in abilities if a.get('status') == status]
        
        return abilities
    
    def get_ability_summary(self, ability_id: str) -> str:
        """
        Get a human-readable summary of an ability.
        
        Args:
            ability_id: Ability identifier
            
        Returns:
            Summary string
        """
        ability = self.get_ability(ability_id)
        if not ability:
            return f"Ability '{ability_id}' not found."
        
        name = ability.get('name', 'Unknown')
        description = ability.get('description', 'No description')
        status = ability.get('status', 'unknown')
        date = ability.get('date_discovered', 'unknown')
        
        summary = f"**{name}** ({status})\n"
        summary += f"Discovered: {date}\n"
        summary += f"{description}\n"
        
        if 'key_features' in ability:
            summary += "\nKey Features:\n"
            for feature in ability['key_features']:
                summary += f"  • {feature}\n"
        
        return summary
    
    def get_all_abilities_summary(self) -> str:
        """
        Get a summary of all abilities.
        
        Returns:
            Summary string of all abilities
        """
        if not self.abilities:
            return "No abilities discovered yet."
        
        summary = f"Janet's Abilities ({len(self.abilities)} total):\n\n"
        
        for ability_id, ability in self.abilities.items():
            name = ability.get('name', 'Unknown')
            status = ability.get('status', 'unknown')
            description = ability.get('description', 'No description')
            
            summary += f"• **{name}** ({status})\n"
            summary += f"  {description}\n\n"
        
        return summary
    
    def can_use_ability(self, ability_id: str) -> bool:
        """
        Check if an ability is available and active.
        
        Args:
            ability_id: Ability identifier
            
        Returns:
            True if ability is active and usable
        """
        ability = self.get_ability(ability_id)
        return ability is not None and ability.get('status') == 'active'
    
    def add_ability(self, ability: Dict) -> bool:
        """
        Add a new ability to the knowledge base.
        
        Args:
            ability: Ability dictionary with required fields
            
        Returns:
            True if added successfully
        """
        if 'id' not in ability:
            print("❌ Ability must have an 'id' field")
            return False
        
        ability_id = ability['id']
        
        # Add discovery date if not present
        if 'date_discovered' not in ability:
            ability['date_discovered'] = datetime.now().strftime('%Y-%m-%d')
        
        # Add to memory
        self.abilities[ability_id] = ability
        
        # Save to file
        return self.save_abilities()
    
    def save_abilities(self) -> bool:
        """
        Save abilities to JSON file.
        
        Returns:
            True if saved successfully
        """
        try:
            data = {
                'abilities': list(self.abilities.values()),
                'metadata': {
                    'last_updated': datetime.now().strftime('%Y-%m-%d'),
                    'total_abilities': len(self.abilities),
                    'active_abilities': len([a for a in self.abilities.values() if a.get('status') == 'active'])
                }
            }
            
            with open(self.abilities_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Saved {len(self.abilities)} abilities")
            return True
        except Exception as e:
            print(f"❌ Error saving abilities: {e}")
            return False


# Singleton instance
_abilities_loader = None


def get_abilities_loader() -> AbilitiesLoader:
    """Get singleton abilities loader instance."""
    global _abilities_loader
    if _abilities_loader is None:
        _abilities_loader = AbilitiesLoader()
    return _abilities_loader


# Convenience functions
def get_ability(ability_id: str) -> Optional[Dict]:
    """Get a specific ability."""
    return get_abilities_loader().get_ability(ability_id)


def list_abilities(category: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    """List abilities with optional filters."""
    return get_abilities_loader().list_abilities(category, status)


def can_use_ability(ability_id: str) -> bool:
    """Check if an ability is available."""
    return get_abilities_loader().can_use_ability(ability_id)


def get_abilities_summary() -> str:
    """Get summary of all abilities."""
    return get_abilities_loader().get_all_abilities_summary()
