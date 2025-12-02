#!/usr/bin/env python3
"""Utility to extract hard‑coded UI strings from the web UI.

It scans the `webui/` directory for JavaScript and HTML files, pulls out
string literals, and creates a skeleton `en.json` dictionary under
`webui/i18n/`. The generated keys are simple snake‑cased versions of the
string text; you should later rename them to a hierarchical structure
(e.g. `settings.save`).

The script is deliberately lightweight – it only uses the Python standard
library, so no extra dependencies are required.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "webui"

# Patterns to capture literal strings.
PATTERNS = [
    # JavaScript: double‑quoted strings that are at least 2 characters long.
    ("js", re.compile(r'"([^\\"]{2,})"')),
    # HTML: text between tags, ignoring whitespace‑only nodes.
    ("html", re.compile(r">\s*([^<]{2,})\s*<")),
]


def collect_strings() -> list[str]:
    """Walk the webui folder and collect unique UI strings.

    Returns a sorted list of distinct strings.
    """
    strings: set[str] = set()
    for file_path in ROOT.rglob("*.*"):
        # Determine file type by extension.
        ext = file_path.suffix.lstrip(".").lower()
        for typ, pattern in PATTERNS:
            if ext != typ:
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as exc:
                print(f"[WARN] Could not read {file_path}: {exc}", file=sys.stderr)
                continue
            for match in pattern.finditer(content):
                s = match.group(1).strip()
                # Skip numbers, empty strings, and obvious placeholders.
                if not s or s.isnumeric():
                    continue
                strings.add(s)
    return sorted(strings)


def main() -> None:
    strings = collect_strings()
    if not strings:
        print("No UI strings found.")
        return
    # Build a simple flat dictionary.
    en_dict: dict[str, str] = {}
    for s in strings:
        # Create a snake‑cased key prefixed with "ui_".
        key = "ui_" + re.sub(r"\s+", "_", s.lower())
        # Ensure uniqueness – if collision, append a number.
        orig_key = key
        i = 1
        while key in en_dict:
            key = f"{orig_key}_{i}"
            i += 1
        en_dict[key] = s

    i18n_dir = ROOT / "i18n"
    i18n_dir.mkdir(parents=True, exist_ok=True)
    en_path = i18n_dir / "en.json"
    en_path.write_text(json.dumps(en_dict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Extracted {len(en_dict)} strings → {en_path}")


if __name__ == "__main__":
    main()
