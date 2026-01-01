"""SpiceDB client wrapper for fine-grained authorization.

VIBE COMPLIANT - Real gRPC integration with SpiceDB, no mocks.
Per login-to-chat-journey design.md Section 5.1

Implements:
- check_permission(user_id, permission, resource_type, resource_id)
- get_permissions(user_id, tenant_id) for session caching
- lookup_resources(user_id, resource_type, permission) for agent list

Personas:
- Security Auditor: Fail-closed authorization, audit logging
- Django Architect: Async gRPC integration
- Performance Engineer: Connection pooling, caching
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

SPICEDB_REQUESTS = Counter(
    "spicedb_requests_total",
    "Total SpiceDB requests",
    ["method", "result"],
)

SPICEDB_LATENCY = Histogram(
    "spicedb_request_duration_seconds",
    "SpiceDB request latency",
    ["method"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class PermissionCheck:
    """Result of a permission check."""

    has_permission: bool
    resource_type: str
    resource_id: str
    permission: str
    user_id: str
    checked_at: str


@dataclass
class ResourceLookup:
    """Result of a resource lookup."""

    resource_type: str
    permission: str
    resource_ids: list[str]
    user_id: str


# =============================================================================
# SPICEDB CLIENT
# =============================================================================


class SpiceDBClient:
    """SpiceDB client for fine-grained authorization.

    Per design.md Section 5.1:
    - Fail-closed: If SpiceDB unavailable, deny all
    - Connection pooling for performance
    - Async gRPC operations
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        token: Optional[str] = None,
        insecure: bool = False,
    ):
        """Initialize SpiceDB client.

        Args:
            host: SpiceDB host. Defaults to SPICEDB_HOST env var.
            port: SpiceDB port. Defaults to SPICEDB_PORT env var.
            token: Pre-shared key. Defaults to SPICEDB_TOKEN env var.
            insecure: Use insecure connection (dev only).
        """
        self.host = host or os.getenv("SPICEDB_HOST", "localhost")
        self.port = port or int(os.getenv("SPICEDB_PORT", "50051"))
        self.token = token or os.getenv("SPICEDB_TOKEN", "")
        self.insecure = insecure or os.getenv("SPICEDB_INSECURE", "false").lower() == "true"

        self._channel = None
        self._stub = None
        self._connected = False

    async def connect(self) -> None:
        """Establish gRPC connection to SpiceDB."""
        import grpc.aio

        try:
            # Import SpiceDB protobuf stubs
            from authzed.api.v1 import (
                permission_service_pb2_grpc as ps_grpc,
            )

            target = f"{self.host}:{self.port}"

            if self.insecure:
                self._channel = grpc.aio.insecure_channel(target)
            else:
                # Use secure channel with token auth
                credentials = grpc.ssl_channel_credentials()
                call_credentials = grpc.access_token_call_credentials(self.token)
                composite_credentials = grpc.composite_channel_credentials(
                    credentials, call_credentials
                )
                self._channel = grpc.aio.secure_channel(target, composite_credentials)

            self._stub = ps_grpc.PermissionsServiceStub(self._channel)
            self._connected = True

            logger.info(f"SpiceDB connected: {target}")

        except ImportError:
            logger.warning(
                "SpiceDB protobuf stubs not installed. "
                "Install with: pip install authzed"
            )
            raise
        except Exception as e:
            logger.error(f"SpiceDB connection failed: {e}")
            raise

    async def close(self) -> None:
        """Close gRPC connection."""
        if self._channel:
            await self._channel.close()
            self._connected = False

    async def _ensure_connected(self) -> None:
        """Ensure gRPC connection is established."""
        if not self._connected:
            await self.connect()

    async def check_permission(
        self,
        user_id: str,
        permission: str,
        resource_type: str,
        resource_id: str,
    ) -> bool:
        """Check if user has permission on resource.

        Per design.md Section 5.1:
        - Fail-closed: Returns False on any error
        - Logs all permission checks for audit

        Args:
            user_id: User ID (subject)
            permission: Permission to check (e.g., "view", "configure")
            resource_type: Resource type (e.g., "agent", "tenant")
            resource_id: Resource ID

        Returns:
            True if user has permission, False otherwise
        """
        import time
        from datetime import datetime, timezone

        start_time = time.perf_counter()

        try:
            await self._ensure_connected()

            from authzed.api.v1 import (
                CheckPermissionRequest,
                ObjectReference,
                SubjectReference,
            )

            request = CheckPermissionRequest(
                resource=ObjectReference(
                    object_type=resource_type,
                    object_id=resource_id,
                ),
                permission=permission,
                subject=SubjectReference(
                    object=ObjectReference(
                        object_type="user",
                        object_id=user_id,
                    ),
                ),
            )

            response = await self._stub.CheckPermission(request)

            # PERMISSIONSHIP_HAS_PERMISSION = 2
            has_permission = response.permissionship == 2

            elapsed = time.perf_counter() - start_time
            SPICEDB_LATENCY.labels(method="check_permission").observe(elapsed)
            SPICEDB_REQUESTS.labels(
                method="check_permission",
                result="granted" if has_permission else "denied",
            ).inc()

            logger.debug(
                f"Permission check: user={user_id}, permission={permission}, "
                f"resource={resource_type}:{resource_id}, result={has_permission}"
            )

            return has_permission

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            SPICEDB_LATENCY.labels(method="check_permission").observe(elapsed)
            SPICEDB_REQUESTS.labels(method="check_permission", result="error").inc()

            # FAIL-CLOSED: Deny on error
            logger.error(
                f"SpiceDB check_permission failed (FAIL-CLOSED): {e}, "
                f"user={user_id}, permission={permission}, "
                f"resource={resource_type}:{resource_id}"
            )
            return False

    async def get_permissions(
        self,
        user_id: str,
        tenant_id: str,
    ) -> list[str]:
        """Get all permissions for user in tenant.

        Per design.md Section 5.1:
        - Used for session caching
        - Returns list of permission strings

        Args:
            user_id: User ID
            tenant_id: Tenant ID

        Returns:
            List of permission strings (e.g., ["view", "configure", "manage"])
        """
        import time

        start_time = time.perf_counter()

        # Define all possible permissions to check
        all_permissions = [
            "view",
            "use",
            "develop",
            "train",
            "administrate",
            "manage",
        ]

        granted_permissions = []

        try:
            await self._ensure_connected()

            from authzed.api.v1 import (
                CheckPermissionRequest,
                ObjectReference,
                SubjectReference,
            )

            # Check each permission
            for permission in all_permissions:
                request = CheckPermissionRequest(
                    resource=ObjectReference(
                        object_type="tenant",
                        object_id=tenant_id,
                    ),
                    permission=permission,
                    subject=SubjectReference(
                        object=ObjectReference(
                            object_type="user",
                            object_id=user_id,
                        ),
                    ),
                )

                try:
                    response = await self._stub.CheckPermission(request)
                    if response.permissionship == 2:  # HAS_PERMISSION
                        granted_permissions.append(permission)
                except Exception:
                    # Skip this permission on error
                    pass

            elapsed = time.perf_counter() - start_time
            SPICEDB_LATENCY.labels(method="get_permissions").observe(elapsed)
            SPICEDB_REQUESTS.labels(method="get_permissions", result="success").inc()

            logger.debug(
                f"Permissions retrieved: user={user_id}, tenant={tenant_id}, "
                f"permissions={granted_permissions}"
            )

            return granted_permissions

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            SPICEDB_LATENCY.labels(method="get_permissions").observe(elapsed)
            SPICEDB_REQUESTS.labels(method="get_permissions", result="error").inc()

            logger.error(f"SpiceDB get_permissions failed: {e}")
            return []

    async def lookup_resources(
        self,
        user_id: str,
        resource_type: str,
        permission: str,
    ) -> list[str]:
        """Lookup all resources user has permission on.

        Per design.md Section 5.1:
        - Used for agent list filtering
        - Returns list of resource IDs

        Args:
            user_id: User ID
            resource_type: Resource type (e.g., "agent")
            permission: Permission to check (e.g., "view")

        Returns:
            List of resource IDs user has permission on
        """
        import time

        start_time = time.perf_counter()

        try:
            await self._ensure_connected()

            from authzed.api.v1 import (
                LookupResourcesRequest,
                ObjectReference,
                SubjectReference,
            )

            request = LookupResourcesRequest(
                resource_object_type=resource_type,
                permission=permission,
                subject=SubjectReference(
                    object=ObjectReference(
                        object_type="user",
                        object_id=user_id,
                    ),
                ),
            )

            resource_ids = []

            # Stream response
            async for response in self._stub.LookupResources(request):
                resource_ids.append(response.resource_object_id)

            elapsed = time.perf_counter() - start_time
            SPICEDB_LATENCY.labels(method="lookup_resources").observe(elapsed)
            SPICEDB_REQUESTS.labels(method="lookup_resources", result="success").inc()

            logger.debug(
                f"Resources lookup: user={user_id}, type={resource_type}, "
                f"permission={permission}, count={len(resource_ids)}"
            )

            return resource_ids

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            SPICEDB_LATENCY.labels(method="lookup_resources").observe(elapsed)
            SPICEDB_REQUESTS.labels(method="lookup_resources", result="error").inc()

            logger.error(f"SpiceDB lookup_resources failed: {e}")
            return []


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_spicedb_client_instance: Optional[SpiceDBClient] = None


async def get_spicedb_client() -> SpiceDBClient:
    """Get or create the singleton SpiceDB client.

    Usage:
        client = await get_spicedb_client()
        has_perm = await client.check_permission(user_id, "view", "agent", agent_id)
    """
    global _spicedb_client_instance
    if _spicedb_client_instance is None:
        _spicedb_client_instance = SpiceDBClient()
        await _spicedb_client_instance.connect()
    return _spicedb_client_instance


__all__ = [
    "SpiceDBClient",
    "PermissionCheck",
    "ResourceLookup",
    "get_spicedb_client",
]
