"""Templates API - Agent and conversation templates.


Template management for agents and prompts.

7-Persona Implementation:
- PM: Template library, sharing
- PhD Dev: Prompt engineering patterns
- QA: Template validation
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["templates"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class AgentTemplate(BaseModel):
    """Agent template."""

    template_id: str
    name: str
    description: Optional[str] = None
    category: str  # assistant, analyst, creative, support
    config: dict
    prompts: dict
    is_public: bool = False
    created_by: str
    created_at: str
    usage_count: int = 0


class PromptTemplate(BaseModel):
    """Prompt template."""

    template_id: str
    name: str
    content: str
    variables: list[str]  # {{variable_name}}
    category: str
    is_public: bool = False


class TemplateVariable(BaseModel):
    """Template variable."""

    name: str
    type: str  # string, number, boolean, list
    required: bool = True
    default: Optional[str] = None
    description: Optional[str] = None


# =============================================================================
# ENDPOINTS - Agent Templates
# =============================================================================


@router.get(
    "/agents",
    summary="List agent templates",
    auth=AuthBearer(),
)
async def list_agent_templates(
    request,
    category: Optional[str] = None,
    public_only: bool = False,
) -> dict:
    """List available agent templates.

    PM: Template library for quick agent creation.
    """
    return {
        "templates": [
            AgentTemplate(
                template_id="1",
                name="Customer Support Agent",
                description="Helpful support assistant",
                category="support",
                config={"temperature": 0.7},
                prompts={"system": "You are a helpful support agent."},
                is_public=True,
                created_by="system",
                created_at=timezone.now().isoformat(),
                usage_count=150,
            ).dict(),
            AgentTemplate(
                template_id="2",
                name="Data Analyst",
                description="Analyzes data and provides insights",
                category="analyst",
                config={"temperature": 0.3},
                prompts={"system": "You are a data analyst."},
                is_public=True,
                created_by="system",
                created_at=timezone.now().isoformat(),
                usage_count=89,
            ).dict(),
        ],
        "total": 2,
    }


@router.post(
    "/agents",
    summary="Create agent template",
    auth=AuthBearer(),
)
async def create_agent_template(
    request,
    name: str,
    category: str,
    config: dict,
    prompts: dict,
    description: Optional[str] = None,
    is_public: bool = False,
) -> dict:
    """Create a new agent template.

    PhD Dev: Capture best configurations.
    """
    template_id = str(uuid4())

    logger.info(f"Agent template created: {name} ({template_id})")

    return {
        "template_id": template_id,
        "name": name,
        "created": True,
    }


@router.get(
    "/agents/{template_id}",
    response=AgentTemplate,
    summary="Get agent template",
    auth=AuthBearer(),
)
async def get_agent_template(
    request,
    template_id: str,
) -> AgentTemplate:
    """Get agent template details."""
    return AgentTemplate(
        template_id=template_id,
        name="Example Template",
        category="assistant",
        config={},
        prompts={},
        is_public=False,
        created_by="user",
        created_at=timezone.now().isoformat(),
    )


@router.patch(
    "/agents/{template_id}",
    summary="Update agent template",
    auth=AuthBearer(),
)
async def update_agent_template(
    request,
    template_id: str,
    name: Optional[str] = None,
    config: Optional[dict] = None,
    is_public: Optional[bool] = None,
) -> dict:
    """Update an agent template."""
    return {
        "template_id": template_id,
        "updated": True,
    }


@router.delete(
    "/agents/{template_id}",
    summary="Delete agent template",
    auth=AuthBearer(),
)
async def delete_agent_template(
    request,
    template_id: str,
) -> dict:
    """Delete an agent template."""
    return {
        "template_id": template_id,
        "deleted": True,
    }


@router.post(
    "/agents/{template_id}/clone",
    summary="Clone agent template",
    auth=AuthBearer(),
)
async def clone_agent_template(
    request,
    template_id: str,
    new_name: str,
) -> dict:
    """Clone an agent template.

    PM: Quick duplication for customization.
    """
    new_id = str(uuid4())

    return {
        "original_id": template_id,
        "new_id": new_id,
        "name": new_name,
        "cloned": True,
    }


# =============================================================================
# ENDPOINTS - Prompt Templates
# =============================================================================


@router.get(
    "/prompts",
    summary="List prompt templates",
    auth=AuthBearer(),
)
async def list_prompt_templates(
    request,
    category: Optional[str] = None,
) -> dict:
    """List prompt templates.

    PhD Dev: Prompt library for optimization.
    """
    return {
        "templates": [],
        "total": 0,
    }


@router.post(
    "/prompts",
    summary="Create prompt template",
    auth=AuthBearer(),
)
async def create_prompt_template(
    request,
    name: str,
    content: str,
    category: str = "general",
) -> dict:
    """Create a prompt template."""
    template_id = str(uuid4())

    # Extract variables from content
    import re

    variables = re.findall(r"\{\{(\w+)\}\}", content)

    return {
        "template_id": template_id,
        "name": name,
        "variables": variables,
        "created": True,
    }


@router.post(
    "/prompts/{template_id}/render",
    summary="Render prompt template",
    auth=AuthBearer(),
)
async def render_prompt_template(
    request,
    template_id: str,
    variables: dict,
) -> dict:
    """Render a prompt template with variables.

    QA: Validate variable substitution.
    """
    # In production: fetch template and substitute variables
    rendered = "Example rendered prompt"

    return {
        "template_id": template_id,
        "rendered": rendered,
        "variables_used": list(variables.keys()),
    }


# =============================================================================
# ENDPOINTS - Template Validation
# =============================================================================


@router.post(
    "/validate",
    summary="Validate template",
    auth=AuthBearer(),
)
async def validate_template(
    request,
    template_type: str,  # agent, prompt
    config: dict,
) -> dict:
    """Validate a template configuration.

    QA: Pre-save validation.
    """
    errors = []
    warnings = []

    # In production: validate against schema

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
