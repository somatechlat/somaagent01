"""Capsule Instance Management Service.

Simple. Elegant. Complete.

Manages CapsuleInstance lifecycle - the running instances of Capsules.
A single Capsule definition can have multiple simultaneous running instances.

VIBE Compliance:
- Rule 82: Professional comments, zero AI slop
- Rule 84: No mocks - real Django ORM operations
- Rule 216: Django 5+ Backend Sovereignty
- Rule 245: Under 650 lines
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet
from prometheus_client import Counter, Gauge

from admin.core.models import Capsule, CapsuleInstance
from services.capsule_core import inject_capsule, verify_capsule

logger = logging.getLogger(__name__)


# =============================================================================
# METRICS
# =============================================================================

instance_operations = Counter(
    "capsule_instance_operations_total",
    "Capsule instance operations count",
    ["operation", "status"],
)

active_instances = Gauge(
    "capsule_instances_active",
    "Number of active capsule instances",
    ["tenant"],
)


# =============================================================================
# INSTANCE MANAGEMENT FUNCTIONS
# =============================================================================


def create_instance(
    capsule_id: UUID,
    session_id: str,
    initial_state: Optional[dict] = None,
) -> CapsuleInstance:
    """Create a new running instance of a Capsule.

    This allows multiple simultaneous instances of the same Capsule
    definition to run in different sessions.

    Args:
        capsule_id: UUID of the Capsule to instantiate
        session_id: Session ID this instance is bound to
        initial_state: Optional initial state dict

    Returns:
        The created CapsuleInstance

    Raises:
        ValueError: If capsule not found or not active
        RuntimeError: If capsule fails verification
    """
    try:
        capsule = Capsule.objects.get(id=capsule_id, status=Capsule.STATUS_ACTIVE)
    except Capsule.DoesNotExist:
        instance_operations.labels(operation="create", status="failure").inc()
        raise ValueError(f"Active capsule {capsule_id} not found")

    # Verify capsule integrity before creating instance
    if not verify_capsule(capsule):
        instance_operations.labels(operation="create", status="failure").inc()
        raise RuntimeError(f"Capsule {capsule.name} failed integrity verification")

    with transaction.atomic():
        instance = CapsuleInstance.objects.create(
            capsule=capsule,
            session_id=session_id,
            state=initial_state or {},
            status="running",
        )

    instance_operations.labels(operation="create", status="success").inc()
    active_instances.labels(tenant=capsule.tenant).inc()

    logger.info(
        "Created instance %s for capsule %s:%s (session=%s)",
        instance.id,
        capsule.name,
        capsule.version,
        session_id,
    )

    return instance


def get_instance(instance_id: UUID) -> CapsuleInstance:
    """Get a specific CapsuleInstance by ID.

    Args:
        instance_id: UUID of the instance

    Returns:
        The CapsuleInstance

    Raises:
        CapsuleInstance.DoesNotExist: If not found
    """
    return CapsuleInstance.objects.select_related("capsule").get(id=instance_id)


def get_instance_by_session(session_id: str) -> Optional[CapsuleInstance]:
    """Get the running instance for a session.

    Args:
        session_id: Session identifier

    Returns:
        The running CapsuleInstance or None
    """
    return CapsuleInstance.objects.select_related("capsule").filter(
        session_id=session_id, status="running"
    ).first()


def list_running_instances(capsule_id: UUID) -> QuerySet[CapsuleInstance]:
    """List all running instances of a specific Capsule.

    Args:
        capsule_id: UUID of the Capsule

    Returns:
        QuerySet of running CapsuleInstance records
    """
    return CapsuleInstance.objects.filter(capsule_id=capsule_id, status="running")


def list_all_running_instances(tenant: str) -> QuerySet[CapsuleInstance]:
    """List ALL running instances for a tenant.

    Args:
        tenant: Tenant identifier

    Returns:
        QuerySet of all running CapsuleInstance records for tenant
    """
    return CapsuleInstance.objects.select_related("capsule").filter(
        capsule__tenant=tenant, status="running"
    )


def count_running_instances(capsule_id: Optional[UUID] = None, tenant: Optional[str] = None) -> int:
    """Count running instances.

    Args:
        capsule_id: Optional specific capsule to count
        tenant: Optional tenant to count all instances for

    Returns:
        Count of running instances
    """
    qs = CapsuleInstance.objects.filter(status="running")

    if capsule_id:
        qs = qs.filter(capsule_id=capsule_id)
    elif tenant:
        qs = qs.filter(capsule__tenant=tenant)

    return qs.count()


def update_instance_state(instance_id: UUID, state: dict) -> CapsuleInstance:
    """Update the state of a running instance.

    Args:
        instance_id: UUID of the instance
        state: New state dict (replaces existing)

    Returns:
        Updated CapsuleInstance

    Raises:
        CapsuleInstance.DoesNotExist: If not found
        ValueError: If instance is not running
    """
    instance = CapsuleInstance.objects.get(id=instance_id)

    if instance.status != "running":
        raise ValueError(f"Cannot update state of {instance.status} instance")

    instance.state = state
    instance.save(update_fields=["state"])

    instance_operations.labels(operation="update_state", status="success").inc()

    return instance


def complete_instance(
    instance_id: UUID,
    final_state: Optional[dict] = None,
) -> CapsuleInstance:
    """Mark an instance as completed.

    Args:
        instance_id: UUID of the instance
        final_state: Optional final state to save

    Returns:
        Completed CapsuleInstance

    Raises:
        CapsuleInstance.DoesNotExist: If not found
    """
    instance = CapsuleInstance.objects.select_related("capsule").get(id=instance_id)

    if instance.status != "running":
        logger.warning("Instance %s already in status: %s", instance_id, instance.status)
        return instance

    with transaction.atomic():
        instance.status = "completed"
        instance.completed_at = datetime.now(timezone.utc)
        if final_state is not None:
            instance.state = final_state
        instance.save()

    instance_operations.labels(operation="complete", status="success").inc()
    active_instances.labels(tenant=instance.capsule.tenant).dec()

    logger.info(
        "Completed instance %s for capsule %s (duration=%s)",
        instance.id,
        instance.capsule.name,
        instance.completed_at - instance.started_at if instance.completed_at else "N/A",
    )

    return instance


def terminate_instance(
    instance_id: UUID,
    reason: str = "terminated",
) -> CapsuleInstance:
    """Forcefully terminate a running instance.

    Args:
        instance_id: UUID of the instance
        reason: Termination reason

    Returns:
        Terminated CapsuleInstance

    Raises:
        CapsuleInstance.DoesNotExist: If not found
    """
    instance = CapsuleInstance.objects.select_related("capsule").get(id=instance_id)

    if instance.status != "running":
        logger.warning("Instance %s already in status: %s", instance_id, instance.status)
        return instance

    with transaction.atomic():
        instance.status = "terminated"
        instance.completed_at = datetime.now(timezone.utc)
        instance.state["termination_reason"] = reason
        instance.save()

    instance_operations.labels(operation="terminate", status="success").inc()
    active_instances.labels(tenant=instance.capsule.tenant).dec()

    logger.info("Terminated instance %s: %s", instance.id, reason)

    return instance


def cleanup_stale_instances(max_age_hours: int = 24) -> int:
    """Clean up stale running instances.

    Instances running longer than max_age_hours are terminated.

    Args:
        max_age_hours: Maximum allowed running time in hours

    Returns:
        Number of instances terminated
    """
    from django.utils import timezone as dj_timezone
    from datetime import timedelta

    cutoff = dj_timezone.now() - timedelta(hours=max_age_hours)

    stale = CapsuleInstance.objects.filter(
        status="running", started_at__lt=cutoff
    )

    count = 0
    for instance in stale:
        try:
            terminate_instance(instance.id, reason=f"stale (>{max_age_hours}h)")
            count += 1
        except Exception as e:
            logger.error("Failed to terminate stale instance %s: %s", instance.id, e)

    if count > 0:
        logger.info("Cleaned up %d stale instances", count)

    return count


__all__ = [
    "create_instance",
    "get_instance",
    "get_instance_by_session",
    "list_running_instances",
    "list_all_running_instances",
    "count_running_instances",
    "update_instance_state",
    "complete_instance",
    "terminate_instance",
    "cleanup_stale_instances",
]
