"""Unit tests for ProvenanceRecorder (no DB required).

Tests verify redaction policies, dataclass logic, and row conversion
without requiring database connections.

Pattern Reference: test_capability_registry.py, test_asset_store.py
"""

import pytest
from datetime import datetime
from uuid import uuid4

from services.common.provenance_recorder import (
    ProvenanceRecorder,
    ProvenanceRecord,
    RedactionPolicy,
)


def make_provenance(**kwargs) -> ProvenanceRecord:
    """Create a test ProvenanceRecord with sensible defaults."""
    defaults = {
        "asset_id": uuid4(),
        "tenant_id": "test-tenant",
        "tool_id": "dalle3_image_gen",
        "provider": "openai",
        "request_id": "req-123",
        "execution_id": uuid4(),
        "plan_id": None,
        "session_id": "session-abc",
        "user_id": "user-456",
        "prompt_summary": "Generate a company logo",
        "generation_params": {"size": "1024x1024", "quality": "hd"},
        "model_version": "dall-e-3",
        "trace_id": "trace-xyz",
        "span_id": "span-123",
        "quality_gate_passed": True,
        "quality_score": 0.85,
        "rework_count": 0,
        "created_at": datetime.now(),
    }
    defaults.update(kwargs)
    return ProvenanceRecord(**defaults)


class TestProvenanceRecord:
    """Tests for ProvenanceRecord dataclass."""

    def test_create_minimal(self):
        asset_id = uuid4()
        record = ProvenanceRecord(
            asset_id=asset_id,
            tenant_id="test",
            tool_id="mermaid",
            provider="local",
        )
        assert record.asset_id == asset_id
        assert record.tenant_id == "test"
        assert record.tool_id == "mermaid"
        assert record.provider == "local"
        assert record.rework_count == 0
        assert record.generation_params == {}

    def test_create_full(self):
        record = make_provenance(
            quality_score=0.92,
            rework_count=1,
        )
        assert record.quality_score == 0.92
        assert record.rework_count == 1
        assert record.quality_gate_passed is True


class TestRedactionPolicy:
    """Tests for RedactionPolicy dataclass."""

    def test_default_policy(self):
        policy = RedactionPolicy()
        assert policy.redact_prompt is False
        assert policy.redact_params is False
        assert policy.max_prompt_length == 500
        assert len(policy.redact_patterns) == 0

    def test_custom_policy(self):
        policy = RedactionPolicy(
            redact_prompt=True,
            max_prompt_length=100,
        )
        assert policy.redact_prompt is True
        assert policy.max_prompt_length == 100

    def test_default_patterns(self):
        patterns = RedactionPolicy.DEFAULT_PATTERNS
        assert len(patterns) > 0
        # Should have OpenAI key pattern
        assert any("sk-" in p for p in patterns)


