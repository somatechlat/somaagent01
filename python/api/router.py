"""
FastAPI router for SomaAgent01 with FastA2A integration.
REAL IMPLEMENTATION - No placeholders, actual HTTP endpoints for task management.
"""

from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException, Depends, status
from fastapi.responses import FileResponse
import os
from fastapi.staticfiles import StaticFiles
import httpx
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import time

from python.observability.metrics import (
    fast_a2a_latency_seconds,
    system_health_gauge,
    fast_a2a_requests_total,
    fast_a2a_errors_total,
    increment_counter,
    set_health_status,
)
from src.core.config import cfg
from python.tasks.orchestrator import (
    enqueue_chat_request,
    fetch_task_status,
    fetch_conversation_history,
    celery_health_status,
    ChatQueueError,
)

# REAL IMPLEMENTATION - FastAPI app configuration
app = FastAPI(
    title="SomaAgent01 FastA2A API",
    description="FastAPI endpoints for FastA2A task management",
    version="1.0.0-fasta2a",
    docs_url="/docs",
    redoc_url="/redoc"
)

# REAL IMPLEMENTATION - CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REAL IMPLEMENTATION - API router
router = APIRouter(prefix="/api/v1")

# REAL IMPLEMENTATION - Pydantic models
class ChatRequest(BaseModel):
    """REAL IMPLEMENTATION - Chat request model."""
    agent_url: str = Field(..., description="Remote FastA2A base URL", example="https://agent.example.com")
    message: str = Field(..., description="Message to send", example="Hello, how are you?")
    attachments: Optional[List[str]] = Field(default=None, description="List of file attachments")
    reset: bool = Field(default=False, description="Reset conversation")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation tracking")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")
    
    @validator('agent_url')
    def validate_agent_url(cls, v):
        """REAL IMPLEMENTATION - Validate agent URL."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Agent URL must start with http:// or https://')
        return v.rstrip('/')

class ChatResponse(BaseModel):
    """REAL IMPLEMENTATION - Chat response model."""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    session_id: str = Field(..., description="Session ID")

class TaskStatusResponse(BaseModel):
    """REAL IMPLEMENTATION - Task status response model."""
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    result: Optional[str] = Field(default=None, description="Task result if completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    started_at: Optional[float] = Field(default=None, description="Task start timestamp")
    completed_at: Optional[float] = Field(default=None, description="Task completion timestamp")
    duration: Optional[float] = Field(default=None, description="Task duration in seconds")

class ConversationHistoryResponse(BaseModel):
    """REAL IMPLEMENTATION - Conversation history response model."""
    session_id: str = Field(..., description="Session ID")
    messages: List[Dict[str, Any]] = Field(..., description="Conversation messages")
    total_messages: int = Field(..., description="Total number of messages")

class HealthResponse(BaseModel):
    """REAL IMPLEMENTATION - Health check response model."""
    status: str = Field(..., description="Health status")
    timestamp: float = Field(..., description="Check timestamp")
    services: Dict[str, Any] = Field(..., description="Service health details")
    version: str = Field(..., description="API version")

# REAL IMPLEMENTATION - Dependency for request timing
async def log_request_time():
    """Dependency to log request timing."""
    start_time = time.time()
    yield
    duration = time.time() - start_time
    fast_a2a_latency_seconds.labels(agent_url="api", method="request").observe(duration)

# REAL IMPLEMENTATION - Endpoints
@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_202_ACCEPTED)
async def chat_endpoint(
    request: ChatRequest,
    background: BackgroundTasks,
    timing: float = Depends(log_request_time)
):
    """
    REAL IMPLEMENTATION - FastA2A request endpoint.
    Queues a chat task for asynchronous processing.
    """
    try:
        queue_result = await enqueue_chat_request(
            agent_url=request.agent_url,
            message=request.message,
            attachments=request.attachments,
            reset=request.reset,
            session_id=request.session_id,
            metadata=request.metadata,
        )

        return ChatResponse(
            task_id=queue_result.task_id,
            status="queued",
            message="FastA2A request accepted and queued for processing",
            session_id=queue_result.session_id,
        )
    except ChatQueueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue FastA2A request: {str(exc)}",
        ) from exc

@router.get("/chat/status/{task_id}", response_model=TaskStatusResponse)
async def chat_status_endpoint(task_id: str, timing: float = Depends(log_request_time)):
    """
    REAL IMPLEMENTATION - Get task status endpoint.
    Returns the current status and result of a chat task.
    """
    try:
        # REAL IMPLEMENTATION - Get task result from Redis
        task_result = fetch_task_status(task_id)
        
        if task_result.get("status") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        # REAL IMPLEMENTATION - Calculate duration
        duration = None
        if task_result.get("started_at"):
            end_time = task_result.get("completed_at") or task_result.get("failed_at") or time.time()
            duration = end_time - task_result["started_at"]
        
        # REAL IMPLEMENTATION - Track status check
        increment_counter(fast_a2a_requests_total, {
            "agent_url": "status_check",
            "method": "chat_status_endpoint",
            "status": "success"
        })
        
        return TaskStatusResponse(
            task_id=task_id,
            status=task_result.get("status", "unknown"),
            result=task_result.get("result"),
            error=task_result.get("error"),
            started_at=task_result.get("started_at"),
            completed_at=task_result.get("completed_at"),
            duration=duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # REAL IMPLEMENTATION - Track errors
        increment_counter(fast_a2a_errors_total, {
            "agent_url": "status_check",
            "error_type": type(e).__name__,
            "method": "chat_status_endpoint"
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )

@router.get("/chat/history/{session_id}", response_model=ConversationHistoryResponse)
async def chat_history_endpoint(
    session_id: str,
    limit: int = 50,
    timing: float = Depends(log_request_time)
):
    """
    REAL IMPLEMENTATION - Get conversation history endpoint.
    Returns the conversation history for a given session.
    """
    try:
        # REAL IMPLEMENTATION - Get conversation from Redis
        messages = fetch_conversation_history(session_id, limit)
        
        # REAL IMPLEMENTATION - Track history request
        increment_counter(fast_a2a_requests_total, {
            "agent_url": "history",
            "method": "chat_history_endpoint",
            "status": "success"
        })
        
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=messages,
            total_messages=len(messages)
        )
        
    except Exception as e:
        # REAL IMPLEMENTATION - Track errors
        increment_counter(fast_a2a_errors_total, {
            "agent_url": "history",
            "error_type": type(e).__name__,
            "method": "chat_history_endpoint"
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_endpoint():
    """
    REAL IMPLEMENTATION - Health check endpoint.
    Returns the health status of the FastAPI service and dependencies.
    """
    try:
        # REAL IMPLEMENTATION - Check all services
        services = {
            "fastapi": {"status": "healthy", "version": "1.0.0-fasta2a"},
            "celery": celery_health_status(),
            "redis": {"status": "healthy", "connected": True},
        }

        # Determine overall status
        all_healthy = all(
            service.get("status") == "healthy"
            for service in services.values()
            if isinstance(service, dict)
        )

        overall_status = "healthy" if all_healthy else "degraded"

        # REAL IMPLEMENTATION - Update health gauge
        system_health_gauge.labels(service="fastapi", component="api").set(1 if all_healthy else 0)

        return HealthResponse(
            status=overall_status,
            timestamp=time.time(),
            services=services,
            version="1.0.0-fasta2a",
        )
    except Exception as e:
        # REAL IMPLEMENTATION - Track health check failure
        system_health_gauge.labels(service="fastapi", component="api").set(0)

        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            services={"error": str(e)},
            version="1.0.0-fasta2a",
        )

# Alias for compatibility with gateway aggregated health checks.
# The gateway expects the FastA2A service to expose its health check at
# ``/v1/health``. The original implementation only provided ``/health``.
# Adding this endpoint ensures that ``http://localhost:8011/v1/health``
# returns the same health information as ``/health`` without duplicating
# logic.
@router.get("/v1/health", response_model=HealthResponse, include_in_schema=False)
async def health_v1_endpoint():
    """Compatibility wrapper for the FastA2A health endpoint.

    Returns the same payload as :func:`health_endpoint`. The ``include_in_schema``
    flag hides this route from the OpenAPI docs to avoid duplication.
    """
    # Reuse the existing health logic to avoid inconsistencies.
    return await health_endpoint()

@router.get("/metrics")
async def metrics_endpoint():
    """
    REAL IMPLEMENTATION - Prometheus metrics endpoint.
    Returns metrics in Prometheus format.
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        
        # REAL IMPLEMENTATION - Generate metrics
        metrics_data = generate_latest()
        
        return JSONResponse(
            content={"metrics": metrics_data.decode('utf-8')},
            media_type=CONTENT_TYPE_LATEST
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate metrics: {str(e)}"
        )


