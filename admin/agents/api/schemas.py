"""Agents API - Pydantic schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Agent(BaseModel):
    """Agent definition."""

    agent_id: str
    name: str
    description: Optional[str] = None
    tenant_id: str
    status: str  # draft, active, paused, archived
    model: str  # gpt-4, claude-3, etc.
    personality: dict
    tools: list[str]
    memory_config: dict
    capsule_id: Optional[str] = None
    created_at: str
    updated_at: str


class AgentUpdatePayload(BaseModel):
    """Agent settings update payload."""

    name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None


class AgentStats(BaseModel):
    """Agent statistics."""

    total_conversations: int
    total_messages: int
    # Nothing in this system records per-message latency or satisfaction.
    # Both are optional and None when unmeasured — a 0.0 here would be a
    # fabricated metric, not a measurement.
    avg_response_time_ms: Optional[float] = None
    satisfaction_score: Optional[float] = None

    # `version`, `deployed_at` and `deployed_by` used to sit here as required
    # fields. They are deployment metadata, not statistics, nothing in the tree
    # reads them, and because they had no defaults every AgentStats() call was
    # missing arguments. They are not optional and unmeasured — they are the
    # wrong schema's fields, so they are gone.


class ToolInfo(BaseModel):
    """Tool metadata for the agent tools screen."""

    name: str
    description: str
    input_schema: Optional[dict] = None


class AgentToolsOut(BaseModel):
    """Agent tools configuration response."""

    agent_id: str
    available_tools: list[ToolInfo]
    enabled_tools: list[str]


class AgentToolsUpdate(BaseModel):
    """Agent tools configuration update payload."""

    tools: list[str]


class CapsuleConfigOut(BaseModel):
    """Capsule configuration response."""

    agent_id: str
    capsule_id: str
    name: str
    description: Optional[str] = None
    status: str
    system_prompt: str
    personality_traits: dict
    neuromodulator_baseline: dict
    learning_config: dict


class CapsuleConfigUpdate(BaseModel):
    """Capsule configuration update payload."""

    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    personality_traits: Optional[dict] = None
    neuromodulator_baseline: Optional[dict] = None
    learning_config: Optional[dict] = None


class CapsuleConfigUpdateResult(BaseModel):
    """Capsule configuration update result."""

    agent_id: str
    capsule_id: str
    updated: bool


class MultimodalConfig(BaseModel):
    """Multimodal capabilities configuration."""

    image_enabled: bool = True
    image_quality: str = "standard"
    image_style: str = "vivid"
    diagram_enabled: bool = True
    diagram_format: str = "svg"
    diagram_theme: str = "default"
    screenshot_enabled: bool = True
    screenshot_width: int = 1920
    screenshot_height: int = 1080
    screenshot_full_page: bool = True
    video_enabled: bool = False
    vision_enabled: bool = True
    chat_model_vision: bool = True
    browser_model_vision: bool = True
    image_provider: str = "dalle3"
    diagram_provider: str = "mermaid"
    screenshot_provider: str = "playwright"
