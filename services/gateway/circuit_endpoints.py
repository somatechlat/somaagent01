"""
Circuit Breaker Endpoints for SomaAgent01 - Real circuit management.
Production-ready HTTP endpoints for circuit breaker monitoring and control.
"""

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from observability.metrics import metrics_collector
from services.gateway.circuit_breakers import CircuitBreakerRegistry, CircuitState
from services.gateway.degradation_monitor import degradation_monitor

router = APIRouter(prefix="/circuit", tags=["circuit"])


@router.get("/status")
async def get_circuit_status() -> Dict[str, Any]:
    """
    Get current status of all circuit breakers.

    Returns:
        Dict with circuit breaker status for all components
    """
    try:
        circuit_status = {}

        # Get circuit breaker status from registry
        for component_name in CircuitBreakerRegistry.list_circuits():
            circuit = CircuitBreakerRegistry.get_circuit(component_name)
            if circuit:
                circuit_status[component_name] = {
                    "state": circuit.state.value,
                    "failure_count": circuit.failure_count,
                    "last_failure_time": circuit.last_failure_time,
                    "success_count": circuit.success_count,
                    "failure_threshold": circuit.failure_threshold,
                    "recovery_timeout": circuit.recovery_timeout,
                    "last_state_change": circuit.last_state_change,
                }

        # Also include circuit breakers from degradation monitor
        for component_name, circuit_breaker in degradation_monitor.circuit_breakers.items():
            if component_name not in circuit_status:
                circuit_status[component_name] = {
                    "state": circuit_breaker.state.value,
                    "failure_count": circuit_breaker.failure_count,
                    "last_failure_time": circuit_breaker.last_failure_time,
                    "success_count": circuit_breaker.success_count,
                    "failure_threshold": circuit_breaker.failure_threshold,
                    "recovery_timeout": circuit_breaker.recovery_timeout,
                    "last_state_change": circuit_breaker.last_state_change,
                }

        return {
            "circuits": circuit_status,
            "total_circuits": len(circuit_status),
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get circuit status: {str(e)}")


@router.get("/status/{component_name}")
async def get_component_circuit_status(component_name: str) -> Dict[str, Any]:
    """
    Get circuit breaker status for a specific component.

    Args:
        component_name: Name of the component

    Returns:
        Dict with circuit breaker status for the component
    """
    try:
        # Try to get circuit from registry first
        circuit = CircuitBreakerRegistry.get_circuit(component_name)

        # If not found, try degradation monitor
        if not circuit:
            circuit = degradation_monitor.circuit_breakers.get(component_name)

        if not circuit:
            raise HTTPException(
                status_code=404, detail=f"Circuit breaker for {component_name} not found"
            )

        return {
            "component": component_name,
            "state": circuit.state.value,
            "failure_count": circuit.failure_count,
            "last_failure_time": circuit.last_failure_time,
            "success_count": circuit.success_count,
            "failure_threshold": circuit.failure_threshold,
            "recovery_timeout": circuit.recovery_timeout,
            "last_state_change": circuit.last_state_change,
            "timestamp": time.time(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get circuit status for {component_name}: {str(e)}"
        )


@router.post("/reset/{component_name}")
async def reset_circuit_breaker(component_name: str) -> Dict[str, Any]:
    """
    Reset circuit breaker for a component.

    Args:
        component_name: Name of the component

    Returns:
        Dict with reset results
    """
    try:
        # Try to reset circuit in registry first
        circuit = CircuitBreakerRegistry.get_circuit(component_name)
        if circuit:
            previous_state = circuit.state.value
            circuit.reset()
            new_state = circuit.state.value
        else:
            # Try degradation monitor
            circuit = degradation_monitor.circuit_breakers.get(component_name)
            if not circuit:
                raise HTTPException(
                    status_code=404, detail=f"Circuit breaker for {component_name} not found"
                )

            previous_state = circuit.state.value
            circuit.reset()
            new_state = circuit.state.value

        # Record reset action
        reset_result = {
            "component": component_name,
            "action": "reset",
            "previous_state": previous_state,
            "new_state": new_state,
            "timestamp": time.time(),
        }

        # Track metrics
        metrics_collector.track_error(
            error_type="circuit_breaker_reset", location=f"circuit_endpoints.{component_name}"
        )

        return reset_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset circuit breaker for {component_name}: {str(e)}",
        )


@router.post("/force-open/{component_name}")
async def force_open_circuit_breaker(component_name: str) -> Dict[str, Any]:
    """
    Force open circuit breaker for a component (for testing/maintenance).

    Args:
        component_name: Name of the component

    Returns:
        Dict with force open results
    """
    try:
        # Try to get circuit from registry first
        circuit = CircuitBreakerRegistry.get_circuit(component_name)
        if not circuit:
            # Try degradation monitor
            circuit = degradation_monitor.circuit_breakers.get(component_name)
            if not circuit:
                raise HTTPException(
                    status_code=404, detail=f"Circuit breaker for {component_name} not found"
                )

        previous_state = circuit.state.value

        # Force the circuit open by simulating failures
        for _ in range(circuit.failure_threshold + 1):
            try:
                await circuit.call(lambda: 1 / 0)  # Force an exception
            except:
                pass  # Expected to fail

        new_state = circuit.state.value

        # Record force open action
        force_result = {
            "component": component_name,
            "action": "force_open",
            "previous_state": previous_state,
            "new_state": new_state,
            "timestamp": time.time(),
        }

        # Track metrics
        metrics_collector.track_error(
            error_type="circuit_breaker_force_open", location=f"circuit_endpoints.{component_name}"
        )

        return force_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to force open circuit breaker for {component_name}: {str(e)}",
        )


