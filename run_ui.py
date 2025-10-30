"""
NEUTRALIZED: legacy UI entrypoint removed.

This file has been neutralized as part of the legacy purge — the Web UI is
served by the Gateway at: http://localhost:${GATEWAY_PORT:-21016}/ui

Do not execute this file. Use the Gateway service instead.
"""

import sys

print("run_ui.py has been removed. Use the Gateway-served UI at http://localhost:${GATEWAY_PORT:-21016}/ui")
sys.exit(0)
