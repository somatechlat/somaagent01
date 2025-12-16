"""Integration tests for CapsuleStore with real PostgreSQL.

Per VIBE Rules: NO mocks, real database, real operations.
"""

import asyncio
import uuid
import pytest

from services.common.capsule_store import CapsuleStore, CapsuleRecord, CapsuleStatus


@pytest.mark.asyncio
async def test_capsule_store_crud():
    """Test full CRUD lifecycle for capsule definitions."""
    store = CapsuleStore()
    await store.ensure_schema()
    
    # Generate unique test data
    tenant_id = f"test_tenant_{uuid.uuid4().hex[:8]}"
    capsule_id = str(uuid.uuid4())
    name = f"test-capsule-{uuid.uuid4().hex[:8]}"
    version = "1.0.0"
    
    # Create a record with all fields
    record = CapsuleRecord(
        capsule_id=capsule_id,
        tenant_id=tenant_id,
        name=name,
        version=version,
        status=CapsuleStatus.DRAFT,
        description="Test capsule for integration testing",
        allowed_tools=["web_search", "code_exec"],
        prohibited_tools=["file_delete"],
        max_wall_clock_seconds=1800,
        egress_mode="restricted",
        data_classification="internal",
        retention_policy_days=30,
    )
    
    # CREATE
    created_id = await store.create(record)
    assert created_id == capsule_id
    
    # READ by ID
    fetched = await store.get(capsule_id)
    assert fetched is not None
    assert fetched.capsule_id == capsule_id
    assert fetched.tenant_id == tenant_id
    assert fetched.name == name
    assert fetched.version == version
    assert fetched.status == CapsuleStatus.DRAFT
    assert fetched.allowed_tools == ["web_search", "code_exec"]
    assert fetched.prohibited_tools == ["file_delete"]
    assert fetched.max_wall_clock_seconds == 1800
    assert fetched.egress_mode == "restricted"
    
    # READ by tenant/name/version
    by_name = await store.get_by_name_version(tenant_id, name, version)
    assert by_name is not None
    assert by_name.capsule_id == capsule_id
    
    # LIST by tenant
    capsules = await store.list(tenant_id=tenant_id)
    assert len(capsules) >= 1
    found = next((c for c in capsules if c.capsule_id == capsule_id), None)
    assert found is not None
    
    # INSTALL
    installed = await store.install(capsule_id)
    assert installed is True
    
    # Verify installed flag
    after_install = await store.get(capsule_id)
    assert after_install.installed is True
    
    # PUBLISH
    published = await store.publish(capsule_id)
    assert published is True
    
    # Verify status changed
    after_publish = await store.get(capsule_id)
    assert after_publish.status == CapsuleStatus.PUBLISHED
    
    # DEPRECATE
    deprecated = await store.deprecate(capsule_id)
    assert deprecated is True
    
    # Verify status changed
    after_deprecate = await store.get(capsule_id)
    assert after_deprecate.status == CapsuleStatus.DEPRECATED
    
    print(f"✅ Capsule CRUD test passed for {capsule_id}")


@pytest.mark.asyncio
async def test_capsule_uniqueness_constraint():
    """Test that tenant/name/version uniqueness is enforced."""
    store = CapsuleStore()
    await store.ensure_schema()
    
    tenant_id = f"test_tenant_{uuid.uuid4().hex[:8]}"
    name = f"unique-capsule-{uuid.uuid4().hex[:8]}"
    version = "1.0.0"
    
    # First insert should succeed
    record1 = CapsuleRecord(
        capsule_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=name,
        version=version,
    )
    await store.create(record1)
    
    # Second insert with same tenant/name/version should fail
    record2 = CapsuleRecord(
        capsule_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=name,
        version=version,
    )
    
    with pytest.raises(Exception):  # asyncpg.UniqueViolationError
        await store.create(record2)
    
    print(f"✅ Uniqueness constraint test passed for {name}")


if __name__ == "__main__":
    asyncio.run(test_capsule_store_crud())
    asyncio.run(test_capsule_uniqueness_constraint())
    print("✅ All capsule integration tests passed")
