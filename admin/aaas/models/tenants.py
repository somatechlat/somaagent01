"""Tenant and TenantUser models.

``Tenant`` is the **data-partition boundary**: every child resource carries
``tenant_id`` so one organisation's memories, agents and audit rows cannot be
read by another. That isolation is a security property and it stays.

It is not a product tenancy. There is no subscription tier, no billing
contact, no trial clock and no churn lifecycle: SomaBrain and the agent are
HTTP + containers, not a commercial offering.

``TenantUser`` is **the one role store**. Every question of the form "which
roles does this principal hold" is answered here and nowhere else — not on a
``LocalIdentity`` JSON field, not in a ``PlatformConfig`` defaults blob, not
in a settings endpoint. What those roles *mean* is
``admin.core.authz.ROLE_PERMISSIONS``; SpiceDB may only narrow what the two
of them together allow. ``TenantUser.roles_for`` is the single resolver, and
it is cached with a hard bound because this is consulted on every request.
"""

import uuid
from collections import OrderedDict
from typing import TYPE_CHECKING, List, Optional

from django.db import models

from admin.aaas.models.choices import TenantRole, TenantStatus

if TYPE_CHECKING:
    from django.db.models import Manager

    from admin.aaas.models.agents import Agent


#: Bounded memo of ``TenantUser.roles_for``. Key is ``(user_id, tenant_id)``.
#: An ``OrderedDict`` is used as a strict LRU: ``move_to_end`` on hit,
#: ``popitem(last=False)`` on overflow. The bound is a named setting — see
#: ``_role_cache_bound`` — never a literal in this module.
_ROLE_CACHE: "OrderedDict[tuple, list]" = OrderedDict()


def _role_cache_bound() -> Optional[int]:
    """How many principals may be memoised at once.

    A named setting (``role_cache_max_entries``), resolved through the real
    settings chain. There is no code-level default: a cache that must be
    bounded cannot be bounded by a number nobody chose.

    Absent means **do not memoise**. The cache is a latency optimisation on
    top of the one store, never an authority — so a missing bound degrades to
    a store read per lookup rather than inventing a size or refusing the
    request. A *present but unusable* value is a configuration error and
    raises, because silently widening a bound (or silently ignoring it) is
    how an unbounded dict reappears.
    """
    from admin.core.helpers.settings import get_settings

    value = getattr(get_settings(), "role_cache_max_entries", None)
    if value is None:
        return None
    try:
        bound = int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"role_cache_max_entries={value!r} is not an integer; refusing to "
            "guess a cache bound."
        ) from exc
    if bound < 1:
        raise RuntimeError(
            f"role_cache_max_entries={bound} must be at least 1; a zero-bound "
            "cache is not a cache and a negative one is a bug."
        )
    return bound


class Tenant(models.Model):
    """Organisation boundary. One row per partition.

    ``id`` is the partition key referenced as ``tenant_id`` across agents,
    capsules, bridges and audit rows.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, help_text="Organisation name")

    slug = models.SlugField(max_length=100, unique=True, help_text="URL-safe identifier for tenant")

    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.ACTIVE,
        db_index=True,
    )

    # Identity-provider realm for this partition's principals.
    keycloak_realm = models.CharField(
        max_length=100, blank=True, help_text="Keycloak realm for this tenant"
    )

    # Per-partition behaviour knobs. Any ceiling that used to live on a plan
    # row is a deployment setting (Django settings), not a tenant column.
    feature_overrides = models.JSONField(
        default=dict, blank=True, help_text="Per-tenant feature configuration overrides"
    )

    metadata = models.JSONField(
        default=dict, blank=True, help_text="Arbitrary metadata for integrations"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    if TYPE_CHECKING:
        agents: Manager["Agent"]
        users: Manager["TenantUser"]

    class Meta:
        """Meta class implementation."""

        db_table = "tenants"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self):
        """Return string representation."""

        return f"{self.name} ({self.status})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "status": self.status,
            "keycloak_realm": self.keycloak_realm,
            "feature_overrides": self.feature_overrides,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TenantUser(models.Model):
    """Org role assignment: which principal holds which catalog role.

    This row is what RBAC reads. It is not a seat, not an invitation and not
    a product membership.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users")

    user_id = models.UUIDField(db_index=True, help_text="Principal ID in the identity provider")

    email = models.EmailField(help_text="User email")

    display_name = models.CharField(max_length=200, blank=True, help_text="User display name")

    role = models.CharField(max_length=20, choices=TenantRole.choices, default=TenantRole.MEMBER)

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "tenant_users"
        ordering = ["-created_at"]
        unique_together = [["tenant", "user_id"]]
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Tenant User"
        verbose_name_plural = "Tenant Users"

    def __str__(self):
        """Return string representation."""

        return f"{self.email} ({self.role} in {self.tenant.name})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),  # type: ignore[reportAttributeAccessIssue]
            "user_id": str(self.user_id),
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }

    # ------------------------------------------------------------------
    # THE ONE ROLE RESOLVER
    # ------------------------------------------------------------------

    @classmethod
    def roles_for(
        cls,
        user_id,
        tenant_id: Optional[str] = None,
    ) -> List[str]:
        """The roles ``user_id`` holds, from the one store.

        This is the only place that answers "which roles does this principal
        hold". Every other surface — the gate, the permission matrix, local
        login, session decode — calls this and never opens a second question.

        FAIL-CLOSED: a principal with no active membership row holds nothing.
        A missing row is not a default grant and never becomes one.

        The answer is memoised in a bounded LRU. Unbounded caches are how a
        process doing millions of authorisation decisions grows without limit;
        the bound is a named setting (``role_cache_max_entries``), not a
        literal, and eviction is strict LRU so a hot principal stays warm and
        a cold one cannot pin memory.

        Args:
            user_id: The principal. A missing id holds nothing.
            tenant_id: Optional partition. When given, only membership in
                that partition counts — authority granted inside one
                organisation does not extend to another.

        Returns:
            Role names, in no particular order. Empty means "holds nothing".
        """
        if not user_id:
            return []

        bound = _role_cache_bound()
        key = (str(user_id), str(tenant_id) if tenant_id is not None else None)
        if bound is not None:
            cached = _ROLE_CACHE.get(key)
            if cached is not None:
                _ROLE_CACHE.move_to_end(key)
                return list(cached)

        qs = cls.objects.filter(user_id=user_id, is_active=True)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        roles = list(qs.values_list("role", flat=True))

        if bound is not None:
            _ROLE_CACHE[key] = roles
            _ROLE_CACHE.move_to_end(key)
            while len(_ROLE_CACHE) > bound:
                _ROLE_CACHE.popitem(last=False)
        return list(roles)

    @classmethod
    def invalidate_role_cache(cls, user_id=None) -> None:
        """Drop memoised roles after a membership write.

        Called from ``save``/``delete`` so a grant taken away cannot survive
        inside a live cache entry. Without this the cache is a second store.
        """
        if user_id is None:
            _ROLE_CACHE.clear()
            return
        prefix = (str(user_id),)
        for key in [k for k in _ROLE_CACHE if k[0] == prefix[0]]:
            del _ROLE_CACHE[key]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invalidate_role_cache(self.user_id)

    def delete(self, *args, **kwargs):
        user_id = self.user_id
        super().delete(*args, **kwargs)
        self.invalidate_role_cache(user_id)
