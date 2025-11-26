#!/usr/bin/env python3
"""
Minimal end-to-end check:
- POST /v1/session/message
- Open SSE /v1/sessions/{id}/events?stream=true
- Print first assistant event snippet then exit 0

Usage:
  python scripts/e2e_quick.py [BASE_URL]
Defaults to http://127.0.0.1:21016
"""

import asyncio
import json
import sys
from typing import Optional

import httpx

from services.common.registry import soma_base_url

BASE = sys.argv[1] if len(sys.argv) > 1 else soma_base_url().rstrip("/")


async def main() -> int:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            BASE + "/v1/session/message",
            headers={"Content-Type": "application/json"},
            json={"message": "hello from e2e_quick.py"},
        )
        if not r.is_success:
            print("POST /v1/session/message failed:", r.status_code, r.text[:200])
            return 2
        data = {}
        try:
            data = r.json()
        except Exception:
            pass
        sid: Optional[str] = data.get("session_id")
        if not sid:
            print("No session_id in response; cannot stream.")
            return 3

    async with httpx.AsyncClient(timeout=None) as client:
        print("Opening SSE for session", sid)
        async with client.stream("GET", f"{BASE}/v1/sessions/{sid}/events?stream=true") as resp:
            if resp.status_code != 200:
                print("SSE open failed:", resp.status_code)
                return 4
            buf = ""
            async for chunk in resp.aiter_text():
                buf += chunk
                while "\n\n" in buf:
                    part, buf = buf.split("\n\n", 1)
                    line = part.strip()
                    if not line.startswith("data:"):
                        continue
                    body = line[5:].strip()
                    try:
                        ev = json.loads(body)
                    except Exception:
                        continue
                    role = (ev.get("role") or "").lower()
                    msg = ev.get("message") or ""
                    print(f"EVENT role={role} len={len(msg)}")
                    if msg:
                        print("SNIP:", msg[:200])
                    if role == "assistant":
                        return 0
    return 5


if __name__ == "__main__":
    try:
        code = asyncio.run(main())
    except KeyboardInterrupt:
        code = 130
    sys.exit(code)
