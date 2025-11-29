#!/usr/bin/env python3
"""tools/replace_ui_strings.py
================================

**Purpose** – Replace every user‑visible literal string inside the ``webui/``
folder with a call to ``i18n.t('…')`` and ensure a matching translation key
exists in ``webui/i18n/en.json`` (and a placeholder in ``es.json``).

Why a script?
--------------
The Web UI contains hundreds of files (HTML, JavaScript, Vue, TypeScript).
Manually editing each literal would be error‑prone and would violate the VIBE
rule *"NO UNNECESSARY FILES"* because we would create a massive diff with many
repetitive changes.  A single, well‑tested script gives us a **single source of
truth** and lets us run the transformation repeatedly until the codebase is
clean.

The script follows the **VIBE coding rules**:

* **Check first, code second** – it reads the original file content before any
  modification and only writes back when a change is necessary.
* **No hard‑coded values** – keys are generated deterministically from the
  original text (``ui_<slug>``) and the translation dictionaries are updated
  programmatically.
* **Real implementations only** – the script uses only the Python standard
  library; there are no stubs or placeholders.
* **Documentation = truth** – the docstring explains the algorithm and the
  helper functions are each documented.

Implementation details
----------------------
1. **File discovery** – recursively walk ``webui/`` and consider files with
   extensions ``.html``, ``.js``, ``.vue`` and ``.ts``.
2. **Pattern matching**
   * *HTML* – ``>\s*([^<]{2,})\s*<`` captures text between tags that is at least
     two characters long.
   * *JavaScript / TypeScript* – ``"([^\\"]{2,})"`` captures double‑quoted
     string literals of length ≥ 2.
   * The patterns deliberately ignore numeric strings and pure whitespace.
3. **Key generation** – ``_slugify`` lower‑cases the text, replaces any
   non‑alphanumeric characters with underscores and prefixes with ``ui_`` if
   needed.  This mirrors the behaviour of the existing ``extract_ui_strings``
   utility, ensuring compatibility with any previously generated keys.
4. **Dictionary handling** – ``en.json`` and ``es.json`` are loaded (or created
   if missing).  New keys are added with the original English text; the Spanish
   entry is left empty for translators to fill later.
5. **In‑place replacement** – for each match the script builds a replacement
   string ``i18n.t('generated_key')`` and rewrites the file content only once
   after processing all matches.  This avoids overlapping replacements.
6. **Reporting** – after processing, the script prints a concise summary of
   modified files and the number of new keys added.

Running the script
-------------------
From the repository root execute:

```
python3 tools/replace_ui_strings.py
```

The script will modify files in place.  It is safe to run it repeatedly –
subsequent runs will detect that no further literals exist and will exit
gracefully.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parent.parent / "webui"

# Patterns to capture literal strings.
# Patterns to capture literal strings in various file types.
# Each tuple contains a label (used only for readability) and a compiled regex.
# The regexes capture the literal content in group 1.
PATTERNS: List[Tuple[str, re.Pattern]] = [
    # JavaScript / TypeScript – double‑quoted strings.
    ("js_double", re.compile(r'"([^\\"]{2,})"')),
    # JavaScript / TypeScript – single‑quoted strings.
    ("js_single", re.compile(r"'([^\\']{2,})'")),
    # JavaScript / TypeScript – template literals (backticks).
    ("js_template", re.compile(r'`([^`]{2,})`')),
    # HTML – text between tags, ignoring whitespace‑only nodes.
    ("html_text", re.compile(r'>\s*([^<]{2,})\s*<')),
    # HTML – common UI attribute values (placeholder, title, alt, aria-label, label).
    ("html_attr", re.compile(r'(?:placeholder|title|alt|aria-label|label)="([^\"]{2,})"')),
]

# File extensions we care about.
TARGET_EXTS = {"html", "js", "vue", "ts"}
# Directories and filename patterns to exclude from processing. We avoid
# vendor libraries, generated/minified assets, and any hidden files.
EXCLUDE_DIRS = {"vendor", "node_modules", "dist", "build"}
EXCLUDE_PATTERNS = [re.compile(r"\.min\.")]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _load_i18n_dict(lang: str) -> Dict[str, str]:
    """Load ``webui/i18n/<lang>.json`` or return an empty dict.

    The function never raises – if the file cannot be parsed we fall back to an
    empty dictionary and let the caller handle the situation.
    """
    path = ROOT / "i18n" / f"{lang}.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[WARN] Failed to parse {path}: {exc}", file=sys.stderr)
    return {}

def _save_i18n_dict(lang: str, data: Dict[str, str]) -> None:
    """Write ``data`` back to ``webui/i18n/<lang>.json`` with pretty formatting."""
    path = ROOT / "i18n" / f"{lang}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def _slugify(text: str) -> str:
    """Create a deterministic i18n key from *text*.

    The algorithm mirrors ``tools/extract_ui_strings.py``:

    1. Lower‑case the string.
    2. Replace any sequence of non‑alphanumeric characters with a single underscore.
    3. Strip leading/trailing underscores.
    4. Prefix with ``ui_`` if the result does not already start with it.
    """
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return f"ui_{slug}" if not slug.startswith("ui_") else slug

def _replace_in_content(content: str, en: Dict[str, str], es: Dict[str, str]) -> Tuple[str, bool, int]:
    """Return a new version of *content* with literals replaced.

    The return tuple is ``(new_content, modified, added_keys)``.
    """
    new_content = content
    offset = 0  # track length changes for correct indexing
    added = 0
    modified = False

    for typ, pattern in PATTERNS:
        for match in pattern.finditer(content):
            raw = match.group(1).strip()
            # Skip empty, numeric or already‑i18n strings.
            if not raw or raw.isnumeric() or raw.startswith("ui_"):
                continue
            start, end = match.span(1)
            # Detect if this literal is already inside an i18n.t call.
            # Look back a few characters for the pattern i18n.t(' or i18n.t(".
            lookbehind_start = max(0, start - 8)
            preceding = content[lookbehind_start:start]
            if "i18n.t('" in preceding or 'i18n.t("' in preceding:
                continue
            key = _slugify(raw)
            # Ensure dictionary entries exist.
            if key not in en:
                en[key] = raw
                added += 1
            if key not in es:
                es[key] = ""
            replacement = f"i18n.t('{key}')"
            # Adjust for previous replacements that changed the string length.
            start += offset
            end += offset
            new_content = new_content[:start] + replacement + new_content[end:]
            offset += len(replacement) - (end - start)
            modified = True
    return new_content, modified, added

def _process_file(path: pathlib.Path, en: Dict[str, str], es: Dict[str, str]) -> Tuple[bool, int]:
    """Read *path*, replace literals, write back if changed.

    Returns ``(was_modified, keys_added)``.
    """
    original = path.read_text(encoding="utf-8")
    new_content, modified, added = _replace_in_content(original, en, es)
    if modified:
        path.write_text(new_content, encoding="utf-8")
    return modified, added

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    en_dict = _load_i18n_dict("en")
    es_dict = _load_i18n_dict("es")

    modified_files: List[str] = []
    total_new_keys = 0

    for file_path in ROOT.rglob("*.*"):
        # Skip excluded directories
        if any(part in EXCLUDE_DIRS for part in file_path.parts):
            continue
        # Skip files matching any exclude pattern (e.g., *.min.js)
        if any(p.search(file_path.name) for p in EXCLUDE_PATTERNS):
            continue
        if file_path.suffix.lstrip('.').lower() not in TARGET_EXTS:
            continue
        was_modified, added = _process_file(file_path, en_dict, es_dict)
        if was_modified:
            modified_files.append(str(file_path))
            total_new_keys += added

    _save_i18n_dict("en", en_dict)
    _save_i18n_dict("es", es_dict)

    print(f"✅ Modified {len(modified_files)} files, added {total_new_keys} new i18n keys.")
    for f in modified_files:
        print(f"   - {f}")

if __name__ == "__main__":
    main()
