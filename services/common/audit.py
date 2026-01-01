"""
Audit wire-tap publisher for policy/tool/task decisions.

VIBE COMPLIANT - Real Kafka integration, no mocks.
Per login-to-chat-journey design.md Section 9.1

Extended with:
- Structured login/logout events
- Permission denied events
- Session events
"""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.common.messaging_utils import build_headers, idempotency_key
from services.common.publisher import DurablePublisher

logger = logging.getLogger(__name__)


# =============================================================================
# AUDIT EVENT SCHEMAS
# =============================================================================


@dataclass
class AuditEvent:
    """Base audit event structure.

    Per design.md Section 9.1:
    - event_type: Type of event
    - timestamp: ISO8601 timestamp
    - user_id: User ID (if authenticated)
    - tenant_id: Tenant ID (if available)
    - ip_address: Client IP
    - user_agent: Client user agent
    - metadata: Additional event-specific data
    """

    event_type: str
    timestamp: str
    user_id: Optional[str]
    tenant_id: Optional[str]
    ip_address: str
    user_agent: str
    metadata: dict

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LoginAuditEvent(AuditEvent):
    """Login attempt audit event.

    Per design.md Property 11:
    - email: User email
    - method: Auth method (password, oauth, sso)
    - result: success, failure, locked, mfa_required
    - failure_reason: Reason for failure (if applicable)
    - mfa_used: Whether MFA was used
    """

    email: str = ""
    method: str = "password"
    result: str = "success"
    failure_reason: Optional[str] = None
    mfa_used: bool = False

    def __post_init__(self):
        super().__post_init__()
        self.event_type = "auth.login"


@dataclass
class LogoutAuditEvent(AuditEvent):
    """Logout audit event.

    Per design.md Section 9.1:
    - reason: Reason for logout (user_initiated, session_expired, forced)
    - session_id: Session that was terminated
    """

    reason: str = "user_initiated"
    session_id: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.event_type = "auth.logout"


@dataclass
class SessionAuditEvent(AuditEvent):
    """Session lifecycle audit event.

    Per design.md Section 9.1:
    - action: created, extended, expired, deleted
    - session_id: Session ID
    - permissions: Permissions granted (for created)
    """

    action: str = "created"
    session_id: str = ""
    permissions: list = None

    def __post_init__(self):
        super().__post_init__()
        self.event_type = "auth.session"
        if self.permissions is None:
            self.permissions = []


@dataclass
class PermissionDeniedAuditEvent(AuditEvent):
    """Permission denied audit event.

    Per design.md Section 9.1:
    - resource_type: Type of resource (agent, conversation, etc.)
    - resource_id: Resource ID
    - permission: Permission that was denied
    - endpoint: API endpoint
    """

    resource_type: str = ""
    resource_id: str = ""
    permission: str = ""
    endpoint: str = ""

    def __post_init__(self):
        super().__post_init__()
        self.event_type = "auth.permission_denied"


# =============================================================================
# AUDIT PUBLISHER
# =============================================================================


