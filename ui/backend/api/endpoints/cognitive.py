"""
Eye of God API - Cognitive Endpoints
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Ninja endpoints
- LLM parameter management
- Prompt template CRUD
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Query

from api.schemas import ErrorResponse

router = Router(tags=["Cognitive"])


# Cognitive parameter schemas
from pydantic import BaseModel, Field


class CognitiveParameter(BaseModel):
    """Cognitive parameter for LLM behavior."""
    key: str
    value: float | int | str | bool
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    category: str = "general"


class CognitiveConfig(BaseModel):
    """Complete cognitive configuration."""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    top_k: int = Field(default=40, ge=1, le=100)
    max_tokens: int = Field(default=4096, ge=1, le=32000)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    stop_sequences: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None


class PromptTemplate(BaseModel):
    """Prompt template for reusable prompts."""
    id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    template: str = Field(..., min_length=1)
    variables: List[str] = Field(default_factory=list)
    category: str = "general"
    is_system: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# In-memory storage for demo (in production, use database)
_cognitive_configs: dict[str, CognitiveConfig] = {}
_prompt_templates: dict[str, List[PromptTemplate]] = {}


@router.get(
    "/config",
    response={200: CognitiveConfig},
    summary="Get cognitive configuration"
)
async def get_cognitive_config(request: HttpRequest) -> CognitiveConfig:
    """
    Get the current cognitive/LLM configuration for the tenant.
    
    Includes temperature, top_p, penalties, and other LLM parameters.
    """
    tenant_id = request.auth.get('tenant_id')
    
    if tenant_id in _cognitive_configs:
        return _cognitive_configs[tenant_id]
    
    # Return defaults
    return CognitiveConfig()


@router.put(
    "/config",
    response={200: CognitiveConfig},
    summary="Update cognitive configuration"
)
async def update_cognitive_config(
    request: HttpRequest,
    config: CognitiveConfig
) -> CognitiveConfig:
    """
    Update the cognitive/LLM configuration.
    
    Requires cognitive:write permission.
    """
    tenant_id = request.auth.get('tenant_id')
    
    _cognitive_configs[tenant_id] = config
    
    return config


@router.post(
    "/config/reset",
    response={200: CognitiveConfig},
    summary="Reset cognitive configuration to defaults"
)
async def reset_cognitive_config(request: HttpRequest) -> CognitiveConfig:
    """
    Reset all cognitive parameters to their default values.
    """
    tenant_id = request.auth.get('tenant_id')
    
    default_config = CognitiveConfig()
    _cognitive_configs[tenant_id] = default_config
    
    return default_config


@router.get(
    "/parameters",
    response={200: List[CognitiveParameter]},
    summary="List all cognitive parameters"
)
async def list_parameters(request: HttpRequest) -> List[CognitiveParameter]:
    """
    Get a list of all available cognitive parameters with their constraints.
    """
    return [
        CognitiveParameter(
            key="temperature",
            value=0.7,
            description="Controls randomness. Lower = more focused, higher = more creative",
            min_value=0.0,
            max_value=2.0,
            category="creativity"
        ),
        CognitiveParameter(
            key="top_p",
            value=0.95,
            description="Nucleus sampling threshold",
            min_value=0.0,
            max_value=1.0,
            category="sampling"
        ),
        CognitiveParameter(
            key="top_k",
            value=40,
            description="Number of tokens to consider for each step",
            min_value=1,
            max_value=100,
            category="sampling"
        ),
        CognitiveParameter(
            key="max_tokens",
            value=4096,
            description="Maximum number of tokens to generate",
            min_value=1,
            max_value=32000,
            category="limits"
        ),
        CognitiveParameter(
            key="presence_penalty",
            value=0.0,
            description="Penalty for tokens already present in context",
            min_value=-2.0,
            max_value=2.0,
            category="penalties"
        ),
        CognitiveParameter(
            key="frequency_penalty",
            value=0.0,
            description="Penalty for frequently used tokens",
            min_value=-2.0,
            max_value=2.0,
            category="penalties"
        ),
    ]


# Prompt Templates CRUD

@router.get(
    "/templates",
    response={200: List[PromptTemplate]},
    summary="List prompt templates"
)
async def list_templates(
    request: HttpRequest,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> List[PromptTemplate]:
    """
    Get all prompt templates for the tenant.
    """
    tenant_id = request.auth.get('tenant_id')
    
    templates = _prompt_templates.get(tenant_id, [])
    
    if category:
        templates = [t for t in templates if t.category == category]
    
    if search:
        search_lower = search.lower()
        templates = [t for t in templates if search_lower in t.name.lower() or search_lower in (t.description or '').lower()]
    
    return templates


@router.post(
    "/templates",
    response={201: PromptTemplate},
    summary="Create prompt template"
)
async def create_template(
    request: HttpRequest,
    template: PromptTemplate
) -> PromptTemplate:
    """
    Create a new prompt template.
    """
    tenant_id = request.auth.get('tenant_id')
    
    from uuid import uuid4
    
    template.id = uuid4()
    template.created_at = datetime.utcnow()
    template.updated_at = datetime.utcnow()
    
    # Extract variables from template ({{variable}})
    import re
    variables = re.findall(r'\{\{(\w+)\}\}', template.template)
    template.variables = list(set(variables))
    
    if tenant_id not in _prompt_templates:
        _prompt_templates[tenant_id] = []
    
    _prompt_templates[tenant_id].append(template)
    
    return template


@router.get(
    "/templates/{template_id}",
    response={200: PromptTemplate, 404: ErrorResponse},
    summary="Get prompt template"
)
async def get_template(
    request: HttpRequest,
    template_id: UUID
) -> PromptTemplate:
    """
    Get a specific prompt template by ID.
    """
    tenant_id = request.auth.get('tenant_id')
    
    templates = _prompt_templates.get(tenant_id, [])
    
    for t in templates:
        if t.id == template_id:
            return t
    
    raise ValueError("Template not found")


@router.put(
    "/templates/{template_id}",
    response={200: PromptTemplate, 404: ErrorResponse},
    summary="Update prompt template"
)
async def update_template(
    request: HttpRequest,
    template_id: UUID,
    template: PromptTemplate
) -> PromptTemplate:
    """
    Update an existing prompt template.
    """
    tenant_id = request.auth.get('tenant_id')
    
    templates = _prompt_templates.get(tenant_id, [])
    
    for i, t in enumerate(templates):
        if t.id == template_id:
            template.id = template_id
            template.created_at = t.created_at
            template.updated_at = datetime.utcnow()
            
            # Re-extract variables
            import re
            variables = re.findall(r'\{\{(\w+)\}\}', template.template)
            template.variables = list(set(variables))
            
            _prompt_templates[tenant_id][i] = template
            return template
    
    raise ValueError("Template not found")


@router.delete(
    "/templates/{template_id}",
    response={204: None, 404: ErrorResponse},
    summary="Delete prompt template"
)
async def delete_template(
    request: HttpRequest,
    template_id: UUID
) -> None:
    """
    Delete a prompt template.
    """
    tenant_id = request.auth.get('tenant_id')
    
    templates = _prompt_templates.get(tenant_id, [])
    
    for i, t in enumerate(templates):
        if t.id == template_id:
            if t.is_system:
                raise ValueError("Cannot delete system template")
            _prompt_templates[tenant_id].pop(i)
            return
    
    raise ValueError("Template not found")


@router.post(
    "/templates/{template_id}/render",
    response={200: dict},
    summary="Render prompt template with variables"
)
async def render_template(
    request: HttpRequest,
    template_id: UUID,
    variables: dict[str, str]
) -> dict:
    """
    Render a prompt template by substituting variables.
    """
    tenant_id = request.auth.get('tenant_id')
    
    templates = _prompt_templates.get(tenant_id, [])
    
    for t in templates:
        if t.id == template_id:
            rendered = t.template
            for key, value in variables.items():
                rendered = rendered.replace(f"{{{{{key}}}}}", value)
            
            return {
                "template_id": str(template_id),
                "rendered": rendered,
                "variables_used": list(variables.keys()),
            }
    
    raise ValueError("Template not found")
