"""Property 2: Repository Pattern Consistency.

Validates: Requirements 11.1, 11.2, 11.3, 11.4

For any data access operation (Postgres, Redis, Kafka), the operation SHALL go
through a repository or adapter interface defined in `core/domain/ports/`.

This test verifies that the application layer does not directly import
infrastructure libraries.
"""

import ast
import pathlib
from typing import Set

# Direct infrastructure imports forbidden in application layer
FORBIDDEN_INFRA_IMPORTS: Set[str] = {
    # Database
    "asyncpg",
    "psycopg2",
    "sqlalchemy",
    # Cache
    "redis",
    "aioredis",
    # Message queue
    "aiokafka",
    "kafka",
    "confluent_kafka",
}


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
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def test_application_layer_no_direct_db_access():
    """Verify application layer has no direct database imports.
    
    Property 2: Repository Pattern Consistency
    Validates: Requirements 11.1, 11.2, 11.3, 11.4
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    app_path = repo / "src" / "core" / "application"
    
    if not app_path.exists():
        # Application layer not yet created - skip
        return
    
    violations: list[str] = []
    
    for filepath in app_path.rglob("*.py"):
        rel_path = filepath.relative_to(repo).as_posix()
        imports = _get_imports(filepath)
        
        for imp in imports:
            if imp in FORBIDDEN_INFRA_IMPORTS:
                violations.append(f"{rel_path}: imports '{imp}'")
    
    assert not violations, (
        "Application layer has forbidden direct infrastructure imports:\n"
        + "\n".join(sorted(set(violations)))
    )


def test_domain_layer_no_direct_db_access():
    """Verify domain layer has no direct database imports.
    
    Property 2 corollary: Domain layer must also be infrastructure-free.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    domain_path = repo / "src" / "core" / "domain"
    
    if not domain_path.exists():
        return
    
    violations: list[str] = []
    
    for filepath in domain_path.rglob("*.py"):
        rel_path = filepath.relative_to(repo).as_posix()
        imports = _get_imports(filepath)
        
        for imp in imports:
            if imp in FORBIDDEN_INFRA_IMPORTS:
                violations.append(f"{rel_path}: imports '{imp}'")
    
    assert not violations, (
        "Domain layer has forbidden direct infrastructure imports:\n"
        + "\n".join(sorted(set(violations)))
    )
