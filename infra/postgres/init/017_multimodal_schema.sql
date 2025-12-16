-- Multimodal Extension Schema (SRS §16)
-- Purpose: Foundation tables for multimodal capabilities (image/video/diagram generation)
-- Author: SomaAgent01 Development Team
-- Date: 2025-12-16
-- Feature Flag: SA01_ENABLE_multimodal_capabilities

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE asset_type AS ENUM ('image', 'video', 'diagram', 'screenshot', 'document');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE execution_status AS ENUM ('pending', 'running', 'success', 'failed', 'skipped');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE capability_health AS ENUM ('healthy', 'degraded', 'unavailable');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE cost_tier AS ENUM ('free', 'low', 'medium', 'high', 'premium');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- TABLE 1: multimodal_assets
-- Stores generated assets (images, videos, diagrams, screenshots)
-- ============================================================================

CREATE TABLE IF NOT EXISTS multimodal_assets (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    session_id TEXT,
    
    -- Asset Classification
    asset_type asset_type NOT NULL,
    format TEXT NOT NULL,                    -- e.g., 'png', 'svg', 'mp4', 'webp'
    
    -- Storage (PostgreSQL bytea for v1, S3 path for v2)
    storage_path TEXT,                       -- S3/MinIO path when external storage enabled
    content BYTEA,                           -- Inline storage for small assets (<10MB)
    content_size_bytes BIGINT NOT NULL DEFAULT 0,
    
    -- Integrity
    checksum_sha256 TEXT NOT NULL,           -- For deduplication and verification
    
    -- Metadata
    original_filename TEXT,
    mime_type TEXT NOT NULL,                 -- e.g., 'image/png', 'video/mp4'
    dimensions JSONB,                        -- e.g., {"width": 1024, "height": 768}
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,                  -- For retention policy enforcement
    
    -- Constraints
    CONSTRAINT chk_storage_location CHECK (
        storage_path IS NOT NULL OR content IS NOT NULL
    )
);

