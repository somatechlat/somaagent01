"""Lago Billing API Client.

VIBE COMPLIANT - Async HTTP client for Lago API.
Per SAAS_ADMIN_SRS.md Section 5.1 - Billing Dashboard.

Lago API Docs: https://doc.getlago.com/api-reference/intro
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class LagoConfig:
    """Lago API configuration."""
    api_url: str = "http://localhost:3000/api/v1"
    api_key: str = ""
    
    @classmethod
    def from_settings(cls) -> "LagoConfig":
        """Load config from Django settings."""
        return cls(
            api_url=getattr(settings, "LAGO_API_URL", "http://localhost:3000/api/v1"),
            api_key=getattr(settings, "LAGO_API_KEY", ""),
        )


class LagoClient:
    """Async client for Lago billing API.
    
    VIBE COMPLIANT:
    - Full async support
    - Proper error handling
    - Typed responses
    """
    
    def __init__(self, config: Optional[LagoConfig] = None):
        self.config = config or LagoConfig.from_settings()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.api_url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    # =========================================================================
    # CUSTOMERS (Tenants)
    # =========================================================================
    
    async def create_customer(
        self,
        external_id: str,
        name: str,
        email: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a customer in Lago (maps to Tenant).
        
        Args:
            external_id: Tenant UUID from our database
            name: Company/tenant name
            email: Billing email
            metadata: Additional metadata
        """
        client = await self._get_client()
        
        payload = {
            "customer": {
                "external_id": external_id,
                "name": name,
                "email": email,
                "metadata": metadata or [],
            }
        }
        
        try:
            response = await client.post("/customers", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Lago create_customer failed: {e}")
            raise LagoError(f"Failed to create customer: {e}")
    
    async def get_customer(self, external_id: str) -> Optional[dict]:
        """Get customer by external ID."""
        client = await self._get_client()
        
        try:
            response = await client.get(f"/customers/{external_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Lago get_customer failed: {e}")
            return None
    
    async def update_customer(
        self,
        external_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> dict:
        """Update customer details."""
        client = await self._get_client()
        
        payload: dict[str, Any] = {"customer": {}}
        if name:
            payload["customer"]["name"] = name
        if email:
            payload["customer"]["email"] = email
        
        response = await client.put(f"/customers/{external_id}", json=payload)
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # SUBSCRIPTIONS
    # =========================================================================
    
    async def create_subscription(
        self,
        customer_external_id: str,
        plan_code: str,
        external_id: Optional[str] = None,
    ) -> dict:
        """Create a subscription for a customer.
        
        Args:
            customer_external_id: Tenant UUID
            plan_code: Lago plan code (e.g., 'pro', 'enterprise')
            external_id: Optional subscription ID
        """
        client = await self._get_client()
        
        payload = {
            "subscription": {
                "external_customer_id": customer_external_id,
                "plan_code": plan_code,
                "external_id": external_id or customer_external_id,
            }
        }
        
        try:
            response = await client.post("/subscriptions", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Lago create_subscription failed: {e}")
            raise LagoError(f"Failed to create subscription: {e}")
    
    async def terminate_subscription(self, external_id: str) -> dict:
        """Terminate a subscription."""
        client = await self._get_client()
        
        response = await client.delete(f"/subscriptions/{external_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_subscription(self, external_id: str) -> Optional[dict]:
        """Get subscription details."""
        client = await self._get_client()
        
        try:
            response = await client.get(f"/subscriptions/{external_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Lago get_subscription failed: {e}")
            return None
    
    # =========================================================================
    # USAGE / EVENTS
    # =========================================================================
    
    async def create_event(
        self,
        transaction_id: str,
        customer_external_id: str,
        code: str,
        properties: Optional[dict] = None,
        timestamp: Optional[datetime] = None,
    ) -> dict:
        """Create a billable event (usage metering).
        
        Args:
            transaction_id: Unique ID for idempotency
            customer_external_id: Tenant UUID
            code: Billable metric code (e.g., 'api_calls', 'tokens')
            properties: Event properties (e.g., {'tokens': 1000})
            timestamp: Event timestamp
        """
        client = await self._get_client()
        
        payload = {
            "event": {
                "transaction_id": transaction_id,
                "external_customer_id": customer_external_id,
                "code": code,
                "properties": properties or {},
                "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            }
        }
        
        try:
            response = await client.post("/events", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Lago create_event failed: {e}")
            raise LagoError(f"Failed to create event: {e}")
    
    async def batch_events(self, events: list[dict]) -> dict:
        """Create multiple events in a batch."""
        client = await self._get_client()
        
        payload = {"events": events}
        
        response = await client.post("/events/batch", json=payload)
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # INVOICES
    # =========================================================================
    
    async def list_invoices(
        self,
        customer_external_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """List invoices with optional filtering."""
        client = await self._get_client()
        
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if customer_external_id:
            params["external_customer_id"] = customer_external_id
        if status:
            params["status"] = status
        
        response = await client.get("/invoices", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_invoice(self, lago_id: str) -> Optional[dict]:
        """Get invoice by Lago ID."""
        client = await self._get_client()
        
        response = await client.get(f"/invoices/{lago_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    
    async def download_invoice(self, lago_id: str) -> bytes:
        """Download invoice PDF."""
        client = await self._get_client()
        
        response = await client.post(f"/invoices/{lago_id}/download")
        response.raise_for_status()
        return response.content
    
    # =========================================================================
    # PLANS
    # =========================================================================
    
    async def list_plans(self, page: int = 1, per_page: int = 20) -> dict:
        """List all billing plans."""
        client = await self._get_client()
        
        response = await client.get("/plans", params={"page": page, "per_page": per_page})
        response.raise_for_status()
        return response.json()
    
    async def get_plan(self, code: str) -> Optional[dict]:
        """Get plan by code."""
        client = await self._get_client()
        
        response = await client.get(f"/plans/{code}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()


class LagoError(Exception):
    """Lago API error."""
    pass


# Singleton instance
_lago_client: Optional[LagoClient] = None


def get_lago_client() -> LagoClient:
    """Get the Lago client singleton."""
    global _lago_client
    if _lago_client is None:
        _lago_client = LagoClient()
    return _lago_client
