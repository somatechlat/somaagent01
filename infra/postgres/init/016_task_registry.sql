-- Task/Tool Registry schema (idempotent)
-- Purpose: enable runtime-registered tasks/tools with policy, safety, and observability metadata.

CREATE TABLE IF NOT EXISTS task_registry (
    name TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('task', 'tool')),
    module_path TEXT NOT NULL,
    callable TEXT NOT NULL,
    queue TEXT NOT NULL,
    rate_limit TEXT,
    max_retries INTEGER,
    soft_time_limit INTEGER,
    time_limit INTEGER,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    tenant_scope TEXT[] DEFAULT '{}',
    persona_scope TEXT[] DEFAULT '{}',
    arg_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    artifact_hash TEXT,
    soma_tags TEXT[] DEFAULT '{}',
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    storage_uri TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    signed_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT task_artifacts_unique UNIQUE (name, version)
);

CREATE OR REPLACE FUNCTION task_registry_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS task_registry_set_updated_at ON task_registry;
CREATE TRIGGER task_registry_set_updated_at
BEFORE UPDATE ON task_registry
FOR EACH ROW EXECUTE FUNCTION task_registry_touch_updated_at();

CREATE INDEX IF NOT EXISTS task_registry_enabled_idx ON task_registry (enabled);
CREATE INDEX IF NOT EXISTS task_registry_queue_idx ON task_registry (queue);
CREATE INDEX IF NOT EXISTS task_registry_kind_idx ON task_registry (kind);
