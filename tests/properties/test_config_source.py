"""Property 4: Configuration Single Source.

Validates: Requirements 4.1, 4.2

For any configuration access in the codebase, it SHALL import from
`src.core.config` and not from any other configuration module.

This test tracks migration progress from legacy config locations.
"""

import pathlib
from typing import Set

# Deprecated config imports that should be migrated to src.core.config
DEPRECATED_CONFIG_IMPORTS: Set[str] = {
    "python.helpers.settings",
    "from python.helpers.settings import",
    "from python.helpers import settings",
}

# Files allowed to import deprecated config (transitional)
ALLOWED_LEGACY_FILES: Set[str] = {
    # Test files
    "tests/",
    # Scripts
    "scripts/",
}

# Legacy usage temporarily allowed in UI settings router (UI schema conversion only)
SERVICES_ALLOWED: Set[str] = set()


def _is_allowed_file(rel_path: str) -> bool:
    """Check if file is allowed to use legacy config imports."""
    for allowed in ALLOWED_LEGACY_FILES:
        if rel_path.startswith(allowed) or rel_path == allowed:
            return True
    return False


def test_new_code_uses_core_config():
    """Verify new code in src/ uses src.core.config for configuration.

    Property 4: Configuration Single Source
    Validates: Requirements 4.1, 4.2

    Note: This test tracks migration progress. Files in python/ are
    transitionally allowed to use legacy imports until fully migrated.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    src_path = repo / "src"

    if not src_path.exists():
        return

    violations: list[str] = []

    for filepath in src_path.rglob("*.py"):
        rel_path = filepath.relative_to(repo).as_posix()

        if _is_allowed_file(rel_path):
            continue

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for deprecated in DEPRECATED_CONFIG_IMPORTS:
            if deprecated in content:
                violations.append(f"{rel_path}: uses deprecated '{deprecated}'")

    assert not violations, "New code should use src.core.config, not legacy imports:\n" + "\n".join(
        sorted(set(violations))
    )


def test_services_config_migration_tracking():
    """Track services/ migration to src.core.config.

    Enforces that services/ no longer import legacy python.helpers.settings
    except for explicitly allowed UI conversion paths.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    services_path = repo / "services"

    if not services_path.exists():
        return

    violations = []

    for filepath in services_path.rglob("*.py"):
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        has_legacy = any(dep in content for dep in DEPRECATED_CONFIG_IMPORTS)
        if has_legacy:
            rel = filepath.relative_to(repo).as_posix()
            if any(rel.startswith(p) for p in SERVICES_ALLOWED):
                continue
            violations.append(rel)

    assert not violations, "services/ files must not import legacy config modules:\n" + "\n".join(
        sorted(set(violations))
    )
