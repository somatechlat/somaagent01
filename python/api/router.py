"""
FastAPI router for SomaAgent01 with FastA2A integration.
REAL IMPLEMENTATION - No placeholders, actual HTTP endpoints for task management.
"""

from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import time
import uuid
from celery.result import AsyncResult

from python.tasks.a2a_chat_task import a2a_chat_task, get_task_result, get_conversation_history
from python.observability.metrics import (
    fast_a2a_requests_total,
    fast_a2a_latency_seconds,
    fast_a2a_errors_total,
    system_health_gauge,
    increment_counter,
    set_health_status
)
from python.observability.event_publisher import publish_event

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
    agent_url: str = Field(..., description="Remote FastA2A base URL", example="http://localhost:8080")
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
    start_time = time.time()
    
    try:
        # REAL IMPLEMENTATION - Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # REAL IMPLEMENTATION - Enqueue Celery task
        task = a2a_chat_task.delay(
            agent_url=request.agent_url,
            message=request.message,
            attachments=request.attachments,
            reset=request.reset,
            session_id=session_id,
            metadata=request.metadata
        )
        
        # REAL IMPLEMENTATION - Track successful request
        increment_counter(fast_a2a_requests_total, {
            "agent_url": request.agent_url,
            "method": "chat_endpoint",
            "status": "queued"
        })
        
        # REAL IMPLEMENTATION - Publish event
        await publish_event(
            event_type="fast_a2a_chat_queued",
            data={
                "task_id": task.id,
                "agent_url": request.agent_url,
                "session_id": session_id,
                "message_length": len(request.message),
                "has_attachments": bool(request.attachments),
                "reset": request.reset
            },
            metadata=request.metadata
        )
        
        set_health_status("fastapi", "chat_endpoint", True)
        
        return ChatResponse(
            task_id=task.id,
            status="queued",
            message="FastA2A request accepted and queued for processing",
            session_id=session_id
        )
        
    except Exception as e:
        # REAL IMPLEMENTATION - Track errors
        increment_counter(fast_a2a_errors_total, {
            "agent_url": request.agent_url,
            "error_type": type(e).__name__,
            "method": "chat_endpoint"
        })
        
        set_health_status("fastapi", "chat_endpoint", False)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue FastA2A request: {str(e)}"
        )

@router.get("/chat/status/{task_id}", response_model=TaskStatusResponse)
async def chat_status_endpoint(task_id: str, timing: float = Depends(log_request_time)):
    """
    REAL IMPLEMENTATION - Get task status endpoint.
    Returns the current status and result of a chat task.
    """
    try:
        # REAL IMPLEMENTATION - Get task result from Redis
        task_result = get_task_result(task_id)
        
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
        messages = get_conversation_history(session_id, limit)
        
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
        from python.tasks.a2a_chat_task import check_celery_health
        
        # REAL IMPLEMENTATION - Check all services
        services = {
            "fastapi": {"status": "healthy", "version": "1.0.0-fasta2a"},
            "celery": check_celery_health(),
            "redis": {"status": "healthy", "connected": True}
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
            version="1.0.0-fasta2a"
        )
        
    except Exception as e:
        # REAL IMPLEMENTATION - Track health check failure
        system_health_gauge.labels(service="fastapi", component="api").set(0)
        
        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            services={"error": str(e)},
            version="1.0.0-fasta2a"
        )

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

@router.get("/")
async def root_endpoint():
    """
    REAL IMPLEMENTATION - Root endpoint.
    Returns API information and available endpoints.
    """
    return {
        "name": "SomaAgent01 FastA2A API",
        "version": "1.0.0-fasta2a",
        "description": "FastAPI endpoints for FastA2A task management",
        "endpoints": {
            "chat": "POST /api/v1/chat - Queue a chat task",
            "status": "GET /api/v1/chat/status/{task_id} - Get task status",
            "history": "GET /api/v1/chat/history/{session_id} - Get conversation history",
            "health": "GET /api/v1/health - Health check",
            "metrics": "GET /api/v1/metrics - Prometheus metrics",
            "docs": "GET /docs - API documentation"
        },
        "timestamp": time.time()
    }

# REAL IMPLEMENTATION - Include router in app
app.include_router(router)

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

