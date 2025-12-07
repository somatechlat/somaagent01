#!/usr/bin/env python3
"""S3 – Rotate encryption key and re-encrypt all settings."""

import os

from python.helpers.vault_adapter import VaultAdapter
from src.core.config import cfg, reload_config


def main():
    old_key = cfg.env("SA01_CRYPTO_FERNET_KEY")
    new_key = VaultAdapter.rotate_key()
    print(f"🔑 New key generated: {new_key}")
    if old_key:
        print("⚠️  Manual re-encrypt loop required (pending implementation)")
    os.environ["SA01_CRYPTO_FERNET_KEY"] = new_key
    reload_config()


if __name__ == "__main__":
    main()
