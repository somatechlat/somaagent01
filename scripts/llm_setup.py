#!/usr/bin/env python3
"""
Removed. Legacy env-driven helper is deprecated.

Use the Gateway Settings UI and POST /v1/llm/credentials instead.
"""
import sys

def main() -> int:
    print("This script has been removed. Configure providers via the Gateway instead.")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
