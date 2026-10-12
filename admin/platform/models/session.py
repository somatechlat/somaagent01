"""Local identity — the session store.

A session is what a person holds after they have authenticated: an opaque
bearer that carries no claims of its own and means nothing except "this
principal, this window". Standalone issues them from the local credential
path (SOMA-01-DEPLOY-001 §4.1); Enterprise federates instead and does not
touch this table.

**The raw token exists exactly once, at issuance.** ``build`` mints it,
returns it to the caller, and stores only its SHA-256. The digest is a
lookup key, not a verifier: it is over 256 bits of CSPRNG output, so a
fast hash is correct here and argon2 would only add latency to every
request. A dump of this table is a list of unusable digests.

**Revocation is the first thing checked and it is permanent.** Whether a
session is live is ``services.common.identity.session.session_decision``
— revocation, then idle, then absolute. This model holds state and
delegates; it is not a second opinion. A write to ``last_seen_at`` cannot
resurrect a revoked session because revocation is checked first and wins.

No credential ever sits on this object: no token, no password, no secret,
no cookie. Only a digest and two clocks.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Tuple

from django.db import models
from django.utils import timezone

from services.common.identity.session import (
    SessionDecision,
    SessionRecord,
    generate_session_token,
    session_decision,
)

__all__ = ["LocalSession"]


class LocalSession(models.Model):
    """One live login for one principal."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- The lookup key. Never the token itself. -----------------------
    # SHA-256 hex of the raw bearer. Deterministic so it can be indexed and
    # matched in one query; one-way so the stored form cannot be replayed.
    token_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA-256 hex of the session token. The token itself is never stored.",
    )

    # --- Who ----------------------------------------------------------
    # A character key, not a foreign key: Enterprise principals carry an
    # opaque identity-provider subject, and a UUID column would reject it.
    principal_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Who this session belongs to. A local identity id or an IdP subject.",
    )

    # --- The two clocks -----------------------------------------------
    created_at = models.DateTimeField(help_text="When the session began. Starts the absolute window.")
    last_seen_at = models.DateTimeField(help_text="When the session was last used. Starts the idle window.")

    # --- Lifecycle ----------------------------------------------------
    revoked = models.BooleanField(
        default=False,
        help_text="Revocation is checked first and is permanent.",
    )
    revoked_at = models.DateTimeField(null=True, blank=True)

    privileged = models.BooleanField(
        default=False,
        help_text=(
            "True for a session whose holder has privileged roles. Carries the "
            "shorter idle and absolute windows."
        ),
    )

    class Meta:
        db_table = "aaas_local_session"
        verbose_name = "Local Session"
        verbose_name_plural = "Local Sessions"
        ordering = ["-created_at"]
        # Names are explicit and match 0004_local_session exactly. Leaving
        # them unnamed makes Django synthesise truncated names on every
        # model load, and the autodetector then reports a rename between the
        # model and the migration — a deploy-time schema change nobody asked
        # for. One name, declared in both places, cannot drift.
        indexes = [
            models.Index(
                fields=["principal_id", "-created_at"],
                name="aaas_local_sess_prin_idx",
            ),
            models.Index(fields=["token_hash"], name="aaas_local_sess_tok_idx"),
        ]

    def __str__(self) -> str:
        """Identify the session without describing it.

        Deliberately prints no digest and no token: a log line that names a
        session must not be a way to obtain one.
        """
        return f"session for {self.principal_id}"

    # ------------------------------------------------------------------
    # Issuance
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        principal_id: str,
        *,
        privileged: bool = False,
        now: Optional[datetime] = None,
    ) -> Tuple[str, "LocalSession"]:
        """Mint a session and return it with its one and only raw token.

        This is the only place a session token exists in the clear. The raw
        is returned to the caller to hand to the person; the row keeps the
        digest. The caller persists — keeping the write and the commit in
        one place is what lets the caller also write the audit entry
        atomically.

        Args:
            principal_id: who the session is for.
            privileged: whether the holder has privileged roles, which
                selects the shorter timeout windows.
            now: the instant the session begins; defaults to now.

        Returns:
            ``(raw_token, record)``. The raw is not recoverable afterwards.
        """
        raw, token_hash = generate_session_token()
        instant = now or timezone.now()
        return raw, cls(
            token_hash=token_hash,
            principal_id=principal_id,
            created_at=instant,
            last_seen_at=instant,
            revoked=False,
            revoked_at=None,
            privileged=privileged,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def mark_revoked(self, *, now: Optional[datetime] = None) -> None:
        """Revoke this session. Idempotent and permanent.

        A second call does not move ``revoked_at``: an audit trail showing
        two kill times for one session is worse than one showing one. The
        caller persists.
        """
        if self.revoked:
            return
        self.revoked = True
        self.revoked_at = now or timezone.now()

    # ------------------------------------------------------------------
    # Delegation to the pure rules
    # ------------------------------------------------------------------

    def to_session_record(self) -> SessionRecord:
        """Project the row into the pure rules' record, field for field."""
        return SessionRecord(
            token_hash=self.token_hash,
            principal_id=self.principal_id,
            created_at=self.created_at,
            last_seen_at=self.last_seen_at,
            revoked=self.revoked,
            privileged=self.privileged,
        )

    def decision(self, *, now: datetime) -> SessionDecision:
        """Ask the pure rules whether this session is live.

        The model holds state and delegates. Whether a session is valid is
        decided in exactly one place.
        """
        return session_decision(self.to_session_record(), now=now)

    def is_valid(self, *, now: datetime) -> bool:
        """Whether this session may be used at ``now``."""
        return self.decision(now=now).valid
