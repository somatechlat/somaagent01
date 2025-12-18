-- Multimodal Outcomes Storage (Phase 6: Learning & Ranking)
-- Purpose: Store execution outcomes for SomaBrain learning system
-- Author: SomaAgent01 Development Team
-- Date: 2025-12-17
-- Feature Flag: SA01_ENABLE_multimodal_capabilities

-- ============================================================================
-- TABLE: multimodal_outcomes
-- Stores execution outcomes for learning and portfolio ranking
-- ============================================================================

CREATE TABLE IF NOT EXISTS multimodal_outcomes (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Correlation IDs
    plan_id UUID NOT NULL,
    task_id TEXT NOT NULL,
    
    -- Execution context
    step_type TEXT NOT NULL,                 -- e.g., 'generate_image', 'create_diagram'
    provider TEXT NOT NULL,                  -- e.g., 'openai', 'local'
    model TEXT NOT NULL,                     -- e.g., 'dall-e-3', 'mermaid-cli'
    
    -- Outcome metrics
    success BOOLEAN NOT NULL,
    latency_ms REAL NOT NULL,                -- Execution duration in milliseconds
    cost_cents REAL NOT NULL DEFAULT 0.0,    -- Estimated cost in cents
    
    -- Quality assessment
    quality_score REAL,                      -- 0.0 to 1.0 from AssetCritic
    feedback TEXT,                           -- Critic feedback or error details
    
    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Indexes for efficient querying
    CONSTRAINT chk_latency_positive CHECK (latency_ms >= 0),
    CONSTRAINT chk_cost_positive CHECK (cost_cents >= 0),
    CONSTRAINT chk_quality_range CHECK (quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0))
);

-- Indexes for efficient queries by PortfolioRanker
CREATE INDEX IF NOT EXISTS idx_mm_outcomes_step_type ON multimodal_outcomes(step_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mm_outcomes_provider ON multimodal_outcomes(provider, success);
CREATE INDEX IF NOT EXISTS idx_mm_outcomes_plan ON multimodal_outcomes(plan_id);
CREATE INDEX IF NOT EXISTS idx_mm_outcomes_timestamp ON multimodal_outcomes(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mm_outcomes_success ON multimodal_outcomes(success, step_type);

-- Comment
COMMENT ON TABLE multimodal_outcomes IS 'Execution outcomes for SomaBrain learning system (Phase 6: Learning & Ranking)';
