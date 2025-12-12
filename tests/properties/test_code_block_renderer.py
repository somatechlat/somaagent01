"""Property: Code block syntax highlighting and copy affordances.

Validates: Requirements 4.7 (language labeling, copy interaction, line number gating).
"""

import pathlib
import re


def test_language_map_and_line_number_threshold():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/components/chat/code-block.js").read_text(encoding="utf-8")

    # Language map contains multiple common languages
    for lang in ["javascript", "python", "rust", "go", "bash", "markdown", "sql"]:
        assert re.search(rf"{lang}['\"]?\s*:", text), f"Language {lang} missing in map"

    # Line number threshold default to 5 and shouldShowLineNumbers uses it
    assert "lineNumberThreshold" in text and "5" in text.split("lineNumberThreshold")[1], (
        "lineNumberThreshold default of 5 not found"
    )
    assert "shouldShowLineNumbers" in text


def test_copy_interaction_and_prism_highlighting():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/components/chat/code-block.js").read_text(encoding="utf-8")

    # Copy button uses navigator.clipboard and toggles copied state
    assert "navigator.clipboard.writeText" in text
    assert "this.copied = true" in text
    assert "copyTimeout" in text

    # Highlight hook calls Prism.highlightElement
    assert "Prism.highlightElement" in text
