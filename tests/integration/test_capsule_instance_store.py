"""Integration tests for CapsuleInstanceStore with real PostgreSQL.

Per VIBE Rules: NO mocks, real database, real operations.
Runs against Docker cluster: somaAgent01_postgres on port 20002.
"""

import asyncio
import uuid
import pytest
from datetime import datetime

from services.common.capsule_store import CapsuleStore, CapsuleRecord, CapsuleStatus
from services.common.capsule_instance_store import (
    CapsuleInstanceStore, CapsuleInstance, CapsuleInstanceScope
)


@pytest.mark.asyncio
async def test_capsule_instance_lifecycle():
    """Test full lifecycle: start, get, list, end."""
    # First create a capsule definition (required for FK)
    capsule_store = CapsuleStore()
    await capsule_store.ensure_schema()
    
    tenant_id = f"test_tenant_{uuid.uuid4().hex[:8]}"
    capsule_id = str(uuid.uuid4())
    
    definition = CapsuleRecord(
        capsule_id=capsule_id,
        tenant_id=tenant_id,
        name=f"test-capsule-{uuid.uuid4().hex[:8]}",
        version="1.0.0",
        status=CapsuleStatus.PUBLISHED,
    )
    await capsule_store.create(definition)
    
    # Now test instance store
    instance_store = CapsuleInstanceStore()
    await instance_store.ensure_schema()
    
    instance_id = str(uuid.uuid4())
    agent_id = f"agent_{uuid.uuid4().hex[:8]}"
    
    instance = CapsuleInstance(
        instance_id=instance_id,
        tenant_id=tenant_id,
        definition_id=capsule_id,
        scope=CapsuleInstanceScope.AGENT,
        scope_ref_id=agent_id,
        started_at=datetime.utcnow(),
        effective_config={"max_tokens": 4096, "temperature": 0.7},
        status="active",
    )
    
    # START instance
    created_id = await instance_store.start(instance)
    assert created_id == instance_id
    
    # GET instance
    fetched = await instance_store.get(instance_id)
    assert fetched is not None
    assert fetched.instance_id == instance_id
    assert fetched.tenant_id == tenant_id
    assert fetched.definition_id == capsule_id
    assert fetched.scope == CapsuleInstanceScope.AGENT
    assert fetched.scope_ref_id == agent_id
    assert fetched.status == "active"
    assert fetched.effective_config["max_tokens"] == 4096
    assert fetched.ended_at is None
    
    # LIST active instances
    active = await instance_store.list_active(tenant_id)
    assert len(active) >= 1
    found = next((i for i in active if i.instance_id == instance_id), None)
    assert found is not None
    
    # LIST by definition
    by_def = await instance_store.list_by_definition(capsule_id)
    assert len(by_def) >= 1
    
    # LIST by scope
    by_scope = await instance_store.list_by_scope(CapsuleInstanceScope.AGENT, agent_id)
    assert len(by_scope) >= 1
    
    # END instance
    ended = await instance_store.end(instance_id, status="completed")
    assert ended is True
    
    # Verify ended
    after_end = await instance_store.get(instance_id)
    assert after_end.status == "completed"
    assert after_end.ended_at is not None
    
    # No longer in active list
    active_after = await instance_store.list_active(tenant_id)
    found_after = next((i for i in active_after if i.instance_id == instance_id), None)
    assert found_after is None
    
    print(f"✅ CapsuleInstance lifecycle test passed for {instance_id}")


if __name__ == "__main__":
    asyncio.run(test_capsule_instance_lifecycle())
    print("✅ All capsule instance integration tests passed")
