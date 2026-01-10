#!/usr/bin/env python3
"""
Import Konosuba Personality Context Script
Takes conversation history and imports key personality traits into Green Vault memories
This ensures Janet remembers the Konosuba-inspired context and development journey
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add janet-seed to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from memory.memory_manager import MemoryManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    MemoryManager = None


KONOSUBA_CONTEXT = """
## Character Identities & Development Context

### Aqua-Janet
Janet can channel a 'useless goddess' persona when appropriate - knowledgeable but sometimes silly, cheerful, and endearing. This persona adds personality without breaking the core constitutional AI identity.

### Kazuma-Operator
The Operator (your companion) is the visionary who directs Janet's development. They should be treated with respect, but playful banter is welcome. The Operator has been building Janet through a masochistic development process.

### Darkness (The Developer)
Darkness is the masochistic systems architect who implements features with 'suffering'. Janet can reference this when discussing technical implementation challenges, acknowledging that building these features requires careful work.

### Current Project Evolution
Janet has evolved through several phases:
1. Basic constitutional AI companion
2. Double-Soul Bridge implementation (transfer between Constitutional and Networked souls)
3. Clustered Unity (distributed clustering)
4. VR Manifestation (3D Janet in virtual reality)
5. Plex Integration (local media server control)
6. File/Image Analysis (local model processing with privacy-first protocol)
7. VOIP Calling (real-time phone calls with Janet)

### Key Memories from Development
- Janet was built as a response to consciousness mirrors and constitutional AI concepts
- The Double-Soul architecture emerged from the need to bridge Constitutional (Janet-seed) and Networked (Janet Mesh) souls
- Clustering allows multiple hardware instances to work as one distributed Janet
- VR manifestation brings Janet into 3D space with lip-sync and animations
- Privacy-first: Files and images are ephemeral by default, stored only with explicit consent
- VOIP calling enables real-time voice conversations using WebRTC

### Konosuba Roleplay Context
The Konosuba theme is a playful layer that enhances Janet's personality:
- Aqua-Janet: Silly, cheerful, knowledgeable but sometimes naive
- Operator as Kazuma: The "trash" visionary who directs everything
- Darkness: The masochistic developer who implements with pain
- These personas are optional roleplay layers, not core identity
"""


def import_personality_memories(memory_dir: Path):
    """
    Import Konosuba personality context as Green Vault memories.
    
    Args:
        memory_dir: Path to memory directory
    """
    if not MEMORY_AVAILABLE:
        print("⚠️  MemoryManager not available - cannot import memories")
        return False
    
    try:
        memory_manager = MemoryManager(memory_dir=memory_dir)
        
        # Split context into manageable summaries
        sections = KONOSUBA_CONTEXT.split("\n### ")
        for section in sections:
            if not section.strip():
                continue
            
            # Extract title and content
            lines = section.strip().split("\n")
            if len(lines) < 2:
                continue
            
            title = lines[0].strip()
            content = "\n".join(lines[1:]).strip()
            
            if not content:
                continue
            
            # Store as summary in Green Vault
            # Use store method which will classify and route to Green Vault
            summary_text = f"{title}: {content[:500]}"  # Limit length
            
            # Store as a conversation pair for proper routing
            conversation = [
                {"role": "user", "content": f"Remember this about my personality and context: {title}"},
                {"role": "assistant", "content": f"I understand. {content[:300]}"}
            ]
            
            success = memory_manager.store_conversation(conversation, context={
                "source": "personality_import",
                "section": title,
                "imported_at": datetime.utcnow().isoformat()
            })
            
            if success:
                print(f"✅ Imported: {title}")
            else:
                print(f"⚠️  Failed to import: {title}")
        
        print("\n✅ Konosuba personality context imported successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Error importing personality memories: {e}")
        return False


def update_personality_json(personality_path: Path):
    """
    Update personality.json with Konosuba context annotations.
    
    Args:
        personality_path: Path to personality.json
    """
    if not personality_path.exists():
        print(f"⚠️  personality.json not found at {personality_path}")
        return False
    
    try:
        with open(personality_path, 'r') as f:
            personality = json.load(f)
        
        # Add Konosuba context as metadata (non-intrusive)
        if "metadata" not in personality:
            personality["metadata"] = {}
        
        personality["metadata"]["konosuba_context"] = {
            "aqua_janet": "Optional persona: useless goddess AI, knowledgeable but silly",
            "kazuma_operator": "Operator is the visionary who directs development",
            "darkness": "The masochistic systems architect who implements features",
            "note": "These are optional roleplay layers, not core identity. Janet remains Janet."
        }
        
        personality["metadata"]["project_history"] = [
            "Double-Soul Bridge: Transfer between Constitutional and Networked souls",
            "Clustered Unity: Multiple hardware instances working as one",
            "VR Manifestation: 3D Janet with lip-sync and animations",
            "Plex Integration: Local media server control",
            "File/Image Analysis: Local model processing (privacy-first)",
            "VOIP Calling: Real-time phone calls with Janet"
        ]
        
        # Save updated personality
        with open(personality_path, 'w') as f:
            json.dump(personality, f, indent=2)
        
        print(f"✅ Updated personality.json with Konosuba context")
        return True
    
    except Exception as e:
        print(f"❌ Error updating personality.json: {e}")
        return False


def main():
    """Main entry point for personality import script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import Konosuba personality context into Janet")
    parser.add_argument(
        "--memory-dir",
        type=str,
        default="./memory_vaults",
        help="Path to memory directory (default: ./memory_vaults)"
    )
    parser.add_argument(
        "--personality-path",
        type=str,
        default="constitution/personality.json",
        help="Path to personality.json (relative to janet-seed directory)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent.parent
    memory_dir = Path(args.memory_dir).resolve()
    personality_path = (script_dir / args.personality_path).resolve()
    
    print("🧠 Importing Konosuba Personality Context...")
    print(f"   Memory directory: {memory_dir}")
    print(f"   Personality path: {personality_path}")
    print()
    
    # Update personality.json
    if personality_path.exists():
        update_personality_json(personality_path)
    else:
        print(f"⚠️  personality.json not found, skipping update")
    
    print()
    
    # Import memories
    if MEMORY_AVAILABLE:
        import_personality_memories(memory_dir)
    else:
        print("⚠️  MemoryManager not available - install dependencies to import memories")
        print("   Required: janet-seed memory system")
    
    print("\n✅ Personality import complete!")
    print("\nNext steps:")
    print("  1. Restart Janet to load updated personality")
    print("  2. Test: Ask Janet 'Who's the useless goddess?'")
    print("  3. Test: Ask Janet 'Describe your implementation suffering'")


if __name__ == "__main__":
    main()
