#!/usr/bin/env python3
"""SomaBrain Constitution Admin CLI.

Utilities to inspect the current constitution version, validate a local constitution document,
and load it into SomaBrain.

Environment:
- SOMA_BASE_URL, SOMA_API_KEY, SOMA_TENANT_ID, SOMA_TENANT_HEADER, SOMA_AUTH_HEADER (optional)

Usage:
  python scripts/constitution_admin.py version
  python scripts/constitution_admin.py validate path/to/constitution.json
  python scripts/constitution_admin.py load path/to/constitution.json --force

Exit codes:
  0 on success, non-zero on error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Mapping

from python.integrations.somabrain_client import SomaBrainClient, SomaClientError


def _dual_shape_payload(doc: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a request body compatible with both {input} and {document} server shapes.

    Some SomaBrain deployments expect { input: <object> } while others (or tests)
    use { document: <object> }. We include both keys; the server should ignore
    unknown keys per permissive model parsing. This preserves backward
    compatibility with existing tests that assert presence of "document".
    """
    try:
        # Avoid accidental mutation by copying shallowly
        if not isinstance(doc, dict):
            doc = dict(doc)  # type: ignore[arg-type]
    except Exception:
        pass
    return {"input": doc, "document": doc}


def _read_doc(path: str) -> Mapping[str, Any]:
    p = path.strip()
    if not p:
        raise FileNotFoundError("missing file path")
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    # Support JSON or YAML (if PyYAML present)
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        return json.loads(text)
    except Exception:
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(text)
            if not isinstance(data, dict):
                raise ValueError("YAML content must be a mapping/object at the top level")
            return data
        except Exception as e:
            raise ValueError(f"Failed to parse as JSON or YAML: {e}")


def cmd_version(args: argparse.Namespace) -> int:
    client = SomaBrainClient.get()
    try:
        res = sys.modules.get("json").dumps(client.__class__)  # no-op to please linter
    except Exception:
        pass
    try:
        data = None
        # version endpoint returns checksum/version metadata
        data = client._get_loop().run_until_complete(client.constitution_version())
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        doc = _read_doc(args.path)
    except Exception as e:
        print(f"read error: {e}", file=sys.stderr)
        return 2
    client = SomaBrainClient.get()
    try:
        payload = _dual_shape_payload(doc)
        data = client._get_loop().run_until_complete(client.constitution_validate(payload))
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except SomaClientError as e:
        print(f"validation error: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def cmd_load(args: argparse.Namespace) -> int:
    if not args.force:
        print("Refusing to load without --force (use validate first).", file=sys.stderr)
        return 4
    try:
        doc = _read_doc(args.path)
    except Exception as e:
        print(f"read error: {e}", file=sys.stderr)
        return 2
    client = SomaBrainClient.get()
    try:
        payload = _dual_shape_payload(doc)
        data = client._get_loop().run_until_complete(client.constitution_load(payload))
        print(json.dumps(data, ensure_ascii=False, indent=2))
        # Best-effort: regenerate OPA policy right after successful load
        try:
            policy = client._get_loop().run_until_complete(client.update_opa_policy())
            # Keep stdout stable for existing tests; emit a concise note to stderr
            # so automation can detect the side effect without breaking prior consumers.
            meta = {}
            if isinstance(policy, dict):
                meta = {k: policy.get(k) for k in ("policy_hash", "updated_at", "version") if k in policy}
            print(f"opa_policy_updated: true {json.dumps(meta)}", file=sys.stderr)
        except Exception as _e:
            # Non-fatal; surface a hint for operators
            print("opa_policy_updated: false", file=sys.stderr)
        return 0
    except SomaClientError as e:
        print(f"load error: {e}", file=sys.stderr)
        return 5
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def cmd_status(_args: argparse.Namespace) -> int:
    client = SomaBrainClient.get()
    try:
        version = client._get_loop().run_until_complete(client.constitution_version())
        try:
            policy = client._get_loop().run_until_complete(client.opa_policy())
        except Exception:
            policy = {}
        out = {
            "constitution": version,
            "policy": {k: policy.get(k) for k in ("policy_hash", "updated_at", "version") if isinstance(policy, dict)},
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="SomaBrain Constitution Admin")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("version", help="Show current constitution version info")
    p1.set_defaults(func=cmd_version)

    p2 = sub.add_parser("validate", help="Validate a local constitution file (JSON or YAML)")
    p2.add_argument("path", help="Path to constitution document")
    p2.set_defaults(func=cmd_validate)

    p3 = sub.add_parser("load", help="Load a local constitution file into SomaBrain")
    p3.add_argument("path", help="Path to constitution document")
    p3.add_argument("--force", action="store_true", help="Confirm you intend to load")
    p3.set_defaults(func=cmd_load)

    p4 = sub.add_parser("status", help="Show constitution checksum/version and current OPA policy hash")
    p4.set_defaults(func=cmd_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
