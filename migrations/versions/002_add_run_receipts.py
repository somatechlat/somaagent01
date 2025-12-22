"""Add run_receipts table for AgentIQ Governor audit records.

Revision ID: 002
Revises: 001
Create Date: 2025-12-21

Creates run_receipts table for persisting AgentIQ RunReceipt records.
Table stores AIQ scores, lane budgets, degradation levels, and confidence
per turn for audit, analytics, and debugging.

This migration is idempotent - safe to run multiple times.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create run_receipts table with indexes."""
    conn = op.get_bind()

    # =========================================================================
    # ENUM TYPE: path_mode
    # =========================================================================
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE path_mode AS ENUM ('fast', 'rescue');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    # =========================================================================
    # ENUM TYPE: degradation_level
    # =========================================================================
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE degradation_level AS ENUM ('L0', 'L1', 'L2', 'L3', 'L4');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    # =========================================================================
    # TABLE: run_receipts
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS run_receipts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            turn_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            capsule_id TEXT,
            aiq_pred REAL NOT NULL CHECK (aiq_pred >= 0.0 AND aiq_pred <= 100.0),
            aiq_obs REAL NOT NULL CHECK (aiq_obs >= 0.0 AND aiq_obs <= 100.0),
            confidence REAL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
            lane_budgets JSONB NOT NULL DEFAULT '{}'::jsonb,
            lane_actual JSONB NOT NULL DEFAULT '{}'::jsonb,
            degradation_level TEXT NOT NULL DEFAULT 'L0',
            path_mode TEXT NOT NULL DEFAULT 'fast',
            tool_k INTEGER NOT NULL DEFAULT 5 CHECK (tool_k >= 0),
            latency_ms REAL NOT NULL CHECK (latency_ms >= 0),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """))

    # =========================================================================
    # INDEXES: run_receipts
    # =========================================================================
    # Primary query patterns: by session, by tenant, by time range
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_run_receipts_session 
        ON run_receipts(session_id, created_at DESC);
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_run_receipts_tenant 
        ON run_receipts(tenant_id, created_at DESC);
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_run_receipts_degradation 
        ON run_receipts(degradation_level) 
        WHERE degradation_level != 'L0';
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_run_receipts_path_mode 
        ON run_receipts(path_mode) 
        WHERE path_mode = 'rescue';
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_run_receipts_created 
        ON run_receipts(created_at DESC);
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_run_receipts_capsule 
        ON run_receipts(capsule_id) 
        WHERE capsule_id IS NOT NULL;
    """))

    # GIN index for JSONB lane queries
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_run_receipts_lane_budgets 
        ON run_receipts USING GIN(lane_budgets);
    """))

    # =========================================================================
    # TABLE COMMENT
    # =========================================================================
    conn.execute(sa.text("""
        COMMENT ON TABLE run_receipts IS 
        'AgentIQ Governor audit records: AIQ scores, lane budgets, degradation, and confidence per turn';
    """))


def downgrade() -> None:
    """Drop run_receipts table and related types."""
    conn = op.get_bind()

    # Drop table
    conn.execute(sa.text("DROP TABLE IF EXISTS run_receipts CASCADE;"))

    # Drop enum types
    conn.execute(sa.text("DROP TYPE IF EXISTS degradation_level;"))
    conn.execute(sa.text("DROP TYPE IF EXISTS path_mode;"))
