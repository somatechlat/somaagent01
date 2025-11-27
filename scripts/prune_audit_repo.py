os.getenv(os.getenv('VIBE_6FF6B2D7'))
import json
import os
import subprocess
import sys
import time
from pathlib import Path
ROOT = Path(os.getcwd())
OUT_DIR = ROOT / os.getenv(os.getenv('VIBE_DCBA56D1'))
OUT_DIR.mkdir(parents=int(os.getenv(os.getenv('VIBE_079F3BE1'))), exist_ok=
    int(os.getenv(os.getenv('VIBE_079F3BE1'))))
OUT_INV = OUT_DIR / os.getenv(os.getenv('VIBE_87DE8BC7'))
OUT_CAND = OUT_DIR / os.getenv(os.getenv('VIBE_BC8F8508'))
OUT_DUPS = OUT_DIR / os.getenv(os.getenv('VIBE_1FDE1966'))
OUT_REFS = OUT_DIR / os.getenv(os.getenv('VIBE_3FFC6062'))
try:
    p = subprocess.run([os.getenv(os.getenv('VIBE_471D42CF')), os.getenv(os
        .getenv('VIBE_C2C68EB4'))], check=int(os.getenv(os.getenv(
        'VIBE_079F3BE1'))), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=int(os.getenv(os.getenv('VIBE_079F3BE1'))))
    files = [line.strip() for line in p.stdout.splitlines() if line.strip()]
except Exception as e:
    print(os.getenv(os.getenv('VIBE_C17D13BE')), e, file=sys.stderr)
    sys.exit(int(os.getenv(os.getenv('VIBE_17A82D0F'))))
EXCLUDE_PREFIXES = [os.getenv(os.getenv('VIBE_A8EEFF3F')), os.getenv(os.
    getenv('VIBE_765DFA4D')), os.getenv(os.getenv('VIBE_AB7C7C7C')), os.
    getenv(os.getenv('VIBE_C06935CD')), os.getenv(os.getenv('VIBE_126C92E8'
    )), os.getenv(os.getenv('VIBE_E207AACE')), os.getenv(os.getenv(
    'VIBE_3612D61D')), os.getenv(os.getenv('VIBE_91DF48B8')), os.getenv(os.
    getenv('VIBE_68BCCD4F'))]
files = [f for f in files if not any(f.startswith(p) for p in EXCLUDE_PREFIXES)
    ]
inventory = []
basename_map = {}
for f in files:
    try:
        st = (ROOT / f).stat()
        size = st.st_size
        mtime = int(st.st_mtime)
    except Exception:
        size = int(os.getenv(os.getenv('VIBE_275CFC28')))
        mtime = int(os.getenv(os.getenv('VIBE_275CFC28')))
    b = os.path.basename(f)
    inventory.append({os.getenv(os.getenv('VIBE_CEE25080')): f, os.getenv(
        os.getenv('VIBE_30A3B8F2')): b, os.getenv(os.getenv('VIBE_7CA1B1C6'
        )): size, os.getenv(os.getenv('VIBE_BDC777C4')): mtime})
    basename_map.setdefault(b, []).append(f)
contents = {}
MAX_READ = int(os.getenv(os.getenv('VIBE_9531BDC2'))) * int(os.getenv(os.
    getenv('VIBE_EDA816DB'))) * int(os.getenv(os.getenv('VIBE_EDA816DB')))
for it in inventory:
    path = it[os.getenv(os.getenv('VIBE_CEE25080'))]
    full = ROOT / path
    try:
        if it[os.getenv(os.getenv('VIBE_7CA1B1C6'))] > MAX_READ:
            contents[path] = None
            continue
        data = full.read_bytes()
        if b'\x00' in data:
            contents[path] = None
            continue
        txt = data.decode(os.getenv(os.getenv('VIBE_48DD9187')), errors=os.
            getenv(os.getenv('VIBE_A787937F')))
        contents[path] = txt
    except Exception:
        contents[path] = None
ref_counts = {}
ref_samples = {}
all_paths = list(contents.keys())
for it in inventory:
    p = it[os.getenv(os.getenv('VIBE_CEE25080'))]
    b = it[os.getenv(os.getenv('VIBE_30A3B8F2'))]
    count = int(os.getenv(os.getenv('VIBE_275CFC28')))
    samples = []
    if not b:
        ref_counts[p] = int(os.getenv(os.getenv('VIBE_275CFC28')))
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
            if len(samples) < int(os.getenv(os.getenv('VIBE_4FC1D49C'))):
                samples.append(other)
    ref_counts[p] = count
    ref_samples[p] = samples
dups = {b: paths for b, paths in basename_map.items() if len(paths) > int(
    os.getenv(os.getenv('VIBE_17A82D0F')))}
