os.getenv(os.getenv('VIBE_4CD4C058'))
from __future__ import annotations
import argparse
import json
import os
import sys
from typing import Any, Mapping
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError


def _read_doc(path: str) ->Mapping[str, Any]:
    p = path.strip()
    if not p:
        raise FileNotFoundError(os.getenv(os.getenv('VIBE_F92BFA0F')))
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    with open(p, os.getenv(os.getenv('VIBE_1F91A9DD')), encoding=os.getenv(
        os.getenv('VIBE_B5AE2993'))) as f:
        text = f.read()
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(os.getenv(os.getenv('VIBE_1767FCD8')))
        return data
    except Exception as e:
        raise ValueError(f'Failed to parse persona JSON: {e}')


def cmd_get(args: argparse.Namespace) ->int:
    client = SomaBrainClient.get()
    try:
        data = client._get_loop().run_until_complete(client.get_persona(
            args.persona_id))
        print(json.dumps(data, ensure_ascii=int(os.getenv(os.getenv(
            'VIBE_7E92D194'))), indent=int(os.getenv(os.getenv(
            'VIBE_B27DE607')))))
        return int(os.getenv(os.getenv('VIBE_F227BBF0')))
    except SomaClientError as e:
        print(f'error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_B27DE607')))
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_B27DE607')))


def cmd_put(args: argparse.Namespace) ->int:
    try:
        doc = _read_doc(args.path)
    except Exception as e:
        print(f'read error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_B27DE607')))
    client = SomaBrainClient.get()
    try:
        data = client._get_loop().run_until_complete(client.put_persona(
            args.persona_id, doc, etag=args.etag))
        print(json.dumps(data, ensure_ascii=int(os.getenv(os.getenv(
            'VIBE_7E92D194'))), indent=int(os.getenv(os.getenv(
            'VIBE_B27DE607')))))
        return int(os.getenv(os.getenv('VIBE_F227BBF0')))
    except SomaClientError as e:
        msg = str(e)
        code = int(os.getenv(os.getenv('VIBE_15D2E77C'))) if os.getenv(os.
            getenv('VIBE_321F44CF')) in msg or os.getenv(os.getenv(
            'VIBE_54C709FD')) in msg else int(os.getenv(os.getenv(
            'VIBE_B27DE607')))
        print(f'error: {e}', file=sys.stderr)
        return code
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_B27DE607')))


def cmd_delete(args: argparse.Namespace) ->int:
    client = SomaBrainClient.get()
    try:
        if args.etag:
            data = client._get_loop().run_until_complete(client._request(os
                .getenv(os.getenv('VIBE_DE1E1037')),
                f'/persona/{args.persona_id}', headers={os.getenv(os.getenv
                ('VIBE_024FA6EC')): args.etag}))
        else:
            data = client._get_loop().run_until_complete(client.
                delete_persona(args.persona_id))
        print(json.dumps({os.getenv(os.getenv('VIBE_90D4ED52')): int(os.
            getenv(os.getenv('VIBE_1F763784'))), os.getenv(os.getenv(
            'VIBE_A8406E3E')): data}, ensure_ascii=int(os.getenv(os.getenv(
            'VIBE_7E92D194'))), indent=int(os.getenv(os.getenv(
            'VIBE_B27DE607')))))
        return int(os.getenv(os.getenv('VIBE_F227BBF0')))
    except SomaClientError as e:
        msg = str(e)
        code = int(os.getenv(os.getenv('VIBE_15D2E77C'))) if os.getenv(os.
            getenv('VIBE_321F44CF')) in msg or os.getenv(os.getenv(
            'VIBE_54C709FD')) in msg else int(os.getenv(os.getenv(
            'VIBE_B27DE607')))
        print(f'error: {e}', file=sys.stderr)
        return code
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_B27DE607')))


def main() ->int:
    parser = argparse.ArgumentParser(description=os.getenv(os.getenv(
        'VIBE_4500E1C8')))
    sub = parser.add_subparsers(dest=os.getenv(os.getenv('VIBE_AEF096F0')),
        required=int(os.getenv(os.getenv('VIBE_1F763784'))))
    p1 = sub.add_parser(os.getenv(os.getenv('VIBE_5AE45EB8')), help=os.
        getenv(os.getenv('VIBE_B61360D2')))
    p1.add_argument(os.getenv(os.getenv('VIBE_091A0CAF')))
    p1.set_defaults(func=cmd_get)
    p2 = sub.add_parser(os.getenv(os.getenv('VIBE_2C1CD5B9')), help=os.
        getenv(os.getenv('VIBE_1B391E0A')))
    p2.add_argument(os.getenv(os.getenv('VIBE_091A0CAF')))
    p2.add_argument(os.getenv(os.getenv('VIBE_269E509E')))
    p2.add_argument(os.getenv(os.getenv('VIBE_D55BDE21')), dest=os.getenv(
        os.getenv('VIBE_2E122528')), default=None)
    p2.set_defaults(func=cmd_put)
    p3 = sub.add_parser(os.getenv(os.getenv('VIBE_FB9CD6C8')), help=os.
        getenv(os.getenv('VIBE_6F8AA23D')))
    p3.add_argument(os.getenv(os.getenv('VIBE_091A0CAF')))
    p3.add_argument(os.getenv(os.getenv('VIBE_D55BDE21')), dest=os.getenv(
        os.getenv('VIBE_2E122528')), default=None)
    p3.set_defaults(func=cmd_delete)
    args = parser.parse_args()
    return args.func(args)


if __name__ == os.getenv(os.getenv('VIBE_D24E417E')):
    raise SystemExit(main())
