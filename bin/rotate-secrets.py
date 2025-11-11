#!/usr/bin/env python3
"""S3 – Rotate encryption key and re-encrypt all settings."""
import os
import sys
from python.helpers.vault_adapter import VaultAdapter

def main():
    old_key = os.getenv("SA01_CRYPTO_FERNET_KEY")
    new_key = VaultAdapter.rotate_key()
    print(f"🔑 New key generated: {new_key}")
    print("⚠️  Manual re-encrypt loop required (not implemented yet)")
    os.environ["SA01_CRYPTO_FERNET_KEY"] = new_key

if __name__ == "__main__":
    main()
