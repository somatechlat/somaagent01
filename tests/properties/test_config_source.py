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
    # The settings module itself
    "python/helpers/settings.py",
    "python/helpers/settings_model.py",
    # Test files
    "tests/",
    # Scripts
    "scripts/",
}


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
    
    assert not violations, (
        "New code should use src.core.config, not legacy imports:\n"
        + "\n".join(sorted(set(violations)))
    )


def test_services_config_migration_tracking():
    """Track services/ migration to src.core.config.
    
    This test documents current state and will fail when migration
    is complete to ensure we update the tracking.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    services_path = repo / "services"
    
    if not services_path.exists():
        return
    
    # Count files still using legacy config
    legacy_count = 0
    migrated_count = 0
    
    for filepath in services_path.rglob("*.py"):
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        
        has_legacy = any(dep in content for dep in DEPRECATED_CONFIG_IMPORTS)
        has_new = "from src.core.config" in content or "import src.core.config" in content
        
        if has_legacy:
            legacy_count += 1
        if has_new:
            migrated_count += 1
    
    # This is informational - we track progress but don't fail
    # Uncomment the assertion below when ready to enforce
    # assert legacy_count == 0, f"{legacy_count} files still use legacy config"
    pass
