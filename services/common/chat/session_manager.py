"""Session management for ChatService.

Extracted from chat_service.py per VIBE Rule 245 (650-line max).
Handles agent session initialization and neuromodulator loading.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional
from uuid import uuid4

from asgiref.sync import sync_to_async

from services.common.chat.metrics import CHAT_LATENCY, CHAT_REQUESTS
from services.common.chat_schemas import AgentSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Service for managing agent sessions.

    Extracted from ChatService to enforce 650-line limit.
    """

    async def _load_neuromodulators(
        self, agent_id: str, tenant_id: Optional[str], persona_id: Optional[str]
    ) -> None:
        """Load neuromodulator baseline from Capsule and apply to SomaBrain.

        GMD Integration: Implements neuromodulator loading per whitepaper.
        Uses default baseline if Capsule not found.
        """
        from admin.core.models import Capsule
        from aaas.brain import brain

        # Default neuromodulators (GMD baseline)
        default_neuro = {
            "dopamine": 0.5,
            "serotonin": 0.5,
            "norepinephrine": 0.5,
            "acetylcholine": 0.5,
        }

        try:

            @sync_to_async
            def get_capsule_neuro():
                capsule = Capsule.objects.filter(id=agent_id).first()
                if capsule and capsule.neuromodulator_baseline:
                    return capsule.neuromodulator_baseline
                return None

            capsule_neuro = await get_capsule_neuro()
            neuromodulators = capsule_neuro or default_neuro

            # Apply to SomaBrain (uses direct or HTTP based on mode)
            try:
                await brain.set_neuromodulators_async(
                    tenant_id=tenant_id or "default",
                    persona_id=persona_id or "default",
                    neuromodulators=neuromodulators,
                )
                logger.info(
                    f"[GMD] Loaded neuromodulators for agent {agent_id[:8]}: {neuromodulators}"
                )
            except Exception as e:
                logger.warning(f"[GMD] Failed to update neuromodulators: {e}")

        except Exception as e:
            logger.warning(f"[GMD] Failed to load capsule neuromodulators: {e}")

    async def initialize_agent_session(
        self, agent_id: str, conversation_id: str, user_context: dict
    ) -> AgentSession:
        """Initialize agent session in local session store."""
        from admin.core.models import Session as SessionModel

        start_time = time.perf_counter()
        try:

            @sync_to_async
            def create_session():
                session_id = str(uuid4())
                return SessionModel.objects.create(
                    session_id=session_id,
                    tenant=user_context.get("tenant_id"),
                    persona_id=user_context.get("persona_id"),
                    metadata={
                        "agent_id": agent_id,
                        "conversation_id": conversation_id,
                        "user_id": user_context.get("user_id"),
                    },
                )

            session_record = await create_session()
            session = AgentSession(
                session_id=session_record.session_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                created_at=session_record.created_at,
            )

            # GMD Integration: Load neuromodulator baseline from Capsule (non-blocking)
            asyncio.create_task(
                self._load_neuromodulators(
                    agent_id=agent_id,
                    tenant_id=user_context.get("tenant_id"),
                    persona_id=user_context.get("persona_id"),
                )
            )

            CHAT_LATENCY.labels(method="initialize_agent_session").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="initialize_agent_session", result="success").inc()
            return session
        except Exception:
            CHAT_LATENCY.labels(method="initialize_agent_session").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="initialize_agent_session", result="error").inc()
            raise


__all__ = ["SessionManager"]
