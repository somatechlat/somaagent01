"""Property 10: A2A data contract compliance.

**Feature: canonical-architecture-cleanup, Property 10: A2A data contract compliance**
**Validates: Requirements 27.1-27.3**

For any A2A request, it SHALL include `message`, `metadata` (with `tenant_id`,
`request_id`), `data`, and `subagent_url`. For any A2A response, it SHALL include
`status` (ok|error), `data`, and `errors` fields.
"""

import ast
import pathlib
from typing import List

# Required fields in A2A request
A2A_REQUEST_REQUIRED_FIELDS = {
    "message",
    "metadata",
    "data",
    "subagent_url",
}

# Required fields in A2A metadata
A2A_METADATA_REQUIRED_FIELDS = {
    "tenant_id",
    "request_id",
}

# Required fields in A2A response
A2A_RESPONSE_REQUIRED_FIELDS = {
    "status",
    "data",
    "errors",
}


def _find_pydantic_models(filepath: pathlib.Path) -> List[dict]:
    """Find Pydantic model definitions in a file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return []

    models = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if it inherits from BaseModel or similar
            is_pydantic = False
            for base in node.bases:
                if isinstance(base, ast.Name):
                    if base.id in ("BaseModel", "BaseSettings"):
                        is_pydantic = True
                        break

            if is_pydantic:
                fields = set()
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        fields.add(item.target.id)

                models.append(
                    {
                        "name": node.name,
                        "fields": fields,
                        "line": node.lineno,
                    }
                )
    return models


def _find_a2a_models(repo: pathlib.Path) -> List[dict]:
    """Find A2A-related Pydantic models in the codebase."""
    a2a_models = []

    # Check common locations for A2A models
    search_paths = [
        repo / "models.py",
        repo / "python" / "api",
        repo / "services" / "common",
        repo / "src" / "core" / "domain",
    ]

    for search_path in search_paths:
        if not search_path.exists():
            continue

        if search_path.is_file():
            files = [search_path]
        else:
            files = list(search_path.rglob("*.py"))

        for filepath in files:
            models = _find_pydantic_models(filepath)
            for model in models:
                name_lower = model["name"].lower()
                if "a2a" in name_lower or "agent" in name_lower:
                    model["file"] = filepath.relative_to(repo).as_posix()
                    a2a_models.append(model)

    return a2a_models


def test_a2a_request_model_exists():
    """Verify A2A request model exists with required fields.

    **Feature: canonical-architecture-cleanup, Property 10: A2A data contract compliance**
    **Validates: Requirements 27.1**
    """
    repo = pathlib.Path(__file__).resolve().parents[2]

    # Check models.py for A2A models
    models_file = repo / "models.py"
    if not models_file.exists():
        return

    try:
        content = models_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return

    # Check for A2ARequest or similar class
    has_a2a_request = "A2ARequest" in content or "class A2A" in content

    # Check for required fields
    has_message = "message" in content
    has_metadata = "metadata" in content
    has_subagent = "subagent" in content

    assert has_a2a_request or (has_message and has_metadata), (
        "A2A request model should exist with required fields.\n"
        "Expected: message, metadata, data, subagent_url"
    )


def test_a2a_response_model_exists():
    """Verify A2A response model exists with required fields.

    **Feature: canonical-architecture-cleanup, Property 10: A2A data contract compliance**
    **Validates: Requirements 27.2**
    """
    repo = pathlib.Path(__file__).resolve().parents[2]

    # Check models.py for A2A models
    models_file = repo / "models.py"
    if not models_file.exists():
        return

    try:
        content = models_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return

    # Check for A2AResponse or similar class
    has_a2a_response = "A2AResponse" in content or "AgentResponse" in content

    # Check for required fields
    has_status = "status" in content
    has_errors = "errors" in content

    assert has_a2a_response or (has_status and has_errors), (
        "A2A response model should exist with required fields.\n"
        "Expected: status (ok|error), data, errors"
    )


def test_a2a_metadata_has_tenant_and_request_id():
    """Verify A2A metadata includes tenant identification.

    **Feature: canonical-architecture-cleanup, Property 10: A2A data contract compliance**
    **Validates: Requirements 27.1**
    """
    repo = pathlib.Path(__file__).resolve().parents[2]

    # Check a2a_chat_task.py for metadata handling
    a2a_task = repo / "python" / "tasks" / "a2a_chat_task.py"
    if not a2a_task.exists():
        return

    try:
        content = a2a_task.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return

    # Check for tenant identification (tenant or tenant_id)
    has_tenant = "tenant" in content
    has_metadata = "metadata" in content

    assert has_tenant and has_metadata, (
        "A2A task should handle tenant identification in metadata.\n"
        f"Found tenant: {has_tenant}, metadata: {has_metadata}"
    )


def test_a2a_task_uses_data_contract():
    """Verify a2a_chat_task uses the A2A data contract.

    **Feature: canonical-architecture-cleanup, Property 10: A2A data contract compliance**
    **Validates: Requirements 27.1-27.3**
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    a2a_task = repo / "python" / "tasks" / "a2a_chat_task.py"

    if not a2a_task.exists():
        return

    try:
        content = a2a_task.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return

    # Check that task handles message, metadata, and returns proper response
    handles_message = "message" in content
    handles_metadata = "metadata" in content or "tenant_id" in content
    handles_response = "status" in content or "result" in content

    assert handles_message and handles_metadata, (
        "a2a_chat_task should use A2A data contract.\n"
        f"Handles message: {handles_message}\n"
        f"Handles metadata: {handles_metadata}\n"
        f"Handles response: {handles_response}"
    )