-- Indexes for multimodal_assets
CREATE INDEX IF NOT EXISTS idx_mm_assets_tenant ON multimodal_assets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mm_assets_type ON multimodal_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_mm_assets_session ON multimodal_assets(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mm_assets_checksum ON multimodal_assets(checksum_sha256);
CREATE INDEX IF NOT EXISTS idx_mm_assets_created ON multimodal_assets(created_at);
CREATE INDEX IF NOT EXISTS idx_mm_assets_expires ON multimodal_assets(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- TABLE 2: multimodal_capabilities
-- Registry of tools/models with modality metadata for capability discovery
-- ============================================================================

CREATE TABLE IF NOT EXISTS multimodal_capabilities (
    -- Identity (composite primary key)
    tool_id TEXT NOT NULL,                   -- e.g., 'dalle3_image_gen', 'mermaid_diagram'
    provider TEXT NOT NULL,                  -- e.g., 'openai', 'stability', 'local'
    
    -- Tenant scoping (NULL = global/system capability)
    tenant_id TEXT,
    
    -- Modality Support
    modalities JSONB NOT NULL DEFAULT '[]'::jsonb,  -- e.g., ["image", "vision"]
    
    -- Schema definitions (JSON Schema format)
    input_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Constraints and limits
    constraints JSONB NOT NULL DEFAULT '{}'::jsonb, -- e.g., {"max_resolution": 1792, "formats": ["png", "jpg"]}
    
    -- Cost and performance
    cost_tier cost_tier NOT NULL DEFAULT 'medium',
    latency_p95_ms INTEGER,                  -- Expected P95 latency in milliseconds
    
    -- Health tracking (for circuit breaker integration)
    health_status capability_health NOT NULL DEFAULT 'healthy',
    last_health_check TIMESTAMPTZ,
    failure_count INTEGER NOT NULL DEFAULT 0,
    
    -- Feature flags and toggles
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Metadata
    display_name TEXT,
    description TEXT,
    documentation_url TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Primary key
    PRIMARY KEY (tool_id, provider)
);

-- Indexes for multimodal_capabilities
CREATE INDEX IF NOT EXISTS idx_mm_caps_tenant ON multimodal_capabilities(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mm_caps_modalities ON multimodal_capabilities USING GIN(modalities);
CREATE INDEX IF NOT EXISTS idx_mm_caps_health ON multimodal_capabilities(health_status);
CREATE INDEX IF NOT EXISTS idx_mm_caps_enabled ON multimodal_capabilities(enabled) WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_mm_caps_cost ON multimodal_capabilities(cost_tier);

-- ============================================================================
-- TABLE 3: multimodal_job_plans
-- Stores Task DSL plans for multimodal workflows
-- ============================================================================

CREATE TABLE IF NOT EXISTS multimodal_job_plans (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    request_id TEXT,                         -- Original request correlation ID
    
    -- Plan content (Task DSL v1.0)
    plan_json JSONB NOT NULL,                -- Full Task DSL document
    plan_version TEXT NOT NULL DEFAULT '1.0',
    
    -- Status tracking
    status job_status NOT NULL DEFAULT 'pending',
    total_steps INTEGER NOT NULL DEFAULT 0,
    completed_steps INTEGER NOT NULL DEFAULT 0,
    
    -- Budget tracking
    budget_limit_cents INTEGER,              -- Maximum spend allowed
    budget_used_cents INTEGER NOT NULL DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Error tracking
    error_message TEXT,
    error_details JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for multimodal_job_plans
CREATE INDEX IF NOT EXISTS idx_mm_plans_tenant ON multimodal_job_plans(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mm_plans_session ON multimodal_job_plans(session_id);
CREATE INDEX IF NOT EXISTS idx_mm_plans_status ON multimodal_job_plans(status);
CREATE INDEX IF NOT EXISTS idx_mm_plans_created ON multimodal_job_plans(created_at);
CREATE INDEX IF NOT EXISTS idx_mm_plans_tenant_status ON multimodal_job_plans(tenant_id, status, created_at);

-- ============================================================================
-- TABLE 4: multimodal_executions
-- Execution history per plan step (for observability and learning)
-- ============================================================================

CREATE TABLE IF NOT EXISTS multimodal_executions (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES multimodal_job_plans(id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,             -- 0-based step index in plan
    
    -- Execution context
    tenant_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    
    -- Status
    status execution_status NOT NULL DEFAULT 'pending',
    attempt_number INTEGER NOT NULL DEFAULT 1,
    
    -- Results
    asset_id UUID REFERENCES multimodal_assets(id) ON DELETE SET NULL,
    
    -- Performance metrics
    latency_ms INTEGER,
    cost_estimate_cents INTEGER,
    
    -- Quality metrics (for AssetCritic feedback)
    quality_score REAL,                      -- 0.0 to 1.0
    quality_feedback JSONB,                  -- Critic's detailed feedback
    
    -- Error tracking
    error_code TEXT,
    error_message TEXT,
    
    -- Fallback tracking
    fallback_reason TEXT,                    -- Why this provider was chosen (fallback ladder)
    original_provider TEXT,                  -- Original provider before fallback
    
    -- Timestamps
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Unique constraint per step attempt
    CONSTRAINT uq_execution_step_attempt UNIQUE (plan_id, step_index, attempt_number)
);

-- Indexes for multimodal_executions
CREATE INDEX IF NOT EXISTS idx_mm_exec_plan ON multimodal_executions(plan_id);
CREATE INDEX IF NOT EXISTS idx_mm_exec_tenant ON multimodal_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mm_exec_status ON multimodal_executions(status);
CREATE INDEX IF NOT EXISTS idx_mm_exec_tool ON multimodal_executions(tool_id, provider);
CREATE INDEX IF NOT EXISTS idx_mm_exec_tenant_status ON multimodal_executions(tenant_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_mm_exec_quality ON multimodal_executions(quality_score) WHERE quality_score IS NOT NULL;

-- ============================================================================
-- TABLE 5: asset_provenance
-- Audit trail linking assets to their generation context
-- ============================================================================

CREATE TABLE IF NOT EXISTS asset_provenance (
    -- Identity (foreign key to asset)
    asset_id UUID PRIMARY KEY REFERENCES multimodal_assets(id) ON DELETE CASCADE,
    
    -- Correlation IDs
    request_id TEXT,
    execution_id UUID REFERENCES multimodal_executions(id) ON DELETE SET NULL,
    plan_id UUID REFERENCES multimodal_job_plans(id) ON DELETE SET NULL,
    
    -- User context
    user_id TEXT,
    tenant_id TEXT NOT NULL,
    session_id TEXT,
    
    -- Generation context (for reproducibility)
    prompt_summary TEXT,                     -- Redacted/summarized prompt (no PII)
    generation_params JSONB NOT NULL DEFAULT '{}'::jsonb,  -- Model params used
    
    -- Tool/model used
    tool_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_version TEXT,
    
    -- Tracing
    trace_id TEXT,                           -- OpenTelemetry trace ID
    span_id TEXT,                            -- OpenTelemetry span ID
    
    -- Quality gate results
    quality_gate_passed BOOLEAN,
    quality_score REAL,
    rework_count INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for asset_provenance
CREATE INDEX IF NOT EXISTS idx_prov_tenant ON asset_provenance(tenant_id);
CREATE INDEX IF NOT EXISTS idx_prov_user ON asset_provenance(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_prov_request ON asset_provenance(request_id) WHERE request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_prov_execution ON asset_provenance(execution_id) WHERE execution_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_prov_tool ON asset_provenance(tool_id, provider);
CREATE INDEX IF NOT EXISTS idx_prov_trace ON asset_provenance(trace_id) WHERE trace_id IS NOT NULL;

-- ============================================================================
-- TRIGGERS: Auto-update updated_at timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION multimodal_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS mm_capabilities_set_updated_at ON multimodal_capabilities;
CREATE TRIGGER mm_capabilities_set_updated_at
BEFORE UPDATE ON multimodal_capabilities
FOR EACH ROW EXECUTE FUNCTION multimodal_touch_updated_at();

DROP TRIGGER IF EXISTS mm_job_plans_set_updated_at ON multimodal_job_plans;
CREATE TRIGGER mm_job_plans_set_updated_at
BEFORE UPDATE ON multimodal_job_plans
FOR EACH ROW EXECUTE FUNCTION multimodal_touch_updated_at();

-- ============================================================================
-- SEED DATA: Register built-in capabilities
-- ============================================================================

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

-- ============================================================================
-- COMMENTS: Table documentation
-- ============================================================================

COMMENT ON TABLE multimodal_assets IS 'Stores generated multimodal assets (images, diagrams, videos, screenshots) with content or S3 reference';
COMMENT ON TABLE multimodal_capabilities IS 'Registry of available multimodal tools/models with modality, cost, and health metadata';
COMMENT ON TABLE multimodal_job_plans IS 'Task DSL plans for multimodal workflows with status and budget tracking';
COMMENT ON TABLE multimodal_executions IS 'Execution history per plan step for observability, learning, and fallback tracking';
COMMENT ON TABLE asset_provenance IS 'Audit trail linking assets to generation context for reproducibility and compliance';