class AuditPublisher:
    def __init__(self, publisher: DurablePublisher, topic: Optional[str] = None) -> None:
        self.publisher = publisher
        self.topic = topic or os.environ.get("AUDIT_TOPIC", "audit.events")

    async def publish(
        self,
        event: Dict[str, Any],
        *,
        tenant: Optional[str] = None,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        correlation: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = build_headers(
            tenant=tenant,
            session_id=session_id,
            persona_id=persona_id,
            event_type=event.get("type"),
            event_id=event.get("event_id"),
            schema=event.get("version") or event.get("schema"),
            correlation=correlation or event.get("correlation_id"),
        )
        return await self.publisher.publish(
            self.topic,
            {**event, "correlation_id": headers["correlation_id"]},
            headers=headers,
            dedupe_key=idempotency_key(event, seed=correlation),
            session_id=session_id,
            tenant=tenant,
        )

    # =========================================================================
    # STRUCTURED AUTH EVENTS
    # =========================================================================

    async def log_login(
        self,
        email: str,
        user_id: Optional[str],
        tenant_id: Optional[str],
        method: str,
        result: str,
        failure_reason: Optional[str],
        ip_address: str,
        user_agent: str,
        mfa_used: bool = False,
    ) -> None:
        """Log login attempt.

        Per design.md Property 11:
        All required fields must be present.
        """
        event = LoginAuditEvent(
            event_type="auth.login",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={},
            email=email,
            method=method,
            result=result,
            failure_reason=failure_reason,
            mfa_used=mfa_used,
        )

        try:
            await self.publish(
                event.to_dict(),
                tenant=tenant_id,
            )
            logger.info(
                f"Audit: login {result}",
                extra={
                    "email": email,
                    "method": method,
                    "result": result,
                    "ip": ip_address,
                },
            )
        except Exception as e:
            # Non-critical - log locally and continue
            logger.warning(f"Audit publish failed (login): {e}")
            await self._store_locally(event)

    async def log_logout(
        self,
        user_id: str,
        tenant_id: Optional[str],
        reason: str,
        session_id: Optional[str],
        ip_address: str,
        user_agent: str,
    ) -> None:
        """Log logout event."""
        event = LogoutAuditEvent(
            event_type="auth.logout",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={},
            reason=reason,
            session_id=session_id,
        )

        try:
            await self.publish(
                event.to_dict(),
                tenant=tenant_id,
                session_id=session_id,
            )
            logger.info(f"Audit: logout user_id={user_id}", extra={"user_id": user_id, "reason": reason})
        except Exception as e:
            logger.warning(f"Audit publish failed (logout): {e}")
            await self._store_locally(event)

    async def log_session(
        self,
        user_id: str,
        tenant_id: Optional[str],
        action: str,
        session_id: str,
        permissions: list,
        ip_address: str,
        user_agent: str,
    ) -> None:
        """Log session lifecycle event."""
        event = SessionAuditEvent(
            event_type="auth.session",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={},
            action=action,
            session_id=session_id,
            permissions=permissions,
        )

        try:
            await self.publish(
                event.to_dict(),
                tenant=tenant_id,
                session_id=session_id,
            )
            logger.info(
                f"Audit: session {action}",
                extra={"user_id": user_id, "session_id": session_id},
            )
        except Exception as e:
            logger.warning(f"Audit publish failed (session): {e}")
            await self._store_locally(event)

    async def log_permission_denied(
        self,
        user_id: str,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        permission: str,
        endpoint: str,
        ip_address: str,
        user_agent: str = "",
    ) -> None:
        """Log permission denied event."""
        event = PermissionDeniedAuditEvent(
            event_type="auth.permission_denied",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={},
            resource_type=resource_type,
            resource_id=resource_id,
            permission=permission,
            endpoint=endpoint,
        )

        try:
            await self.publish(
                event.to_dict(),
                tenant=tenant_id,
            )
            logger.warning(
                f"Audit: permission denied user={user_id} resource={resource_type}:{resource_id}",
                extra={
                    "user_id": user_id,
                    "resource": f"{resource_type}:{resource_id}",
                    "permission": permission,
                },
            )
        except Exception as e:
            logger.warning(f"Audit publish failed (permission_denied): {e}")
            await self._store_locally(event)

    async def _store_locally(self, event: AuditEvent) -> None:
        """Store event in PostgreSQL as fallback when Kafka unavailable.

        Per design.md Section 9.1:
        - Fallback to local DB when Kafka unavailable
        """
        from asgiref.sync import sync_to_async

        try:
            from admin.core.models import AuditLog

            @sync_to_async
            def store():
                AuditLog.objects.create(
                    tenant=event.tenant_id or "",
                    user_id=event.user_id,
                    action=event.event_type,
                    resource_type="auth",
                    resource_id=None,
                    new_value=event.to_dict(),
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                )

            await store()
            logger.debug(f"Audit event stored locally: {event.event_type}")

        except Exception as e:
            # Last resort - just log
            logger.error(f"Failed to store audit event locally: {e}")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_audit_publisher_instance: Optional[AuditPublisher] = None


async def get_audit_publisher() -> Optional[AuditPublisher]:
    """Get or create the singleton AuditPublisher.

    Returns None if publisher not configured (no Kafka).
    """
    global _audit_publisher_instance
    if _audit_publisher_instance is None:
        try:
            from services.common.publisher import get_durable_publisher

            publisher = await get_durable_publisher()
            if publisher:
                _audit_publisher_instance = AuditPublisher(publisher)
        except Exception as e:
            logger.warning(f"AuditPublisher not available: {e}")
            return None
    return _audit_publisher_instance
