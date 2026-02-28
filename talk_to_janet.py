#!/usr/bin/env python3
"""
Simple script to talk to Janet interactively
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core import JanetCore

def main():
    print("🎤 Starting Janet...")
    print("=" * 60)
    
    # Initialize Janet
    janet = JanetCore()
    
    print("\n✅ Janet is ready! Type your message and press Enter.")
    print("   Type 'exit' or 'quit' to stop.\n")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nJanet: Goodbye! 👋")
                break
            
            # Send to Janet and get response
            print("Janet: ", end="", flush=True)
            response = janet.process_message(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nJanet: Goodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Type your message again or 'exit' to quit.\n")

if __name__ == "__main__":
    main()
