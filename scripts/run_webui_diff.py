#!/usr/bin/env python3
import difflib
import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "tmp" / "agent_zero"
TGT = ROOT / "webui"
OUT = ROOT / "tmp" / "compare"
DIFFS = OUT / "diffs"
ASSET = OUT / "asset_diffs"
LEGACY = OUT / "legacy_calls.txt"
REPORT = OUT / "report.md"

TEXT_EXTS = {".html", ".htm", ".js", ".css", ".json", ".md", ".txt", ".vue", ".ts", ".jsx", ".tsx"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".ico", ".webp"}

os.makedirs(DIFFS, exist_ok=True)
os.makedirs(ASSET, exist_ok=True)


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_text(path: Path):
    try:
        suf = path.suffix.lower()
        if suf in TEXT_EXTS:
            return True
        # small heuristic: try decode a small chunk
        with path.open("rb") as f:
            sample = f.read(4096)
        sample.decode("utf-8")
        return True
    except Exception:
        return False


def relpaths(base: Path):
    files = []
    if not base.exists():
        return files
    for p in base.rglob("*"):
        if p.is_file():
            files.append(p.relative_to(base))
    return sorted(files)


ref_files = relpaths(REF)
tgt_files = relpaths(TGT)
all_files = sorted(set(ref_files) | set(tgt_files))

report_lines = []
legacy_lines = []
report_lines.append("# WebUI Diff Report\n")
report_lines.append(f"Reference dir: {REF}\n")
report_lines.append(f"Target dir: {TGT}\n")
report_lines.append(f"Total reference files: {len(ref_files)}")
report_lines.append(f"Total target files: {len(tgt_files)}")
report_lines.append("")

for rel in all_files:
    refp = REF / rel
    tgtp = TGT / rel
    in_ref = refp.exists()
    in_tgt = tgtp.exists()
    if not in_ref:
        report_lines.append(f"- ONLY IN TARGET: {rel}")
        continue
    if not in_tgt:
        report_lines.append(f"- ONLY IN REFERENCE: {rel}")
        continue
    # both exist
    try:
        ref_hash = sha256(refp)
        tgt_hash = sha256(tgtp)
    except Exception as e:
        report_lines.append(f"- ERROR hashing {rel}: {e}")
        continue
    if ref_hash == tgt_hash:
        # identical
        continue
    # differ
    suf = rel.suffix.lower()
    safe_rel_path = str(rel).replace(os.sep, "__")
    diff_out = DIFFS / (safe_rel_path + ".diff")
    os.makedirs(diff_out.parent, exist_ok=True)
    report_lines.append(f"- DIFFER: {rel}  (ref-sha={ref_hash[:10]} tgt-sha={tgt_hash[:10]})")
    if suf in IMAGE_EXTS:
        # asset differing, write checksums
        with (ASSET / (safe_rel_path + ".txt")).open("w") as f:
            f.write(f"ref: {refp}\n")
            f.write(f"tgt: {tgtp}\n")
            f.write(f"ref_sha256: {ref_hash}\n")
            f.write(f"tgt_sha256: {tgt_hash}\n")
        continue
    # try to produce text diff
    if is_text(refp) and is_text(tgtp):
        try:
            with refp.open("r", encoding="utf-8", errors="replace") as f:
                ref_lines = f.read().splitlines(True)
            with tgtp.open("r", encoding="utf-8", errors="replace") as f:
                tgt_lines = f.read().splitlines(True)
            ud = difflib.unified_diff(ref_lines, tgt_lines, fromfile=str(refp), tofile=str(tgtp))
            with diff_out.open("w", encoding="utf-8") as of:
                of.writelines(ud)
        except Exception as e:
            report_lines.append(f"  - failed to diff as text: {e}")
    else:
        with diff_out.open("w") as of:
            of.write(f"BINARY DIFFER: ref_sha={ref_hash}\n tgt_sha={tgt_hash}\n")

# scan for legacy network calls in target and reference
patterns = ["api/", "http://", "https://", "localhost", "127.0.0.1", "old", "legacy"]
for base in (REF, TGT):
    for p in relpaths(base):
        full = base / p
        if not is_text(full):
            continue
        try:
            text = full.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pat in patterns:
                if pat in line:
                    legacy_lines.append(f"{base}/{p}:{i}: {pat}: {line.strip()}")

# write outputs
with open(REPORT, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

with open(LEGACY, "w", encoding="utf-8") as f:
    f.write("\n".join(legacy_lines))

print("Diff run complete.")
print(f"Wrote report to: {REPORT}")
print(f"Per-file diffs (text/binary markers) in: {DIFFS}")
print(f"Asset diff metadata in: {ASSET}")
print(f"Legacy/network calls in: {LEGACY}")
