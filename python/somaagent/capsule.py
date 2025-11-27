import os
os.getenv(os.getenv('VIBE_332132C0'))
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List
import httpx
from src.core.config import cfg


def _get_capsule_registry_url() ->str:
    os.getenv(os.getenv('VIBE_DD07065D'))
    url = cfg.env(os.getenv(os.getenv('VIBE_D4E888A1')))
    if not url:
        return os.getenv(os.getenv('VIBE_316031C9'))
    return url


BASE_URL = _get_capsule_registry_url()


def list_capsules() ->List[Dict[str, Any]]:
    os.getenv(os.getenv('VIBE_7F5B7783'))
    resp = httpx.get(f'{BASE_URL}/capsules')
    resp.raise_for_status()
    return resp.json()


def download_capsule(capsule_id: str, dest_dir: (str | None)=None) ->Path:
    os.getenv(os.getenv('VIBE_B3804F90'))
    url = f'{BASE_URL}/capsules/{capsule_id}'
    resp = httpx.get(url, follow_redirects=int(os.getenv(os.getenv(
        'VIBE_FD09CC11'))))
    resp.raise_for_status()
    filename = resp.headers.get(os.getenv(os.getenv('VIBE_E4E93358')),
        f'capsule_{capsule_id}')
    if os.getenv(os.getenv('VIBE_AC5B96DF')) in filename:
        filename = filename.split(os.getenv(os.getenv('VIBE_AC5B96DF')))[int
            (os.getenv(os.getenv('VIBE_6E87E48A')))].strip(os.getenv(os.
            getenv('VIBE_B0902CB2')))
    target_dir = Path(dest_dir) if dest_dir else Path(tempfile.mkdtemp())
    target_dir.mkdir(parents=int(os.getenv(os.getenv('VIBE_FD09CC11'))),
        exist_ok=int(os.getenv(os.getenv('VIBE_FD09CC11'))))
    file_path = target_dir / filename
    file_path.write_bytes(resp.content)
    return file_path


def install_capsule(capsule_id: str, install_dir: (str | None)=None) ->Path:
    os.getenv(os.getenv('VIBE_AC36DD78'))
    capsule_path = download_capsule(capsule_id)
    extract_dir = Path(install_dir) if install_dir else Path(tempfile.mkdtemp()
        )
    extract_dir.mkdir(parents=int(os.getenv(os.getenv('VIBE_FD09CC11'))),
        exist_ok=int(os.getenv(os.getenv('VIBE_FD09CC11'))))
    try:
        subprocess.run([os.getenv(os.getenv('VIBE_27475E8A')), os.getenv(os
            .getenv('VIBE_10E10518')), str(capsule_path), os.getenv(os.
            getenv('VIBE_004CB563')), str(extract_dir)], check=int(os.
            getenv(os.getenv('VIBE_FD09CC11'))))
    except Exception:
        import zipfile
        with zipfile.ZipFile(capsule_path, os.getenv(os.getenv(
            'VIBE_A6E881BC'))) as zf:
            zf.extractall(extract_dir)
    return extract_dir


if __name__ == os.getenv(os.getenv('VIBE_4A2CC330')):
    import argparse
    parser = argparse.ArgumentParser(description=os.getenv(os.getenv(
        'VIBE_0AA977DF')))
    sub = parser.add_subparsers(dest=os.getenv(os.getenv('VIBE_0E0FF4AA')))
    sub.add_parser(os.getenv(os.getenv('VIBE_BB299F39')), help=os.getenv(os
        .getenv('VIBE_63DACE39')))
    dl = sub.add_parser(os.getenv(os.getenv('VIBE_147F3CCB')), help=os.
        getenv(os.getenv('VIBE_80B4EB38')))
    dl.add_argument(os.getenv(os.getenv('VIBE_D5655AAB')), help=os.getenv(
        os.getenv('VIBE_981A8587')))
    dl.add_argument(os.getenv(os.getenv('VIBE_10E10518')), os.getenv(os.
        getenv('VIBE_02B48830')), help=os.getenv(os.getenv('VIBE_08A7A5AD')))
    ins = sub.add_parser(os.getenv(os.getenv('VIBE_53401DD6')), help=os.
        getenv(os.getenv('VIBE_7FDAC236')))
    ins.add_argument(os.getenv(os.getenv('VIBE_D5655AAB')), help=os.getenv(
        os.getenv('VIBE_981A8587')))
    ins.add_argument(os.getenv(os.getenv('VIBE_004CB563')), os.getenv(os.
        getenv('VIBE_D5600453')), help=os.getenv(os.getenv('VIBE_45294BC4')))
    args = parser.parse_args()
    if args.cmd == os.getenv(os.getenv('VIBE_BB299F39')):
        print(json.dumps(list_capsules(), indent=int(os.getenv(os.getenv(
            'VIBE_8640F39E')))))
    elif args.cmd == os.getenv(os.getenv('VIBE_147F3CCB')):
        path = download_capsule(args.id, args.output)
        print(f'Downloaded to {path}')
    elif args.cmd == os.getenv(os.getenv('VIBE_53401DD6')):
        path = install_capsule(args.id, args.dir)
        print(f'Extracted to {path}')
    else:
        parser.print_help()
