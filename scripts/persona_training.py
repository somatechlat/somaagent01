#!/usr/bin/env python3
"""Persona training helper.

Usage examples:
  python scripts/persona_training.py start --persona biology_researcher
  python scripts/persona_training.py close --persona biology_researcher
"""
from __future__ import annotations

import argparse
import asyncio
import uuid

import httpx

parser = argparse.ArgumentParser(description="Persona training helper")
sub = parser.add_subparsers(dest="command", required=True)

start = sub.add_parser("start")
start.add_argument("--persona", required=True)
start.add_argument("--gateway", default="http://localhost:8001")

close = sub.add_parser("close")
close.add_argument("--persona", required=True)
close.add_argument("--notes", default="")
close.add_argument("--repository", default="http://localhost:8011")


async def call_gateway(persona: str, gateway: str, message: str) -> None:
    async with httpx.AsyncClient() as client:
        payload = {
            "session_id": str(uuid.uuid4()),
            "persona_id": persona,
            "message": message,
            "metadata": {"tenant": "training", "source": "training_cli"},
        }
        await client.post(f"{gateway}/v1/session/message", json=payload)


async def post_persona_notes(persona: str, notes: str, repository: str) -> None:
    async with httpx.AsyncClient() as client:
        payload = {
            "role": f"training_notes_{persona}",
            "deployment_mode": "TRAINING",
            "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "base_url": "https://slm.somaagent01.dev/v1",
            "temperature": 0.2,
            "extra": {"notes": notes},
        }
        await client.post(f"{repository}/v1/model-profiles", json=payload)


async def main() -> None:
    args = parser.parse_args()
    if args.command == "start":
        await call_gateway(
            args.persona,
            args.gateway,
            "Entering training mode under human supervision.",
        )
        print(f"Training session started for persona {args.persona}")
    elif args.command == "close":
        notes = args.notes or "Training session closed. Generate persona package."
        await post_persona_notes(args.persona, notes, args.repository)
        print(f"Training session closed for persona {args.persona}")


if __name__ == "__main__":
    asyncio.run(main())
