"""Local identity — the credential record.

``LocalIdentity`` is who a person is when the agent holds the credential
itself: Standalone, per SOMA-01-DEPLOY-001 §4.1. Enterprise federates the
same person to an identity provider and never touches this table.

**It is an authentication record, not an authority record.** It says which
*roles* a person holds. It never says what those roles mean — that is
``admin.core.authz``, one catalog, identical in every deployment mode. A
role name this table has never heard of grants nothing.

What is deliberately absent:

* **No plaintext password, ever.** Only an argon2id PHC string, which is a
  verifier under a pepper held in Vault. A dump of this table without Vault
  is inert.
* **No MFA seeds, no recovery codes, no session tokens.** Those are secrets
  and they live in Vault (VIBE Rule 164). This table holds only their state
  and their hashes.
* **No permission field.** Authority is computed, never stored, so a stale
  row cannot carry a stale grant.

The credential rules themselves live in ``services.common.identity`` and are
pure functions. This model is storage plus the fail-closed glue.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from django.db import models
from django.utils import timezone

from services.common.identity.lockout import LockoutState
from services.common.identity.password import (
    check_password_policy,
    hash_password,
    verify_password,
)

__all__ = ["LocalIdentity"]


class LocalIdentity(models.Model):
    """A person who authenticates with a password the agent itself holds."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- Who ------------------------------------------------------------
    username = models.CharField(
        max_length=150, unique=True, help_text="Sign-in name. Compared case-insensitively."
    )
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=150, blank=True, default="")

    # --- Credential -----------------------------------------------------
    # Argon2id PHC string under the Vault-held pepper. A verifier, not a
    # credential: it cannot be turned back into a password, and without the
    # pepper it cannot even be matched.
    password_hash = models.CharField(max_length=255, blank=True, default="")
    password_changed_at = models.DateTimeField(null=True, blank=True)

    # --- Lockout ledger (mirrors services.common.identity.lockout) ------
    failure_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    hard_locked = models.BooleanField(default=False)

    # --- MFA state (the factors themselves live in Vault) ---------------
    mfa_required = models.BooleanField(default=False)
    mfa_enrolled = models.BooleanField(default=False)

    # --- Lifecycle ------------------------------------------------------
    is_active = models.BooleanField(
        default=True,
        help_text="False means this person cannot authenticate at all.",
    )
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    # --- Which roles this person holds. Authority is the catalog's. -----
    roles = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Role names this person holds. Every name is resolved through "
            "admin.core.authz; an unknown name grants nothing."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "aaas_local_identity"
        verbose_name = "Local Identity"
        verbose_name_plural = "Local Identities"
        ordering = ["username"]

    def __str__(self) -> str:
        return self.username

    # ------------------------------------------------------------------
    # Credential
    # ------------------------------------------------------------------

    def set_password(
        self,
        password: str,
        pepper: str,
        *,
        now: Optional[datetime] = None,
        **hash_params,
    ) -> None:
        """Hash and store a new password.

        Args:
            password: the candidate. Never retained, never echoed in an error.
            pepper: the HMAC key from Vault (VIBE Rule 164).
            now: the instant to record as the change time; defaults to now.
            **hash_params: forwarded to ``hash_password``. Tests use cheap
                parameters; production uses the policy defaults.

        Raises:
            PasswordPolicyError: if the candidate fails policy. Storing a
                password the product would refuse to accept is how weak
                credentials get written.
        """
        check_password_policy(
            password,
            username=self.username,
            email=self.email,
            privileged=bool(self.roles and set(self.roles) & _PRIVILEGED_ROLES),
        )
        self.password_hash = hash_password(password, pepper, **hash_params)
        self.password_changed_at = now or timezone.now()

    def verify_password(self, password: str, pepper: str) -> bool:
        """Check a presented password.

        FAIL-CLOSED on every path. A disabled identity, an identity with no
        password set, a wrong password and a hash made under another pepper
        are all False. This method never raises on a bad credential.
        """
        if not self.is_active:
            return False
        if not self.password_hash:
            return False
        return verify_password(password, self.password_hash, pepper)

    # ------------------------------------------------------------------
    # Lockout ledger
    # ------------------------------------------------------------------

    def to_lockout_state(self) -> LockoutState:
        """Project the stored ledger into the pure rules' state."""
        return LockoutState(
            failure_count=self.failure_count,
            locked_until=self.locked_until,
            hard_locked=self.hard_locked,
        )

    def apply_lockout_state(self, state: LockoutState) -> None:
        """Write a pure-rules state back onto the row."""
        self.failure_count = state.failure_count
        self.locked_until = state.locked_until
        self.hard_locked = state.hard_locked


#: Roles whose holder is granted more than ordinary use, so they are held to
#: the longer password minimum. Mirrors the assignment lists in
#: ``admin.core.authz``: anyone provisioned with, or assignable to, a role
#: that can change who holds what.
_PRIVILEGED_ROLES = frozenset(
    {"sysadmin", "org_admin", "agent_owner", "agent_operator"}
)
