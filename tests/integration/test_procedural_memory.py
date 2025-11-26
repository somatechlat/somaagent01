import re
import uuid

import pytest
from services.common.procedure_repository import ensure_schema

from services.tool_executor.procedure_tools import (
    GetProcedureTool,
    SaveProcedureTool,
    SearchProceduresTool,
)
from src.core.config import cfg

# Use a unique ID for testing
TEST_ID = f"test_proc_{uuid.uuid4()}"


@pytest.mark.asyncio
async def test_procedural_memory_flow():
    dsn = cfg.settings().database.dsn
    # Adjust for host if needed
    if "@postgres" in dsn:
        if ":5432" in dsn:
            dsn = dsn.replace("@postgres:5432", "@localhost:20002")
        else:
            dsn = dsn.replace("@postgres", "@localhost:20002")

    print(f"Using DSN: {dsn}")

    # Ensure schema
    await ensure_schema(dsn)

    # 1. Save Procedure
    save_tool = SaveProcedureTool()
    result = await save_tool.execute(
        title=f"How to Deploy {TEST_ID}",
        description="Deployment steps for the app",
        steps=["Build Docker image", "Push to registry", "Apply k8s manifests"],
        tags=["devops", "deployment", TEST_ID],
    )
    print(f"Save Result: {result}")
    assert "saved with ID" in result

    # 2. Search Procedure
    search_tool = SearchProceduresTool()
    search_result = await search_tool.execute(TEST_ID)
    print(f"Search Result: {search_result}")
    assert f"How to Deploy {TEST_ID}" in search_result

    # Extract ID from search result
    match = re.search(r"ID: ([a-f0-9\-]+)", search_result)
    assert match
    proc_id = match.group(1)

    # 3. Get Procedure
    get_tool = GetProcedureTool()
    full_proc = await get_tool.execute(proc_id)
    print(f"Get Result: {full_proc}")
    assert f"How to Deploy {TEST_ID}" in full_proc
    assert "1. Build Docker image" in full_proc
    assert "2. Push to registry" in full_proc
