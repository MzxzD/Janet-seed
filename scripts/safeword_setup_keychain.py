#!/usr/bin/env python3
"""
One-time SafeWord → Keychain setup. Store your safe word so "safeword unlock"
uses Touch ID instead of typing. Run in your terminal.

Usage:
    python3 scripts/safeword_setup_keychain.py

Requires: pip install janetxapple-passwords-fusion
"""

import sys
import getpass

if sys.platform != "darwin":
    print("Keychain SafeWord is macOS only.")
    sys.exit(1)

try:
    from janetxapple.keychain_macos import credential_store
except ImportError:
    print("Install: pip install janetxapple-passwords-fusion")
    sys.exit(1)

SERVICE = "janet.safeword.unlock"

def main():
    safe_word = getpass.getpass("Enter safe word (Touch ID will protect it): ").strip()
    if not safe_word:
        print("No safe word entered.")
        sys.exit(1)
    r = credential_store(SERVICE, safe_word, account=SERVICE)
    if "error" in r:
        print(f"Failed: {r['error']}")
        sys.exit(1)
    print("✓ Safe word stored in Keychain. Future 'safeword unlock' will use Touch ID.")

if __name__ == "__main__":
    main()
