"""Temporal owns the async cycle: workers start, hot chat is not behind it."""

from __future__ import annotations

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