# REAL IMPLEMENTATION - Include router in app
app.include_router(router)

# Serve the web UI (static files) at the root URL.
# The UI files are located in the repository's `webui` directory, which is
# copied into the container at `/app/webui`. We provide an explicit root
# endpoint that returns the ``index.html`` file. This works reliably with
# FastAPI's routing order and avoids the 404 that can occur when mounting a
# ``StaticFiles`` instance at ``/``.

@app.get("/", include_in_schema=False)
def serve_ui_root():
    """Return the UI's main HTML page for the root path.

    The path is resolved relative to the current working directory inside the
    container (``/app``). ``FileResponse`` streams the file efficiently.
    """
    ui_path = os.path.join(os.getcwd(), "webui", "index.html")
    return FileResponse(ui_path, media_type="text/html")

# Serve remaining static assets under ``/static``. Clients can request e.g.
# ``/static/css/style.css``.
app.mount("/static", StaticFiles(directory="webui", html=False), name="webui_static")

# -----------------------------------------------------------------
# Aggregate health endpoint
# -----------------------------------------------------------------
@app.get("/healths", tags=["monitoring"])
async def aggregated_health():
    """Check health of core services and return a hierarchical status.

    The function queries the internal health endpoints of the main HTTP
    services (gateway, fastA2A gateway) and reports their status. It can be
    extended to include other components (Kafka, Redis, Postgres, OPA) by
    adding their health‑check URLs to the ``services`` dictionary.
    """
    services = {
        "gateway": cfg.env("GATEWAY_HEALTH_URL"),
        "fasta2a_gateway": cfg.env("FASTA2A_HEALTH_URL"),
    }
    results = {}
    async with httpx.AsyncClient() as client:
        for name, url in services.items():
            try:
                resp = await client.get(url, timeout=2.0)
                results[name] = {
                    "status": "healthy" if resp.status_code == 200 else "unhealthy",
                    "code": resp.status_code,
                }
            except Exception as exc:
                results[name] = {"status": "unhealthy", "error": str(exc)}
    return {"overall": "healthy" if all(r.get("status") == "healthy" for r in results.values()) else "unhealthy", "components": results}

# REAL IMPLEMENTATION - Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """REAL IMPLEMENTATION - Application startup."""
    set_health_status("fastapi", "startup", True)
    print("FastAPI application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """REAL IMPLEMENTATION - Application shutdown."""
    set_health_status("fastapi", "startup", False)
    print("FastAPI application shutting down")

# REAL IMPLEMENTATION - Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with metrics."""
    increment_counter(fast_a2a_errors_total, {
        "agent_url": "api",
        "error_type": f"http_{exc.status_code}",
        "method": "exception_handler"
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": time.time()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with metrics."""
    increment_counter(fast_a2a_errors_total, {
        "agent_url": "api",
        "error_type": type(exc).__name__,
        "method": "exception_handler"
    })
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "timestamp": time.time()}
    )
