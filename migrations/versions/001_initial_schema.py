"""Initial schema migration.

Creates all tables, ENUM types, indexes, triggers, and seed data
for SomaAgent01 database schema.

Revision ID: 001
Revises: None
Create Date: 2025-12-21

This migration is idempotent - safe to run multiple times.
All CREATE statements use IF NOT EXISTS.
All ENUM types use DO/EXCEPTION blocks.
All seed data uses ON CONFLICT DO NOTHING.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables, types, indexes, triggers, and seed data."""
    conn = op.get_bind()

    # =========================================================================
    # ENUM TYPES (idempotent with DO/EXCEPTION blocks)
    # =========================================================================
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE asset_type AS ENUM ('image', 'video', 'diagram', 'screenshot', 'document');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE execution_status AS ENUM ('pending', 'running', 'success', 'failed', 'skipped');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE capability_health AS ENUM ('healthy', 'degraded', 'unavailable');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE cost_tier AS ENUM ('free', 'low', 'medium', 'high', 'premium');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    # =========================================================================
    # EXTENSION: pgvector (for session_embeddings)
    # =========================================================================
    conn.execute(sa.text("""
        CREATE EXTENSION IF NOT EXISTS vector;
    """))

    # =========================================================================
    # TABLE 1: task_registry
    # =========================================================================
    conn.execute(sa.text("""
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
    """))

    # task_registry indexes
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS task_registry_enabled_idx ON task_registry (enabled);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS task_registry_queue_idx ON task_registry (queue);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS task_registry_kind_idx ON task_registry (kind);
    """))

    # =========================================================================
    # TABLE 2: task_artifacts
    # =========================================================================
    conn.execute(sa.text("""
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
    """))

    # =========================================================================
    # TABLE 3: tool_catalog
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS tool_catalog (
            name TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            parameters_schema JSONB NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            cost_impact TEXT CHECK (cost_impact IN ('low', 'medium', 'high')) DEFAULT 'low',
            profiles TEXT[] DEFAULT '{"standard"}',
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """))

    # =========================================================================
    # TABLE 4: tenant_tool_flags
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS tenant_tool_flags (
            tenant_id TEXT NOT NULL,
            tool_name TEXT NOT NULL REFERENCES tool_catalog(name) ON DELETE CASCADE,
            enabled BOOLEAN NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (tenant_id, tool_name)
        );
    """))

    # =========================================================================
    # TABLE 5: prompts
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prompts (
            id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            version INTEGER NOT NULL DEFAULT 1,
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """))

    # =========================================================================
    # TABLE 6: multimodal_assets
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS multimodal_assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id TEXT NOT NULL,
            session_id TEXT,
            asset_type asset_type NOT NULL,
            format TEXT NOT NULL,
            storage_path TEXT,
            content BYTEA,
            content_size_bytes BIGINT NOT NULL DEFAULT 0,
            checksum_sha256 TEXT NOT NULL,
            original_filename TEXT,
            mime_type TEXT NOT NULL,
            dimensions JSONB,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ,
            CONSTRAINT chk_storage_location CHECK (
                storage_path IS NOT NULL OR content IS NOT NULL
            )
        );
    """))

    # multimodal_assets indexes
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_assets_tenant ON multimodal_assets(tenant_id);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_assets_type ON multimodal_assets(asset_type);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_assets_session ON multimodal_assets(session_id) WHERE session_id IS NOT NULL;
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_assets_checksum ON multimodal_assets(checksum_sha256);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_assets_created ON multimodal_assets(created_at);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_assets_expires ON multimodal_assets(expires_at) WHERE expires_at IS NOT NULL;
    """))

    # =========================================================================
    # TABLE 7: multimodal_capabilities
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS multimodal_capabilities (
            tool_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            tenant_id TEXT,
            modalities JSONB NOT NULL DEFAULT '[]'::jsonb,
            input_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
            output_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
            constraints JSONB NOT NULL DEFAULT '{}'::jsonb,
            cost_tier cost_tier NOT NULL DEFAULT 'medium',
            latency_p95_ms INTEGER,
            health_status capability_health NOT NULL DEFAULT 'healthy',
            last_health_check TIMESTAMPTZ,
            failure_count INTEGER NOT NULL DEFAULT 0,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            display_name TEXT,
            description TEXT,
            documentation_url TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (tool_id, provider)
        );
    """))

    # multimodal_capabilities indexes
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_caps_tenant ON multimodal_capabilities(tenant_id) WHERE tenant_id IS NOT NULL;
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_caps_modalities ON multimodal_capabilities USING GIN(modalities);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_caps_health ON multimodal_capabilities(health_status);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_caps_enabled ON multimodal_capabilities(enabled) WHERE enabled = TRUE;
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_caps_cost ON multimodal_capabilities(cost_tier);
    """))

    # =========================================================================
    # TABLE 8: multimodal_job_plans
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS multimodal_job_plans (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            request_id TEXT,
            plan_json JSONB NOT NULL,
            plan_version TEXT NOT NULL DEFAULT '1.0',
            status job_status NOT NULL DEFAULT 'pending',
            total_steps INTEGER NOT NULL DEFAULT 0,
            completed_steps INTEGER NOT NULL DEFAULT 0,
            budget_limit_cents INTEGER,
            budget_used_cents INTEGER NOT NULL DEFAULT 0,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            error_message TEXT,
            error_details JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """))

    # multimodal_job_plans indexes
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_plans_tenant ON multimodal_job_plans(tenant_id);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_plans_session ON multimodal_job_plans(session_id);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_plans_status ON multimodal_job_plans(status);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_plans_created ON multimodal_job_plans(created_at);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_plans_tenant_status ON multimodal_job_plans(tenant_id, status, created_at);
    """))

    # =========================================================================
    # TABLE 9: multimodal_executions
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS multimodal_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id UUID NOT NULL REFERENCES multimodal_job_plans(id) ON DELETE CASCADE,
            step_index INTEGER NOT NULL,
            tenant_id TEXT NOT NULL,
            tool_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            status execution_status NOT NULL DEFAULT 'pending',
            attempt_number INTEGER NOT NULL DEFAULT 1,
            asset_id UUID REFERENCES multimodal_assets(id) ON DELETE SET NULL,
            latency_ms INTEGER,
            cost_estimate_cents INTEGER,
            quality_score REAL,
            quality_feedback JSONB,
            error_code TEXT,
            error_message TEXT,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_execution_step_attempt UNIQUE (plan_id, step_index, attempt_number)
        );
    """))

    # multimodal_executions indexes
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_exec_plan ON multimodal_executions(plan_id);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_exec_tenant ON multimodal_executions(tenant_id);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_exec_status ON multimodal_executions(status);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_exec_tool ON multimodal_executions(tool_id, provider);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_exec_tenant_status ON multimodal_executions(tenant_id, status, created_at);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_exec_quality ON multimodal_executions(quality_score) WHERE quality_score IS NOT NULL;
    """))

    # =========================================================================
    # TABLE 10: asset_provenance
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS asset_provenance (
            asset_id UUID PRIMARY KEY REFERENCES multimodal_assets(id) ON DELETE CASCADE,
            request_id TEXT,
            execution_id UUID REFERENCES multimodal_executions(id) ON DELETE SET NULL,
            plan_id UUID REFERENCES multimodal_job_plans(id) ON DELETE SET NULL,
            user_id TEXT,
            tenant_id TEXT NOT NULL,
            session_id TEXT,
            prompt_summary TEXT,
            generation_params JSONB NOT NULL DEFAULT '{}'::jsonb,
            tool_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            model_version TEXT,
            trace_id TEXT,
            span_id TEXT,
            quality_gate_passed BOOLEAN,
            quality_score REAL,
            rework_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """))

    # asset_provenance indexes
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_prov_tenant ON asset_provenance(tenant_id);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_prov_user ON asset_provenance(user_id) WHERE user_id IS NOT NULL;
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_prov_request ON asset_provenance(request_id) WHERE request_id IS NOT NULL;
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_prov_execution ON asset_provenance(execution_id) WHERE execution_id IS NOT NULL;
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_prov_tool ON asset_provenance(tool_id, provider);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_prov_trace ON asset_provenance(trace_id) WHERE trace_id IS NOT NULL;
    """))

    # =========================================================================
    # TABLE 11: multimodal_outcomes
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS multimodal_outcomes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id UUID NOT NULL,
            task_id TEXT NOT NULL,
            step_type TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            latency_ms REAL NOT NULL,
            cost_cents REAL NOT NULL DEFAULT 0.0,
            quality_score REAL,
            feedback TEXT,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT chk_latency_positive CHECK (latency_ms >= 0),
            CONSTRAINT chk_cost_positive CHECK (cost_cents >= 0),
            CONSTRAINT chk_quality_range CHECK (quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0))
        );
    """))

    # multimodal_outcomes indexes
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_outcomes_step_type ON multimodal_outcomes(step_type, timestamp DESC);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_outcomes_provider ON multimodal_outcomes(provider, success);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_outcomes_plan ON multimodal_outcomes(plan_id);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_outcomes_timestamp ON multimodal_outcomes(timestamp DESC);
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_mm_outcomes_success ON multimodal_outcomes(success, step_type);
    """))

    # =========================================================================
    # TABLE 12: session_embeddings
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS session_embeddings (
            id BIGSERIAL PRIMARY KEY,
            session_id UUID NOT NULL,
            text TEXT NOT NULL,
            vector VECTOR(384),
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT session_embeddings_session_text_key UNIQUE (session_id, text)
        );
    """))

    # session_embeddings ivfflat index (for similarity search)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS session_embeddings_vector_idx 
        ON session_embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
    """))

    # =========================================================================
    # TRIGGERS: Auto-update updated_at timestamps
    # =========================================================================
    conn.execute(sa.text("""
        CREATE OR REPLACE FUNCTION task_registry_touch_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    conn.execute(sa.text("""
        DROP TRIGGER IF EXISTS task_registry_set_updated_at ON task_registry;
    """))
    conn.execute(sa.text("""
        CREATE TRIGGER task_registry_set_updated_at
        BEFORE UPDATE ON task_registry
        FOR EACH ROW EXECUTE FUNCTION task_registry_touch_updated_at();
    """))

    conn.execute(sa.text("""
        CREATE OR REPLACE FUNCTION multimodal_touch_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    conn.execute(sa.text("""
        DROP TRIGGER IF EXISTS mm_capabilities_set_updated_at ON multimodal_capabilities;
    """))
    conn.execute(sa.text("""
        CREATE TRIGGER mm_capabilities_set_updated_at
        BEFORE UPDATE ON multimodal_capabilities
        FOR EACH ROW EXECUTE FUNCTION multimodal_touch_updated_at();
    """))

    conn.execute(sa.text("""
        DROP TRIGGER IF EXISTS mm_job_plans_set_updated_at ON multimodal_job_plans;
    """))
    conn.execute(sa.text("""
        CREATE TRIGGER mm_job_plans_set_updated_at
        BEFORE UPDATE ON multimodal_job_plans
        FOR EACH ROW EXECUTE FUNCTION multimodal_touch_updated_at();
    """))

    # =========================================================================
    # SEED DATA: tool_catalog
    # =========================================================================
    conn.execute(sa.text("""
        INSERT INTO tool_catalog (name, description, parameters_schema, cost_impact, profiles)
        VALUES
            ('echo', 'Echoes input text back', 
             '{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}', 
             'low', '{"standard","enhanced"}'),
            ('document_ingest', 'Extract text from uploaded document', 
             '{"type":"object","properties":{"attachment_id":{"type":"string"}},"required":["attachment_id"]}', 
             'medium', '{"enhanced","max"}')
        ON CONFLICT (name) DO NOTHING;
    """))

    # =========================================================================
    # SEED DATA: prompts
    # =========================================================================
    conn.execute(sa.text("""
        INSERT INTO prompts (id, name, version, content)
        VALUES (
            'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
            'multimodal_critic',
            1,
            'You are an expert design critic. Evaluate the provided image against these criteria:
{criteria}

Return JSON only: {{
  "pass": bool,
  "score": float(0.0-1.0),
  "feedback": "string"
}}'
        ) ON CONFLICT (name) DO NOTHING;
    """))

    # =========================================================================
    # SEED DATA: multimodal_capabilities
    # =========================================================================
    conn.execute(sa.text("""
        INSERT INTO multimodal_capabilities (
            tool_id, provider, modalities, cost_tier, health_status,
            display_name, description, constraints, input_schema, output_schema
        ) VALUES
            -- OpenAI DALL-E 3
            (
                'dalle3_image_gen', 'openai',
                '["image"]'::jsonb, 'high', 'healthy',
                'DALL-E 3 Image Generation', 'Generate images using OpenAI DALL-E 3',
                '{"max_resolution": 1792, "formats": ["png", "jpg"], "aspect_ratios": ["1:1", "16:9", "9:16"]}'::jsonb,
                '{"type": "object", "properties": {"prompt": {"type": "string"}, "size": {"type": "string"}, "quality": {"type": "string"}}}'::jsonb,
                '{"type": "object", "properties": {"url": {"type": "string"}, "revised_prompt": {"type": "string"}}}'::jsonb
            ),
            -- Mermaid Diagram (Local)
            (
                'mermaid_diagram', 'local',
                '["diagram"]'::jsonb, 'free', 'healthy',
                'Mermaid Diagram Renderer', 'Generate diagrams from Mermaid DSL using local mmdc CLI',
                '{"formats": ["svg", "png", "pdf"], "max_nodes": 100}'::jsonb,
                '{"type": "object", "properties": {"code": {"type": "string"}, "format": {"type": "string"}}}'::jsonb,
                '{"type": "object", "properties": {"svg": {"type": "string"}, "png_base64": {"type": "string"}}}'::jsonb
            ),
            -- PlantUML Diagram (Local)
            (
                'plantuml_diagram', 'local',
                '["diagram"]'::jsonb, 'free', 'healthy',
                'PlantUML Diagram Renderer', 'Generate UML diagrams from PlantUML syntax',
                '{"formats": ["svg", "png"], "max_complexity": "medium"}'::jsonb,
                '{"type": "object", "properties": {"code": {"type": "string"}, "format": {"type": "string"}}}'::jsonb,
                '{"type": "object", "properties": {"svg": {"type": "string"}, "png_base64": {"type": "string"}}}'::jsonb
            ),
            -- Playwright Screenshot (Local)
            (
                'playwright_screenshot', 'local',
                '["screenshot"]'::jsonb, 'low', 'healthy',
                'Playwright Screenshot Capture', 'Capture screenshots of web pages using Playwright',
                '{"formats": ["png", "jpg", "webp"], "max_resolution": 3840, "viewport_presets": ["desktop", "tablet", "mobile"]}'::jsonb,
                '{"type": "object", "properties": {"url": {"type": "string"}, "viewport": {"type": "object"}, "full_page": {"type": "boolean"}}}'::jsonb,
                '{"type": "object", "properties": {"screenshot_base64": {"type": "string"}, "viewport_used": {"type": "object"}}}'::jsonb
            ),
            -- Stability AI Image Generation
            (
                'stability_image_gen', 'stability',
                '["image"]'::jsonb, 'medium', 'healthy',
                'Stable Diffusion Image Generation', 'Generate images using Stability AI Stable Diffusion',
                '{"max_resolution": 1024, "formats": ["png", "jpg"], "models": ["sdxl", "sd3"]}'::jsonb,
                '{"type": "object", "properties": {"prompt": {"type": "string"}, "negative_prompt": {"type": "string"}, "width": {"type": "integer"}, "height": {"type": "integer"}}}'::jsonb,
                '{"type": "object", "properties": {"image_base64": {"type": "string"}, "seed": {"type": "integer"}}}'::jsonb
            )
        ON CONFLICT (tool_id, provider) DO UPDATE SET
            modalities = EXCLUDED.modalities,
            constraints = EXCLUDED.constraints,
            input_schema = EXCLUDED.input_schema,
            output_schema = EXCLUDED.output_schema,
            display_name = EXCLUDED.display_name,
            description = EXCLUDED.description,
            updated_at = NOW();
    """))

    # =========================================================================
    # TABLE COMMENTS
    # =========================================================================
    conn.execute(sa.text("""
        COMMENT ON TABLE task_registry IS 'Runtime-registered tasks/tools with policy and observability metadata';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE task_artifacts IS 'Versioned task artifacts with SHA256 checksums for verification';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE tool_catalog IS 'Centralized tool catalog with parameters schema and cost classification';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE tenant_tool_flags IS 'Per-tenant tool overrides with fail-closed semantics';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE prompts IS 'Dynamic prompt management with versioning';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE multimodal_assets IS 'Stores generated multimodal assets (images, diagrams, videos, screenshots) with content or S3 reference';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE multimodal_capabilities IS 'Registry of available multimodal tools/models with modality, cost, and health metadata';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE multimodal_job_plans IS 'Task DSL plans for multimodal workflows with status and budget tracking';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE multimodal_executions IS 'Execution history per plan step for observability and learning';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE asset_provenance IS 'Audit trail linking assets to generation context for reproducibility and compliance';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE multimodal_outcomes IS 'Execution outcomes for SomaBrain learning system (Phase 6: Learning & Ranking)';
    """))
    conn.execute(sa.text("""
        COMMENT ON TABLE session_embeddings IS 'Vector embeddings for session content with pgvector similarity search';
    """))


def downgrade() -> None:
    """Drop all tables, triggers, functions, and types in reverse FK order."""
    conn = op.get_bind()

    # =========================================================================
    # DROP TRIGGERS
    # =========================================================================
    conn.execute(sa.text("DROP TRIGGER IF EXISTS task_registry_set_updated_at ON task_registry;"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS mm_capabilities_set_updated_at ON multimodal_capabilities;"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS mm_job_plans_set_updated_at ON multimodal_job_plans;"))

    # =========================================================================
    # DROP FUNCTIONS
    # =========================================================================
    conn.execute(sa.text("DROP FUNCTION IF EXISTS task_registry_touch_updated_at();"))
    conn.execute(sa.text("DROP FUNCTION IF EXISTS multimodal_touch_updated_at();"))

    # =========================================================================
    # DROP TABLES (reverse FK order)
    # =========================================================================
    # Tables with no dependents first, then work up the FK chain
    conn.execute(sa.text("DROP TABLE IF EXISTS session_embeddings CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS multimodal_outcomes CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS asset_provenance CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS multimodal_executions CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS multimodal_job_plans CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS multimodal_capabilities CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS multimodal_assets CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS prompts CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS tenant_tool_flags CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS tool_catalog CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS task_artifacts CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS task_registry CASCADE;"))

    # =========================================================================
    # DROP ENUM TYPES
    # =========================================================================
    conn.execute(sa.text("DROP TYPE IF EXISTS cost_tier;"))
    conn.execute(sa.text("DROP TYPE IF EXISTS capability_health;"))
    conn.execute(sa.text("DROP TYPE IF EXISTS execution_status;"))
    conn.execute(sa.text("DROP TYPE IF EXISTS job_status;"))
    conn.execute(sa.text("DROP TYPE IF EXISTS asset_type;"))

    # Note: We don't drop the vector extension as it may be used by other schemas
