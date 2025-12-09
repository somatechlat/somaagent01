"""Property 7: No Direct Infrastructure Imports in Domain.

Validates: Requirements 11.4, 12.4

For any module in `core/domain/`, it SHALL NOT import from `core/infrastructure/`
or external infrastructure libraries (asyncpg, redis, aiokafka, httpx for direct calls).
"""

import ast
import pathlib
from typing import Set

# Infrastructure modules that domain layer must not import
FORBIDDEN_IMPORTS: Set[str] = {
    # Direct infrastructure imports
    "asyncpg",
    "redis",
    "aiokafka",
    "kafka",
    "psycopg2",
    "sqlalchemy",
    # Internal infrastructure layer
    "src.core.infrastructure",
    "core.infrastructure",
    # External service clients (should go through ports)
    "services.common.session_repository",
    "services.common.event_bus",
    "services.common.policy_client",
    "python.integrations.somabrain_client",
}

# Known exceptions - files that violate domain isolation
# This should be EMPTY - all violations must be fixed, not tracked
KNOWN_DOMAIN_VIOLATIONS: Set[str] = set()


def _get_imports(filepath: pathlib.Path) -> Set[str]:
    """Extract all import module names from a Python file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return set()

    imports: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
            imports.add(node.module)
    return imports


def test_domain_has_no_infrastructure_imports():
    """Verify domain layer has no direct infrastructure imports.
    
    Property 7: No Direct Infrastructure Imports in Domain
    Validates: Requirements 11.4, 12.4
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    domain_path = repo / "src" / "core" / "domain"
    
    if not domain_path.exists():
        return
    
    violations: list[str] = []
    
    for filepath in domain_path.rglob("*.py"):
        if filepath.name == "__init__.py":
            continue
            
        rel_path = filepath.relative_to(repo).as_posix()
        
        # Skip known violations (tracked architectural debt)
        if rel_path in KNOWN_DOMAIN_VIOLATIONS:
            continue
            
        imports = _get_imports(filepath)
        
        for imp in imports:
            for forbidden in FORBIDDEN_IMPORTS:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    violations.append(f"{rel_path}: imports '{imp}'")
    
    assert not violations, (
        "Domain layer has forbidden infrastructure imports:\n"
        + "\n".join(sorted(set(violations)))
    )


def test_domain_ports_are_abstract():
    """Verify all port interfaces are abstract base classes.
    
    Property 7 corollary: Ports must be abstract interfaces.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    ports_path = repo / "src" / "core" / "domain" / "ports"
    
    if not ports_path.exists():
        return
    
    violations: list[str] = []
    
    for filepath in ports_path.rglob("*.py"):
        if filepath.name == "__init__.py":
            continue
            
        rel_path = filepath.relative_to(repo).as_posix()
        
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            continue
        
        # Find classes that end with "Port" and verify they inherit from ABC
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith("Port"):
                has_abc = False
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "ABC":
                        has_abc = True
                        break
                if not has_abc:
                    violations.append(f"{rel_path}: {node.name} does not inherit from ABC")
    
    assert not violations, (
        "Port interfaces must inherit from ABC:\n"
        + "\n".join(sorted(set(violations)))
    )
