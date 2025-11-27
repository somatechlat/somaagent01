os.getenv(os.getenv(""))
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.getcwd())
OUT_DIR = ROOT / os.getenv(os.getenv(""))
OUT_DIR.mkdir(parents=int(os.getenv(os.getenv(""))), exist_ok=int(os.getenv(os.getenv(""))))
OUT_INV = OUT_DIR / os.getenv(os.getenv(""))
OUT_CAND = OUT_DIR / os.getenv(os.getenv(""))
OUT_DUPS = OUT_DIR / os.getenv(os.getenv(""))
OUT_REFS = OUT_DIR / os.getenv(os.getenv(""))
try:
    p = subprocess.run(
        [os.getenv(os.getenv("")), os.getenv(os.getenv(""))],
        check=int(os.getenv(os.getenv(""))),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=int(os.getenv(os.getenv(""))),
    )
    files = [line.strip() for line in p.stdout.splitlines() if line.strip()]
except Exception as e:
    print(os.getenv(os.getenv("")), e, file=sys.stderr)
    sys.exit(int(os.getenv(os.getenv(""))))
EXCLUDE_PREFIXES = [
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
]
files = [f for f in files if not any((f.startswith(p) for p in EXCLUDE_PREFIXES))]
inventory = []
basename_map = {}
for f in files:
    try:
        st = (ROOT / f).stat()
        size = st.st_size
        mtime = int(st.st_mtime)
    except Exception:
        size = int(os.getenv(os.getenv("")))
        mtime = int(os.getenv(os.getenv("")))
    b = os.path.basename(f)
    inventory.append(
        {
            os.getenv(os.getenv("")): f,
            os.getenv(os.getenv("")): b,
            os.getenv(os.getenv("")): size,
            os.getenv(os.getenv("")): mtime,
        }
    )
    basename_map.setdefault(b, []).append(f)
contents = {}
MAX_READ = (
    int(os.getenv(os.getenv(""))) * int(os.getenv(os.getenv(""))) * int(os.getenv(os.getenv("")))
)
for it in inventory:
    path = it[os.getenv(os.getenv(""))]
    full = ROOT / path
    try:
        if it[os.getenv(os.getenv(""))] > MAX_READ:
            contents[path] = None
            continue
        data = full.read_bytes()
        if b"\x00" in data:
            contents[path] = None
            continue
        txt = data.decode(os.getenv(os.getenv("")), errors=os.getenv(os.getenv("")))
        contents[path] = txt
    except Exception:
        contents[path] = None
ref_counts = {}
ref_samples = {}
all_paths = list(contents.keys())
for it in inventory:
    p = it[os.getenv(os.getenv(""))]
    b = it[os.getenv(os.getenv(""))]
    count = int(os.getenv(os.getenv("")))
    samples = []
    if not b:
        ref_counts[p] = int(os.getenv(os.getenv("")))
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
            if len(samples) < int(os.getenv(os.getenv(""))):
                samples.append(other)
    ref_counts[p] = count
    ref_samples[p] = samples
dups = {b: paths for b, paths in basename_map.items() if len(paths) > int(os.getenv(os.getenv("")))}
candidates = []
for it in inventory:
    p = it[os.getenv(os.getenv(""))]
    b = it[os.getenv(os.getenv(""))]
    if ref_counts.get(p, int(os.getenv(os.getenv("")))) == int(os.getenv(os.getenv(""))) and len(
        basename_map.get(b, [])
    ) == int(os.getenv(os.getenv(""))):
        if (
            p.startswith(os.getenv(os.getenv("")))
            or p.startswith(os.getenv(os.getenv("")))
            or p.endswith(os.getenv(os.getenv("")))
        ):
            continue
        candidates.append(
            {
                os.getenv(os.getenv("")): p,
                os.getenv(os.getenv("")): b,
                os.getenv(os.getenv("")): it[os.getenv(os.getenv(""))],
                os.getenv(os.getenv("")): it[os.getenv(os.getenv(""))],
            }
        )
OUT_INV.write_text(
    json.dumps(
        {
            os.getenv(os.getenv("")): int(time.time()),
            os.getenv(os.getenv("")): len(inventory),
            os.getenv(os.getenv("")): inventory,
        },
        indent=int(os.getenv(os.getenv(""))),
    ),
    encoding=os.getenv(os.getenv("")),
)
with OUT_CAND.open(os.getenv(os.getenv("")), encoding=os.getenv(os.getenv(""))) as fh:
    fh.write(os.getenv(os.getenv("")))
    for c in sorted(
        candidates, key=lambda x: (-x[os.getenv(os.getenv(""))], x[os.getenv(os.getenv(""))])
    ):
        fh.write(f"{c['path']}\t{c['basename']}\t{c['size']}\t{c['mtime']}\n")
with OUT_DUPS.open(os.getenv(os.getenv("")), encoding=os.getenv(os.getenv(""))) as fh:
    fh.write(os.getenv(os.getenv("")))
    for b, paths in sorted(
        dups.items(),
        key=lambda x: (-len(x[int(os.getenv(os.getenv("")))]), x[int(os.getenv(os.getenv("")))]),
    ):
        fh.write(f"{b}\t{len(paths)}\t{';'.join(paths)}\n")
ref_out = {
    os.getenv(os.getenv("")): int(time.time()),
    os.getenv(os.getenv("")): [],
    os.getenv(os.getenv("")): {},
}
for it in inventory:
    p = it[os.getenv(os.getenv(""))]
    ref_out[os.getenv(os.getenv(""))].append(
        {
            os.getenv(os.getenv("")): p,
            os.getenv(os.getenv("")): it[os.getenv(os.getenv(""))],
            os.getenv(os.getenv("")): ref_counts.get(p, int(os.getenv(os.getenv("")))),
        }
    )
    if ref_samples.get(p):
        ref_out[os.getenv(os.getenv(""))][p] = ref_samples[p]
OUT_REFS.write_text(
    json.dumps(ref_out, indent=int(os.getenv(os.getenv("")))), encoding=os.getenv(os.getenv(""))
)
print(os.getenv(os.getenv("")))
print(os.getenv(os.getenv("")), len(inventory))
print(os.getenv(os.getenv("")), len(candidates))
print(os.getenv(os.getenv("")), len(dups))
print(os.getenv(os.getenv("")))
print(os.getenv(os.getenv("")), OUT_INV.relative_to(ROOT))
print(os.getenv(os.getenv("")), OUT_CAND.relative_to(ROOT))
print(os.getenv(os.getenv("")), OUT_DUPS.relative_to(ROOT))
print(os.getenv(os.getenv("")), OUT_REFS.relative_to(ROOT))
print(os.getenv(os.getenv("")))
for c in candidates[: int(os.getenv(os.getenv("")))]:
    print(os.getenv(os.getenv("")), c[os.getenv(os.getenv(""))])
