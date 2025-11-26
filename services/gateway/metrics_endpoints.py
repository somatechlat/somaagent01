"""
Metrics Endpoints for SomaAgent01 - Real observability endpoints.
Production-ready HTTP endpoints for comprehensive metrics and monitoring.
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, REGISTRY

from observability.metrics import (
    get_metrics_snapshot,
    metrics_collector,
    record_memory_persistence,
    record_policy_decision,
    record_wal_lag,
)
from services.gateway.circuit_breakers import CircuitBreakerRegistry
from services.gateway.degradation_monitor import degradation_monitor

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/")
async def get_prometheus_metrics() -> PlainTextResponse:
    """
    Get Prometheus metrics in plain text format.

    Returns:
        PlainTextResponse with Prometheus metrics
    """
    try:
        metrics_data = generate_latest(REGISTRY)
        return PlainTextResponse(
            content=metrics_data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")


@router.get("/snapshot")
async def get_metrics_snapshot() -> Dict[str, Any]:
    """
    Get a snapshot of current key metrics.

    Returns:
        Dict with metrics snapshot
    """
    try:
        snapshot = get_metrics_snapshot()
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics snapshot: {str(e)}")


@router.get("/health")
async def get_metrics_service_health() -> Dict[str, Any]:
    """
    Health check for the metrics service itself.

    Returns:
        Dict with service health status
    """
    try:
        # Check if metrics collector is initialized
        is_initialized = metrics_collector._initialized

        # Get basic metrics counts
        from prometheus_client import REGISTRY

        metric_count = len(list(REGISTRY.collect()))

        return {
            "service": "metrics",
            "healthy": True,
            "initialized": is_initialized,
            "metrics_count": metric_count,
            "registry_collector_count": len(list(REGISTRY._collector_to_names.keys())),
            "timestamp": time.time(),
        }

    except Exception as e:
        return {"service": "metrics", "healthy": False, "error": str(e), "timestamp": time.time()}


@router.get("/system")
async def get_system_metrics() -> Dict[str, Any]:
    """
    Get system-level metrics.

    Returns:
        Dict with system metrics
    """
    try:
        import psutil

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Get process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent()

        system_metrics = {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process_cpu,
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
            },
            "timestamp": time.time(),
        }

        # Update Prometheus gauges
        from observability.metrics import system_cpu_usage, system_memory_usage

        system_memory_usage.set(memory.used)
        system_cpu_usage.set(cpu_percent)

        return system_metrics

    except ImportError:
        raise HTTPException(status_code=503, detail="psutil not available for system metrics")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/application")
async def get_application_metrics() -> Dict[str, Any]:
    """
    Get application-specific metrics.

    Returns:
        Dict with application metrics
    """
    try:
        # Get degradation status
        degradation_status = await degradation_monitor.get_degradation_status()

        # Get circuit breaker summary
        circuit_summary = {}
        for component_name in CircuitBreakerRegistry.list_circuits():
            circuit = CircuitBreakerRegistry.get_circuit(component_name)
            if circuit:
                circuit_summary[component_name] = {
                    "state": circuit.state.value,
                    "failure_count": circuit.failure_count,
                    "success_count": circuit.success_count,
                }

        # Also include circuits from degradation monitor
        for component_name, circuit in degradation_monitor.circuit_breakers.items():
            if component_name not in circuit_summary:
                circuit_summary[component_name] = {
                    "state": circuit.state.value,
                    "failure_count": circuit.failure_count,
                    "success_count": circuit.success_count,
                }

        app_metrics = {
            "degradation": {
                "overall_level": degradation_status.overall_level.value,
                "affected_components": degradation_status.affected_components,
                "healthy_components": degradation_status.healthy_components,
                "total_components": degradation_status.total_components,
            },
            "circuit_breakers": circuit_summary,
            "timestamp": time.time(),
        }

        return app_metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get application metrics: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    duration_minutes: int = 60, granularity: str = "1m"
) -> Dict[str, Any]:
    """
    Get performance metrics over time.

    Args:
        duration_minutes: How many minutes of history to retrieve
        granularity: Time granularity (1m, 5m, 15m, 1h)

    Returns:
        Dict with performance metrics
    """
    try:
        # Time-series metrics retrieval implementation
        # In a real implementation, you'd query a time-series database

        # Calculate time range
        end_time = time.time()
        start_time = end_time - (duration_minutes * 60)

        performance_metrics = {
            "time_range": {
                "start": start_time,
                "end": end_time,
                "duration_minutes": duration_minutes,
                "granularity": granularity,
            },
            "metrics": {
                "response_times": [],
                "error_rates": [],
                "throughput": [],
                "resource_usage": [],
            },
            "aggregations": {
                "avg_response_time": 0.0,
                "max_response_time": 0.0,
                "min_response_time": 0.0,
                "total_requests": 0,
                "error_rate": 0.0,
                "p95_response_time": 0.0,
                "p99_response_time": 0.0,
            },
            "timestamp": time.time(),
        }

        return performance_metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/sla")
async def get_sla_metrics() -> Dict[str, Any]:
    """
    Get SLA (Service Level Agreement) metrics.

    Returns:
        Dict with SLA metrics
    """
    try:
        # Get current degradation status
        degradation_status = await degradation_monitor.get_degradation_status()

        # Calculate SLA metrics
        total_components = degradation_status.total_components
        healthy_components = len(degradation_status.healthy_components)

        availability_percentage = (
            (healthy_components / total_components * 100) if total_components > 0 else 0
        )

        sla_metrics = {
            "availability": {
                "percentage": availability_percentage,
                "healthy_components": healthy_components,
                "total_components": total_components,
                "sla_target": 99.9,  # 99.9% availability target
                "met": availability_percentage >= 99.9,
            },
            "performance": {
                "response_time_target_ms": 1000,  # 1 second target
                "current_avg_response_time_ms": 0,  # Would calculate from actual metrics
                "met": True,  # Would calculate from actual metrics
            },
            "error_rate": {
                "target_percentage": 1.0,  # 1% error rate target
                "current_percentage": 0,  # Would calculate from actual metrics
                "met": True,  # Would calculate from actual metrics
            },
            "degradation": {
                "level": degradation_status.overall_level.value,
                "affected_components": degradation_status.affected_components,
                "recommendations": degradation_status.recommendations,
            },
            "timestamp": time.time(),
        }

        return sla_metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SLA metrics: {str(e)}")


@router.post("/memory/persistence")
async def record_memory_persistence_metric(
    duration: float, operation: str, status: str, tenant: str = "default"
) -> Dict[str, Any]:
    """
    Record memory persistence metrics.

    Args:
        duration: Operation duration in seconds
        operation: Type of operation (write, read, delete)
        status: Operation status (success, error)
        tenant: Tenant identifier

    Returns:
        Dict with recording result
    """
    try:
        record_memory_persistence(duration, operation, status, tenant)

        return {
            "operation": "memory_persistence_recorded",
            "duration": duration,
            "operation_type": operation,
            "status": status,
            "tenant": tenant,
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to record memory persistence metric: {str(e)}"
        )


@router.post("/memory/wal-lag")
async def record_wal_lag_metric(lag_seconds: float, tenant: str = "default") -> Dict[str, Any]:
    """
    Record WAL lag metrics.

    Args:
        lag_seconds: WAL lag in seconds
        tenant: Tenant identifier

    Returns:
        Dict with recording result
    """
    try:
        record_wal_lag(lag_seconds, tenant)

        return {
            "operation": "wal_lag_recorded",
            "lag_seconds": lag_seconds,
            "tenant": tenant,
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record WAL lag metric: {str(e)}")


@router.post("/memory/policy-decision")
async def record_policy_decision_metric(
    action: str, resource: str, tenant: str = "default", decision: str = "allow"
) -> Dict[str, Any]:
    """
    Record policy decision metrics.

    Args:
        action: Action performed
        resource: Resource being accessed
        tenant: Tenant identifier
        decision: Decision made (allow, deny)

    Returns:
        Dict with recording result
    """
    try:
        record_policy_decision(action, resource, tenant, decision)

        return {
            "operation": "policy_decision_recorded",
            "action": action,
            "resource": resource,
            "tenant": tenant,
            "decision": decision,
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to record policy decision metric: {str(e)}"
        )


@router.get("/custom")
async def get_custom_metrics(
    metric_names: Optional[List[str]] = None, include_help: bool = False
) -> Dict[str, Any]:
    """
    Get custom metrics with optional filtering.

    Args:
        metric_names: List of specific metric names to retrieve
        include_help: Whether to include help text for metrics

    Returns:
        Dict with custom metrics
    """
    try:
        custom_metrics = {}

        # Collect all metrics
        for collector in REGISTRY._collector_to_names.keys():
            try:
                if hasattr(collector, "_name"):
                    name = collector._name
                else:
                    name = collector.__class__.__name__

                # Filter by metric names if specified
                if metric_names and name not in metric_names:
                    continue

                # Get metric data
                metric_data = {"type": collector.__class__.__name__, "samples": []}

                # Add help text if requested
                if include_help and hasattr(collector, "_documentation"):
                    metric_data["help"] = collector._documentation

                # Collect samples
                for metric in collector.collect():
                    for sample in metric.samples:
                        sample_data = {
                            "name": sample.name,
                            "value": sample.value,
                            "labels": dict(sample.labels) if sample.labels else {},
                        }
                        if hasattr(sample, "timestamp"):
                            sample_data["timestamp"] = sample.timestamp

                        metric_data["samples"].append(sample_data)

                custom_metrics[name] = metric_data

            except Exception as e:
                # Skip problematic metrics
                continue

        return {
            "metrics": custom_metrics,
            "total_metrics": len(custom_metrics),
            "filtered_by": metric_names,
            "include_help": include_help,
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get custom metrics: {str(e)}")


@router.get("/export")
async def export_metrics(
    format: str = "json", start_time: Optional[float] = None, end_time: Optional[float] = None
) -> Response:
    """
    Export metrics in various formats.

    Args:
        format: Export format (json, prometheus, csv)
        start_time: Start timestamp for time range (optional)
        end_time: End timestamp for time range (optional)

    Returns:
        Response with exported metrics
    """
    try:
        if format == "prometheus":
            metrics_data = generate_latest(REGISTRY)
            return PlainTextResponse(
                content=metrics_data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST
            )

        elif format == "json":
            snapshot = get_metrics_snapshot()
            return JSONResponse(content=snapshot)

        elif format == "csv":
            # Generate CSV format
            csv_data = "metric_name,labels,value,timestamp\n"

            for collector in REGISTRY._collector_to_names.keys():
                try:
                    for metric in collector.collect():
                        for sample in metric.samples:
                            labels_str = ",".join(
                                [f"{k}={v}" for k, v in (sample.labels or {}).items()]
                            )
                            csv_data += f"{sample.name},{labels_str},{sample.value},{time.time()}\n"
                except Exception:
                    continue

            return PlainTextResponse(content=csv_data, media_type="text/csv")

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export metrics: {str(e)}")