candidates = []
for it in inventory:
    p = it[os.getenv(os.getenv('VIBE_CEE25080'))]
    b = it[os.getenv(os.getenv('VIBE_30A3B8F2'))]
    if ref_counts.get(p, int(os.getenv(os.getenv('VIBE_275CFC28')))) == int(os
        .getenv(os.getenv('VIBE_275CFC28'))) and len(basename_map.get(b, [])
        ) == int(os.getenv(os.getenv('VIBE_17A82D0F'))):
        if p.startswith(os.getenv(os.getenv('VIBE_62AC3453'))) or p.startswith(
            os.getenv(os.getenv('VIBE_FF451A29'))) or p.endswith(os.getenv(
            os.getenv('VIBE_9634237B'))):
            continue
        candidates.append({os.getenv(os.getenv('VIBE_CEE25080')): p, os.
            getenv(os.getenv('VIBE_30A3B8F2')): b, os.getenv(os.getenv(
            'VIBE_7CA1B1C6')): it[os.getenv(os.getenv('VIBE_7CA1B1C6'))],
            os.getenv(os.getenv('VIBE_BDC777C4')): it[os.getenv(os.getenv(
            'VIBE_BDC777C4'))]})
OUT_INV.write_text(json.dumps({os.getenv(os.getenv('VIBE_26041D21')): int(
    time.time()), os.getenv(os.getenv('VIBE_E3002DAA')): len(inventory), os
    .getenv(os.getenv('VIBE_988E880C')): inventory}, indent=int(os.getenv(
    os.getenv('VIBE_9531BDC2')))), encoding=os.getenv(os.getenv(
    'VIBE_48DD9187')))
with OUT_CAND.open(os.getenv(os.getenv('VIBE_0A1D150E')), encoding=os.
    getenv(os.getenv('VIBE_48DD9187'))) as fh:
    fh.write(os.getenv(os.getenv('VIBE_BEA198C1')))
    for c in sorted(candidates, key=lambda x: (-x[os.getenv(os.getenv(
        'VIBE_7CA1B1C6'))], x[os.getenv(os.getenv('VIBE_CEE25080'))])):
        fh.write(f"{c['path']}\t{c['basename']}\t{c['size']}\t{c['mtime']}\n")
with OUT_DUPS.open(os.getenv(os.getenv('VIBE_0A1D150E')), encoding=os.
    getenv(os.getenv('VIBE_48DD9187'))) as fh:
    fh.write(os.getenv(os.getenv('VIBE_5EC2A0D6')))
    for b, paths in sorted(dups.items(), key=lambda x: (-len(x[int(os.
        getenv(os.getenv('VIBE_17A82D0F')))]), x[int(os.getenv(os.getenv(
        'VIBE_275CFC28')))])):
        fh.write(f"{b}\t{len(paths)}\t{';'.join(paths)}\n")
ref_out = {os.getenv(os.getenv('VIBE_26041D21')): int(time.time()), os.
    getenv(os.getenv('VIBE_48E520B0')): [], os.getenv(os.getenv(
    'VIBE_4B43F294')): {}}
for it in inventory:
    p = it[os.getenv(os.getenv('VIBE_CEE25080'))]
    ref_out[os.getenv(os.getenv('VIBE_48E520B0'))].append({os.getenv(os.
        getenv('VIBE_CEE25080')): p, os.getenv(os.getenv('VIBE_30A3B8F2')):
        it[os.getenv(os.getenv('VIBE_30A3B8F2'))], os.getenv(os.getenv(
        'VIBE_48E520B0')): ref_counts.get(p, int(os.getenv(os.getenv(
        'VIBE_275CFC28'))))})
    if ref_samples.get(p):
        ref_out[os.getenv(os.getenv('VIBE_4B43F294'))][p] = ref_samples[p]
OUT_REFS.write_text(json.dumps(ref_out, indent=int(os.getenv(os.getenv(
    'VIBE_9531BDC2')))), encoding=os.getenv(os.getenv('VIBE_48DD9187')))
print(os.getenv(os.getenv('VIBE_A9964881')))
print(os.getenv(os.getenv('VIBE_525DF34A')), len(inventory))
print(os.getenv(os.getenv('VIBE_8D812D6A')), len(candidates))
print(os.getenv(os.getenv('VIBE_1DA78613')), len(dups))
print(os.getenv(os.getenv('VIBE_70DE9646')))
print(os.getenv(os.getenv('VIBE_0CEA93AC')), OUT_INV.relative_to(ROOT))
print(os.getenv(os.getenv('VIBE_0CEA93AC')), OUT_CAND.relative_to(ROOT))
print(os.getenv(os.getenv('VIBE_0CEA93AC')), OUT_DUPS.relative_to(ROOT))
print(os.getenv(os.getenv('VIBE_0CEA93AC')), OUT_REFS.relative_to(ROOT))
print(os.getenv(os.getenv('VIBE_9550E57F')))
for c in candidates[:int(os.getenv(os.getenv('VIBE_75721419')))]:
    print(os.getenv(os.getenv('VIBE_298E35AA')), c[os.getenv(os.getenv(
        'VIBE_CEE25080'))])
