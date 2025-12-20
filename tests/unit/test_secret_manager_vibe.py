"""
Unit tests for SecretManager - VIBE Compliance Verification.

This test file ensures that SecretManager follows VIBE Rule #1:
NO ALTERNATES - Fail fast when Redis URL is not configured.
"""

import os
import pytest


def test_secret_manager_fails_fast_without_redis_url():
    """
    VIBE Rule #1 Enforcement: SecretManager MUST raise RuntimeError
    at instantiation if SA01_REDIS_URL is not set.
    
    This prevents silent failures and deferred AttributeErrors when
    encrypt_value() or decrypt_value() are called later.
    """
    # Save original env vars
    original_sa01 = os.environ.get("SA01_REDIS_URL")
    original_redis = os.environ.get("REDIS_URL")
    
    try:
        # Clear Redis URL environment variable
        if "SA01_REDIS_URL" in os.environ:
            del os.environ["SA01_REDIS_URL"]
        if "REDIS_URL" in os.environ:
            del os.environ["REDIS_URL"]
        
        # Act & Assert: Instantiation MUST raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            from services.common.secret_manager import SecretManager
            SecretManager()  # Should fail immediately
        
        # Verify error message is clear and cites VIBE
        error_message = str(exc_info.value)
        assert "SA01_REDIS_URL" in error_message
        assert "REQUIRED" in error_message
        assert "VIBE" in error_message
        assert "No alternate sources" in error_message
        
    finally:
        # Restore original environment
        if original_sa01:
            os.environ["SA01_REDIS_URL"] = original_sa01
        if original_redis:
            os.environ["REDIS_URL"] = original_redis


def test_secret_manager_accepts_sa01_redis_url():
    """
    Positive test: SecretManager successfully initializes when
    SA01_REDIS_URL is set.
    """
    original = os.environ.get("SA01_REDIS_URL")
    
    try:
        os.environ["SA01_REDIS_URL"] = "redis://localhost:6379/0"
        
        from services.common.secret_manager import SecretManager
        manager = SecretManager()  # Should succeed
        
        assert manager._redis is not None, "Redis client should be initialized"
        
    finally:
        if original:
            os.environ["SA01_REDIS_URL"] = original
        elif "SA01_REDIS_URL" in os.environ:
            del os.environ["SA01_REDIS_URL"]

