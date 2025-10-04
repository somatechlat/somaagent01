#!/usr/bin/env python3
"""CLI utility to send a message through the SomaAgent 01 gateway and print responses."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid

import httpx
import websockets

parser = argparse.ArgumentParser(description="Send message to SomaAgent 01")
parser.add_argument("text", help="Message text")
parser.add_argument("--gateway", default="http://localhost:8001", help="Gateway base URL")
parser.add_argument("--persona", default=None, help="Persona ID")
parser.add_argument("--session", default=None, help="Existing session ID")


async def main() -> None:
    args = parser.parse_args()
    session_id = args.session or str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "persona_id": args.persona,
        "message": args.text,
        "metadata": {"tenant": "local"},
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{args.gateway}/v1/session/message", json=payload)
        resp.raise_for_status()

    ws_url = args.gateway.replace("http", "ws") + f"/v1/session/{session_id}/stream"
    print(f"Streaming responses (session={session_id})...")
    async with websockets.connect(ws_url) as websocket:
        try:
            while True:
                data = await websocket.recv()
                event = json.loads(data)
                print(json.dumps(event, indent=2))
        except websockets.exceptions.ConnectionClosed:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
