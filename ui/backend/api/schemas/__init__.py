"""
Eye of God API - Pydantic Schemas
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Pydantic schemas
- Full type hints
- Validation rules
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ===========================================================================
# ENUMS
# ===========================================================================

class AgentMode(str, Enum):
    """Agent operating modes per design spec."""
    STANDARD = "STD"  # Full capabilities
    TRAINING = "TRN"  # Learn from user corrections
    ADMIN = "ADM"     # System configuration
    DEVELOPER = "DEV" # Debug tools visible
    READONLY = "RO"   # View only, no actions
    DANGER = "DGR"    # Override safety checks


class SettingsTab(str, Enum):
    """Settings tab identifiers."""
    AGENT = "agent"
    EXTERNAL = "external"
    CONNECTIVITY = "connectivity"
    SYSTEM = "system"


# ===========================================================================
# AUTH SCHEMAS
# ===========================================================================

class TokenRequest(BaseModel):
    """JWT token request."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


class UserInfo(BaseModel):
    """Current user information."""
    id: UUID
    tenant_id: UUID
    username: str
    email: Optional[str] = None
    role: str
    mode: AgentMode = AgentMode.STANDARD
    permissions: List[str] = []


# ===========================================================================
# SETTINGS SCHEMAS
# ===========================================================================

class SettingsBase(BaseModel):
    """Base settings schema."""
    data: Dict[str, Any] = Field(default_factory=dict)


class SettingsCreate(SettingsBase):
    """Settings creation schema."""
    tab: SettingsTab


class SettingsUpdate(SettingsBase):
    """Settings update schema."""
    version: int = 1


class SettingsResponse(SettingsBase):
    """Settings response schema."""
    tab: SettingsTab
    updated_at: datetime
    version: int


# ===========================================================================
# THEME SCHEMAS
# ===========================================================================

class ThemeVariables(BaseModel):
    """Theme CSS variable definitions."""
    bg_void: Optional[str] = Field(None, alias="--eog-bg-void")
    bg_base: Optional[str] = Field(None, alias="--eog-bg-base")
    surface: Optional[str] = Field(None, alias="--eog-surface")
    text_main: Optional[str] = Field(None, alias="--eog-text-main")
    text_dim: Optional[str] = Field(None, alias="--eog-text-dim")
    accent: Optional[str] = Field(None, alias="--eog-accent")
    danger: Optional[str] = Field(None, alias="--eog-danger")
    success: Optional[str] = Field(None, alias="--eog-success")
    warning: Optional[str] = Field(None, alias="--eog-warning")
    info: Optional[str] = Field(None, alias="--eog-info")

    class Config:
        populate_by_name = True


class ThemeBase(BaseModel):
    """Base theme schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    version: str = Field(default="1.0.0")
    author: str = Field(default="Anonymous")
    variables: Dict[str, str] = Field(default_factory=dict)

    @field_validator('variables')
    @classmethod
    def validate_no_xss(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Reject XSS patterns in CSS values."""
        xss_patterns = ['<script', 'javascript:', 'url(', 'expression(']
        for key, value in v.items():
            value_lower = value.lower()
            for pattern in xss_patterns:
                if pattern in value_lower:
                    raise ValueError(f"XSS pattern detected in {key}")
        return v


class ThemeCreate(ThemeBase):
    """Theme creation schema."""
    pass


class ThemeUpdate(BaseModel):
    """Theme update schema (partial)."""
    name: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[Dict[str, str]] = None


class ThemeResponse(ThemeBase):
    """Theme response schema."""
    id: UUID
    tenant_id: UUID
    is_approved: bool = False
    downloads: int = 0
    created_at: datetime
    updated_at: datetime


# ===========================================================================
# MODE SCHEMAS
# ===========================================================================

class ModeChange(BaseModel):
    """Mode change request."""
    mode: AgentMode


class ModeResponse(BaseModel):
    """Mode response."""
    mode: AgentMode
    changed_at: datetime
    changed_by: UUID


# ===========================================================================
# MEMORY SCHEMAS
# ===========================================================================

class MemoryType(str, Enum):
    """Memory types."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryBase(BaseModel):
    """Base memory schema."""
    content: str = Field(..., min_length=1, max_length=10000)
    memory_type: MemoryType = MemoryType.EPISODIC
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryCreate(MemoryBase):
    """Memory creation schema."""
    pass


class MemoryResponse(MemoryBase):
    """Memory response schema."""
    id: UUID
    tenant_id: UUID
    agent_id: UUID
    access_count: int = 0
    last_accessed: datetime
    created_at: datetime


class MemorySearch(BaseModel):
    """Memory search request."""
    query: str = Field(..., min_length=1, max_length=1000)
    memory_type: Optional[MemoryType] = None
    limit: int = Field(default=10, ge=1, le=100)
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)


class MemorySearchResult(BaseModel):
    """Memory search result."""
    memory: MemoryResponse
    score: float = Field(ge=0.0, le=1.0)


# ===========================================================================
# COMMON SCHEMAS
# ===========================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    code: Optional[str] = None
    path: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_prev: bool = False
