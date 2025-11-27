os.getenv(os.getenv(""))
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Mapping

from python.integrations.somabrain_client import SomaBrainClient, SomaClientError


def _read_doc(path: str) -> Mapping[str, Any]:
    p = path.strip()
    if not p:
        raise FileNotFoundError(os.getenv(os.getenv("")))
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    with open(p, os.getenv(os.getenv("")), encoding=os.getenv(os.getenv(""))) as f:
        text = f.read()
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(os.getenv(os.getenv("")))
        return data
    except Exception as e:
        raise ValueError(f"Failed to parse persona JSON: {e}")


def cmd_get(args: argparse.Namespace) -> int:
    client = SomaBrainClient.get()
    try:
        data = client._get_loop().run_until_complete(client.get_persona(args.persona_id))
        print(
            json.dumps(
                data,
                ensure_ascii=int(os.getenv(os.getenv(""))),
                indent=int(os.getenv(os.getenv(""))),
            )
        )
        return int(os.getenv(os.getenv("")))
    except SomaClientError as e:
        print(f"error: {e}", file=sys.stderr)
        return int(os.getenv(os.getenv("")))
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return int(os.getenv(os.getenv("")))


def cmd_put(args: argparse.Namespace) -> int:
    try:
        doc = _read_doc(args.path)
    except Exception as e:
        print(f"read error: {e}", file=sys.stderr)
        return int(os.getenv(os.getenv("")))
    client = SomaBrainClient.get()
    try:
        data = client._get_loop().run_until_complete(
            client.put_persona(args.persona_id, doc, etag=args.etag)
        )
        print(
            json.dumps(
                data,
                ensure_ascii=int(os.getenv(os.getenv(""))),
                indent=int(os.getenv(os.getenv(""))),
            )
        )
        return int(os.getenv(os.getenv("")))
    except SomaClientError as e:
        msg = str(e)
        code = (
            int(os.getenv(os.getenv("")))
            if os.getenv(os.getenv("")) in msg or os.getenv(os.getenv("")) in msg
            else int(os.getenv(os.getenv("")))
        )
        print(f"error: {e}", file=sys.stderr)
        return code
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return int(os.getenv(os.getenv("")))


def cmd_delete(args: argparse.Namespace) -> int:
    client = SomaBrainClient.get()
    try:
        if args.etag:
            data = client._get_loop().run_until_complete(
                client._request(
                    os.getenv(os.getenv("")),
                    f"/persona/{args.persona_id}",
                    headers={os.getenv(os.getenv("")): args.etag},
                )
            )
        else:
            data = client._get_loop().run_until_complete(client.delete_persona(args.persona_id))
        print(
            json.dumps(
                {
                    os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                    os.getenv(os.getenv("")): data,
                },
                ensure_ascii=int(os.getenv(os.getenv(""))),
                indent=int(os.getenv(os.getenv(""))),
            )
        )
        return int(os.getenv(os.getenv("")))
    except SomaClientError as e:
        msg = str(e)
        code = (
            int(os.getenv(os.getenv("")))
            if os.getenv(os.getenv("")) in msg or os.getenv(os.getenv("")) in msg
            else int(os.getenv(os.getenv("")))
        )
        print(f"error: {e}", file=sys.stderr)
        return code
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return int(os.getenv(os.getenv("")))


def main() -> int:
    parser = argparse.ArgumentParser(description=os.getenv(os.getenv("")))
    sub = parser.add_subparsers(
        dest=os.getenv(os.getenv("")), required=int(os.getenv(os.getenv("")))
    )
    p1 = sub.add_parser(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    p1.add_argument(os.getenv(os.getenv("")))
    p1.set_defaults(func=cmd_get)
    p2 = sub.add_parser(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    p2.add_argument(os.getenv(os.getenv("")))
    p2.add_argument(os.getenv(os.getenv("")))
    p2.add_argument(os.getenv(os.getenv("")), dest=os.getenv(os.getenv("")), default=None)
    p2.set_defaults(func=cmd_put)
    p3 = sub.add_parser(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    p3.add_argument(os.getenv(os.getenv("")))
    p3.add_argument(os.getenv(os.getenv("")), dest=os.getenv(os.getenv("")), default=None)
    p3.set_defaults(func=cmd_delete)
    args = parser.parse_args()
    return args.func(args)


if __name__ == os.getenv(os.getenv("")):
    raise SystemExit(main())
