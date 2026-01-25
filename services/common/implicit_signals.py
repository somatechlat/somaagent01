"""Implicit RL signal collection from user behavior.

No UI buttons needed - learns from natural interaction patterns.
Implements GMD (Governing Memory Dynamics) reward publishing via SomaBrain.

Configured via Capsule.learning_config (Rule 91).
System Defaults (Fallbacks):
- η (eta): 0.08
- λ (lambda): 2.05e-5
- α (alpha): 640
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Prometheus metrics
IMPLICIT_SIGNALS = Counter(
    "implicit_rl_signals_total",
    "Implicit RL signals collected",
    labelnames=("signal_type", "result"),
)

# GMD System Defaults (Used only if Capsule.learning_config is missing/empty)
DEFAULTS = {
    "abandonment_threshold": 10,
    "follow_up_window": 300,
    "min_engaged_turns": 5,
    "reward_copy": 0.7,
    "reward_regenerate": -0.5,
    "reward_follow_up": 0.3,
    "reward_abandonment": -0.3,
    "reward_engagement_max": 0.5,
    "reward_tool_success": 0.5,
    "reward_tool_fail": -0.2,
    "reward_long_response": 0.3,
}


async def signal_follow_up(
    session_id: str,
    time_since_last: float,
    learning_config: Optional[Dict[str, Any]] = None,
) -> bool:
    """User sent a follow-up message - positive signal.

    GMD Integration: This updates SomaBrain's reward model for better recall.
    """
    from aaas.brain import brain

    config = learning_config or {}
    window = config.get("follow_up_window", DEFAULTS["follow_up_window"])
    base_reward = config.get("reward_follow_up", DEFAULTS["reward_follow_up"])

    if time_since_last < window:
        # Reward scales inversely with response time (faster = better)
        # Formula: Base * (1 - t/window)
        reward_value = base_reward * (1 - time_since_last / window)

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


async def signal_regenerate(
    session_id: str,
    message_id: str,
    learning_config: Optional[Dict[str, Any]] = None,
) -> bool:
    """User requested regeneration - negative signal.

    This is a strong indicator the response was unsatisfactory.
    """
    from aaas.brain import brain

    config = learning_config or {}
    value = config.get("reward_regenerate", DEFAULTS["reward_regenerate"])

    success = await brain.apply_feedback_async(
        session_id=session_id,
        signal="regenerate",
        value=value,
        meta={"message_id": message_id},
    )
    if success:
        IMPLICIT_SIGNALS.labels(signal_type="regenerate", result="ok").inc()
        logger.info(f"[GMD] Regenerate signal: {value} for session {session_id[:8]}")
    else:
        IMPLICIT_SIGNALS.labels(signal_type="regenerate", result="error").inc()
    return success


async def signal_copy(
    session_id: str,
    message_id: str,
    learning_config: Optional[Dict[str, Any]] = None,
) -> bool:
    """User copied response - very positive signal.

    Indicates the response was valuable enough to reuse.
    """
    from aaas.brain import brain

    config = learning_config or {}
    value = config.get("reward_copy", DEFAULTS["reward_copy"])

    success = await brain.apply_feedback_async(
        session_id=session_id,
        signal="copy",
        value=value,
        meta={"message_id": message_id},
    )
    if success:
        IMPLICIT_SIGNALS.labels(signal_type="copy", result="ok").inc()
        logger.info(f"[GMD] Copy signal: +{value} for session {session_id[:8]}")
    else:
        IMPLICIT_SIGNALS.labels(signal_type="copy", result="error").inc()
    return success


async def signal_conversation_end(
    session_id: str,
    total_turns: int,
    last_was_assistant: bool,
    learning_config: Optional[Dict[str, Any]] = None,
) -> bool:
    """Conversation ended - evaluate quality based on engagement.

    GMD Integration: Uses turn count as proxy for conversation quality.
    """
    from aaas.brain import brain

    config = learning_config or {}
    min_turns = config.get("min_engaged_turns", DEFAULTS["min_engaged_turns"])

    if total_turns < 2 and last_was_assistant:
        # User abandoned after first response
        value = config.get("reward_abandonment", DEFAULTS["reward_abandonment"])
        success = await brain.apply_feedback_async(
            session_id=session_id,
            signal="abandonment",
            value=value,
            meta={"turns": total_turns},
        )
        if success:
            IMPLICIT_SIGNALS.labels(signal_type="abandonment", result="ok").inc()
            logger.info(f"[GMD] Abandonment signal: {value} for session {session_id[:8]}")
        return success

    elif total_turns >= min_turns:
        # Long engaged conversation - positive signal
        max_reward = config.get("reward_engagement_max", DEFAULTS["reward_engagement_max"])
        # Reward scales with turn count (capped)
        reward = min(max_reward, 0.1 * (total_turns - min_turns + 1))
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


async def signal_tool_usage(
    session_id: str,
    tool_name: str,
    success: bool,
    learning_config: Optional[Dict[str, Any]] = None,
) -> bool:
    """User's request led to successful tool execution.

    Indicates actionable, concrete value from the response.
    """
    from aaas.brain import brain

    config = learning_config or {}
    if success:
        value = config.get("reward_tool_success", DEFAULTS["reward_tool_success"])
    else:
        value = config.get("reward_tool_fail", DEFAULTS["reward_tool_fail"])

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


async def signal_long_response(
    session_id: str,
    user_message_length: int,
    learning_config: Optional[Dict[str, Any]] = None,
) -> bool:
    """User sent a long message after assistant response.

    Long messages indicate engagement and thoughtful interaction.
    """
    from aaas.brain import brain

    config = learning_config or {}
    max_reward = config.get("reward_long_response", DEFAULTS["reward_long_response"])

    if user_message_length > 200:  # >200 chars = engaged
        reward = min(max_reward, 0.1 * (user_message_length / 200))
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
