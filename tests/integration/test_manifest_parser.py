"""Integration tests for ManifestParser with real PostgreSQL.

Per VIBE Rules: NO mocks, real database, real operations.
Runs against Docker cluster: somaAgent01_postgres on port 20002.
"""

import asyncio
import uuid
import pytest

from services.common.manifest_parser import (
    ManifestParser, ManifestValidationError, parse_manifest
)
from services.common.capsule_store import CapsuleStore, CapsuleStatus


VALID_MANIFEST_YAML = """
id: "{capsule_id}"
name: "test-capsule"
version: "1.0.0"
description: "Test capsule for integration testing"

# Tool Policy
allowed_tools:
  - web_search
  - code_exec
prohibited_tools:
  - file_delete
tool_risk_profile: standard

# Resource Limits
max_wall_clock_seconds: 1800
max_concurrent_nodes: 3

# Network Policy
egress_mode: restricted
allowed_domains:
  - "*.example.com"
  - "api.openai.com"

# Policy & Guardrails
opa_policy_packages:
  - soma/capsule_security

# HITL
default_hitl_mode: optional
max_pending_hitl: 5

# Classification
data_classification: internal
retention_policy_days: 90
"""


INVALID_MANIFEST_YAML = """
name: "invalid-capsule"
# Missing id and version
egress_mode: "invalid_value"
tool_risk_profile: "not_valid"
max_wall_clock_seconds: -100
"""


PROD_RESTRICTED_MANIFEST = """
id: "prod-test"
name: "prod-capsule"
version: "1.0.0"
egress_mode: open
default_hitl_mode: none
tool_risk_profile: critical
"""


@pytest.mark.asyncio
async def test_parse_valid_manifest():
    """Test parsing a valid manifest YAML."""
    capsule_id = str(uuid.uuid4())
    yaml_content = VALID_MANIFEST_YAML.format(capsule_id=capsule_id)
    
    parser = ManifestParser(environment="DEV")
    data = parser.parse_string(yaml_content)
    
    result = parser.validate(data)
    assert result.valid is True
    assert len(result.errors) == 0
    
    print(f"✅ Valid manifest parsed successfully")


@pytest.mark.asyncio
async def test_parse_invalid_manifest():
    """Test validation catches invalid fields."""
    parser = ManifestParser(environment="DEV")
    data = parser.parse_string(INVALID_MANIFEST_YAML)
    
    result = parser.validate(data)
    assert result.valid is False
    assert len(result.errors) > 0
    
    # Should catch: missing id, invalid egress_mode, invalid tool_risk_profile, negative integer
    error_text = " ".join(result.errors)
    assert "id" in error_text.lower() or "required" in error_text.lower()
    assert "egress_mode" in error_text
    
    print(f"✅ Invalid manifest correctly rejected with {len(result.errors)} errors")


@pytest.mark.asyncio
async def test_prod_restrictions():
    """Test PROD environment restrictions."""
    parser = ManifestParser(environment="PROD")
    data = parser.parse_string(PROD_RESTRICTED_MANIFEST)
    
    result = parser.validate(data)
    assert result.valid is False
    
    # Should reject: open egress in PROD, no HITL for critical risk
    error_text = " ".join(result.errors)
    assert "egress" in error_text.lower() or "open" in error_text.lower()
    
    print(f"✅ PROD restrictions correctly enforced with {len(result.errors)} errors")


@pytest.mark.asyncio
async def test_manifest_to_capsule_record():
    """Test converting manifest to CapsuleRecord and persisting."""
    tenant_id = f"test_tenant_{uuid.uuid4().hex[:8]}"
    capsule_id = str(uuid.uuid4())
    yaml_content = VALID_MANIFEST_YAML.format(capsule_id=capsule_id)
    
    # Parse and persist
    record = await parse_manifest(
        content=yaml_content,
        tenant_id=tenant_id,
        environment="DEV",
        persist=True
    )
    
    assert record.capsule_id == capsule_id
    assert record.tenant_id == tenant_id
    assert record.name == "test-capsule"
    assert record.version == "1.0.0"
    assert record.egress_mode == "restricted"
    assert record.tool_risk_profile == "standard"
    assert "web_search" in record.allowed_tools
    assert "file_delete" in record.prohibited_tools
    
    # Verify persisted to DB
    store = CapsuleStore()
    fetched = await store.get(capsule_id)
    assert fetched is not None
    assert fetched.name == "test-capsule"
    
    print(f"✅ Manifest converted to CapsuleRecord and persisted: {capsule_id}")


if __name__ == "__main__":
    asyncio.run(test_parse_valid_manifest())
    asyncio.run(test_parse_invalid_manifest())
    asyncio.run(test_prod_restrictions())
    asyncio.run(test_manifest_to_capsule_record())
    print("✅ All manifest parser integration tests passed")