class TestPromptRedaction:
    """Tests for prompt redaction logic."""

    def test_no_redaction(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        prompt = "Generate a blue logo"
        result = recorder._redact_prompt(prompt)
        assert result == prompt

    def test_full_redaction(self):
        policy = RedactionPolicy(redact_prompt=True)
        recorder = ProvenanceRecorder(
            dsn="postgresql://test@localhost/test",
            redaction_policy=policy,
        )
        result = recorder._redact_prompt("Generate a logo with sk-abc123")
        assert result == "[REDACTED]"

    def test_truncation(self):
        policy = RedactionPolicy(max_prompt_length=20)
        recorder = ProvenanceRecorder(
            dsn="postgresql://test@localhost/test",
            redaction_policy=policy,
        )
        long_prompt = "A" * 100
        result = recorder._redact_prompt(long_prompt)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")

    def test_none_prompt(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        result = recorder._redact_prompt(None)
        assert result is None

    def test_openai_key_redaction(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        # Real-looking but fake OpenAI key
        prompt = "Use API key sk-abcdefghijklmnopqrstuvwxyz012345678901234567 for access"
        result = recorder._redact_prompt(prompt)
        assert "sk-" not in result
        assert "[REDACTED]" in result

    def test_email_redaction(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        prompt = "Send to user@example.com"
        result = recorder._redact_prompt(prompt)
        assert "user@example.com" not in result
        assert "[REDACTED]" in result


class TestParamsRedaction:
    """Tests for generation params redaction."""

    def test_no_redaction(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        params = {"size": "1024x1024", "quality": "hd"}
        result = recorder._redact_params(params)
        assert result == params

    def test_full_redaction(self):
        policy = RedactionPolicy(redact_params=True)
        recorder = ProvenanceRecorder(
            dsn="postgresql://test@localhost/test",
            redaction_policy=policy,
        )
        params = {"size": "1024x1024", "api_key": "secret"}
        result = recorder._redact_params(params)
        assert result == {"redacted": True}

    def test_sensitive_key_redaction(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        params = {
            "size": "1024x1024",
            "api_key": "sk-secret",
            "password": "admin123",
            "config": {
                "secret_token": "abc",
            },
        }
        result = recorder._redact_params(params)
        
        assert result["size"] == "1024x1024"
        assert result["api_key"] == "[REDACTED]"
        assert result["password"] == "[REDACTED]"
        assert result["config"]["secret_token"] == "[REDACTED]"

    def test_empty_params(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        result = recorder._redact_params({})
        assert result == {}


class TestPatternApplication:
    """Tests for pattern-based redaction."""

    def test_ssn_pattern(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        text = "SSN: 123-45-6789"
        result = recorder._apply_patterns(text)
        assert "123-45-6789" not in result
        assert "[REDACTED]" in result

    def test_credit_card_pattern(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        text = "Card: 4111-1111-1111-1111"
        result = recorder._apply_patterns(text)
        assert "4111" not in result
        assert "[REDACTED]" in result

    def test_no_match(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        text = "Just plain text"
        result = recorder._apply_patterns(text)
        assert result == text


class TestRowConversion:
    """Tests for row-to-record conversion."""

    def test_row_to_record_complete(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        asset_id = uuid4()
        execution_id = uuid4()
        
        mock_row = {
            "asset_id": asset_id,
            "tenant_id": "acme-corp",
            "request_id": "req-abc",
            "execution_id": execution_id,
            "plan_id": None,
            "session_id": "session-123",
            "user_id": "user-xyz",
            "prompt_summary": "Generate logo",
            "generation_params": '{"size": "1024x1024"}',
            "tool_id": "dalle3_image_gen",
            "provider": "openai",
            "model_version": "dall-e-3",
            "trace_id": "trace-abc",
            "span_id": "span-123",
            "quality_gate_passed": True,
            "quality_score": 0.9,
            "rework_count": 0,
            "created_at": datetime(2025, 12, 16, 10, 0, 0),
        }
        
        record = recorder._row_to_record(mock_row)
        
        assert record.asset_id == asset_id
        assert record.tenant_id == "acme-corp"
        assert record.tool_id == "dalle3_image_gen"
        assert record.provider == "openai"
        assert record.generation_params["size"] == "1024x1024"
        assert record.quality_score == 0.9

    def test_row_to_record_nulls(self):
        recorder = ProvenanceRecorder(dsn="postgresql://test@localhost/test")
        asset_id = uuid4()
        
        mock_row = {
            "asset_id": asset_id,
            "tenant_id": "test",
            "request_id": None,
            "execution_id": None,
            "plan_id": None,
            "session_id": None,
            "user_id": None,
            "prompt_summary": None,
            "generation_params": None,
            "tool_id": "mermaid",
            "provider": "local",
            "model_version": None,
            "trace_id": None,
            "span_id": None,
            "quality_gate_passed": None,
            "quality_score": None,
            "rework_count": None,
            "created_at": None,
        }
        
        record = recorder._row_to_record(mock_row)
        
        assert record.asset_id == asset_id
        assert record.generation_params == {}
        assert record.rework_count == 0
        assert record.quality_gate_passed is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
