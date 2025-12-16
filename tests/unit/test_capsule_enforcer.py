"""Unit tests for CapsuleEnforcer (no DB required).

These tests verify enforcement logic using in-memory CapsuleRecord objects.
"""

import pytest
import time

from services.common.capsule_store import CapsuleRecord, CapsuleStatus
from services.common.capsule_enforcer import (
    CapsuleEnforcer, 
    EgressEnforcer, 
    ResourceEnforcer, 
    HITLEnforcer,
    ExportEnforcer,
    EnforcementAction,
)


def make_capsule(**kwargs) -> CapsuleRecord:
    """Create a test CapsuleRecord with sensible defaults."""
    defaults = {
        "capsule_id": "test-capsule",
        "tenant_id": "test-tenant",
        "name": "Test Capsule",
        "version": "1.0.0",
        "status": CapsuleStatus.PUBLISHED,
        "egress_mode": "restricted",
        "allowed_domains": ["*.example.com", "api.openai.com"],
        "blocked_domains": ["malware.bad.com"],
        "allowed_tools": ["web_search", "code_exec"],
        "prohibited_tools": ["file_delete", "system_exec"],
        "max_wall_clock_seconds": 60,
        "max_concurrent_nodes": 3,
        "default_hitl_mode": "optional",
        "risk_thresholds": {"tool_call": 0.7, "code_exec": 0.5},
        "max_pending_hitl": 5,
        "rl_export_allowed": True,
        "rl_export_scope": "tenant",
        "rl_excluded_fields": ["password", "api_key", "secret"],
    }
    defaults.update(kwargs)
    return CapsuleRecord(**defaults)


class TestEgressEnforcer:
    """Tests for egress/domain policy enforcement."""
    
    def test_restricted_mode_allowed_domain(self):
        capsule = make_capsule()
        enforcer = EgressEnforcer(capsule)
        
        result = enforcer.check_domain("api.example.com")
        assert result.action == EnforcementAction.ALLOW
        assert "example.com" in result.reason
    
    def test_restricted_mode_blocked_domain(self):
        capsule = make_capsule()
        enforcer = EgressEnforcer(capsule)
        
        result = enforcer.check_domain("unknown.domain.com")
        assert result.action == EnforcementAction.DENY
    
    def test_explicit_block(self):
        capsule = make_capsule()
        enforcer = EgressEnforcer(capsule)
        
        result = enforcer.check_domain("malware.bad.com")
        assert result.action == EnforcementAction.DENY
        assert "explicitly blocked" in result.reason
    
    def test_none_mode_blocks_all(self):
        capsule = make_capsule(egress_mode="none")
        enforcer = EgressEnforcer(capsule)
        
        result = enforcer.check_domain("api.example.com")
        assert result.action == EnforcementAction.DENY
    
    def test_open_mode_allows_all(self):
        capsule = make_capsule(egress_mode="open", blocked_domains=[])
        enforcer = EgressEnforcer(capsule)
        
        result = enforcer.check_domain("any.random.domain.com")
        assert result.action == EnforcementAction.ALLOW
    
    def test_wildcard_matching(self):
        capsule = make_capsule(allowed_domains=["*.openai.com"])
        enforcer = EgressEnforcer(capsule)
        
        assert enforcer.check_domain("api.openai.com").allowed
        assert enforcer.check_domain("chat.openai.com").allowed
        assert not enforcer.check_domain("openai.com.evil.com").allowed


class TestResourceEnforcer:
    """Tests for resource limit enforcement."""
    
    def test_wall_clock_within_limit(self):
        capsule = make_capsule(max_wall_clock_seconds=10)
        enforcer = ResourceEnforcer(capsule)
        enforcer.start()
        
        result = enforcer.check_wall_clock()
        assert result.action == EnforcementAction.ALLOW
    
    def test_concurrency_within_limit(self):
        capsule = make_capsule(max_concurrent_nodes=3)
        enforcer = ResourceEnforcer(capsule)
        
        result = enforcer.check_concurrency(2)
        assert result.action == EnforcementAction.ALLOW
    
    def test_concurrency_at_limit(self):
        capsule = make_capsule(max_concurrent_nodes=3)
        enforcer = ResourceEnforcer(capsule)
        
        result = enforcer.check_concurrency(3)
        assert result.action == EnforcementAction.DENY
    
    def test_acquire_release_nodes(self):
        capsule = make_capsule(max_concurrent_nodes=2)
        enforcer = ResourceEnforcer(capsule)
        
        # Acquire 2 nodes
        assert enforcer.acquire_node().allowed
        assert enforcer.acquire_node().allowed
        
        # Third should fail
        assert not enforcer.acquire_node().allowed
        
        # Release one and retry
        enforcer.release_node()
        assert enforcer.acquire_node().allowed


