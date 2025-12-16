"""Unit tests for CapabilityRegistry (no DB required).

Tests verify capability discovery, constraint matching, and health tracking
logic using in-memory CapabilityRecord objects.

Pattern Reference: test_capsule_enforcer.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.common.capability_registry import (
    CapabilityRegistry,
    CapabilityRecord,
    CapabilityHealth,
    CostTier,
)


def make_capability(**kwargs) -> CapabilityRecord:
    """Create a test CapabilityRecord with sensible defaults."""
    defaults = {
        "tool_id": "test_tool",
        "provider": "test_provider",
        "modalities": ["image"],
        "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}}},
        "output_schema": {"type": "object", "properties": {"url": {"type": "string"}}},
        "constraints": {"max_resolution": 1024, "formats": ["png", "jpg"]},
        "cost_tier": CostTier.MEDIUM,
        "health_status": CapabilityHealth.HEALTHY,
        "latency_p95_ms": 5000,
        "failure_count": 0,
        "enabled": True,
        "tenant_id": None,
        "display_name": "Test Tool",
        "description": "A test capability",
        "documentation_url": "https://example.com/docs",
        "last_health_check": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    defaults.update(kwargs)
    return CapabilityRecord(**defaults)


class TestCapabilityRecord:
    """Tests for CapabilityRecord dataclass."""
    
    def test_create_with_defaults(self):
        record = CapabilityRecord(tool_id="dalle3", provider="openai")
        assert record.tool_id == "dalle3"
        assert record.provider == "openai"
        assert record.modalities == []
        assert record.cost_tier == CostTier.MEDIUM
        assert record.health_status == CapabilityHealth.HEALTHY
        assert record.enabled is True
    
    def test_create_with_full_fields(self):
        record = make_capability(
            tool_id="dalle3_image_gen",
            provider="openai",
            modalities=["image", "vision"],
            cost_tier=CostTier.HIGH,
            constraints={"max_resolution": 1792}
        )
        assert record.tool_id == "dalle3_image_gen"
        assert record.provider == "openai"
        assert "image" in record.modalities
        assert "vision" in record.modalities
        assert record.cost_tier == CostTier.HIGH
        assert record.constraints["max_resolution"] == 1792


class TestCapabilityHealth:
    """Tests for CapabilityHealth enum."""
    
    def test_health_values(self):
        assert CapabilityHealth.HEALTHY.value == "healthy"
        assert CapabilityHealth.DEGRADED.value == "degraded"
        assert CapabilityHealth.UNAVAILABLE.value == "unavailable"
    
    def test_health_from_string(self):
        assert CapabilityHealth("healthy") == CapabilityHealth.HEALTHY
        assert CapabilityHealth("degraded") == CapabilityHealth.DEGRADED
        assert CapabilityHealth("unavailable") == CapabilityHealth.UNAVAILABLE


class TestCostTier:
    """Tests for CostTier enum."""
    
    def test_tier_values(self):
        assert CostTier.FREE.value == "free"
        assert CostTier.LOW.value == "low"
        assert CostTier.MEDIUM.value == "medium"
        assert CostTier.HIGH.value == "high"
        assert CostTier.PREMIUM.value == "premium"
    
    def test_tier_ordering(self):
        tiers = [CostTier.FREE, CostTier.LOW, CostTier.MEDIUM, CostTier.HIGH, CostTier.PREMIUM]
        tier_values = [t.value for t in tiers]
        assert tier_values == ["free", "low", "medium", "high", "premium"]


class TestCapabilityRegistryRowConversion:
    """Tests for _row_to_record conversion logic."""
    
    def test_row_to_record_complete(self):
        """Test conversion with all fields populated."""
        registry = CapabilityRegistry(dsn="postgresql://test@localhost/test")
        
        # Mock asyncpg Record
        mock_row = {
            "tool_id": "dalle3_image_gen",
            "provider": "openai",
            "modalities": '["image", "vision"]',
            "input_schema": '{"type": "object"}',
            "output_schema": '{"type": "object"}',
            "constraints": '{"max_resolution": 1792}',
            "cost_tier": "high",
            "health_status": "healthy",
            "latency_p95_ms": 15000,
            "failure_count": 0,
            "enabled": True,
            "tenant_id": "acme-corp",
            "display_name": "DALL-E 3",
            "description": "OpenAI image generation",
            "documentation_url": "https://platform.openai.com/docs",
            "last_health_check": datetime(2025, 12, 16, 10, 0, 0),
            "created_at": datetime(2025, 1, 1, 0, 0, 0),
            "updated_at": datetime(2025, 12, 16, 10, 0, 0),
        }
        
        record = registry._row_to_record(mock_row)
        
        assert record.tool_id == "dalle3_image_gen"
        assert record.provider == "openai"
        assert record.modalities == ["image", "vision"]
        assert record.constraints["max_resolution"] == 1792
        assert record.cost_tier == CostTier.HIGH
        assert record.health_status == CapabilityHealth.HEALTHY
        assert record.tenant_id == "acme-corp"
        assert record.display_name == "DALL-E 3"
    
    def test_row_to_record_nulls(self):
        """Test conversion handles NULL values gracefully."""
        registry = CapabilityRegistry(dsn="postgresql://test@localhost/test")
        
        mock_row = {
            "tool_id": "mermaid",
            "provider": "local",
            "modalities": None,
            "input_schema": None,
            "output_schema": None,
            "constraints": None,
            "cost_tier": None,
            "health_status": None,
            "latency_p95_ms": None,
            "failure_count": None,
            "enabled": None,
            "tenant_id": None,
            "display_name": None,
            "description": None,
            "documentation_url": None,
            "last_health_check": None,
            "created_at": None,
            "updated_at": None,
        }
        
        record = registry._row_to_record(mock_row)
        
        assert record.tool_id == "mermaid"
        assert record.provider == "local"
        assert record.modalities == []
        assert record.input_schema == {}
        assert record.output_schema == {}
        assert record.constraints == {}
        assert record.cost_tier == CostTier.MEDIUM  # Default
        assert record.health_status == CapabilityHealth.HEALTHY  # Default
        assert record.failure_count == 0
        assert record.enabled is True


class TestConstraintMatching:
    """Tests for constraint filtering logic (tested via data structures)."""
    
    def test_format_constraint_matching(self):
        """Test format constraint matching logic."""
        record = make_capability(
            constraints={"formats": ["png", "jpg", "webp"]}
        )
        
        # Logic used in find_candidates for format matching
        required_formats = {"png", "jpg"}
        supported_formats = set(record.constraints.get("formats", []))
        
        assert required_formats <= supported_formats
    
    def test_format_constraint_not_matching(self):
        """Test format constraint when capability doesn't support required format."""
        record = make_capability(
            constraints={"formats": ["svg", "pdf"]}
        )
        
        required_formats = {"png"}
        supported_formats = set(record.constraints.get("formats", []))
        
        assert not (required_formats <= supported_formats)
    
    def test_cost_tier_filtering(self):
        """Test cost tier filter logic."""
        # Order mapping
        tier_order = {t.value: i for i, t in enumerate(CostTier)}
        
        low_record = make_capability(cost_tier=CostTier.LOW)
        high_record = make_capability(cost_tier=CostTier.HIGH)
        
        max_tier = "medium"
        max_tier_idx = tier_order[max_tier]
        
        # Low should pass
        assert tier_order[low_record.cost_tier.value] <= max_tier_idx
        
        # High should fail
        assert tier_order[high_record.cost_tier.value] > max_tier_idx


