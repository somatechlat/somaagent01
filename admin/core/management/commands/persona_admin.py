#!/usr/bin/env python3
"""SomaBrain Persona Admin CLI (CAS via ETag).

Manage personas with optimistic concurrency using ETag/If-Match.

Usage:
  python scripts/persona_admin.py get <persona_id>
  python scripts/persona_admin.py put <persona_id> <path/to/persona.json> [--etag <etag>]
  python scripts/persona_admin.py delete <persona_id> [--etag <etag>]

Exit codes:
  0 on success, non-zero on error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Mapping

from admin.agents.services.somabrain_integration import SomaBrainClient, SomaClientError


def _read_doc(path: str) -> Mapping[str, Any]:
    """Execute read doc.

    Args:
        path: The path.
    """

    p = path.strip()
    if not p:
        raise FileNotFoundError("missing file path")
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("persona JSON must be an object at top level")
        return data
    except Exception as e:
        raise ValueError(f"Failed to parse persona JSON: {e}")


def cmd_get(args: argparse.Namespace) -> int:
    """Execute cmd get.

    Args:
        args: The args.
    """

    client = SomaBrainClient.get()
    try:
        data = client._get_loop().run_until_complete(client.get_persona(args.persona_id))
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except SomaClientError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def cmd_put(args: argparse.Namespace) -> int:
    """Execute cmd put.

    Args:
        args: The args.
    """

    try:
        doc = _read_doc(args.path)
    except Exception as e:
        print(f"read error: {e}", file=sys.stderr)
        return 2
    client = SomaBrainClient.get()
    try:
        data = client._get_loop().run_until_complete(
            client.put_persona(args.persona_id, doc, etag=args.etag)
        )
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except SomaClientError as e:
        # Surface conflict status distinctly when server returns 412
        msg = str(e)
        code = 3 if "412" in msg or "Precondition Failed" in msg else 2
        print(f"error: {e}", file=sys.stderr)
        return code
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def cmd_delete(args: argparse.Namespace) -> int:
    """Execute cmd delete.

    Args:
        args: The args.
    """

    client = SomaBrainClient.get()
    try:
        # currently doesn't take etag; we can handle optimistic delete via put with a tombstone if API required.
        if args.etag:
            # without altering the shared client. We'll use a private call for now.
            data = client._get_loop().run_until_complete(
                client._request(
                    "DELETE", f"/persona/{args.persona_id}", headers={"If-Match": args.etag}
                )
            )
        else:
            data = client._get_loop().run_until_complete(client.delete_persona(args.persona_id))
        print(json.dumps({"deleted": True, "result": data}, ensure_ascii=False, indent=2))
        return 0
    except SomaClientError as e:
        msg = str(e)
        code = 3 if "412" in msg or "Precondition Failed" in msg else 2
        print(f"error: {e}", file=sys.stderr)
        return code
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def main() -> int:
    """Execute main."""

    parser = argparse.ArgumentParser(description="SomaBrain Persona Admin (CAS)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("get", help="Fetch persona JSON by id")
    p1.add_argument("persona_id")
    p1.set_defaults(func=cmd_get)

    p2 = sub.add_parser("put", help="Create/update persona with optional ETag (If-Match)")
    p2.add_argument("persona_id")
    p2.add_argument("path")
    p2.add_argument("--etag", dest="etag", default=None)
    p2.set_defaults(func=cmd_put)

    p3 = sub.add_parser("delete", help="Delete persona with optional ETag (If-Match)")
    p3.add_argument("persona_id")
    p3.add_argument("--etag", dest="etag", default=None)
    p3.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
