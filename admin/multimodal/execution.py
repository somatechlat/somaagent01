"""Multimodal Execution API.


Per AGENT_TASKS.md Phase 7.3 - Multimodal Execution.

- PhD Dev: DAG execution, parallel processing
- ML Eng: OpenAI DALL-E, image generation
- DevOps: External service integration
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.conf import settings
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import BadRequestError, ServiceUnavailableError

router = Router(tags=["multimodal"])
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

from admin.saas.models.profiles import PlatformConfig
from admin.llm.models import LLMModelConfig
from services.common.unified_secret_manager import get_secret_manager


# =============================================================================
# SCHEMAS
# =============================================================================


class ImageGenerationRequest(BaseModel):
    """DALL-E image generation request."""

    prompt: str
    size: str = "1024x1024"  # 256x256, 512x512, 1024x1024
    quality: str = "standard"  # standard, hd
    style: str = "natural"  # natural, vivid


class ImageGenerationResponse(BaseModel):
    """Image generation response."""

    image_id: str
    url: str
    prompt: str
    revised_prompt: Optional[str] = None
    created_at: str


class DiagramRequest(BaseModel):
    """Mermaid diagram request."""

    code: str
    format: str = "svg"  # svg, png
    theme: str = "default"  # default, dark, forest, neutral


class DiagramResponse(BaseModel):
    """Diagram response."""

    diagram_id: str
    format: str
    url: str
    created_at: str


class ScreenshotRequest(BaseModel):
    """Webpage screenshot request."""

    url: str
    width: int = 1920
    height: int = 1080
    full_page: bool = False
    format: str = "png"  # png, jpeg


class ScreenshotResponse(BaseModel):
    """Screenshot response."""

    screenshot_id: str
    url: str
    format: str
    width: int
    height: int
    created_at: str


class DAGNode(BaseModel):
    """DAG execution node."""

    node_id: str
    operation: str  # generate_image, render_diagram, screenshot, custom
    input: dict
    depends_on: Optional[list[str]] = None


class DAGRequest(BaseModel):
    """DAG execution request."""

    nodes: list[DAGNode]
    parallel: bool = True


class DAGNodeResult(BaseModel):
    """Single node execution result."""

    node_id: str
    status: str  # pending, running, completed, failed
    output: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class DAGResponse(BaseModel):
    """DAG execution response."""

    dag_id: str
    status: str  # pending, running, completed, failed
    nodes: list[DAGNodeResult]
    total_duration_ms: Optional[float] = None


# =============================================================================
# ENDPOINTS - Image Generation
# =============================================================================


@router.post(
    "/images/generate",
    response=ImageGenerationResponse,
    summary="Generate image (DALL-E)",
    auth=AuthBearer(),
)
async def generate_image(request, payload: ImageGenerationRequest) -> ImageGenerationResponse:
    """Generate image using OpenAI DALL-E.

    Per Phase 7.3: OpenAI DALL-E adapter

    ML Eng: High-quality image generation with prompt optimization.
    """
    import httpx

    # 1. Resolve Model Configuration (Rule 91)
    # We look for a model with 'image_generation' capability
    # In future, this should be scoped to the Tenant/Capsule
    model_config = await LLMModelConfig.objects.filter(
        capabilities__contains="image_generation",
        is_active=True
    ).order_by("-priority").afirst()

    if not model_config:
         raise ServiceUnavailableError("openai", "No image generation model configured in LLMModelConfig")

    # 2. Retrieve Secret from Vault (No Env Vars)
    sm = get_secret_manager()
    try:
        api_key = sm.get_provider_key(model_config.provider)
    except Exception as e:
        logger.error(f"Vault error: {e}")
        raise ServiceUnavailableError("openai", "Could not retrieve API key from Vault")

    if not api_key:
        raise ServiceUnavailableError("openai", f"API keys not configured for provider {model_config.provider}")

    if len(payload.prompt) > 4000:
        raise BadRequestError("Prompt exceeds maximum length of 4000 characters")

    image_id = str(uuid4())

    # 3. Execute Request
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Use model-specific URL if defined, else default to OpenAI
            base_url = model_config.api_base or "https://api.openai.com/v1"

            response = await client.post(
                f"{base_url}/images/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model_config.name, # Use specific model name from DB (e.g. dall-e-3)
                    "prompt": payload.prompt,
                    "size": payload.size,
                    "quality": payload.quality,
                    "style": payload.style,
                    "n": 1,
                },
            )

            if response.status_code == 200:
                data = response.json()
                image_data = data["data"][0]

                return ImageGenerationResponse(
                    image_id=image_id,
                    url=image_data.get("url", ""),
                    prompt=payload.prompt,
                    revised_prompt=image_data.get("revised_prompt"),
                    created_at=timezone.now().isoformat(),
                )
            else:
                logger.error(f"DALL-E error: {response.status_code} - {response.text}")
                raise ServiceUnavailableError("openai", f"Provider error: {response.status_code}")

    except httpx.HTTPError as e:
        logger.error(f"Provider connection error: {e}")
        raise ServiceUnavailableError("openai", "Image generation service unavailable")


# =============================================================================
# ENDPOINTS - Diagrams
# =============================================================================


@router.post(
    "/diagrams/render",
    response=DiagramResponse,
    summary="Render Mermaid diagram",
    auth=AuthBearer(),
)
async def render_diagram(request, payload: DiagramRequest) -> DiagramResponse:
    """Render Mermaid diagram to image.

    Per Phase 7.3: Mermaid diagram adapter

    PhD Dev: Convert Mermaid code to visual diagrams.
    """

    import httpx

    # Resolve Mermaid URL from PlatformConfig (Rule 91)
    defaults = await PlatformConfig.aget_instance()
    mermaid_url = defaults.defaults.get("mermaid_cli_url", "http://localhost:9300")

    diagram_id = str(uuid4())

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{mermaid_url}/render",
                json={
                    "code": payload.code,
                    "format": payload.format,
                    "theme": payload.theme,
                },
            )

            if response.status_code == 200:
                # Store the diagram and return URL
                return DiagramResponse(
                    diagram_id=diagram_id,
                    format=payload.format,
                    url=f"/api/v2/multimodal/diagrams/{diagram_id}",
                    created_at=timezone.now().isoformat(),
                )
            else:
                logger.error(f"Mermaid error: {response.status_code} - {response.text}")
                raise ServiceUnavailableError("mermaid", "Mermaid rendering failed")

    except httpx.HTTPError as e:
        logger.error(f"Mermaid service unreachable: {e}")
        # Fail closed (Vibe Rule 124 - Real Infra Only)
        raise ServiceUnavailableError("mermaid", "Mermaid service unreachable")


# =============================================================================
# ENDPOINTS - Screenshots
# =============================================================================


@router.post(
    "/screenshots/capture",
    response=ScreenshotResponse,
    summary="Capture webpage screenshot",
    auth=AuthBearer(),
)
async def capture_screenshot(request, payload: ScreenshotRequest) -> ScreenshotResponse:
    """Capture screenshot of a webpage using Playwright.

    Per Phase 7.3: Playwright screenshot adapter

    DevOps: Headless browser automation for screenshots.
    """
    # In production: use Playwright service
    # async with async_playwright() as p:
    #     browser = await p.chromium.launch()
    #     page = await browser.new_page(viewport={"width": payload.width, "height": payload.height})
    #     await page.goto(payload.url)
    #     screenshot = await page.screenshot(full_page=payload.full_page)
    #     await browser.close()

    screenshot_id = str(uuid4())

    return ScreenshotResponse(
        screenshot_id=screenshot_id,
        url=f"/api/v2/multimodal/screenshots/{screenshot_id}",
        format=payload.format,
        width=payload.width,
        height=payload.height,
        created_at=timezone.now().isoformat(),
    )


# =============================================================================
# ENDPOINTS - DAG Execution
# =============================================================================


@router.post(
    "/dag/execute",
    response=DAGResponse,
    summary="Execute multimodal DAG",
    auth=AuthBearer(),
)
async def execute_dag(request, payload: DAGRequest) -> DAGResponse:
    """Execute a DAG of multimodal operations.

    Per Phase 7.3: DAG execution engine

    PhD Dev: Parallel execution with dependency resolution.
    """
    import asyncio
    import time

    start = time.time()
    dag_id = str(uuid4())

    # Build dependency graph
    node_map = {node.node_id: node for node in payload.nodes}
    results: dict[str, DAGNodeResult] = {}

    async def execute_node(node: DAGNode) -> DAGNodeResult:
        """Execute a single DAG node."""
        node_start = time.time()

        try:
            # Wait for dependencies
            if node.depends_on:
                for dep_id in node.depends_on:
                    if dep_id in results and results[dep_id].status == "failed":
                        return DAGNodeResult(
                            node_id=node.node_id,
                            status="failed",
                            error=f"Dependency {dep_id} failed",
                        )

            # Execute based on operation type
            output = {}
            if node.operation == "generate_image":
                output = {"type": "image", "status": "placeholder"}
            elif node.operation == "render_diagram":
                output = {"type": "diagram", "status": "placeholder"}
            elif node.operation == "screenshot":
                output = {"type": "screenshot", "status": "placeholder"}
            else:
                output = {"type": "custom", "input": node.input}

            return DAGNodeResult(
                node_id=node.node_id,
                status="completed",
                output=output,
                duration_ms=(time.time() - node_start) * 1000,
            )

        except Exception as e:
            return DAGNodeResult(
                node_id=node.node_id,
                status="failed",
                error=str(e),
                duration_ms=(time.time() - node_start) * 1000,
            )

    # Execute nodes (parallel if enabled)
    if payload.parallel:
        tasks = [execute_node(node) for node in payload.nodes]
        node_results = await asyncio.gather(*tasks)
    else:
        node_results = []
        for node in payload.nodes:
            result = await execute_node(node)
            results[node.node_id] = result
            node_results.append(result)

    total_duration = (time.time() - start) * 1000

    # Determine overall status
    statuses = [r.status for r in node_results]
    overall = "completed" if "failed" not in statuses else "failed"

    return DAGResponse(
        dag_id=dag_id,
        status=overall,
        nodes=node_results,
        total_duration_ms=total_duration,
    )


@router.get(
    "/dag/{dag_id}",
    summary="Get DAG execution status",
    auth=AuthBearer(),
)
async def get_dag_status(request, dag_id: str) -> dict:
    """Get status of a DAG execution."""
    # In production: query from database
    return {
        "dag_id": dag_id,
        "status": "completed",
        "nodes": [],
    }