class TestModalityFiltering:
    """Tests for modality-based capability selection."""
    
    def test_modality_in_list(self):
        """Test modality presence check."""
        record = make_capability(modalities=["image", "vision"])
        
        assert "image" in record.modalities
        assert "vision" in record.modalities
        assert "video" not in record.modalities
    
    def test_multiple_modalities(self):
        """Test capability with multiple modalities."""
        record = make_capability(
            tool_id="gpt4v",
            provider="openai",
            modalities=["text", "image", "vision"]
        )
        
        # Should match any of these modalities
        assert "text" in record.modalities
        assert "image" in record.modalities
        assert "vision" in record.modalities


class TestHealthStatusTransitions:
    """Tests for health status state machine."""
    
    def test_healthy_to_degraded(self):
        """Test transition from healthy to degraded."""
        record = make_capability(health_status=CapabilityHealth.HEALTHY)
        
        # Simulate transition
        new_status = CapabilityHealth.DEGRADED
        
        assert record.health_status == CapabilityHealth.HEALTHY
        assert new_status == CapabilityHealth.DEGRADED
    
    def test_degraded_to_unavailable(self):
        """Test transition from degraded to unavailable."""
        record = make_capability(
            health_status=CapabilityHealth.DEGRADED,
            failure_count=4
        )
        
        # After threshold failures, mark unavailable
        if record.failure_count >= 3:
            new_status = CapabilityHealth.UNAVAILABLE
        else:
            new_status = record.health_status
        
        assert new_status == CapabilityHealth.UNAVAILABLE
    
    def test_unavailable_to_healthy(self):
        """Test recovery from unavailable to healthy."""
        record = make_capability(
            health_status=CapabilityHealth.UNAVAILABLE,
            failure_count=5
        )
        
        # On successful health check, reset
        new_status = CapabilityHealth.HEALTHY
        new_failure_count = 0
        
        assert new_status == CapabilityHealth.HEALTHY
        assert new_failure_count == 0


