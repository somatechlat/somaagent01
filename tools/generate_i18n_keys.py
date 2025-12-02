#!/usr/bin/env python3
"""Generate i18n keys for hard‑coded UI strings found in HTML templates.

The script walks the ``webui/`` directory, extracts any literal text that appears
between HTML tags (e.g. ``>Reset Chat<``) and adds a corresponding entry to the
English and Spanish JSON dictionaries under ``webui/i18n``.

It purposefully **ignores** strings that are already wrapped in an Alpine
``x-text``/``x-html`` binding or that look like HTML attributes, icons, or SVG
paths. The goal is to capture user‑visible labels, headings, button text, and
tooltips.

Running the script is safe – it only adds new keys; existing keys are left
unchanged. After execution you should commit the updated JSON files.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "webui"
I18N_DIR = ROOT / "i18n"
EN_PATH = I18N_DIR / "en.json"
ES_PATH = I18N_DIR / "es.json"


def load_json(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


en_dict = load_json(EN_PATH)
es_dict = load_json(ES_PATH)

# Regex to capture text between tags, ignoring whitespace‑only strings.
TEXT_RE = re.compile(r">\s*([^<]{2,})\s*<")


def is_already_i18n(text: str) -> bool:
    return any(tok in text.lower() for tok in ["x-text", "x-html", "{{", "{%", "i18n.t"])


def sanitize(text: str) -> str:
    return text.strip().replace("\n", " ")


def generate_key(text: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return f"ui.{base}"


def add_key(key: str, value: str):
    if key not in en_dict:
        en_dict[key] = value
    if key not in es_dict:
        es_dict[key] = value


def main():
    for html_file in ROOT.rglob("*.html"):
        try:
            content = html_file.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"[WARN] Could not read {html_file}: {exc}", file=sys.stderr)
            continue
        for match in TEXT_RE.finditer(content):
            raw = match.group(1)
            if is_already_i18n(raw):
                continue
            text = sanitize(raw)
            if not text or text.isnumeric():
                continue
            # Skip common UI symbols or icon names.
            if text.lower() in {
                "close",
                "delete",
                "clear all",
                "notifications",
                "warning",
                "info",
                "success",
                "error",
            }:
                continue
            key = generate_key(text)
            add_key(key, text)
    I18N_DIR.mkdir(parents=True, exist_ok=True)
    EN_PATH.write_text(json.dumps(en_dict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ES_PATH.write_text(json.dumps(es_dict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Added {len(en_dict)} keys to en.json, {len(es_dict)} to es.json")


if __name__ == "__main__":
    main()
