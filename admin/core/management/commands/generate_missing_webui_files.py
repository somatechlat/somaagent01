"""Module generate_missing_webui_files."""

#!/usr/bin/env python3
import json
import os
from pathlib import Path

"""
Management command to identify and generate missing WebUI files.
Compares reference implementation with target directory.
"""

repo_root = Path(__file__).resolve().parents[1]
ref_webui = repo_root / "tmp" / "agent_zero" / "webui"
tgt_webui = repo_root / "webui"
out_dir = repo_root / "tmp" / "compare"
out_dir.mkdir(parents=True, exist_ok=True)

ref_files = []
for root, dirs, files in os.walk(ref_webui):
    for f in files:
        p = Path(root) / f
        rel = p.relative_to(ref_webui).as_posix()
        ref_files.append(rel)

tgt_files = set()
for root, dirs, files in os.walk(tgt_webui):
    for f in files:
        p = Path(root) / f
        rel = p.relative_to(tgt_webui).as_posix()
        tgt_files.add(rel)

missing = [p for p in sorted(ref_files) if p not in tgt_files]

with open(out_dir / "missing_webui_files.txt", "w") as fh:
    fh.write(f"Reference webui dir: {ref_webui}\n")
    fh.write(f"Target webui dir: {tgt_webui}\n")
    fh.write(f"Total reference files: {len(ref_files)}\n")
    fh.write(f"Total target files: {len(tgt_files)}\n")
    fh.write(f"Missing files (present in reference, missing in target): {len(missing)}\n\n")
    for p in missing:
        fh.write(p + "\n")

with open(out_dir / "missing_webui_files.json", "w") as fh:
    json.dump(
        {
            "ref_dir": str(ref_webui),
            "tgt_dir": str(tgt_webui),
            "ref_count": len(ref_files),
            "tgt_count": len(tgt_files),
            "missing_count": len(missing),
            "missing": missing,
        },
        fh,
        indent=2,
    )

print("Wrote missing files:", out_dir / "missing_webui_files.txt")