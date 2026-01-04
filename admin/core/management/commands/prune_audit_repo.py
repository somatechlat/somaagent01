#!/usr/bin/env python3
"""Non-destructive prune audit script writing outputs into repo ./tmp directory.
Produces:
 - ./tmp/prune_inventory.json
 - ./tmp/prune_candidates.tsv
 - ./tmp/prune_dups.tsv
 - ./tmp/prune_refs.json

Run from repo root.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.getcwd())
OUT_DIR = ROOT / "tmp"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_INV = OUT_DIR / "prune_inventory.json"
OUT_CAND = OUT_DIR / "prune_candidates.tsv"
OUT_DUPS = OUT_DIR / "prune_dups.tsv"
OUT_REFS = OUT_DIR / "prune_refs.json"

# 1) Get tracked files
try:
    p = subprocess.run(
        ["git", "ls-files"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    files = [line.strip() for line in p.stdout.splitlines() if line.strip()]
except Exception as e:
    print("Failed to run git ls-files:", e, file=sys.stderr)
    sys.exit(1)

# Filter out obvious large or vendor dirs to speed scanning
# Also ignore the repository `tmp/` output directory as requested
EXCLUDE_PREFIXES = [
    "node_modules/",
    ".git/",
    "venv/",
    "env/",
    "__pycache__/",
    "dist/",
    "build/",
    "site-packages/",
    "tmp/",
]
files = [f for f in files if not any(f.startswith(p) for p in EXCLUDE_PREFIXES)]

# 2) Build inventory
inventory = []
basename_map = {}
for f in files:
    try:
        st = (ROOT / f).stat()
        size = st.st_size
        mtime = int(st.st_mtime)
    except Exception:
        size = 0
        mtime = 0
    b = os.path.basename(f)
    inventory.append({"path": f, "basename": b, "size": size, "mtime": mtime})
    basename_map.setdefault(b, []).append(f)

# 3) Read text contents for search index (skip large files and non-text)
contents = {}
MAX_READ = 2 * 1024 * 1024  # 2 MB per file max
for it in inventory:
    path = it["path"]
    full = ROOT / path
    try:
        if it["size"] > MAX_READ:
            contents[path] = None
            continue
        data = full.read_bytes()
        # heuristic: check for null bytes
        if b"\0" in data:
            contents[path] = None
            continue
        txt = data.decode("utf-8", errors="ignore")
        contents[path] = txt
    except Exception:
        contents[path] = None

# 4) Count references of each file's basename across other files
ref_counts = {}
ref_samples = {}
all_paths = list(contents.keys())
for it in inventory:
    p = it["path"]
    b = it["basename"]
    count = 0
    samples = []
    if not b:
        ref_counts[p] = 0
        ref_samples[p] = []
        continue
    for other in all_paths:
        if other == p:
            continue
        txt = contents.get(other)
        if not txt:
            continue
        if b in txt:
            found = txt.count(b)
            count += found
            if len(samples) < 5:
                samples.append(other)
    ref_counts[p] = count
    ref_samples[p] = samples

# 5) Detect duplicates by basename
dups = {b: paths for b, paths in basename_map.items() if len(paths) > 1}

# 6) Produce candidate list heuristics
candidates = []
for it in inventory:
    p = it["path"]
    b = it["basename"]
    if ref_counts.get(p, 0) == 0 and len(basename_map.get(b, [])) == 1:
        # skip tests, fixtures, docs heuristically
        if p.startswith("tests/") or p.startswith("docs/") or p.endswith(".md"):
            continue
        candidates.append({"path": p, "basename": b, "size": it["size"], "mtime": it["mtime"]})

# 7) Write outputs
OUT_INV.write_text(
    json.dumps(
        {"generated_at": int(time.time()), "count": len(inventory), "inventory": inventory},
        indent=2,
    ),
    encoding="utf-8",
)

with OUT_CAND.open("w", encoding="utf-8") as fh:
    fh.write("path\tbasename\tsize\tmtime\n")
    for c in sorted(candidates, key=lambda x: (-x["size"], x["path"])):
        fh.write(f"{c['path']}\t{c['basename']}\t{c['size']}\t{c['mtime']}\n")

with OUT_DUPS.open("w", encoding="utf-8") as fh:
    fh.write("basename\tpaths_count\tpaths\n")
    for b, paths in sorted(dups.items(), key=lambda x: (-len(x[1]), x[0])):
        fh.write(f"{b}\t{len(paths)}\t{';'.join(paths)}\n")

# 8) Summarize and write refs
ref_out = {"generated_at": int(time.time()), "refs": [], "samples": {}}
for it in inventory:
    p = it["path"]
    ref_out["refs"].append({"path": p, "basename": it["basename"], "refs": ref_counts.get(p, 0)})
    if ref_samples.get(p):
        ref_out["samples"][p] = ref_samples[p]

OUT_REFS.write_text(json.dumps(ref_out, indent=2), encoding="utf-8")

print("Scan complete")
print("Tracked files scanned:", len(inventory))
print("Candidates (heuristic, refs==0, non-duplicate):", len(candidates))
print("Duplicate basename groups:", len(dups))
print("\nOutputs under tmp/:")
print(" -", OUT_INV.relative_to(ROOT))
print(" -", OUT_CAND.relative_to(ROOT))
print(" -", OUT_DUPS.relative_to(ROOT))
print(" -", OUT_REFS.relative_to(ROOT))
print("\nPreview top 20 candidates:")
for c in candidates[:20]:
    print(" *", c["path"])