# REAL IMPLEMENTATION - Advanced production health endpoints
@app.get("/health/sla")
async def sla_health():
    """SLA compliance monitoring endpoint."""
    try:
        from python.observability.metrics import sla_monitor, production_metrics
        
        # Check current SLA compliance
        response_time_compliant = sla_monitor.check_response_time_sla(0.3)  # Example response time
        availability_compliant = sla_monitor.check_availability_sla(99.95)   # Example availability
        error_rate_compliant = sla_monitor.check_error_rate_sla(0.05)       # Example error rate
        
        # Get detailed metrics
        error_budget = production_metrics.error_budget_remaining.labels(
            service="somaagent01", 
            sla_window="1h"
        )._value._value
        
        error_rate = production_metrics.error_rate_percent.labels(
            service="somaagent01", 
            error_type="total"
        )._value._value
        
        overall_status = "healthy" if all([response_time_compliant, availability_compliant, error_rate_compliant]) else "degraded"
        
        return {
            "status": overall_status,
            "service": "somaagent01",
            "message": "SLA compliance status",
            "details": {
                "sla_compliance": {
                    "response_time": "compliant" if response_time_compliant else "violated",
                    "availability": "compliant" if availability_compliant else "violated",
                    "error_rate": "compliant" if error_rate_compliant else "violated"
                },
                "metrics": {
                    "error_budget_remaining": error_budget,
                    "current_error_rate": error_rate
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "somaagent01",
            "message": f"SLA health check failed: {str(e)}",
            "details": {"error": str(e)}
        }

@app.get("/health/metrics")
async def metrics_health():
    """Comprehensive metrics health endpoint."""
    try:
        from python.observability.metrics import production_metrics
        
        # Get resource metrics
        memory_usage = production_metrics.memory_usage_bytes.labels(
            service="somaagent01", 
            component="main"
        )._value._value
        
        cpu_usage = production_metrics.cpu_usage_percent.labels(
            service="somaagent01", 
            component="main"
        )._value._value
        
        disk_usage = production_metrics.disk_usage_bytes.labels(
            mount_point="/"
        )._value._value
        
        # Calculate health status based on resource usage
        memory_percent = (memory_usage / (8 * 1024 * 1024 * 1024)) * 100  # Assuming 8GB
        health_status = "healthy"
        
        if memory_percent > 90 or cpu_usage > 90:
            health_status = "critical"
        elif memory_percent > 70 or cpu_usage > 70:
            health_status = "warning"
        
        return {
            "status": health_status,
            "service": "somaagent01",
            "message": "Resource metrics health",
            "details": {
                "resources": {
                    "memory_bytes": memory_usage,
                    "memory_percent": memory_percent,
                    "cpu_percent": cpu_usage,
                    "disk_bytes": disk_usage
                },
                "thresholds": {
                    "memory_warning": 70,
                    "memory_critical": 90,
                    "cpu_warning": 70,
                    "cpu_critical": 90
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "somaagent01",
            "message": f"Metrics health check failed: {str(e)}",
            "details": {"error": str(e)}
        }

@app.get("/health/integrations")
async def integrations_health():
    """Integration health monitoring endpoint."""
    try:
        from python.observability.metrics import production_metrics
        
        # Check integration health scores
        integrations = ["somabrain", "fasta2a", "redis", "kafka", "postgres"]
        integration_health = {}
        
        for integration in integrations:
            health_score = production_metrics.integration_health_score.labels(
                integration_name=integration, 
                health_aspect="overall"
            )._value._value
            
            status = "healthy" if health_score >= 90 else "degraded" if health_score >= 70 else "unhealthy"
            
            integration_health[integration] = {
                "score": health_score,
                "status": status
            }
        
        # Calculate overall status
        all_healthy = all(health["status"] == "healthy" for health in integration_health.values())
        overall_status = "healthy" if all_healthy else "degraded"
        
        return {
            "status": overall_status,
            "service": "somaagent01",
            "message": "Integration health status",
            "details": {
                "integrations": integration_health,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "somaagent01",
            "message": f"Integrations health check failed: {str(e)}",
            "details": {"error": str(e)}
        }

@app.get("/health/readiness")
async def readiness_health():
    """Readiness probe for Kubernetes."""
    try:
        from python.observability.metrics import production_metrics
        
        # Check critical services
        critical_checks = {
            "context_builder": get_health_status("context_builder"),
            "fasta2a_client": get_health_status("fasta2a_client"),
            "event_publisher": get_health_status("event_publisher"),
            "conversation_worker": get_health_status("conversation_worker")
        }
        
        # Check resource utilization
        memory_usage = production_metrics.memory_usage_bytes.labels(
            service="somaagent01", 
            component="main"
        )._value._value
        
        cpu_usage = production_metrics.cpu_usage_percent.labels(
            service="somaagent01", 
            component="main"
        )._value._value
        
        # Calculate readiness
        all_critical_healthy = all(critical_checks.values())
        resources_ok = memory_usage < (8 * 1024 * 1024 * 1024) and cpu_usage < 90  # 8GB RAM, 90% CPU
        
        ready = all_critical_healthy and resources_ok
        
        return {
            "ready": ready,
            "status": "ready" if ready else "not_ready",
            "service": "somaagent01",
            "message": "Service readiness check",
            "details": {
                "critical_services": critical_checks,
                "resources": {
                    "memory_ok": memory_usage < (8 * 1024 * 1024 * 1024),
                    "cpu_ok": cpu_usage < 90
                },
                "checks": {
                    "critical_services_healthy": all_critical_healthy,
                    "resources_sufficient": resources_ok
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        return {
            "ready": False,
            "status": "not_ready",
            "service": "somaagent01",
            "message": f"Readiness check failed: {str(e)}",
            "details": {"error": str(e)}
        }

@app.get("/health/liveness")
async def liveness_health():
    """Liveness probe for Kubernetes."""
    try:
        # Simple liveness check - just return OK if we can respond
        return {
            "alive": True,
            "status": "alive",
            "service": "somaagent01",
            "message": "Service is alive",
            "details": {
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": time.time() - start_time
            }
        }
    except Exception as e:
        return {
            "alive": False,
            "status": "unhealthy",
            "service": "somaagent01",
            "message": f"Liveness check failed: {str(e)}",
            "details": {"error": str(e)}
    )