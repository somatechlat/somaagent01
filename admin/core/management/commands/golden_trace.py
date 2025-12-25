#!/usr/bin/env python3
"""Golden trace capture & compare utility.

Usage:
  python scripts/golden_trace.py capture --session <uuid> --out golden_trace.json \
      --prompt "Hello" --internal-token TOKEN
  python scripts/golden_trace.py compare --in golden_trace.json --prompt "Hello" --internal-token TOKEN

The script performs an internal streaming invoke (requiring X-Internal-Token)
and records the ordered event sequence (type, hash(message), sequence, roles)
to a JSON file. A compare run regenerates a fresh trace and reports diffs.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import uuid
from typing import Any, Dict, List

import httpx


def _get_gateway_base() -> str:
    """Get gateway base URL. Fails fast if not configured."""
    return cfg.get_somabrain_url()


def _hash(text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()
    return f"sha1:{h}"[:18]


async def _stream_prompt(prompt: str, internal_token: str, model: str) -> List[Dict[str, Any]]:
    url = f"{_get_gateway_base()}/v1/llm/invoke/stream"
    session_id = str(uuid.uuid4())
    body = {
        "role": "dialogue",
        "session_id": session_id,
        "persona_id": None,
        "tenant": "public",
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "overrides": {"model": model, "temperature": 0.0},
    }
    headers = {"X-Internal-Token": internal_token}
    out: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=body, headers=headers) as r:
            if r.status_code != 200:
                raise RuntimeError(f"stream status {r.status_code}")
            async for line in r.aiter_lines():
                if not line:
                    continue
                if not line.startswith("data: "):
                    continue
                raw = line[len("data: ") :].strip()
                if raw == "[DONE]":
                    break
                try:
                    ev = json.loads(raw)
                except Exception:
                    continue
                # Shape event
                msg = ev.get("message") or ""
                md = ev.get("metadata") or {}
                out.append(
                    {
                        "type": ev.get("type"),
                        "role": ev.get("role"),
                        "hash": _hash(msg) if msg else None,
                        "sequence": md.get("sequence"),
                        "done": md.get("done"),
                        "error_code": md.get("error_code"),
                    }
                )
    return out


def _diff(expected: List[Dict[str, Any]], actual: List[Dict[str, Any]]) -> Dict[str, Any]:
    diffs: Dict[str, Any] = {"missing": [], "extra": [], "order_mismatch": []}
    # Compare by index for ordering, then membership ignoring sequence differences
    for i, exp in enumerate(expected):
        if i >= len(actual):
            diffs["missing"].append(exp)
            continue
        act = actual[i]
        # Compare selected keys ignoring dynamic sequence values
        for k in ("type", "role", "hash", "done", "error_code"):
            if exp.get(k) != act.get(k):
                diffs["order_mismatch"].append({"index": i, "expected": exp, "actual": act})
                break
    if len(actual) > len(expected):
        diffs["extra"].extend(actual[len(expected) :])
    return diffs


async def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--prompt", required=True)
    cap.add_argument("--out", required=True)
    cap.add_argument("--model", default="gpt-4o-mini")
    cap.add_argument("--internal-token", required=True)

    comp = sub.add_parser("compare")
    comp.add_argument("--prompt", required=True)
    comp.add_argument("--in", dest="inp", required=True)
    comp.add_argument("--model", default="gpt-4o-mini")
    comp.add_argument("--internal-token", required=True)

    args = ap.parse_args(argv)
    if args.cmd == "capture":
        trace = await _stream_prompt(args.prompt, args.internal_token, args.model)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(trace, f, ensure_ascii=False, indent=2)
        print(f"wrote {len(trace)} events to {args.out}")
        return 0
    if args.cmd == "compare":
        with open(args.inp, "r", encoding="utf-8") as f:
            expected = json.load(f)
        actual = await _stream_prompt(args.prompt, args.internal_token, args.model)
        diff = _diff(expected, actual)
        if any(diff[k] for k in diff):
            print(json.dumps(diff, indent=2, ensure_ascii=False))
            print("DIFF DETECTED")
            return 2
        print("Golden trace match")
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
