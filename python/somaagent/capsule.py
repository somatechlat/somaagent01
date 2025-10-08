"""Utility SDK for interacting with the Capsule Registry service.
Provides high‑level functions to list, download, and install capsule artifacts.
The functions use the public HTTP API exposed by ``services/capsule_registry/main.py``.
"""

import os
import json
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any

import httpx

# Base URL – can be overridden via env var for testing / staging.
BASE_URL = os.getenv("CAPSULE_REGISTRY_URL", "http://localhost:8000")


def list_capsules() -> List[Dict[str, Any]]:
    """Return a list of capsule metadata dictionaries.

    The endpoint ``GET /capsules`` returns a JSON array of objects matching the
    ``CapsuleMeta`` model defined in the service.
    """
    resp = httpx.get(f"{BASE_URL}/capsules")
    resp.raise_for_status()
    return resp.json()


def download_capsule(capsule_id: str, dest_dir: str | None = None) -> Path:
    """Download the capsule file for ``capsule_id``.

    Args:
        capsule_id: The UUID of the capsule to retrieve.
        dest_dir: Optional directory to write the file into. If omitted, a
            temporary directory is created and the path is returned.

    Returns:
        Path to the downloaded file.
    """
    url = f"{BASE_URL}/capsules/{capsule_id}"
    resp = httpx.get(url, follow_redirects=True)
    resp.raise_for_status()
    # The response is a streamed file; ``httpx`` already provides the content.
    filename = resp.headers.get("content-disposition", f"capsule_{capsule_id}")
    # Strip any surrounding quotes or filename= prefix.
    if "filename=" in filename:
        filename = filename.split("filename=")[1].strip('"')
    target_dir = Path(dest_dir) if dest_dir else Path(tempfile.mkdtemp())
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / filename
    file_path.write_bytes(resp.content)
    return file_path


def install_capsule(capsule_id: str, install_dir: str | None = None) -> Path:
    """Download and extract a capsule into ``install_dir``.

    Capsules are expected to be zip archives containing the payload. The function
    downloads the capsule, extracts it, and returns the path to the extracted
    directory.
    """
    capsule_path = download_capsule(capsule_id)
    extract_dir = Path(install_dir) if install_dir else Path(tempfile.mkdtemp())
    extract_dir.mkdir(parents=True, exist_ok=True)
    # Use ``unzip`` if available; fallback to Python's zipfile.
    try:
        subprocess.run(["unzip", "-o", str(capsule_path), "-d", str(extract_dir)], check=True)
    except Exception:
        import zipfile
        with zipfile.ZipFile(capsule_path, "r") as zf:
            zf.extractall(extract_dir)
    return extract_dir

# Convenience wrapper for CLI usage
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simple capsule SDK CLI")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("list", help="List available capsules")
    dl = sub.add_parser("download", help="Download a capsule file")
    dl.add_argument("id", help="Capsule UUID")
    dl.add_argument("-o", "--output", help="Output directory")
    ins = sub.add_parser("install", help="Download and extract a capsule")
    ins.add_argument("id", help="Capsule UUID")
    ins.add_argument("-d", "--dir", help="Installation directory")
    args = parser.parse_args()
    if args.cmd == "list":
        print(json.dumps(list_capsules(), indent=2))
    elif args.cmd == "download":
        path = download_capsule(args.id, args.output)
        print(f"Downloaded to {path}")
    elif args.cmd == "install":
        path = install_capsule(args.id, args.dir)
        print(f"Extracted to {path}")
    else:
        parser.print_help()
