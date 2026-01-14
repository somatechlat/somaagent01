"""Implicit RL signal collection from user behavior.

No UI buttons needed - learns from natural interaction patterns.
Implements GMD (Governing Memory Dynamics) reward publishing via SomaBrain.

GMD Parameters (from whitepaper):
- η (eta): 0.08 - memory decay rate
- λ (lambda): 2.05e-5 - regularization
- α (alpha): 640 - cleanup constant
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Prometheus metrics
IMPLICIT_SIGNALS = Counter(
    "implicit_rl_signals_total",
    "Implicit RL signals collected",
    labelnames=("signal_type", "result"),
)

# Signal thresholds (tuned for GMD)
ABANDONMENT_THRESHOLD_SECONDS = 10  # User leaves within 10s = bad
FOLLOW_UP_WINDOW_SECONDS = 300  # Follow-up within 5min = good
MIN_ENGAGED_TURNS = 5  # Minimum turns for engagement signal


async def signal_follow_up(session_id: str, time_since_last: float) -> bool:
    """User sent a follow-up message - positive signal.

    GMD Integration: This updates SomaBrain's reward model for better recall.
    """
    from saas.brain import brain

    if time_since_last < FOLLOW_UP_WINDOW_SECONDS:
        # Reward scales inversely with response time (faster = better)
        reward_value = 0.3 * (1 - time_since_last / FOLLOW_UP_WINDOW_SECONDS)
        success = await brain.apply_feedback_async(
            session_id=session_id,
            signal="follow_up",
            value=reward_value,
            meta={"time_since_last": time_since_last},
        )
        if success:
            IMPLICIT_SIGNALS.labels(signal_type="follow_up", result="ok").inc()
            logger.info(f"[GMD] Follow-up signal: +{reward_value:.3f} for session {session_id[:8]}")
        else:
            IMPLICIT_SIGNALS.labels(signal_type="follow_up", result="error").inc()
        return success
    return False


async def signal_regenerate(session_id: str, message_id: str) -> bool:
    """User requested regeneration - negative signal.

    This is a strong indicator the response was unsatisfactory.
    """
    from saas.brain import brain

    success = await brain.apply_feedback_async(
        session_id=session_id,
        signal="regenerate",
        value=-0.5,
        meta={"message_id": message_id},
    )
    if success:
        IMPLICIT_SIGNALS.labels(signal_type="regenerate", result="ok").inc()
        logger.info(f"[GMD] Regenerate signal: -0.5 for session {session_id[:8]}")
    else:
        IMPLICIT_SIGNALS.labels(signal_type="regenerate", result="error").inc()
    return success


async def signal_copy(session_id: str, message_id: str) -> bool:
    """User copied response - very positive signal.

    Indicates the response was valuable enough to reuse.
    """
    from saas.brain import brain

    success = await brain.apply_feedback_async(
        session_id=session_id,
        signal="copy",
        value=0.7,
        meta={"message_id": message_id},
    )
    if success:
        IMPLICIT_SIGNALS.labels(signal_type="copy", result="ok").inc()
        logger.info(f"[GMD] Copy signal: +0.7 for session {session_id[:8]}")
    else:
        IMPLICIT_SIGNALS.labels(signal_type="copy", result="error").inc()
    return success


async def signal_conversation_end(
    session_id: str, total_turns: int, last_was_assistant: bool
) -> bool:
    """Conversation ended - evaluate quality based on engagement.

    GMD Integration: Uses turn count as proxy for conversation quality.
    """
    from saas.brain import brain

    if total_turns < 2 and last_was_assistant:
        # User abandoned after first response
        success = await brain.apply_feedback_async(
            session_id=session_id,
            signal="abandonment",
            value=-0.3,
            meta={"turns": total_turns},
        )
        if success:
            IMPLICIT_SIGNALS.labels(signal_type="abandonment", result="ok").inc()
            logger.info(f"[GMD] Abandonment signal: -0.3 for session {session_id[:8]}")
        return success

    elif total_turns >= MIN_ENGAGED_TURNS:
        # Long engaged conversation - positive signal
        # Reward scales with turn count (capped)
        reward = min(0.5, 0.1 * (total_turns - MIN_ENGAGED_TURNS + 1))
        success = await brain.apply_feedback_async(
            session_id=session_id,
            signal="engagement",
            value=reward,
            meta={"turns": total_turns},
        )
        if success:
            IMPLICIT_SIGNALS.labels(signal_type="engagement", result="ok").inc()
            logger.info(f"[GMD] Engagement signal: +{reward:.2f} for session {session_id[:8]}")
        return success

    return False


async def signal_tool_usage(session_id: str, tool_name: str, success: bool) -> bool:
    """User's request led to successful tool execution.

    Indicates actionable, concrete value from the response.
    """
    from saas.brain import brain

    value = 0.5 if success else -0.2
    result = await brain.apply_feedback_async(
        session_id=session_id,
        signal="tool_usage",
        value=value,
        meta={"tool": tool_name, "success": success},
    )
    if result:
        IMPLICIT_SIGNALS.labels(signal_type="tool_usage", result="ok").inc()
        logger.info(f"[GMD] Tool signal: {value:+.1f} for {tool_name}")
    return result


async def signal_long_response(session_id: str, user_message_length: int) -> bool:
    """User sent a long message after assistant response.

    Long messages indicate engagement and thoughtful interaction.
    """
    from saas.brain import brain

    if user_message_length > 200:  # >200 chars = engaged
        reward = min(0.3, 0.1 * (user_message_length / 200))
        success = await brain.apply_feedback_async(
            session_id=session_id,
            signal="long_response",
            value=reward,
            meta={"length": user_message_length},
        )
        if success:
            IMPLICIT_SIGNALS.labels(signal_type="long_response", result="ok").inc()
        return success
    return False


__all__ = [
    "signal_follow_up",
    "signal_regenerate",
    "signal_copy",
    "signal_conversation_end",
    "signal_tool_usage",
    "signal_long_response",
]