class TestHITLEnforcer:
    """Tests for HITL (Human-in-the-Loop) enforcement."""
    
    def test_mode_none_allows_all(self):
        capsule = make_capsule(default_hitl_mode="none")
        enforcer = HITLEnforcer(capsule)
        
        result = enforcer.check_action("tool_call", risk_score=0.9)
        assert result.action == EnforcementAction.ALLOW
    
    def test_mode_required_requires_hitl(self):
        capsule = make_capsule(default_hitl_mode="required")
        enforcer = HITLEnforcer(capsule)
        
        result = enforcer.check_action("tool_call", risk_score=0.1)
        assert result.action == EnforcementAction.REQUIRE_HITL
    
    def test_mode_optional_low_risk(self):
        capsule = make_capsule(default_hitl_mode="optional")
        enforcer = HITLEnforcer(capsule)
        
        result = enforcer.check_action("tool_call", risk_score=0.3)
        assert result.action == EnforcementAction.ALLOW
    
    def test_mode_optional_high_risk(self):
        capsule = make_capsule(default_hitl_mode="optional")
        enforcer = HITLEnforcer(capsule)
        
        result = enforcer.check_action("tool_call", risk_score=0.8)
        assert result.action == EnforcementAction.REQUIRE_HITL
    
    def test_prohibited_tool_denied(self):
        capsule = make_capsule()
        enforcer = HITLEnforcer(capsule)
        
        result = enforcer.check_action("tool_call", tool_name="file_delete")
        assert result.action == EnforcementAction.DENY


class TestExportEnforcer:
    """Tests for RL export policy enforcement."""
    
    def test_export_allowed(self):
        capsule = make_capsule(rl_export_allowed=True)
        enforcer = ExportEnforcer(capsule)
        
        result = enforcer.check_export(scope="tenant")
        assert result.action == EnforcementAction.ALLOW
    
    def test_export_disabled(self):
        capsule = make_capsule(rl_export_allowed=False)
        enforcer = ExportEnforcer(capsule)
        
        result = enforcer.check_export(scope="tenant")
        assert result.action == EnforcementAction.DENY
    
    def test_global_export_denied_for_tenant_scope(self):
        capsule = make_capsule(rl_export_scope="tenant")
        enforcer = ExportEnforcer(capsule)
        
        result = enforcer.check_export(scope="global")
        assert result.action == EnforcementAction.DENY
    
    def test_filter_excluded_fields(self):
        capsule = make_capsule(rl_excluded_fields=["password", "secret"])
        enforcer = ExportEnforcer(capsule)
        
        data = {"username": "alice", "password": "hunter2", "secret": "xyz"}
        filtered = enforcer.filter_export_data(data)
        
        assert filtered["username"] == "alice"
        assert filtered["password"] == "[REDACTED]"
        assert filtered["secret"] == "[REDACTED]"


class TestCapsuleEnforcer:
    """Tests for the combined CapsuleEnforcer."""
    
    def test_tool_call_allowed(self):
        capsule = make_capsule()
        enforcer = CapsuleEnforcer(capsule)
        
        result = enforcer.check_tool_call("web_search", risk_score=0.2)
        assert result.allowed
    
    def test_tool_call_prohibited(self):
        capsule = make_capsule()
        enforcer = CapsuleEnforcer(capsule)
        
        result = enforcer.check_tool_call("file_delete")
        assert not result.allowed
        assert "prohibited" in result.reason
    
    def test_tool_call_not_in_allowed_list(self):
        capsule = make_capsule()
        enforcer = CapsuleEnforcer(capsule)
        
        result = enforcer.check_tool_call("unknown_tool")
        assert not result.allowed
        assert "not in allowed list" in result.reason
    
    def test_tool_call_with_blocked_domain(self):
        capsule = make_capsule()
        enforcer = CapsuleEnforcer(capsule)
        
        result = enforcer.check_tool_call(
            "web_search", 
            target_domain="malware.bad.com"
        )
        assert not result.allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
