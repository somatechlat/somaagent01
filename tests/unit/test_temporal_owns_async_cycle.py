"""Temporal owns the async cycle: workers start, hot chat is not behind it."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR = ROOT / "infra" / "aaas" / "aaas" / "supervisord.conf"


def test_supervisord_starts_the_conversation_temporal_worker():
    text = SUPERVISOR.read_text(encoding="utf-8")
    assert "conversation_worker.temporal_worker" in text or "conversation-temporal" in text


def test_supervisord_starts_the_delegation_temporal_worker():
    text = SUPERVISOR.read_text(encoding="utf-8")
    assert "delegation_gateway.temporal_worker" in text or "delegation-temporal" in text


def test_hot_chat_token_path_is_not_behind_temporal():
    """chat_orchestrator is the hot path; it must not start workflows per token."""
    src = (ROOT / "admin" / "core" / "chat_orchestrator.py").read_text(encoding="utf-8")
    assert "start_workflow" not in src
    assert "temporalio" not in src


def test_post_message_starts_a_workflow():
    src = (ROOT / "admin" / "core" / "api" / "sessions.py").read_text(encoding="utf-8")
    assert "start_workflow" in src


def test_a2a_execute_starts_a_workflow():
    src = (ROOT / "admin" / "gateway" / "api" / "gateway.py").read_text(encoding="utf-8")
    assert "start_workflow" in src


# ---------------------------------------------------------------------------
# Schedule intervals are behaviour (SOMA-STD-CONFIG-001 R-BEH-01/02), not env.
# ---------------------------------------------------------------------------

SCHEDULE_KEYS = (
    ("SA01_SLEEP_CYCLE_HOURS", 6),
    ("SA01_JOB_ADVANCE_SECONDS", 60),
    ("SA01_OUTBOX_REPLAY_SECONDS", 30),
)


def test_schedule_intervals_are_declared_once_on_settings_model():
    """R-VAL-01: the schema default lives on SettingsModel and nowhere else."""
    src = (ROOT / "admin" / "core" / "helpers" / "settings_model.py").read_text(encoding="utf-8")
    for key, default in SCHEDULE_KEYS:
        assert f'_dj("{key}", {default})' in src, f"{key} must be _dj-declared with {default}"


def test_schedule_intervals_are_registered_in_key_category():
    """R-BEH-02: administrable means the key is in the registry an admin CRUDs."""
    from admin.core.helpers.capsule_settings import KEY_CATEGORY

    for key, _ in SCHEDULE_KEYS:
        assert key in KEY_CATEGORY, f"{key} missing from KEY_CATEGORY"


def test_schedule_specs_reads_through_get_settings_not_env():
    """R-BEH-02 / R-VAL-03: the worker reads the single resolver, never os.environ."""
    src = (
        ROOT / "services" / "conversation_worker" / "temporal_worker.py"
    ).read_text(encoding="utf-8")
    for key, _ in SCHEDULE_KEYS:
        assert f'os.environ.get("{key}"' not in src, f"{key} is still read from env at a call site"
    assert "get_settings" in src, "temporal_worker must read schedule cadence via get_settings()"


def test_schedule_default_numbers_appear_in_exactly_one_place():
    """AP-03: the number must not be duplicated as a call-site or Django literal."""
    offenders: list[str] = []
    for rel in (
        "services/conversation_worker/temporal_worker.py",
        "config/settings.py",
        "services/gateway/settings.py",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        for key, _ in SCHEDULE_KEYS:
            if re.search(rf'os\.environ\.get\(\s*"{key}"\s*,', text):
                offenders.append(f"{rel}: {key} carries its own default")
    assert not offenders, "schedule defaults duplicated:\n  " + "\n  ".join(offenders)
