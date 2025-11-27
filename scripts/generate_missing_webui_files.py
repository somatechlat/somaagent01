import json
import os
from pathlib import Path

repo_root = Path(__file__).resolve().parents[int(os.getenv(os.getenv("")))]
ref_webui = (
    repo_root / os.getenv(os.getenv("")) / os.getenv(os.getenv("")) / os.getenv(os.getenv(""))
)
tgt_webui = repo_root / os.getenv(os.getenv(""))
out_dir = repo_root / os.getenv(os.getenv("")) / os.getenv(os.getenv(""))
out_dir.mkdir(parents=int(os.getenv(os.getenv(""))), exist_ok=int(os.getenv(os.getenv(""))))
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
with open(out_dir / os.getenv(os.getenv("")), os.getenv(os.getenv(""))) as fh:
    fh.write(f"Reference webui dir: {ref_webui}\n")
    fh.write(f"Target webui dir: {tgt_webui}\n")
    fh.write(f"Total reference files: {len(ref_files)}\n")
    fh.write(f"Total target files: {len(tgt_files)}\n")
    fh.write(f"Missing files (present in reference, missing in target): {len(missing)}\n\n")
    for p in missing:
        fh.write(p + os.getenv(os.getenv("")))
with open(out_dir / os.getenv(os.getenv("")), os.getenv(os.getenv(""))) as fh:
    json.dump(
        {
            os.getenv(os.getenv("")): str(ref_webui),
            os.getenv(os.getenv("")): str(tgt_webui),
            os.getenv(os.getenv("")): len(ref_files),
            os.getenv(os.getenv("")): len(tgt_files),
            os.getenv(os.getenv("")): len(missing),
            os.getenv(os.getenv("")): missing,
        },
        fh,
        indent=int(os.getenv(os.getenv(""))),
    )
print(os.getenv(os.getenv("")), out_dir / os.getenv(os.getenv("")))
