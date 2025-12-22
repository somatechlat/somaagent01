"""
Eye of God SomaBrain Client
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real HTTP client
- Async operations
- Retry logic
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import httpx
import os

LOGGER = logging.getLogger(__name__)


@dataclass
class Memory:
    """Memory record from SomaBrain."""
    id: str
    tenant_id: str
    agent_id: str
    content: str
    memory_type: str
    importance: float
    metadata: Dict[str, Any]
    created_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0


@dataclass
class SearchResult:
    """Semantic search result."""
    memory: Memory
    score: float
    highlights: List[str]


class SomaBrainClient:
    """
    Client for SomaBrain memory service.
    
    Provides memory storage, retrieval, and semantic search.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url or os.getenv('SOMABRAIN_URL', 'http://localhost:8030')
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        client = await self._get_client()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    LOGGER.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
        
        raise last_error
    
    # Memory CRUD Operations
    
    async def create_memory(
        self,
        tenant_id: str,
        agent_id: str,
        content: str,
        memory_type: str = 'episodic',
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        Create a new memory.
        
        Args:
            tenant_id: Tenant UUID
            agent_id: Agent UUID
            content: Memory content text
            memory_type: Type (episodic, semantic, procedural)
            importance: Importance score 0-1
            metadata: Additional metadata
            
        Returns:
            Created memory record
        """
        response = await self._request(
            'POST',
            '/api/v1/memories',
            json={
                'tenant_id': tenant_id,
                'agent_id': agent_id,
                'content': content,
                'memory_type': memory_type,
                'importance': importance,
                'metadata': metadata or {},
            }
        )
        
        data = response.json()
        return self._parse_memory(data)
    
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID."""
        try:
            response = await self._request('GET', f'/api/v1/memories/{memory_id}')
            return self._parse_memory(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """Update a memory."""
        updates = {}
        if content is not None:
            updates['content'] = content
        if importance is not None:
            updates['importance'] = importance
        if metadata is not None:
            updates['metadata'] = metadata
        
        response = await self._request(
            'PATCH',
            f'/api/v1/memories/{memory_id}',
            json=updates
        )
        
        return self._parse_memory(response.json())
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        try:
            await self._request('DELETE', f'/api/v1/memories/{memory_id}')
            return True
        except httpx.HTTPStatusError:
            return False
    
    async def list_memories(
        self,
        tenant_id: str,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Memory]:
        """List memories with filtering."""
        params = {
            'tenant_id': tenant_id,
            'limit': limit,
            'offset': offset,
        }
        if agent_id:
            params['agent_id'] = agent_id
        if memory_type:
            params['memory_type'] = memory_type
        
        response = await self._request('GET', '/api/v1/memories', params=params)
        
        return [self._parse_memory(m) for m in response.json()]
    
    # Semantic Search
    
    async def search(
        self,
        tenant_id: str,
        query: str,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.5,
    ) -> List[SearchResult]:
        """
        Perform semantic search across memories.
        
        Args:
            tenant_id: Tenant UUID
            query: Search query text
            agent_id: Optional agent filter
            memory_type: Optional type filter
            limit: Max results
            min_score: Minimum similarity score
            
        Returns:
            List of search results with scores
        """
        payload = {
            'tenant_id': tenant_id,
            'query': query,
            'limit': limit,
            'min_score': min_score,
        }
        if agent_id:
            payload['agent_id'] = agent_id
        if memory_type:
            payload['memory_type'] = memory_type
        
        response = await self._request('POST', '/api/v1/memories/search', json=payload)
        
        results = []
        for item in response.json():
            results.append(SearchResult(
                memory=self._parse_memory(item['memory']),
                score=item['score'],
                highlights=item.get('highlights', []),
            ))
        
        return results
    
    # Importance Updates
    
    async def boost_importance(self, memory_id: str, boost: float = 0.1) -> Memory:
        """Boost memory importance (called on access)."""
        response = await self._request(
            'POST',
            f'/api/v1/memories/{memory_id}/boost',
            json={'boost': boost}
        )
        return self._parse_memory(response.json())
    
    async def decay_importance(
        self,
        tenant_id: str,
        decay_rate: float = 0.01,
    ) -> int:
        """Apply decay to all memories (background job)."""
        response = await self._request(
            'POST',
            '/api/v1/memories/decay',
            json={'tenant_id': tenant_id, 'decay_rate': decay_rate}
        )
        return response.json().get('affected', 0)
    
    # Consolidation
    
    async def consolidate(
        self,
        tenant_id: str,
        agent_id: str,
        threshold: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Consolidate similar memories.
        
        Merges memories that are semantically very similar.
        """
        response = await self._request(
            'POST',
            '/api/v1/memories/consolidate',
            json={
                'tenant_id': tenant_id,
                'agent_id': agent_id,
                'threshold': threshold,
            }
        )
        return response.json()
    
    # Health Check
    
    async def health(self) -> Dict[str, Any]:
        """Check SomaBrain health."""
        response = await self._request('GET', '/health')
        return response.json()
    
    # Helpers
    
    def _parse_memory(self, data: Dict[str, Any]) -> Memory:
        """Parse memory from API response."""
        return Memory(
            id=data['id'],
            tenant_id=data['tenant_id'],
            agent_id=data['agent_id'],
            content=data['content'],
            memory_type=data.get('memory_type', 'episodic'),
            importance=data.get('importance', 0.5),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            last_accessed=datetime.fromisoformat(data['last_accessed'].replace('Z', '+00:00')) if data.get('last_accessed') else None,
            access_count=data.get('access_count', 0),
        )


# Singleton instance
somabrain_client = SomaBrainClient()
