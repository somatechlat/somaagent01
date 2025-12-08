"""Session repository port interface.

This port defines the contract for session persistence operations.
The interface matches the existing PostgresSessionStore methods exactly
to enable seamless wrapping of the production implementation.

Production Implementation:
    services.common.session_repository.PostgresSessionStore
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass(slots=True)
class SessionEnvelopeDTO:
    """Data transfer object for session envelope.
    
    Mirrors services.common.session_repository.SessionEnvelope structure.
    """
    session_id: UUID
    persona_id: Optional[str]
    tenant: Optional[str]
    subject: Optional[str]
    issuer: Optional[str]
    scope: Optional[str]
    metadata: Dict[str, Any]
    analysis: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SessionRepositoryPort(ABC):
    """Abstract interface for session persistence.
    
    This port wraps the existing PostgresSessionStore implementation.
    All methods match the production implementation signature exactly.
    """
    
    @abstractmethod
    async def append_event(self, session_id: str, event: Dict[str, Any]) -> None:
        """Append an event to the session timeline.
        
        Args:
            session_id: The session identifier
            event: Event payload to persist
        """
        ...
    
    @abstractmethod
    async def list_events(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """List events for a session in reverse chronological order.
        
        Args:
            session_id: The session identifier
            limit: Maximum number of events to return
            
        Returns:
            List of event payloads
        """
        ...
    
    @abstractmethod
    async def list_events_after(
        self,
        session_id: str,
        *,
        after_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List events after a specific event ID.
        
        Args:
            session_id: The session identifier
            after_id: Return events after this ID (None for all)
            limit: Maximum number of events to return
            
        Returns:
            List of event records with id, occurred_at, and payload
        """
        ...
    
    @abstractmethod
    async def get_envelope(self, session_id: str) -> Optional[SessionEnvelopeDTO]:
        """Get the session envelope (metadata container).
        
        Args:
            session_id: The session identifier
            
        Returns:
            Session envelope or None if not found
        """
        ...
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> Dict[str, int]:
        """Delete all events and envelope for a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dict with counts of deleted rows
        """
        ...
    
    @abstractmethod
    async def reset_session(self, session_id: str) -> Dict[str, int]:
        """Clear timeline events but keep envelope.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dict with counts of affected rows
        """
        ...
    
    @abstractmethod
    async def list_sessions(
        self,
        *,
        limit: int = 50,
        tenant: Optional[str] = None,
    ) -> List[SessionEnvelopeDTO]:
        """List session envelopes.
        
        Args:
            limit: Maximum number of sessions to return
            tenant: Filter by tenant (optional)
            
        Returns:
            List of session envelopes
        """
        ...
    
    @abstractmethod
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
        """Backfill or update a session envelope.
        
        Args:
            session_id: The session identifier
            persona_id: Persona identifier
            tenant: Tenant identifier
            subject: Subject identifier
            issuer: Token issuer
            scope: Authorization scope
            metadata: Session metadata
            analysis: Analysis data
            created_at: Creation timestamp
            updated_at: Update timestamp
        """
        ...
    
    @abstractmethod
    async def ping(self) -> None:
        """Health check - verify database connectivity."""
        ...
    
    @abstractmethod
    async def close(self) -> None:
        """Close database connections and release resources."""
        ...