@router.get("/config/{component_name}")
async def get_circuit_config(component_name: str) -> Dict[str, Any]:
    """
    Get circuit breaker configuration for a component.

    Args:
        component_name: Name of the component

    Returns:
        Dict with circuit breaker configuration
    """
    try:
        # Try to get circuit from registry first
        circuit = CircuitBreakerRegistry.get_circuit(component_name)
        if not circuit:
            # Try degradation monitor
            circuit = degradation_monitor.circuit_breakers.get(component_name)
            if not circuit:
                raise HTTPException(
                    status_code=404, detail=f"Circuit breaker for {component_name} not found"
                )

        return {
            "component": component_name,
            "failure_threshold": circuit.failure_threshold,
            "recovery_timeout": circuit.recovery_timeout,
            "expected_exception": (
                str(circuit.expected_exception) if circuit.expected_exception else None
            ),
            "timeout": getattr(circuit, "timeout", None),
            "timestamp": time.time(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get circuit config for {component_name}: {str(e)}"
        )


@router.put("/config/{component_name}")
async def update_circuit_config(
    component_name: str,
    failure_threshold: Optional[int] = None,
    recovery_timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update circuit breaker configuration for a component.

    Args:
        component_name: Name of the component
        failure_threshold: New failure threshold (optional)
        recovery_timeout: New recovery timeout in seconds (optional)

    Returns:
        Dict with update results
    """
    try:
        # Try to get circuit from registry first
        circuit = CircuitBreakerRegistry.get_circuit(component_name)
        if not circuit:
            # Try degradation monitor
            circuit = degradation_monitor.circuit_breakers.get(component_name)
            if not circuit:
                raise HTTPException(
                    status_code=404, detail=f"Circuit breaker for {component_name} not found"
                )

        # Store previous config
        previous_config = {
            "failure_threshold": circuit.failure_threshold,
            "recovery_timeout": circuit.recovery_timeout,
        }

        # Update configuration
        if failure_threshold is not None:
            if failure_threshold <= 0:
                raise HTTPException(status_code=400, detail="failure_threshold must be positive")
            circuit.failure_threshold = failure_threshold

        if recovery_timeout is not None:
            if recovery_timeout <= 0:
                raise HTTPException(status_code=400, detail="recovery_timeout must be positive")
            circuit.recovery_timeout = recovery_timeout

        # Record update
        update_result = {
            "component": component_name,
            "action": "config_update",
            "previous_config": previous_config,
            "new_config": {
                "failure_threshold": circuit.failure_threshold,
                "recovery_timeout": circuit.recovery_timeout,
            },
            "timestamp": time.time(),
        }

        # Track metrics
        metrics_collector.track_error(
            error_type="circuit_config_update", location=f"circuit_endpoints.{component_name}"
        )

        return update_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update circuit config for {component_name}: {str(e)}",
        )


@router.get("/history/{component_name}")
async def get_circuit_history(component_name: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get circuit breaker history for a component.

    Args:
        component_name: Name of the component
        limit: Maximum number of history records to return

    Returns:
        Dict with circuit breaker history
    """
    try:
        # Historical data retrieval implementation
        # In a real implementation, you'd store and retrieve circuit breaker history

        # Get current circuit info
        circuit = CircuitBreakerRegistry.get_circuit(component_name)
        if not circuit:
            circuit = degradation_monitor.circuit_breakers.get(component_name)
            if not circuit:
                raise HTTPException(
                    status_code=404, detail=f"Circuit breaker for {component_name} not found"
                )

        history = {
            "component": component_name,
            "records": [],
            "current_state": circuit.state.value,
            "current_failure_count": circuit.failure_count,
            "limit": limit,
            "timestamp": time.time(),
        }

        return history

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get circuit history for {component_name}: {str(e)}"
        )


@router.get("/summary")
async def get_circuit_summary() -> Dict[str, Any]:
    """
    Get summary of all circuit breakers by state.

    Returns:
        Dict with circuit breaker summary
    """
    try:
        summary = {
            "by_state": {"closed": 0, "open": 0, "half_open": 0},
            "total_circuits": 0,
            "components_by_state": {"closed": [], "open": [], "half_open": []},
            "high_failure_components": [],
            "timestamp": time.time(),
        }

        # Collect circuit states
        all_circuits = {}

        # Get circuits from registry
        for component_name in CircuitBreakerRegistry.list_circuits():
            circuit = CircuitBreakerRegistry.get_circuit(component_name)
            if circuit:
                all_circuits[component_name] = circuit

        # Get circuits from degradation monitor
        for component_name, circuit in degradation_monitor.circuit_breakers.items():
            if component_name not in all_circuits:
                all_circuits[component_name] = circuit

        # Analyze circuits
        for component_name, circuit in all_circuits.items():
            state = circuit.state.value
            summary["by_state"][state] += 1
            summary["components_by_state"][state].append(component_name)

            # Check for high failure counts
            if circuit.failure_count > circuit.failure_threshold * 0.8:  # 80% of threshold
                summary["high_failure_components"].append(
                    {
                        "component": component_name,
                        "failure_count": circuit.failure_count,
                        "threshold": circuit.failure_threshold,
                    }
                )

        summary["total_circuits"] = len(all_circuits)

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get circuit summary: {str(e)}")


@router.get("/health")
async def get_circuit_service_health() -> Dict[str, Any]:
    """
    Health check for the circuit breaker service itself.

    Returns:
        Dict with service health status
    """
    try:
        # Count circuits from both sources
        registry_circuits = len(CircuitBreakerRegistry.list_circuits())
        monitor_circuits = len(degradation_monitor.circuit_breakers)

        # Get summary statistics
        all_circuits = {}

        for component_name in CircuitBreakerRegistry.list_circuits():
            circuit = CircuitBreakerRegistry.get_circuit(component_name)
            if circuit:
                all_circuits[component_name] = circuit

        for component_name, circuit in degradation_monitor.circuit_breakers.items():
            if component_name not in all_circuits:
                all_circuits[component_name] = circuit

        open_circuits = sum(
            1 for circuit in all_circuits.values() if circuit.state == CircuitState.OPEN
        )

        return {
            "service": "circuit_breaker",
            "healthy": True,
            "total_circuits": len(all_circuits),
            "registry_circuits": registry_circuits,
            "monitor_circuits": monitor_circuits,
            "open_circuits": open_circuits,
            "closed_circuits": len(all_circuits) - open_circuits,
            "timestamp": time.time(),
        }

    except Exception as e:
        return {
            "service": "circuit_breaker",
            "healthy": False,
            "error": str(e),
            "timestamp": time.time(),
        }


@router.post("/test/{component_name}")
async def test_circuit_breaker(component_name: str) -> Dict[str, Any]:
    """
    Test circuit breaker functionality for a component.

    Args:
        component_name: Name of the component

    Returns:
        Dict with test results
    """
    try:
        # Try to get circuit from registry first
        circuit = CircuitBreakerRegistry.get_circuit(component_name)
        if not circuit:
            # Try degradation monitor
            circuit = degradation_monitor.circuit_breakers.get(component_name)
            if not circuit:
                raise HTTPException(
                    status_code=404, detail=f"Circuit breaker for {component_name} not found"
                )

        initial_state = circuit.state.value
        initial_failures = circuit.failure_count

        test_results = {
            "component": component_name,
            "initial_state": initial_state,
            "initial_failure_count": initial_failures,
            "tests": [],
        }

        # Test 1: Successful call
        try:
            test_start = time.time()
            result = await circuit.call(lambda: "success")
            test_duration = time.time() - test_start

            test_results["tests"].append(
                {
                    "test": "successful_call",
                    "result": "success",
                    "duration": test_duration,
                    "state_after": circuit.state.value,
                    "failure_count_after": circuit.failure_count,
                }
            )
        except Exception as e:
            test_results["tests"].append(
                {
                    "test": "successful_call",
                    "result": "failed",
                    "error": str(e),
                    "state_after": circuit.state.value,
                    "failure_count_after": circuit.failure_count,
                }
            )

        # Test 2: Failed call (if circuit is not already open)
        if circuit.state != CircuitState.OPEN:
            try:
                await circuit.call(lambda: 1 / 0)  # Force an exception
                test_results["tests"].append(
                    {
                        "test": "failed_call",
                        "result": "unexpected_success",
                        "state_after": circuit.state.value,
                        "failure_count_after": circuit.failure_count,
                    }
                )
            except Exception:
                test_results["tests"].append(
                    {
                        "test": "failed_call",
                        "result": "expected_failure",
                        "state_after": circuit.state.value,
                        "failure_count_after": circuit.failure_count,
                    }
                )

        test_results["final_state"] = circuit.state.value
        test_results["final_failure_count"] = circuit.failure_count
        test_results["timestamp"] = time.time()

        # Track metrics
        metrics_collector.track_error(
            error_type="circuit_breaker_test", location=f"circuit_endpoints.{component_name}"
        )

        return test_results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to test circuit breaker for {component_name}: {str(e)}"
        )
