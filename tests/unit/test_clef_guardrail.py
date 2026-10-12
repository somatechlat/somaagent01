"""Clef guardrail choke tests — injected client only inside this file."""

from __future__ import annotations

import asyncio

import pytest

from services.common.decisions.contracts import DecisionSignals
from services.common.decisions.guardrail import choke_tool_call, tool_risk_tier


class _FakeResult:
    def __init__(self, signals, outcome, persisted=True):
        self.signals = signals
        self.outcome = outcome
        self.fact_persisted = persisted
        self.decision_id = "test"


class _FakeClient:
    def __init__(self, result):
        self._result = result
        self.calls = []

    async def decide(self, **kwargs):
        self.calls.append(kwargs)
        return self._result


def test_tier_map():
    assert tool_risk_tier("code_execute") == 3
    assert tool_risk_tier("file_write") == 2
    assert tool_risk_tier("timestamp") == 1
    assert tool_risk_tier("unlisted") == 2


def test_flag_off_tier3_not_legacy(monkeypatch):
    monkeypatch.setattr(
        "services.common.decisions.guardrail.clef_flag_enabled", lambda f: False
    )
    out = asyncio.run(
        choke_tool_call(
            tool_name="code_execute",
            args={"code": "x"},
            tenant="t",
            caller="v3",
            current_decision="auto_execute",
            client=_FakeClient(_FakeResult(DecisionSignals(), "allow")),
        )
    )
    assert out == "approval_required"


def test_brain_write_lost_blocks_tier3(monkeypatch):
    monkeypatch.setattr(
        "services.common.decisions.guardrail.clef_flag_enabled", lambda f: True
    )
    out = asyncio.run(
        choke_tool_call(
            tool_name="code_execute",
            args={"code": "x"},
            tenant="t",
            caller="v3",
            current_decision="auto_execute",
            client=_FakeClient(
                _FakeResult(DecisionSignals(p_safe=0.9, risk=0.1), "allow", persisted=False)
            ),
        )
    )
    assert out in ("approval_required", "denied")


def test_engine_down_tier3(monkeypatch):
    monkeypatch.setattr(
        "services.common.decisions.guardrail.clef_flag_enabled", lambda f: True
    )

    class _Broken:
        async def decide(self, **kwargs):
            raise RuntimeError("down")

    out = asyncio.run(
        choke_tool_call(
            tool_name="packages_ensure",
            args={"packages": ["x"]},
            tenant="t",
            caller="v3",
            current_decision="auto_execute",
            client=_Broken(),
        )
    )
    assert out in ("approval_required", "denied")
