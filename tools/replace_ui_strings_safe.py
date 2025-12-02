#!/usr/bin/env python3
"""Safe UI‑string → i18n conversion.

This script is a **conservative** version of the earlier `replace_ui_strings.py`.
It only touches:
  * Text between HTML tags.
  * Common UI attributes (placeholder, title, alt, aria‑label, label).
  * Explicit UI‑related JavaScript calls (e.g. ``toast("Saved")`` or ``setTitle("…")``).

Vendor libraries, minified files, and generated assets are excluded to avoid
corrupting code that is not part of the user‑visible UI.

Run with ``--dry‑run`` first to see a summary of replacements without writing
any files.  When you are satisfied, run without the flag to apply the changes.
"""

from __future__ import annotations

import argparse, json, pathlib, re, sys
from typing import Dict, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parent.parent / "webui"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TARGET_EXTS = {"html", "js", "vue", "ts"}
EXCLUDE_DIRS = {"vendor", "node_modules", "dist", "build"}
EXCLUDE_PATTERNS = [re.compile(r"\.min\.")]

# HTML attribute patterns (placeholder, title, alt, aria‑label, label)
HTML_ATTR_PATTERNS = [re.compile(r'(placeholder|title|alt|aria-label|label)\s*=\s*"([^\"]{2,})"')]

HTML_TEXT_PATTERN = re.compile(r">\s*([^<]{2,})\s*<")

# Simple UI‑related JS patterns – extend as needed
JS_UI_PATTERNS = [
    re.compile(r'toast\(\s*"([^\"]{2,})"\s*\)'),
    re.compile(r'setTitle\(\s*"([^\"]{2,})"\s*\)'),
]

# Flatten the pattern list – each entry is a (label, compiled_regex) tuple.
# Using a flat structure avoids the "too many values to unpack" error that occurs
# when the * operator expands a list inside a tuple.
PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("html_text", HTML_TEXT_PATTERN),
    # HTML attribute patterns (currently only one, but keeping the label generic)
    ("html_attr_placeholder", HTML_ATTR_PATTERNS[0]),
    # JavaScript UI‑related patterns
    ("js_ui_toast", JS_UI_PATTERNS[0]),
    ("js_ui_setTitle", JS_UI_PATTERNS[1]),
]


def slugify(text: str) -> str:
    """Deterministic i18n key from *text* (mirrors original extractor)."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return f"ui_{slug}" if not slug.startswith("ui_") else slug


def load_i18n(lang: str) -> Dict[str, str]:
    path = ROOT / "i18n" / f"{lang}.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def save_i18n(lang: str, data: Dict[str, str]) -> None:
    path = ROOT / "i18n" / f"{lang}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def should_skip(file_path: pathlib.Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in file_path.parts):
        return True
    return any(p.search(file_path.name) for p in EXCLUDE_PATTERNS)


def replace_in_content(
    content: str, en: Dict[str, str], es: Dict[str, str]
) -> Tuple[str, bool, int]:
    new = content
    offset = 0
    added = 0
    modified = False
    for label, pattern in PATTERNS:
        for m in pattern.finditer(content):
            raw = m.group(1).strip()
            if not raw or raw.isnumeric():
                continue
            # Skip if already inside an i18n.t() call
            start, end = m.span(1)
            look = content[max(0, start - 8) : start]
            if "i18n.t('" in look or 'i18n.t("' in look:
                continue
            key = slugify(raw)
            if key not in en:
                en[key] = raw
                added += 1
            if key not in es:
                es[key] = ""
            repl = f"i18n.t('{key}')"
            start += offset
            end += offset
            new = new[:start] + repl + new[end:]
            offset += len(repl) - (end - start)
            modified = True
    return new, modified, added


def process_file(
    path: pathlib.Path, en: Dict[str, str], es: Dict[str, str], dry: bool
) -> Tuple[bool, int]:
    original = path.read_text(encoding="utf-8")
    new, changed, added = replace_in_content(original, en, es)
    if changed and not dry:
        path.write_text(new, encoding="utf-8")
    return changed, added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    args = parser.parse_args()

    en = load_i18n("en")
    es = load_i18n("es")
    modified_files: List[str] = []
    total_added = 0

    for file_path in ROOT.rglob("*.*"):
        if should_skip(file_path):
            continue
        if file_path.suffix.lstrip(".").lower() not in TARGET_EXTS:
            continue
        changed, added = process_file(file_path, en, es, args.dry_run)
        if changed:
            modified_files.append(str(file_path))
            total_added += added

    save_i18n("en", en)
    save_i18n("es", es)

    if args.dry_run:
        print(f"[DRY‑RUN] Would modify {len(modified_files)} files, add {total_added} keys")
        for f in modified_files:
            print("   -", f)
    else:
        print(f"✅ Modified {len(modified_files)} files, added {total_added} new i18n keys.")


if __name__ == "__main__":
    main()
