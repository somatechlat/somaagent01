os.getenv(os.getenv('VIBE_B9E3EE98'))
from __future__ import annotations
import argparse
import json
import os
import sys
from typing import Any, Mapping
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError


def _dual_shape_payload(doc: Mapping[str, Any]) ->Mapping[str, Any]:
    os.getenv(os.getenv('VIBE_F8A11515'))
    try:
        if not isinstance(doc, dict):
            doc = dict(doc)
    except Exception:
        pass
    return {os.getenv(os.getenv('VIBE_B4743A4B')): doc, os.getenv(os.getenv
        ('VIBE_69457C94')): doc}


def _read_doc(path: str) ->Mapping[str, Any]:
    p = path.strip()
    if not p:
        raise FileNotFoundError(os.getenv(os.getenv('VIBE_75E9D0B3')))
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    with open(p, os.getenv(os.getenv('VIBE_52629AAB')), encoding=os.getenv(
        os.getenv('VIBE_54A20E62'))) as f:
        text = f.read()
    try:
        return json.loads(text)
    except Exception:
        try:
            import yaml
            data = yaml.safe_load(text)
            if not isinstance(data, dict):
                raise ValueError(os.getenv(os.getenv('VIBE_186637BE')))
            return data
        except Exception as e:
            raise ValueError(f'Failed to parse as JSON or YAML: {e}')


def cmd_version(args: argparse.Namespace) ->int:
    client = SomaBrainClient.get()
    try:
        res = sys.modules.get(os.getenv(os.getenv('VIBE_70C2992B'))).dumps(
            client.__class__)
    except Exception:
        pass
    try:
        data = None
        data = client._get_loop().run_until_complete(client.
            constitution_version())
        print(json.dumps(data, ensure_ascii=int(os.getenv(os.getenv(
            'VIBE_9FFFCC94'))), indent=int(os.getenv(os.getenv(
            'VIBE_1B0489B5')))))
        return int(os.getenv(os.getenv('VIBE_F1B8F4EF')))
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1B0489B5')))


def cmd_validate(args: argparse.Namespace) ->int:
    try:
        doc = _read_doc(args.path)
    except Exception as e:
        print(f'read error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1B0489B5')))
    client = SomaBrainClient.get()
    try:
        payload = _dual_shape_payload(doc)
        data = client._get_loop().run_until_complete(client.
            constitution_validate(payload))
        print(json.dumps(data, ensure_ascii=int(os.getenv(os.getenv(
            'VIBE_9FFFCC94'))), indent=int(os.getenv(os.getenv(
            'VIBE_1B0489B5')))))
        return int(os.getenv(os.getenv('VIBE_F1B8F4EF')))
    except SomaClientError as e:
        print(f'validation error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_63DCF7C6')))
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1B0489B5')))


def cmd_load(args: argparse.Namespace) ->int:
    if not args.force:
        print(os.getenv(os.getenv('VIBE_E4F87F40')), file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_4E43B6FA')))
    try:
        doc = _read_doc(args.path)
    except Exception as e:
        print(f'read error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1B0489B5')))
    client = SomaBrainClient.get()
    try:
        payload = _dual_shape_payload(doc)
        data = client._get_loop().run_until_complete(client.
            constitution_load(payload))
        print(json.dumps(data, ensure_ascii=int(os.getenv(os.getenv(
            'VIBE_9FFFCC94'))), indent=int(os.getenv(os.getenv(
            'VIBE_1B0489B5')))))
        try:
            policy = client._get_loop().run_until_complete(client.
                update_opa_policy())
            meta = {}
            if isinstance(policy, dict):
                meta = {k: policy.get(k) for k in (os.getenv(os.getenv(
                    'VIBE_721B39F3')), os.getenv(os.getenv('VIBE_1820B9B2')
                    ), os.getenv(os.getenv('VIBE_4FF1C00D'))) if k in policy}
            print(f'opa_policy_updated: true {json.dumps(meta)}', file=sys.
                stderr)
        except Exception as _e:
            print(os.getenv(os.getenv('VIBE_D0E717F2')), file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_F1B8F4EF')))
    except SomaClientError as e:
        print(f'load error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_E3C9619E')))
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1B0489B5')))


def cmd_status(_args: argparse.Namespace) ->int:
    client = SomaBrainClient.get()
    try:
        version = client._get_loop().run_until_complete(client.
            constitution_version())
        try:
            policy = client._get_loop().run_until_complete(client.opa_policy())
        except Exception:
            policy = {}
        out = {os.getenv(os.getenv('VIBE_A1AE7DB0')): version, os.getenv(os
            .getenv('VIBE_FC277F03')): {k: policy.get(k) for k in (os.
            getenv(os.getenv('VIBE_721B39F3')), os.getenv(os.getenv(
            'VIBE_1820B9B2')), os.getenv(os.getenv('VIBE_4FF1C00D'))) if
            isinstance(policy, dict)}}
        print(json.dumps(out, ensure_ascii=int(os.getenv(os.getenv(
            'VIBE_9FFFCC94'))), indent=int(os.getenv(os.getenv(
            'VIBE_1B0489B5')))))
        return int(os.getenv(os.getenv('VIBE_F1B8F4EF')))
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1B0489B5')))


def main() ->int:
    parser = argparse.ArgumentParser(description=os.getenv(os.getenv(
        'VIBE_0CC937D2')))
    sub = parser.add_subparsers(dest=os.getenv(os.getenv('VIBE_37A02C90')),
        required=int(os.getenv(os.getenv('VIBE_2874BA6C'))))
    p1 = sub.add_parser(os.getenv(os.getenv('VIBE_4FF1C00D')), help=os.
        getenv(os.getenv('VIBE_F5E29D06')))
    p1.set_defaults(func=cmd_version)
    p2 = sub.add_parser(os.getenv(os.getenv('VIBE_F3012956')), help=os.
        getenv(os.getenv('VIBE_E2811839')))
    p2.add_argument(os.getenv(os.getenv('VIBE_9F4B1497')), help=os.getenv(
        os.getenv('VIBE_6832EE9B')))
    p2.set_defaults(func=cmd_validate)
    p3 = sub.add_parser(os.getenv(os.getenv('VIBE_7EDBEDAC')), help=os.
        getenv(os.getenv('VIBE_1FFDCCA0')))
    p3.add_argument(os.getenv(os.getenv('VIBE_9F4B1497')), help=os.getenv(
        os.getenv('VIBE_6832EE9B')))
    p3.add_argument(os.getenv(os.getenv('VIBE_F4C0F404')), action=os.getenv
        (os.getenv('VIBE_BB09A7D2')), help=os.getenv(os.getenv(
        'VIBE_349787DF')))
    p3.set_defaults(func=cmd_load)
    p4 = sub.add_parser(os.getenv(os.getenv('VIBE_540BF821')), help=os.
        getenv(os.getenv('VIBE_435C4638')))
    p4.set_defaults(func=cmd_status)
    args = parser.parse_args()
    return args.func(args)


if __name__ == os.getenv(os.getenv('VIBE_0BA2F606')):
    raise SystemExit(main())
