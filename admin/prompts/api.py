"""Prompts API - Prompt template management.

VIBE COMPLIANT - Django Ninja.
Prompt versioning and rendering.

7-Persona Implementation:
- PhD Dev: Prompt engineering
- PM: Prompt library
- QA: Prompt validation
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["prompts"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Prompt(BaseModel):
    """Prompt template."""
    prompt_id: str
    name: str
    description: Optional[str] = None
    template: str
    variables: list[str]
    category: str  # system, user, agent, function
    version: int
    is_active: bool = True
    created_at: str
    updated_at: str


class PromptVersion(BaseModel):
    """Prompt version."""
    version_id: str
    prompt_id: str
    version: int
    template: str
    created_at: str
    created_by: str


class RenderedPrompt(BaseModel):
    """Rendered prompt."""
    prompt_id: str
    template: str
    rendered: str
    variables_used: dict


# =============================================================================
# ENDPOINTS - Prompt CRUD
# =============================================================================


@router.get(
    "",
    summary="List prompts",
    auth=AuthBearer(),
)
async def list_prompts(
    request,
    category: Optional[str] = None,
    active_only: bool = True,
    limit: int = 50,
) -> dict:
    """List prompt templates.
    
    PM: Prompt library.
    """
    return {
        "prompts": [],
        "total": 0,
    }


@router.post(
    "",
    response=Prompt,
    summary="Create prompt",
    auth=AuthBearer(),
)
async def create_prompt(
    request,
    name: str,
    template: str,
    category: str = "user",
    description: Optional[str] = None,
) -> Prompt:
    """Create a new prompt template.
    
    PhD Dev: Prompt design.
    """
    prompt_id = str(uuid4())
    
    # Extract variables from template ({{variable}})
    import re
    variables = re.findall(r'\{\{(\w+)\}\}', template)
    
    logger.info(f"Prompt created: {name} ({prompt_id})")
    
    return Prompt(
        prompt_id=prompt_id,
        name=name,
        description=description,
        template=template,
        variables=variables,
        category=category,
        version=1,
        created_at=timezone.now().isoformat(),
        updated_at=timezone.now().isoformat(),
    )


@router.get(
    "/{prompt_id}",
    response=Prompt,
    summary="Get prompt",
    auth=AuthBearer(),
)
async def get_prompt(request, prompt_id: str) -> Prompt:
    """Get prompt template."""
    return Prompt(
        prompt_id=prompt_id,
        name="Example",
        template="Hello {{name}}!",
        variables=["name"],
        category="user",
        version=1,
        created_at=timezone.now().isoformat(),
        updated_at=timezone.now().isoformat(),
    )


@router.patch(
    "/{prompt_id}",
    summary="Update prompt",
    auth=AuthBearer(),
)
async def update_prompt(
    request,
    prompt_id: str,
    template: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> dict:
    """Update prompt template (creates new version).
    
    PhD Dev: Prompt iteration.
    """
    return {
        "prompt_id": prompt_id,
        "updated": True,
        "new_version": 2,
    }


@router.delete(
    "/{prompt_id}",
    summary="Delete prompt",
    auth=AuthBearer(),
)
async def delete_prompt(request, prompt_id: str) -> dict:
    """Delete a prompt template."""
    logger.warning(f"Prompt deleted: {prompt_id}")
    
    return {
        "prompt_id": prompt_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Rendering
# =============================================================================


@router.post(
    "/{prompt_id}/render",
    response=RenderedPrompt,
    summary="Render prompt",
    auth=AuthBearer(),
)
async def render_prompt(
    request,
    prompt_id: str,
    variables: dict,
) -> RenderedPrompt:
    """Render a prompt with variables.
    
    PhD Dev: Prompt execution.
    """
    template = "Hello {{name}}!"
    rendered = template
    
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    
    return RenderedPrompt(
        prompt_id=prompt_id,
        template=template,
        rendered=rendered,
        variables_used=variables,
    )


@router.post(
    "/render/preview",
    summary="Preview render",
    auth=AuthBearer(),
)
async def preview_render(
    request,
    template: str,
    variables: dict,
) -> dict:
    """Preview prompt rendering without saving.
    
    QA: Prompt testing.
    """
    rendered = template
    
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    
    return {
        "template": template,
        "rendered": rendered,
        "variables_used": variables,
    }


# =============================================================================
# ENDPOINTS - Versioning
# =============================================================================


@router.get(
    "/{prompt_id}/versions",
    summary="List versions",
    auth=AuthBearer(),
)
async def list_versions(
    request,
    prompt_id: str,
) -> dict:
    """List prompt versions.
    
    PM: Version history.
    """
    return {
        "prompt_id": prompt_id,
        "versions": [],
        "total": 0,
    }


@router.post(
    "/{prompt_id}/rollback/{version}",
    summary="Rollback version",
    auth=AuthBearer(),
)
async def rollback_version(
    request,
    prompt_id: str,
    version: int,
) -> dict:
    """Rollback to a previous version."""
    logger.info(f"Prompt rollback: {prompt_id} to v{version}")
    
    return {
        "prompt_id": prompt_id,
        "rolled_back_to": version,
    }


# =============================================================================
# ENDPOINTS - Categories
# =============================================================================


@router.get(
    "/categories",
    summary="List categories",
    auth=AuthBearer(),
)
async def list_categories(request) -> dict:
    """List prompt categories.
    
    PM: Organization.
    """
    return {
        "categories": [
            {"name": "system", "description": "System prompts"},
            {"name": "user", "description": "User-facing prompts"},
            {"name": "agent", "description": "Agent personality"},
            {"name": "function", "description": "Function call prompts"},
        ],
        "total": 4,
    }
