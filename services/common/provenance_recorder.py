"""Provenance Recorder for multimodal asset audit trails.

Records the generation context and lineage for each asset, including
prompt summaries, tool/model used, trace IDs, and quality gate results.
Supports redaction policies for sensitive information.

SRS Reference: Section 16.4.2 (Provenance System)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg

from src.core.config import cfg

__all__ = [
    "ProvenanceRecord",
    "ProvenanceRecorder",
    "RedactionPolicy",
]

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RedactionPolicy:
    """Policy for redacting sensitive information from provenance records.
    
    Attributes:
        redact_prompt: Whether to redact prompt content
        redact_params: Whether to redact generation parameters
        redact_patterns: Regex patterns to redact (e.g., API keys, emails)
        max_prompt_length: Maximum prompt summary length (chars)
    """
    redact_prompt: bool = False
    redact_params: bool = False
    redact_patterns: List[str] = field(default_factory=list)
    max_prompt_length: int = 500

    # Default patterns for common sensitive data
    DEFAULT_PATTERNS = [
        r'\bsk-[a-zA-Z0-9]{20,}\b',  # OpenAI API keys (sk- followed by 20+ alphanumeric)
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b(?:\d{4}[- ]?){3}\d{4}\b',  # Credit card numbers
    ]


@dataclass(slots=True)
class ProvenanceRecord:
    """Provenance record linking an asset to its generation context.
    
    Provides a complete audit trail for reproducibility and compliance.
    
    Attributes:
        asset_id: UUID of the asset this provenance belongs to
        tenant_id: Tenant that owns the asset
        request_id: Original request correlation ID
        execution_id: UUID of the multimodal_execution record
        plan_id: UUID of the job plan (if part of a plan)
        session_id: Session where asset was generated
        user_id: User who initiated the request
        prompt_summary: Redacted/summarized prompt
        generation_params: Model parameters used (may be redacted)
        tool_id: Tool used to generate
        provider: Provider of the tool
        model_version: Specific model version if applicable
        trace_id: OpenTelemetry trace ID
        span_id: OpenTelemetry span ID
        quality_gate_passed: Whether quality gate was passed
        quality_score: Final quality score (0.0-1.0)
        rework_count: Number of rework attempts
        created_at: Record creation timestamp
    """
    asset_id: UUID
    tenant_id: str
    tool_id: str
    provider: str
    request_id: Optional[str] = None
    execution_id: Optional[UUID] = None
    plan_id: Optional[UUID] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    prompt_summary: Optional[str] = None
    generation_params: Dict[str, Any] = field(default_factory=dict)
    model_version: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    quality_gate_passed: Optional[bool] = None
    quality_score: Optional[float] = None
    rework_count: int = 0
    created_at: Optional[datetime] = None


class ProvenanceRecorder:
    """Records and retrieves provenance information for multimodal assets.
    
    Provides audit trail functionality with optional redaction of sensitive
    information based on configured policies.
    
    Usage:
        recorder = ProvenanceRecorder()
        
        # Record provenance for a generated asset
        await recorder.record(
            asset_id=asset.id,
            tenant_id="acme-corp",
            tool_id="dalle3_image_gen",
            provider="openai",
            prompt_summary="Generate a logo for...",
            generation_params={"size": "1024x1024"},
            trace_id="abc123",
        )
        
        # Retrieve provenance
        prov = await recorder.get(asset_id)
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        redaction_policy: Optional[RedactionPolicy] = None,
    ) -> None:
        """Initialize recorder with database and redaction policy.
        
        Args:
            dsn: PostgreSQL connection string. Defaults to config value.
            redaction_policy: Policy for redacting sensitive info. Defaults to standard.
        """
        self._dsn = dsn or cfg.settings().database.dsn
        self._policy = redaction_policy or RedactionPolicy()

    async def ensure_schema(self) -> None:
        """Verify the asset_provenance table exists.
        
        Raises RuntimeError if table doesn't exist.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'asset_provenance'
                )
            """)
            if not exists:
                raise RuntimeError(
                    "asset_provenance table does not exist. "
                    "Run migration 017_multimodal_schema.sql."
                )
        finally:
            await conn.close()

    async def record(
        self,
        asset_id: UUID,
        tenant_id: str,
        tool_id: str,
        provider: str,
        request_id: Optional[str] = None,
        execution_id: Optional[UUID] = None,
        plan_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        prompt_summary: Optional[str] = None,
        generation_params: Optional[Dict[str, Any]] = None,
        model_version: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        quality_gate_passed: Optional[bool] = None,
        quality_score: Optional[float] = None,
        rework_count: int = 0,
    ) -> ProvenanceRecord:
        """Record provenance for an asset.
        
        Applies redaction policy before storing.
        
        Args:
            asset_id: UUID of the asset
            tenant_id: Owning tenant
            tool_id: Tool used for generation
            provider: Provider of the tool
            request_id: Correlation ID for the request
            execution_id: Execution record ID
            plan_id: Job plan ID (if applicable)
            session_id: Session ID
            user_id: User who initiated request
            prompt_summary: Summary of the prompt (will be redacted)
            generation_params: Model parameters (will be redacted)
            model_version: Model version string
            trace_id: OpenTelemetry trace ID
            span_id: OpenTelemetry span ID
            quality_gate_passed: Quality gate result
            quality_score: Quality score (0.0-1.0)
            rework_count: Number of rework attempts
            
        Returns:
            ProvenanceRecord with the stored data
        """
        # Apply redaction policy
        redacted_prompt = self._redact_prompt(prompt_summary)
        redacted_params = self._redact_params(generation_params or {})
        
        conn = await asyncpg.connect(self._dsn)
        try:
            import json
            
            await conn.execute("""
                INSERT INTO asset_provenance (
                    asset_id, tenant_id, request_id, execution_id, plan_id,
                    session_id, user_id, prompt_summary, generation_params,
                    tool_id, provider, model_version, trace_id, span_id,
                    quality_gate_passed, quality_score, rework_count
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
                )
                ON CONFLICT (asset_id) DO UPDATE SET
                    quality_gate_passed = EXCLUDED.quality_gate_passed,
                    quality_score = EXCLUDED.quality_score,
                    rework_count = EXCLUDED.rework_count
            """,
                asset_id,
                tenant_id,
                request_id,
                execution_id,
                plan_id,
                session_id,
                user_id,
                redacted_prompt,
                json.dumps(redacted_params),
                tool_id,
                provider,
                model_version,
                trace_id,
                span_id,
                quality_gate_passed,
                quality_score,
                rework_count,
            )
            
            logger.info(
                "Recorded provenance for asset %s (tool=%s/%s)",
                asset_id, tool_id, provider
            )
            
            return ProvenanceRecord(
                asset_id=asset_id,
                tenant_id=tenant_id,
                request_id=request_id,
                execution_id=execution_id,
                plan_id=plan_id,
                session_id=session_id,
                user_id=user_id,
                prompt_summary=redacted_prompt,
                generation_params=redacted_params,
                tool_id=tool_id,
                provider=provider,
                model_version=model_version,
                trace_id=trace_id,
                span_id=span_id,
                quality_gate_passed=quality_gate_passed,
                quality_score=quality_score,
                rework_count=rework_count,
                created_at=datetime.now(),
            )
        finally:
            await conn.close()

    async def get(self, asset_id: UUID) -> Optional[ProvenanceRecord]:
        """Retrieve provenance for an asset.
        
        Args:
            asset_id: UUID of the asset
            
        Returns:
            ProvenanceRecord if found, None otherwise
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                "SELECT * FROM asset_provenance WHERE asset_id = $1",
                asset_id,
            )
            
            if not row:
                return None
            
            return self._row_to_record(row)
        finally:
            await conn.close()

    async def list_by_tool(
        self,
        tenant_id: str,
        tool_id: str,
        provider: str,
        limit: int = 100,
    ) -> List[ProvenanceRecord]:
        """List provenance records for a specific tool/provider.
        
        Useful for analyzing tool usage patterns.
        
        Args:
            tenant_id: Tenant to query
            tool_id: Tool ID to filter by
            provider: Provider to filter by
            limit: Maximum results
            
        Returns:
            List of ProvenanceRecord
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            rows = await conn.fetch("""
                SELECT * FROM asset_provenance 
                WHERE tenant_id = $1 AND tool_id = $2 AND provider = $3
                ORDER BY created_at DESC
                LIMIT $4
            """,
                tenant_id, tool_id, provider, limit,
            )
            
            return [self._row_to_record(r) for r in rows]
        finally:
            await conn.close()

    async def list_by_trace(
        self,
        trace_id: str,
    ) -> List[ProvenanceRecord]:
        """List all provenance records for a trace.
        
        Useful for debugging distributed operations.
        
        Args:
            trace_id: OpenTelemetry trace ID
            
        Returns:
            List of ProvenanceRecord
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            rows = await conn.fetch(
                "SELECT * FROM asset_provenance WHERE trace_id = $1 ORDER BY created_at",
                trace_id,
            )
            
            return [self._row_to_record(r) for r in rows]
        finally:
            await conn.close()

    async def update_quality(
        self,
        asset_id: UUID,
        quality_gate_passed: bool,
        quality_score: float,
        rework_count: int,
    ) -> bool:
        """Update quality gate results for a provenance record.
        
        Called after AssetCritic evaluation.
        
        Args:
            asset_id: UUID of the asset
            quality_gate_passed: Whether quality check passed
            quality_score: Score from 0.0 to 1.0
            rework_count: Number of rework attempts
            
        Returns:
            True if updated, False if not found
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute("""
                UPDATE asset_provenance
                SET quality_gate_passed = $2,
                    quality_score = $3,
                    rework_count = $4
                WHERE asset_id = $1
            """,
                asset_id, quality_gate_passed, quality_score, rework_count,
            )
            
            _, count_str = result.split(" ")
            return int(count_str) > 0
        finally:
            await conn.close()

    def _redact_prompt(self, prompt: Optional[str]) -> Optional[str]:
        """Apply redaction policy to prompt summary.
        
        Args:
            prompt: Original prompt text
            
        Returns:
            Redacted prompt or None
        """
        if prompt is None:
            return None
        
        if self._policy.redact_prompt:
            return "[REDACTED]"
        
        # Truncate to max length
        if len(prompt) > self._policy.max_prompt_length:
            prompt = prompt[:self._policy.max_prompt_length] + "..."
        
        # Apply pattern-based redaction
        prompt = self._apply_patterns(prompt)
        
        return prompt

    def _redact_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply redaction policy to generation parameters.
        
        Args:
            params: Original parameters
            
        Returns:
            Redacted parameters
        """
        if self._policy.redact_params:
            return {"redacted": True}
        
        # Deep copy and redact sensitive keys
        import copy
        result = copy.deepcopy(params)
        
        sensitive_keys = {"api_key", "secret", "token", "password", "credential"}
        
        def redact_dict(d: dict) -> None:
            for key in list(d.keys()):
                if any(s in key.lower() for s in sensitive_keys):
                    d[key] = "[REDACTED]"
                elif isinstance(d[key], dict):
                    redact_dict(d[key])
                elif isinstance(d[key], str):
                    d[key] = self._apply_patterns(d[key])
        
        redact_dict(result)
        return result

    def _apply_patterns(self, text: str) -> str:
        """Apply regex patterns to redact sensitive data.
        
        Args:
            text: Text to process
            
        Returns:
            Text with patterns redacted
        """
        patterns = self._policy.redact_patterns or RedactionPolicy.DEFAULT_PATTERNS
        
        for pattern in patterns:
            text = re.sub(pattern, "[REDACTED]", text)
        
        return text

    def _row_to_record(self, row: asyncpg.Record) -> ProvenanceRecord:
        """Convert database row to ProvenanceRecord.
        
        Args:
            row: asyncpg Record from query
            
        Returns:
            ProvenanceRecord instance
        """
        import json
        
        generation_params = {}
        if row.get("generation_params"):
            generation_params = json.loads(row["generation_params"])
        
        return ProvenanceRecord(
            asset_id=row["asset_id"],
            tenant_id=row["tenant_id"],
            request_id=row.get("request_id"),
            execution_id=row.get("execution_id"),
            plan_id=row.get("plan_id"),
            session_id=row.get("session_id"),
            user_id=row.get("user_id"),
            prompt_summary=row.get("prompt_summary"),
            generation_params=generation_params,
            tool_id=row["tool_id"],
            provider=row["provider"],
            model_version=row.get("model_version"),
            trace_id=row.get("trace_id"),
            span_id=row.get("span_id"),
            quality_gate_passed=row.get("quality_gate_passed"),
            quality_score=row.get("quality_score"),
            rework_count=row.get("rework_count") or 0,
            created_at=row.get("created_at"),
        )
