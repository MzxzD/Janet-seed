#!/usr/bin/env python3
"""
Store a secret in Red Vault (encrypted at rest).
Standalone script — same encryption as janet-seed RedVault.

Usage:
    cd Janet-Projects/JanetOS/janet-seed
    python3 scripts/store_in_redvault.py SECRET_ID "secret value"

    # Or pipe from stdin (avoids URL in shell history):
    echo "https://..." | python3 scripts/store_in_redvault.py instagram_web_login -

Safe word is prompted interactively (not echoed).
Run in your terminal — non-interactive use will fail at the safe-word prompt.
"""

import sys
import json
import getpass
from pathlib import Path
from datetime import datetime

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def _derive_key(safe_word: str) -> bytes:
    salt = b'janet_red_vault_salt'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(safe_word.encode()))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    if not HAS_CRYPTO:
        print("Error: Install cryptography: pip install cryptography")
        sys.exit(1)
    
    secret_id = sys.argv[1]
    secret_input = sys.argv[2]
    
    if secret_input == "-":
        secret_data = sys.stdin.read().strip()
    else:
        secret_data = secret_input
    
    if not secret_data:
        print("Error: secret data is empty")
        sys.exit(1)
    
    janet_home = Path.home() / ".janet"
    vault_dir = Path(
        __import__("os").environ.get("JANET_HOME", str(janet_home))
    ).expanduser() / "memory" / "red_vault"
    
    vault_dir.mkdir(parents=True, exist_ok=True)
    metadata_file = vault_dir / "red_vault_metadata.json"
    
    # Load metadata
    metadata = {}
    if metadata_file.exists():
        try:
            metadata = json.loads(metadata_file.read_text())
        except Exception:
            pass
    
    safe_word = getpass.getpass("Safe word: ")
    
    try:
        key = _derive_key(safe_word)
        cipher = Fernet(key)
        encrypted = cipher.encrypt(secret_data.encode())
        
        secret_file = vault_dir / f"{secret_id}.enc"
        secret_file.write_bytes(encrypted)
        
        metadata[secret_id] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "encrypted": True
        }
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        print(f"✓ Stored in Red Vault: {secret_id}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
