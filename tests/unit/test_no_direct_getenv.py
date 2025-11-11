"""Enforce that production code does not call ``os.getenv`` directly.

The project mandates that all runtime configuration be accessed through the
central ``services.common.runtime_config.env`` helper. Direct ``os.getenv``
or ``os.environ.get`` calls are only permitted in a small whitelist of
bootstrap modules (settings, runtime_config, vault integration, etc.).

This test walks the ``services`` package (excluding the ``tests`` directory)
and asserts that no non‑whitelisted file contains such calls. It parses the
source with ``ast`` to reliably locate the calls regardless of formatting.
"""

import ast
import pathlib

# Relative paths (from repository root) that are allowed to use ``os.getenv``
WHITELISTED_PATHS = {
    "services/common/settings_sa01.py",
    "services/common/settings_base.py",
    "services/common/runtime_config.py",
    "services/common/vault_secrets.py",
}


def _is_whitelisted(file_path: pathlib.Path) -> bool:
    """Return ``True`` if ``file_path`` is in the whitelist.

    ``file_path`` is an absolute path; we compare its repository‑relative
    representation against ``WHITELISTED_PATHS``.
    """
    repo_root = pathlib.Path(__file__).parents[2]
    rel = file_path.relative_to(repo_root)
    return str(rel) in WHITELISTED_PATHS


def _find_env_calls(node: ast.AST) -> list[ast.Call]:
    """Recursively collect ``os.getenv`` and ``os.environ.get`` call nodes.

    The function returns a flat list of matching ``ast.Call`` objects.
    """
    calls: list[ast.Call] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Call):
            # Detect ``os.getenv``
            if (
                isinstance(child.func, ast.Attribute)
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == "os"
                and child.func.attr == "getenv"
            ):
                calls.append(child)
            # Detect ``os.environ.get``
            if (
                isinstance(child.func, ast.Attribute)
                and isinstance(child.func.value, ast.Attribute)
                and isinstance(child.func.value.value, ast.Name)
                and child.func.value.value.id == "os"
                and child.func.value.attr == "environ"
                and child.func.attr == "get"
            ):
                calls.append(child)
        # Recurse into all child nodes
        calls.extend(_find_env_calls(child))
    return calls


def test_no_direct_os_getenv_calls() -> None:
    """Fail if any non‑whitelisted production file uses ``os.getenv``.

    The test scans all ``.py`` files under ``services`` (excluding any that are
    inside a ``tests`` directory). Whitelisted modules are exempt because they
    are responsible for bootstrapping configuration.
    """
    repo_root = pathlib.Path(__file__).parents[2]
    services_dir = repo_root / "services"
    offending: dict[pathlib.Path, list[int]] = {}

    for py_file in services_dir.rglob("*.py"):
        # Skip test files and any generated caches
        if "tests" in py_file.parts:
            continue
        if py_file.name == "__init__.py" and py_file.parent.name == "__pycache__":
            continue
        if _is_whitelisted(py_file):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception:
            # If the file cannot be read we let the regular test suite surface
            # the problem; skip it here.
            continue
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            # Syntax errors are handled by the normal test run; ignore here.
            continue
        calls = _find_env_calls(tree)
        if calls:
            offending[py_file] = [c.lineno for c in calls]

    assert not offending, (
        "Direct os.getenv / os.environ.get calls found in production code: "
        + ", ".join(
            f"{p.relative_to(repo_root)} (lines {','.join(map(str, lines))})"
            for p, lines in offending.items()
        )
    )
