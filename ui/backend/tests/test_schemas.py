"""
Eye of God Unit Tests - API Schemas
Per VIBE Coding Rules: Unit tests allowed to use mocks

Tests Pydantic schema validation without database.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError

# Import schemas
import sys
sys.path.insert(0, 'ui/backend')

from api.schemas import (
    AgentMode,
    SettingsTab,
    TokenRequest,
    TokenResponse,
    UserInfo,
    SettingsUpdate,
    ThemeBase,
    ThemeCreate,
    ThemeVariables,
    ModeChange,
    MemoryType,
    MemoryCreate,
    MemorySearch,
    HealthResponse,
    ErrorResponse,
)


class TestAgentModeEnum:
    """Test AgentMode enum values."""
    
    def test_all_modes_defined(self):
        """All 6 agent modes should be defined."""
        modes = list(AgentMode)
        assert len(modes) == 6
        assert AgentMode.STANDARD.value == "STD"
        assert AgentMode.TRAINING.value == "TRN"
        assert AgentMode.ADMIN.value == "ADM"
        assert AgentMode.DEVELOPER.value == "DEV"
        assert AgentMode.READONLY.value == "RO"
        assert AgentMode.DANGER.value == "DGR"


class TestTokenSchemas:
    """Test authentication token schemas."""
    
    def test_token_request_valid(self):
        """Valid token request should pass."""
        req = TokenRequest(username="testuser", password="password123")
        assert req.username == "testuser"
        assert req.password == "password123"
    
    def test_token_request_username_too_short(self):
        """Username must be at least 3 characters."""
        with pytest.raises(ValidationError):
            TokenRequest(username="ab", password="password123")
    
    def test_token_request_password_too_short(self):
        """Password must be at least 8 characters."""
        with pytest.raises(ValidationError):
            TokenRequest(username="testuser", password="short")
    
    def test_token_response_defaults(self):
        """Token response should have correct defaults."""
        resp = TokenResponse(access_token="test.token.here")
        assert resp.token_type == "bearer"
        assert resp.expires_in == 86400


class TestUserInfoSchema:
    """Test user info schema."""
    
    def test_user_info_complete(self):
        """Complete user info should validate."""
        user = UserInfo(
            id=uuid4(),
            tenant_id=uuid4(),
            username="testuser",
            email="test@example.com",
            role="admin",
            mode=AgentMode.STANDARD,
            permissions=["mode:use", "settings:read"],
        )
        assert user.username == "testuser"
        assert len(user.permissions) == 2
    
    def test_user_info_defaults(self):
        """User info defaults should be applied."""
        user = UserInfo(
            id=uuid4(),
            tenant_id=uuid4(),
            username="testuser",
            role="member",
        )
        assert user.mode == AgentMode.STANDARD
        assert user.permissions == []


class TestThemeSchemas:
    """Test theme-related schemas."""
    
    def test_theme_create_valid(self):
        """Valid theme creation should pass."""
        theme = ThemeCreate(
            name="Dark Mode",
            description="A dark theme",
            author="Developer",
            variables={"--eog-bg-void": "#0f172a"},
        )
        assert theme.name == "Dark Mode"
        assert "--eog-bg-void" in theme.variables
    
    def test_theme_create_xss_blocked(self):
        """XSS patterns should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ThemeCreate(
                name="Malicious",
                variables={"--eog-bg": "url(javascript:alert(1))"},
            )
        assert "XSS pattern" in str(exc_info.value)
    
    def test_theme_create_script_tag_blocked(self):
        """Script tags in variables should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ThemeCreate(
                name="Malicious",
                variables={"--eog-test": "<script>alert(1)</script>"},
            )
        assert "XSS pattern" in str(exc_info.value)
    
    def test_theme_name_length_limits(self):
        """Theme name should respect length limits."""
        # Too long name should fail
        with pytest.raises(ValidationError):
            ThemeCreate(name="x" * 101, variables={})
        
        # Empty name should fail
        with pytest.raises(ValidationError):
            ThemeCreate(name="", variables={})


class TestMemorySchemas:
    """Test memory-related schemas."""
    
    def test_memory_create_valid(self):
        """Valid memory creation should pass."""
        mem = MemoryCreate(
            content="This is a test memory",
            memory_type=MemoryType.EPISODIC,
            importance=0.8,
        )
        assert mem.content == "This is a test memory"
        assert mem.importance == 0.8
    
    def test_memory_importance_range(self):
        """Importance must be between 0 and 1."""
        with pytest.raises(ValidationError):
            MemoryCreate(content="test", importance=1.5)
        
        with pytest.raises(ValidationError):
            MemoryCreate(content="test", importance=-0.1)
    
    def test_memory_search_valid(self):
        """Valid memory search should pass."""
        search = MemorySearch(query="test query", limit=20)
        assert search.query == "test query"
        assert search.limit == 20
    
    def test_memory_search_limit_range(self):
        """Search limit must be 1-100."""
        with pytest.raises(ValidationError):
            MemorySearch(query="test", limit=0)
        
        with pytest.raises(ValidationError):
            MemorySearch(query="test", limit=101)


class TestSettingsSchemas:
    """Test settings-related schemas."""
    
    def test_settings_tab_values(self):
        """All settings tabs should be defined."""
        tabs = list(SettingsTab)
        assert len(tabs) == 4
        assert SettingsTab.AGENT.value == "agent"
        assert SettingsTab.EXTERNAL.value == "external"
        assert SettingsTab.CONNECTIVITY.value == "connectivity"
        assert SettingsTab.SYSTEM.value == "system"
    
    def test_settings_update_valid(self):
        """Valid settings update should pass."""
        update = SettingsUpdate(
            data={"chat_provider": "openai"},
            version=1,
        )
        assert update.data["chat_provider"] == "openai"
        assert update.version == 1


class TestModeSchemas:
    """Test mode-related schemas."""
    
    def test_mode_change_valid(self):
        """Valid mode change should pass."""
        change = ModeChange(mode=AgentMode.DEVELOPER)
        assert change.mode == AgentMode.DEVELOPER
    
    def test_mode_change_all_modes(self):
        """All modes should be valid for mode change."""
        for mode in AgentMode:
            change = ModeChange(mode=mode)
            assert change.mode == mode


class TestCommonSchemas:
    """Test common response schemas."""
    
    def test_health_response(self):
        """Health response should include required fields."""
        health = HealthResponse(
            status="healthy",
            version="2.0.0",
            timestamp=datetime.utcnow(),
        )
        assert health.status == "healthy"
    
    def test_error_response(self):
        """Error response should accept all fields."""
        error = ErrorResponse(
            detail="Something went wrong",
            code="VALIDATION_ERROR",
            path="/api/v2/settings",
        )
        assert error.detail == "Something went wrong"
        assert error.code == "VALIDATION_ERROR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
