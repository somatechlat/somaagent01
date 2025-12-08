"""Session repository adapter wrapping PostgresSessionStore.

This adapter implements SessionRepositoryPort by delegating ALL operations
to the existing production PostgresSessionStore implementation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.common.session_repository import PostgresSessionStore, SessionEnvelope
from src.core.domain.ports.repositories.session_repository import (
    SessionEnvelopeDTO,
    SessionRepositoryPort,
)


class PostgresSessionRepositoryAdapter(SessionRepositoryPort):
    """Implements SessionRepositoryPort using existing PostgresSessionStore.
    
    Delegates ALL operations to services.common.session_repository.PostgresSessionStore.
    """
    
    def __init__(self, store: Optional[PostgresSessionStore] = None, dsn: Optional[str] = None):
        """Initialize adapter with existing store or create new one.
        
        Args:
            store: Existing PostgresSessionStore instance (preferred)
            dsn: Database DSN (used if store not provided)
        """
        self._store = store or PostgresSessionStore(dsn=dsn)
    
    @staticmethod
    def _to_dto(envelope: SessionEnvelope) -> SessionEnvelopeDTO:
        """Convert production SessionEnvelope to DTO."""
        return SessionEnvelopeDTO(
            session_id=envelope.session_id,
            persona_id=envelope.persona_id,
            tenant=envelope.tenant,
            subject=envelope.subject,
            issuer=envelope.issuer,
            scope=envelope.scope,
            metadata=envelope.metadata,
            analysis=envelope.analysis,
            created_at=envelope.created_at,
            updated_at=envelope.updated_at,
        )
    
    async def append_event(self, session_id: str, event: Dict[str, Any]) -> None:
        await self._store.append_event(session_id, event)
    
    async def list_events(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        return await self._store.list_events(session_id, limit)
    
    async def list_events_after(
        self,
        session_id: str,
        *,
        after_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return await self._store.list_events_after(session_id, after_id=after_id, limit=limit)
    
    async def get_envelope(self, session_id: str) -> Optional[SessionEnvelopeDTO]:
        envelope = await self._store.get_envelope(session_id)
        return self._to_dto(envelope) if envelope else None
    
    async def delete_session(self, session_id: str) -> Dict[str, int]:
        return await self._store.delete_session(session_id)
    
    async def reset_session(self, session_id: str) -> Dict[str, int]:
        return await self._store.reset_session(session_id)
    
    async def list_sessions(
        self,
        *,
        limit: int = 50,
        tenant: Optional[str] = None,
    ) -> List[SessionEnvelopeDTO]:
        envelopes = await self._store.list_sessions(limit=limit, tenant=tenant)
        return [self._to_dto(e) for e in envelopes]
    
    async def backfill_envelope(
        self,
        session_id: str,
        *,
        persona_id: Optional[str],
        tenant: Optional[str],
        subject: Optional[str],
        issuer: Optional[str],
        scope: Optional[str],
        metadata: Dict[str, Any],
        analysis: Dict[str, Any],
        created_at: Optional[datetime],
        updated_at: Optional[datetime],
    ) -> None:
        await self._store.backfill_envelope(
            session_id,
            persona_id=persona_id,
            tenant=tenant,
            subject=subject,
            issuer=issuer,
            scope=scope,
            metadata=metadata,
            analysis=analysis,
            created_at=created_at,
            updated_at=updated_at,
        )
    
    async def ping(self) -> None:
        await self._store.ping()
    
    async def close(self) -> None:
        await self._store.close()
