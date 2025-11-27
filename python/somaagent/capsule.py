import os

os.getenv(os.getenv(""))
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import httpx

from src.core.config import cfg


def _get_capsule_registry_url() -> str:
    os.getenv(os.getenv(""))
    url = cfg.env(os.getenv(os.getenv("")))
    if not url:
        return os.getenv(os.getenv(""))
    return url


BASE_URL = _get_capsule_registry_url()


def list_capsules() -> List[Dict[str, Any]]:
    os.getenv(os.getenv(""))
    resp = httpx.get(f"{BASE_URL}/capsules")
    resp.raise_for_status()
    return resp.json()


def download_capsule(capsule_id: str, dest_dir: str | None = None) -> Path:
    os.getenv(os.getenv(""))
    url = f"{BASE_URL}/capsules/{capsule_id}"
    resp = httpx.get(url, follow_redirects=int(os.getenv(os.getenv(""))))
    resp.raise_for_status()
    filename = resp.headers.get(os.getenv(os.getenv("")), f"capsule_{capsule_id}")
    if os.getenv(os.getenv("")) in filename:
        filename = filename.split(os.getenv(os.getenv("")))[int(os.getenv(os.getenv("")))].strip(
            os.getenv(os.getenv(""))
        )
    target_dir = Path(dest_dir) if dest_dir else Path(tempfile.mkdtemp())
    target_dir.mkdir(parents=int(os.getenv(os.getenv(""))), exist_ok=int(os.getenv(os.getenv(""))))
    file_path = target_dir / filename
    file_path.write_bytes(resp.content)
    return file_path


def install_capsule(capsule_id: str, install_dir: str | None = None) -> Path:
    os.getenv(os.getenv(""))
    capsule_path = download_capsule(capsule_id)
    extract_dir = Path(install_dir) if install_dir else Path(tempfile.mkdtemp())
    extract_dir.mkdir(parents=int(os.getenv(os.getenv(""))), exist_ok=int(os.getenv(os.getenv(""))))
    try:
        subprocess.run(
            [
                os.getenv(os.getenv("")),
                os.getenv(os.getenv("")),
                str(capsule_path),
                os.getenv(os.getenv("")),
                str(extract_dir),
            ],
            check=int(os.getenv(os.getenv(""))),
        )
    except Exception:
        import zipfile

        with zipfile.ZipFile(capsule_path, os.getenv(os.getenv(""))) as zf:
            zf.extractall(extract_dir)
    return extract_dir


if __name__ == os.getenv(os.getenv("")):
    import argparse

    parser = argparse.ArgumentParser(description=os.getenv(os.getenv("")))
    sub = parser.add_subparsers(dest=os.getenv(os.getenv("")))
    sub.add_parser(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    dl = sub.add_parser(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    dl.add_argument(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    dl.add_argument(
        os.getenv(os.getenv("")), os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    ins = sub.add_parser(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    ins.add_argument(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    ins.add_argument(
        os.getenv(os.getenv("")), os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    args = parser.parse_args()
    if args.cmd == os.getenv(os.getenv("")):
        print(json.dumps(list_capsules(), indent=int(os.getenv(os.getenv("")))))
    elif args.cmd == os.getenv(os.getenv("")):
        path = download_capsule(args.id, args.output)
        print(f"Downloaded to {path}")
    elif args.cmd == os.getenv(os.getenv("")):
        path = install_capsule(args.id, args.dir)
        print(f"Extracted to {path}")
    else:
        parser.print_help()
