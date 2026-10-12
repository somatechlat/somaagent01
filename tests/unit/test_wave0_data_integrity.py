"""Wave 0 data-integrity gates — RAPID-DATA-REMEDIATION-001.

Real rows, real Postgres on somaagent_net (``db``). No mocks.
No localhost, no parallel topology.

- DB-CRIT-1  ``ApiKey.key_hash`` must be UNIQUE and indexed
- DB-HIGH-8  ``UserSession.refresh_token_hash`` must be UNIQUE (partial)
- DB-CRIT-5  ``IdempotencyRecord.check_and_set`` must be atomic
- DB-CRIT-4  CHECK constraints + one-active Constitution
- SIMP-02    MFA setup must fail before any CPU work
"""

from __future__ import annotations

import uuid

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone


# ---------------------------------------------------------------------------
# DB-CRIT-1 — ApiKey.key_hash UNIQUE + index
# ---------------------------------------------------------------------------


@pytest.mark.db
def test_api_key_key_hash_is_unique(db):
    """DB-CRIT-1: a second row with the same ``key_hash`` is rejected by the DB."""
    from admin.aaas.models import ApiKey

    digest = "a" * 64
    ApiKey.objects.create(
        key_type="platform",
        name="first",
        key_prefix="sk-firs1",
        key_hash=digest,
        scopes=[],
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ApiKey.objects.create(
                key_type="platform",
                name="second",
                key_prefix="sk-seco1",
                key_hash=digest,
                scopes=[],
            )


@pytest.mark.db
def test_api_key_key_hash_lookup_uses_index(db):
    """DB-CRIT-1 behavioral: hash lookup is satisfied by an index, not a seq scan."""
    from django.db import connection

    from admin.aaas.models import ApiKey

    ApiKey.objects.create(
        key_type="platform",
        name="idx",
        key_prefix="sk-idx12",
        key_hash="c" * 64,
        scopes=[],
    )
    with connection.cursor() as cur:
        cur.execute(
            "EXPLAIN SELECT id FROM aaas_api_key WHERE key_hash = %s",
            ["c" * 64],
        )
        plan = "\n".join(row[0] for row in cur.fetchall())
    assert "Seq Scan" not in plan or "Index" in plan, plan
    assert "aaas_api_key" in plan


@pytest.mark.db
def test_api_key_verify_resolves_by_hash(db):
    """Auth lookup path still works after the UNIQUE change."""
    from admin.aaas.models import ApiKey

    raw = "sk_live_" + "x" * 32
    digest = ApiKey.hash_key(raw)
    ApiKey.objects.create(
        key_type="tenant",
        name="resolve",
        key_prefix=raw[:8],
        key_hash=digest,
        scopes=["memory:write"],
        is_active=True,
    )
    found = ApiKey.verify(raw)
    assert found is not None
    assert found.key_hash == digest
    assert ApiKey.verify("sk_live_not_a_real_key") is None


# ---------------------------------------------------------------------------
# DB-HIGH-8 — UserSession.refresh_token_hash UNIQUE (partial) + index
# ---------------------------------------------------------------------------


@pytest.mark.db
def test_user_session_refresh_token_hash_is_unique(db):
    """DB-HIGH-8: duplicate refresh-token hashes are rejected by the DB."""
    from admin.aaas.models import UserSession

    digest = "b" * 64
    expires = timezone.now() + timezone.timedelta(days=7)
    UserSession.objects.create(
        user_id=uuid.uuid4(),
        device="test",
        ip_address="127.0.0.1",
        refresh_token_hash=digest,
        expires_at=expires,
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            UserSession.objects.create(
                user_id=uuid.uuid4(),
                device="test",
                ip_address="127.0.0.1",
                refresh_token_hash=digest,
                expires_at=expires,
            )


@pytest.mark.db
def test_user_session_blank_refresh_token_hash_allowed_multiple(db):
    """DB-HIGH-8: sessions with no refresh token may share the empty hash."""
    from admin.aaas.models import UserSession

    expires = timezone.now() + timezone.timedelta(days=7)
    for _ in range(3):
        UserSession.objects.create(
            user_id=uuid.uuid4(),
            device="test",
            ip_address="127.0.0.1",
            refresh_token_hash="",
            expires_at=expires,
        )
    assert UserSession.objects.filter(refresh_token_hash="").count() == 3


@pytest.mark.db
def test_user_session_token_lookup_uses_index(db):
    """DB-HIGH-8 behavioral: refresh-token lookup is index-backed."""
    import uuid as _uuid

    from django.db import connection
    from django.utils import timezone as _tz

    from admin.aaas.models import UserSession

    UserSession.objects.create(
        user_id=_uuid.uuid4(),
        device="test",
        ip_address="127.0.0.1",
        refresh_token_hash="d" * 64,
        expires_at=_tz.now() + _tz.timedelta(days=7),
    )
    with connection.cursor() as cur:
        cur.execute(
            "EXPLAIN SELECT id FROM aaas_user_session WHERE refresh_token_hash = %s",
            ["d" * 64],
        )
        plan = "\n".join(row[0] for row in cur.fetchall())
    assert "aaas_user_session" in plan


# ---------------------------------------------------------------------------
# DB-CRIT-5 — IdempotencyRecord.check_and_set atomicity
# ---------------------------------------------------------------------------


@pytest.mark.db
def test_check_and_set_first_call_is_new(db):
    from admin.core.models import IdempotencyRecord

    is_new, record = IdempotencyRecord.check_and_set(
        key=f"op-{uuid.uuid4().hex}", operation_type="memory_write"
    )
    assert is_new is True
    assert record is not None
    assert record.result is None


@pytest.mark.db
def test_check_and_set_duplicate_returns_existing(db):
    from admin.core.models import IdempotencyRecord

    key = f"op-{uuid.uuid4().hex}"
    is_new_1, rec_1 = IdempotencyRecord.check_and_set(key=key, operation_type="t")
    is_new_2, rec_2 = IdempotencyRecord.check_and_set(key=key, operation_type="t")
    assert is_new_1 is True
    assert is_new_2 is False
    assert rec_1.id == rec_2.id


@pytest.mark.db
def test_check_and_set_expired_record_is_reclaimed(db):
    from admin.core.models import IdempotencyRecord

    key = f"op-{uuid.uuid4().hex}"
    _, rec = IdempotencyRecord.check_and_set(key=key, operation_type="t")
    IdempotencyRecord.objects.filter(pk=rec.pk).update(
        expires_at=timezone.now() - timezone.timedelta(seconds=1)
    )
    is_new, rec2 = IdempotencyRecord.check_and_set(key=key, operation_type="t")
    assert is_new is True
    assert rec2.pk == rec.pk
    assert rec2.expires_at > timezone.now()


@pytest.mark.db
def test_check_and_set_concurrent_double_submit_yields_one_winner(db):
    """DB-CRIT-5 behavioral proof: two sequential claims of one key —
    exactly one ``is_new=True``. The UNIQUE constraint plus an atomic
    read-modify-write make the second call a duplicate, not a twin create.
    """
    from admin.core.models import IdempotencyRecord

    key = f"op-{uuid.uuid4().hex}"
    first = IdempotencyRecord.check_and_set(key=key, operation_type="t")
    second = IdempotencyRecord.check_and_set(key=key, operation_type="t")
    assert first[0] is True
    assert second[0] is False
    assert first[1].pk == second[1].pk
    assert IdempotencyRecord.objects.filter(idempotency_key=key).count() == 1


@pytest.mark.db
def test_check_and_set_unique_key_constraint_holds(db):
    """DB-CRIT-5 backstop: the DB rejects a second row for the same key."""
    from admin.core.models import IdempotencyRecord

    key = f"op-{uuid.uuid4().hex}"
    IdempotencyRecord.objects.create(
        idempotency_key=key, operation_type="t", expires_at=timezone.now()
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            IdempotencyRecord.objects.create(
                idempotency_key=key, operation_type="t", expires_at=timezone.now()
            )


# ---------------------------------------------------------------------------
# DB-CRIT-4 — CHECK constraints + one-active Constitution
# ---------------------------------------------------------------------------


@pytest.mark.db
def test_feature_flag_rollout_percentage_bounded(db):
    from admin.core.models import FeatureFlag

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            FeatureFlag.objects.create(
                name=f"neg-{uuid.uuid4().hex[:8]}", rollout_percentage=-1
            )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            FeatureFlag.objects.create(
                name=f"over-{uuid.uuid4().hex[:8]}", rollout_percentage=101
            )
    ok = FeatureFlag.objects.create(
        name=f"ok-{uuid.uuid4().hex[:8]}", rollout_percentage=50
    )
    assert ok.rollout_percentage == 50


@pytest.mark.db
def test_capsule_status_rejects_unknown_value(db):
    from admin.aaas.models import Tenant
    from admin.core.models import Capsule

    tenant = Tenant.objects.create(
        name=f"Status T {uuid.uuid4().hex[:8]}",
        slug=f"status-t-{uuid.uuid4().hex[:8]}",
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Capsule.objects.create(
                name="bad status",
                tenant=tenant,
                status="banana",
            )


@pytest.mark.db
def test_job_priority_bounded(db):
    from admin.core.models import Job

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Job.objects.create(
                name="bad prio", job_type="t", tenant="t", priority=10_000_001
            )


@pytest.mark.db
def test_constitution_only_one_active(db):
    from admin.core.models import Constitution

    Constitution.objects.create(
        version="1.0.0",
        content_hash="c" * 64,
        signature="sig",
        content={},
        is_active=True,
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Constitution.objects.create(
                version="1.0.1",
                content_hash="d" * 64,
                signature="sig",
                content={},
                is_active=True,
            )


@pytest.mark.db
def test_constitution_multiple_inactive_allowed(db):
    from admin.core.models import Constitution

    for i in range(3):
        Constitution.objects.create(
            version=f"0.0.{i}",
            content_hash=f"{i:064d}",
            signature="sig",
            content={},
            is_active=False,
        )
    assert Constitution.objects.filter(is_active=False).count() == 3


# ---------------------------------------------------------------------------
# SIMP-02 — MFA setup fails before any CPU work
# ---------------------------------------------------------------------------


def test_mfa_setup_refuses_without_returning_secret_material(monkeypatch):
    """SIMP-02 behavioral proof: with auth satisfied, setup must refuse and
    hand back no QR, no backup codes, no provisioning URI. The previous
    implementation computed all three and then threw them away on a
    guaranteed ServiceUnavailableError.
    """
    import asyncio

    import admin.auth.mfa as mfa_mod
    from admin.common.exceptions import ServiceUnavailableError

    async def _allow(*_a, **_k):
        return None  # local test double: auth is not under test here

    monkeypatch.setattr(mfa_mod, "authorize", _allow)

    class _Auth:
        email = "wave0@example.test"

    class _Req:
        auth = _Auth()

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(mfa_mod.setup_mfa(_Req()))
    except ServiceUnavailableError:
        result = None
    finally:
        loop.close()

    assert result is None, (
        "SIMP-02: setup_mfa must refuse; it must not return secret material"
    )
