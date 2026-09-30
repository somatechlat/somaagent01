"""GenerateResponseUseCase — no dummy credentials, no discarded configuration.

Two contracts are on trial.

**The internal token is a credential, never a placeholder.** It is stored in
Vault (``infra/standalone/init_vault.py`` seeds
``secret/agent/credentials/gateway_internal_token``) and sent as
``X-Internal-Token`` on every internal gateway call. The chain used to
substitute a dummy at three separate points:

    get_credential("gateway_internal_token") or ""   # absent -> ""
    self._internal_token or ""                       # ""      -> ""
    headers = {"X-Internal-Token": ...}              # sent empty

An empty string standing in for a missing secret is a dummy credential. It is
the same failure as hardcoding one: the request goes out looking like a
credential with a value nobody issued. These claims pin the opposite — the
operation refuses.

**The configured default model must actually be sent.** ``execute`` resolves
``model = input_data.model or self._default_model`` and then dropped the result:
``_build_overrides`` only wrote ``overrides["model"]`` when the *input* carried
one, and the ``model`` handed to ``_stream_response`` was never read. So a
deployment that configured a default model silently got the gateway's own
default instead. ``default_model``'s own parameter default was the literal
placeholder ``"unknown"``.

Nothing here is stubbed, faked or stood in for. The publisher is passed as a
bare ``object()``: the constructor only stores it and never calls it, so there
is nothing to substitute. A stand-in publisher would be a mock of a dependency
this test does not exercise.

Run:
    pytest tests/unit/test_generate_response_use_case.py -v
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from admin.core.application.use_cases.conversation.generate_response import (
    GenerateResponseInput,
    GenerateResponseUseCase,
)

# ``GenerateResponseUseCase.__init__`` stores the publisher and never invokes
# it. The only real implementation, ``DurablePublisher``, needs a live Kafka
# bus to construct, so the honest options were a stand-in (a mock of a
# dependency this test does not exercise) or an argument the constructor does
# not touch. This is the second: ``cast`` asserts nothing about behaviour, it
# only silences a type checker that cannot see the value is never used.
UNUSED_PUBLISHER = cast(Any, object())


def _build(internal_token):
    return GenerateResponseUseCase(
        gateway_base="http://gateway.internal:9000",
        internal_token=internal_token,
        publisher=UNUSED_PUBLISHER,
        outbound_topic="conversation.outbound",
        default_model="model-a",
    )


class TestInternalTokenIsRequired:
    """A missing or empty internal token must refuse construction, not send ""."""

    def test_an_empty_token_is_not_a_credential(self):
        """``""`` is exactly what the old ``or ""`` produced. It must not be accepted."""
        with pytest.raises(ValueError):
            _build("")

    def test_a_missing_token_is_not_a_credential(self):
        """``None`` is what ``get_credential`` returns when Vault holds no key."""
        with pytest.raises(ValueError):
            _build(None)

    def test_a_whitespace_token_is_not_a_credential(self):
        """A token of spaces is no more issued than an empty one."""
        with pytest.raises(ValueError):
            _build("   ")

    def test_the_refusal_names_the_problem_without_echoing_a_value(self):
        """An error is not a place to print a credential."""
        with pytest.raises(ValueError) as exc:
            _build("")
        message = str(exc.value)
        assert "token" in message.lower()
        assert "from-env" not in message

    def test_a_real_token_is_accepted(self):
        """The control.

        Without it the refusals above would be satisfied by a constructor that
        simply always raises.
        """
        assert _build("a-real-issued-token-value") is not None


# ---------------------------------------------------------------------------
# Model resolution — the configured default must reach the gateway
# ---------------------------------------------------------------------------


def _input(model: str | None) -> GenerateResponseInput:
    return GenerateResponseInput(
        session_id="s-1",
        persona_id=None,
        messages=[{"role": "user", "content": "hello"}],
        tenant="tenant-a",
        model=model,
    )


class TestModelResolution:
    """``default_model`` is configuration. It must be sent, not discarded."""

    def test_the_configured_default_model_is_actually_sent(self):
        """When the caller names no model, the deployment's default goes out.

        ``execute`` computed ``input_data.model or self._default_model`` and
        then threw the result away: ``_build_overrides`` keyed off
        ``input_data.model`` alone. A deployment that set a default model was
        silently getting the gateway's own default instead.
        """
        use_case = _build("a-real-issued-token-value")
        assert use_case._default_model == "model-a"
        overrides = use_case._build_overrides(_input(None))
        assert overrides.get("model") == "model-a"

    def test_an_explicit_model_still_wins(self):
        """The control for the claim above: a caller-chosen model is honoured."""
        use_case = _build("a-real-issued-token-value")
        overrides = use_case._build_overrides(_input("caller-chosen-model"))
        assert overrides.get("model") == "caller-chosen-model"

    def test_the_default_model_is_not_a_placeholder(self):
        """``"unknown"`` was the parameter's default. A placeholder is not a model.

        Sending ``model: "unknown"`` would reach the gateway as a real
        identifier. A missing model must refuse construction instead.
        """
        with pytest.raises(ValueError):
            GenerateResponseUseCase(
                gateway_base="http://gateway.internal:9000",
                internal_token="a-real-issued-token-value",
                publisher=UNUSED_PUBLISHER,
                outbound_topic="conversation.outbound",
                default_model="unknown",
            )

    def test_an_empty_default_model_is_refused(self):
        """``""`` is what the call sites produced from ``SA01_LLM_MODEL or ""``."""
        with pytest.raises(ValueError):
            GenerateResponseUseCase(
                gateway_base="http://gateway.internal:9000",
                internal_token="a-real-issued-token-value",
                publisher=UNUSED_PUBLISHER,
                outbound_topic="conversation.outbound",
                default_model="",
            )

    def test_a_real_default_model_still_constructs(self):
        """Control: a genuinely configured model is accepted."""
        assert _build("a-real-issued-token-value") is not None
