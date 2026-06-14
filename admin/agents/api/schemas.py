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
    avg_response_time_ms: float
    satisfaction_score: Optional[float] = None


class AgentDeployment(BaseModel):
    """Agent deployment info."""

    agent_id: str
    environment: str
    version: str
    deployed_at: str
    deployed_by: str


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
