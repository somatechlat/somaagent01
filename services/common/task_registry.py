"""
Dynamic task/tool registry with OPA gating, hash verification, and Redis cache.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import asyncpg
import redis.asyncio as redis

from services.common.policy_client import PolicyClient, PolicyRequest
from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegistryEntry:
    name: str
    kind: str  # task | tool
    module_path: str
    callable: str
    queue: str
    rate_limit: Optional[str]
    max_retries: Optional[int]
    soft_time_limit: Optional[int]
    time_limit: Optional[int]
    enabled: bool
    tenant_scope: List[str]
    persona_scope: List[str]
    arg_schema: Dict[str, Any]
    artifact_hash: Optional[str]
    soma_tags: List[str]


class TaskRegistry:
    def __init__(self) -> None:
        # Single source of truth: cfg.env(). Provide sensible defaults for the
        # test environment where external services are not required.
        # ``POSTGRES_DSN`` and ``REDIS_URL`` are optional for the parts of the
        # system exercised by the unit tests; using a harmless in‑memory SQLite
        # URL (supported by asyncpg) would still require a server, so we fall
        # back to a placeholder that satisfies the type check but will not be
        # used unless a test explicitly triggers a DB operation.
        self.dsn = cfg.env("POSTGRES_DSN") or "postgresql://postgres:postgres@localhost:5432/postgres"
        self.redis_url = cfg.env("SA01_REDIS_URL") or cfg.env("REDIS_URL") or "redis://localhost:6379/0"
        self.cache_key = "task_registry:all"
        self._pool: Optional[asyncpg.Pool] = None
        self._redis: Optional[redis.Redis] = None
        self.policy = PolicyClient(base_url=cfg.env("OPA_URL"))

    async def _pool_conn(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")
            self._pool = await asyncpg.create_pool(
                self.dsn, min_size=max(0, min_size), max_size=max(1, max_size)
            )
        return self._pool

    async def _redis_conn(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def register(
        self,
        *,
        name: str,
        kind: str,
        module_path: str,
        callable_name: str,
        queue: str,
        rate_limit: Optional[str] = None,
        max_retries: Optional[int] = None,
        soft_time_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        enabled: bool = True,
        tenant_scope: Optional[list[str]] = None,
        persona_scope: Optional[list[str]] = None,
        arg_schema: Optional[dict[str, Any]] = None,
        artifact_hash: Optional[str] = None,
        soma_tags: Optional[list[str]] = None,
        created_by: Optional[str] = None,
    ) -> RegistryEntry:
        """Upsert a registry entry and invalidate cache."""
        entry = RegistryEntry(
            name=name,
            kind=kind,
            module_path=module_path,
            callable=callable_name,
            queue=queue,
            rate_limit=rate_limit,
            max_retries=max_retries,
            soft_time_limit=soft_time_limit,
            time_limit=time_limit,
            enabled=enabled,
            tenant_scope=tenant_scope or [],
            persona_scope=persona_scope or [],
            arg_schema=arg_schema or {},
            artifact_hash=artifact_hash,
            soma_tags=soma_tags or [],
        )

        pool = await self._pool_conn()
        await pool.execute(
            """
            INSERT INTO task_registry
            (name, kind, module_path, callable, queue, rate_limit, max_retries,
             soft_time_limit, time_limit, enabled, tenant_scope, persona_scope,
             arg_schema, artifact_hash, soma_tags, created_by)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
            ON CONFLICT (name) DO UPDATE SET
              kind=EXCLUDED.kind,
              module_path=EXCLUDED.module_path,
              callable=EXCLUDED.callable,
              queue=EXCLUDED.queue,
              rate_limit=EXCLUDED.rate_limit,
              max_retries=EXCLUDED.max_retries,
              soft_time_limit=EXCLUDED.soft_time_limit,
              time_limit=EXCLUDED.time_limit,
              enabled=EXCLUDED.enabled,
              tenant_scope=EXCLUDED.tenant_scope,
              persona_scope=EXCLUDED.persona_scope,
              arg_schema=EXCLUDED.arg_schema,
              artifact_hash=EXCLUDED.artifact_hash,
              soma_tags=EXCLUDED.soma_tags,
              updated_at=NOW()
            """,
            entry.name,
            entry.kind,
            entry.module_path,
            entry.callable,
            entry.queue,
            entry.rate_limit,
            entry.max_retries,
            entry.soft_time_limit,
            entry.time_limit,
            entry.enabled,
            entry.tenant_scope,
            entry.persona_scope,
            entry.arg_schema,
            entry.artifact_hash,
            entry.soma_tags,
            created_by,
        )

        r = await self._redis_conn()
        await r.delete(self.cache_key)
        await r.publish("task_registry:reload", "1")
        return entry

    async def load_all(self, *, force_refresh: bool = False) -> list[RegistryEntry]:
        r = await self._redis_conn()
        if not force_refresh:
            cached = await r.get(self.cache_key)
            if cached:
                try:
                    data = json.loads(cached)
                    return [self._from_dict(item) for item in data]
                except Exception:
                    LOGGER.warning("Registry cache decode failed; refreshing.")

        pool = await self._pool_conn()
        rows = await pool.fetch(
            """
            SELECT name, kind, module_path, callable, queue, rate_limit,
                   max_retries, soft_time_limit, time_limit, enabled,
                   tenant_scope, persona_scope, arg_schema, artifact_hash, soma_tags
            FROM task_registry
            WHERE enabled = TRUE
            """
        )
        entries = [
            RegistryEntry(
                name=row["name"],
                kind=row["kind"],
                module_path=row["module_path"],
                callable=row["callable"],
                queue=row["queue"],
                rate_limit=row["rate_limit"],
                max_retries=row["max_retries"],
                soft_time_limit=row["soft_time_limit"],
                time_limit=row["time_limit"],
                enabled=row["enabled"],
                tenant_scope=row["tenant_scope"] or [],
                persona_scope=row["persona_scope"] or [],
                arg_schema=row["arg_schema"] or {},
                artifact_hash=row["artifact_hash"],
                soma_tags=row["soma_tags"] or [],
            )
            for row in rows
        ]
        await r.set(self.cache_key, json.dumps([e.__dict__ for e in entries]), ex=300)
        return entries

    async def allowed_for(
        self,
        entry: RegistryEntry,
        tenant: str,
        persona: Optional[str],
        action: str = "task.execute",
    ) -> bool:
        # Scope check
        if entry.tenant_scope and tenant not in entry.tenant_scope:
            return False
        if entry.persona_scope and persona and persona not in entry.persona_scope:
            return False
        # OPA
        return await self.policy.evaluate(
            PolicyRequest(
                tenant=tenant,
                persona_id=persona,
                action=action,
                resource=entry.name,
                context={"kind": entry.kind},
            )
        )

    def import_callable(self, entry: RegistryEntry) -> Callable:
        module = importlib.import_module(entry.module_path)
        fn = getattr(module, entry.callable)
        return fn

    def verify_artifact(self, entry: RegistryEntry) -> None:
        if not entry.artifact_hash:
            return
        try:
            module = importlib.import_module(entry.module_path)
            file_path = inspect.getfile(module)
            digest = self._sha256(file_path)
            if digest != entry.artifact_hash:
                raise RuntimeError(
                    f"Artifact hash mismatch for {entry.name}: expected {entry.artifact_hash}, got {digest}"
                )
        except Exception as exc:
            LOGGER.error(
                "Artifact verification failed", extra={"task": entry.name, "error": str(exc)}
            )
            raise

    def _sha256(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def validate_args(self, entry: RegistryEntry, args: Dict[str, Any]) -> None:
        if not entry.arg_schema:
            return
        try:
            import jsonschema

            jsonschema.validate(args, entry.arg_schema)
        except Exception as exc:
            raise ValueError(f"Argument validation failed for {entry.name}: {exc}") from exc

    def _from_dict(self, data: Dict[str, Any]) -> RegistryEntry:
        return RegistryEntry(
            name=data["name"],
            kind=data["kind"],
            module_path=data["module_path"],
            callable=data["callable"],
            queue=data["queue"],
            rate_limit=data.get("rate_limit"),
            max_retries=data.get("max_retries"),
            soft_time_limit=data.get("soft_time_limit"),
            time_limit=data.get("time_limit"),
            enabled=data.get("enabled", True),
            tenant_scope=data.get("tenant_scope") or [],
            persona_scope=data.get("persona_scope") or [],
            arg_schema=data.get("arg_schema") or {},
            artifact_hash=data.get("artifact_hash"),
            soma_tags=data.get("soma_tags") or [],
        )