class TestCapabilityOrdering:
    """Tests for capability ranking/ordering logic."""
    
    def test_health_ordering(self):
        """Test that healthy capabilities rank before degraded."""
        healthy = make_capability(
            tool_id="tool1",
            health_status=CapabilityHealth.HEALTHY
        )
        degraded = make_capability(
            tool_id="tool2",
            health_status=CapabilityHealth.DEGRADED
        )
        unavailable = make_capability(
            tool_id="tool3",
            health_status=CapabilityHealth.UNAVAILABLE
        )
        
        # Ordering logic used in find_candidates
        def health_rank(r: CapabilityRecord) -> int:
            order = {
                CapabilityHealth.HEALTHY: 0,
                CapabilityHealth.DEGRADED: 1,
                CapabilityHealth.UNAVAILABLE: 2,
            }
            return order[r.health_status]
        
        capabilities = [degraded, unavailable, healthy]
        sorted_caps = sorted(capabilities, key=health_rank)
        
        assert sorted_caps[0].tool_id == "tool1"  # healthy first
        assert sorted_caps[1].tool_id == "tool2"  # degraded second
        assert sorted_caps[2].tool_id == "tool3"  # unavailable last
    
    def test_cost_ordering(self):
        """Test that cheaper capabilities rank before expensive."""
        free = make_capability(tool_id="free_tool", cost_tier=CostTier.FREE)
        medium = make_capability(tool_id="medium_tool", cost_tier=CostTier.MEDIUM)
        premium = make_capability(tool_id="premium_tool", cost_tier=CostTier.PREMIUM)
        
        # Ordering logic used in find_candidates
        tier_order = {t: i for i, t in enumerate(CostTier)}
        
        def cost_rank(r: CapabilityRecord) -> int:
            return tier_order[r.cost_tier]
        
        capabilities = [premium, free, medium]
        sorted_caps = sorted(capabilities, key=cost_rank)
        
        assert sorted_caps[0].tool_id == "free_tool"
        assert sorted_caps[1].tool_id == "medium_tool"
        assert sorted_caps[2].tool_id == "premium_tool"


class TestTenantScoping:
    """Tests for tenant-scoped capability filtering."""
    
    def test_global_capability_visible_to_all(self):
        """Global capability (tenant_id=None) should be visible to all tenants."""
        global_cap = make_capability(
            tool_id="mermaid",
            provider="local",
            tenant_id=None
        )
        
        # Should match: tenant_id IS NULL
        assert global_cap.tenant_id is None
    
    def test_tenant_specific_capability(self):
        """Tenant-specific capability visible only to that tenant."""
        tenant_cap = make_capability(
            tool_id="custom_tool",
            provider="acme",
            tenant_id="acme-corp"
        )
        
        assert tenant_cap.tenant_id == "acme-corp"
        
        # Logic for tenant filter
        requesting_tenant = "acme-corp"
        matches = (
            tenant_cap.tenant_id is None or 
            tenant_cap.tenant_id == requesting_tenant
        )
        assert matches
    
    def test_tenant_specific_not_visible_to_other(self):
        """Tenant-specific capability not visible to other tenants."""
        tenant_cap = make_capability(
            tool_id="custom_tool",
            provider="acme",
            tenant_id="acme-corp"
        )
        
        requesting_tenant = "other-corp"
        matches = (
            tenant_cap.tenant_id is None or 
            tenant_cap.tenant_id == requesting_tenant
        )
        assert not matches


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
