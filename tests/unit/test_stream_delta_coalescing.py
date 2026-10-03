"""Streaming must be fast: coalesce deltas, never re-send the whole reply.

Per-token WebSocket frames dominate the cost of a stream turn: one JSON
serialise + one frame + one Prometheus label lookup per token. The ``chat.done``
message then re-sent the entire response body that had already been streamed.
That is wasted bytes on the wire and wasted work at the end of every turn.

The contract the UI already supports (``chunk.content ?? this._streamContent``)
means ``chat.done`` does not need to carry the body at all.
"""

from __future__ import annotations

import inspect

from services.gateway.consumers import chat as chat_mod


def test_chat_done_does_not_resend_the_response_body():
    """chat.done is metadata, not a second delivery of the stream."""
    src = inspect.getsource(chat_mod.ChatConsumer._handle_chat)
    done_block = src[src.index("MSG_CHAT_DONE") :]
    assert '"content"' not in done_block.split("except")[0], (
        "chat.done still re-sends the full response body"
    )


def test_delta_send_is_coalesced_not_per_token():
    """The consumer must not await a send for every single token."""
    src = inspect.getsource(chat_mod.ChatConsumer._handle_chat)
    assert "chat_mod_flush" in src or "_FLUSH" in src or "coalesc" in src.lower(), (
        "streaming still sends one WebSocket frame per token"
    )


def test_flush_threshold_is_sub_perceptual():
    """Coalescing must never add human-noticeable latency (< 100ms)."""
    assert chat_mod._FLUSH_INTERVAL_S < 0.1
    assert chat_mod._FLUSH_MAX_CHARS > 0
