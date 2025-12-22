"""Add agent_skins table for AgentSkin UIX theme storage.

Revision ID: 003
Revises: 002
Create Date: 2025-12-21

Creates agent_skins table for storing theme definitions with JSONB variables.
Supports multi-tenant isolation and admin approval workflow.

This migration is idempotent - safe to run multiple times.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create agent_skins table with indexes."""
    conn = op.get_bind()

    # =========================================================================
    # TABLE: agent_skins
    # =========================================================================
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS agent_skins (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            name TEXT NOT NULL CHECK (char_length(name) <= 50),
            description TEXT CHECK (char_length(description) <= 200),
            version TEXT NOT NULL CHECK (version ~ '^[0-9]+\\.[0-9]+\\.[0-9]+$'),
            author TEXT CHECK (char_length(author) <= 100),
            variables JSONB NOT NULL DEFAULT '{}'::jsonb,
            changelog JSONB DEFAULT '[]'::jsonb,
            is_approved BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_skins_tenant_name UNIQUE (tenant_id, name)
        );
    """))

    # =========================================================================
    # INDEXES: agent_skins
    # =========================================================================
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_skins_tenant 
        ON agent_skins(tenant_id);
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_skins_approved 
        ON agent_skins(is_approved) 
        WHERE is_approved = TRUE;
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_skins_name 
        ON agent_skins(name);
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_skins_created 
        ON agent_skins(created_at DESC);
    """))

    # GIN index for JSONB variable queries
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_skins_variables 
        ON agent_skins USING GIN(variables);
    """))

    # =========================================================================
    # TRIGGER: updated_at auto-update
    # =========================================================================
    conn.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_agent_skins_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TRIGGER trigger_skins_updated_at
            BEFORE UPDATE ON agent_skins
            FOR EACH ROW EXECUTE FUNCTION update_agent_skins_updated_at();
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    # =========================================================================
    # TABLE COMMENT
    # =========================================================================
    conn.execute(sa.text("""
        COMMENT ON TABLE agent_skins IS 
        'AgentSkin UIX theme definitions with JSONB CSS variables';
    """))

    # =========================================================================
    # SEED DATA: Default themes
    # =========================================================================
    conn.execute(sa.text("""
        INSERT INTO agent_skins (tenant_id, name, description, version, author, variables, is_approved)
        SELECT
            '00000000-0000-0000-0000-000000000000'::uuid,
            'default',
            'Default light theme',
            '1.0.0',
            'SomaTech',
            '{
                "--bg-void": "#fcfcfc",
                "--glass-surface": "rgba(255, 255, 255, 0.95)",
                "--glass-border": "rgba(0, 0, 0, 0.04)",
                "--text-main": "#334155",
                "--text-dim": "#94a3b8",
                "--accent-slate": "#64748b"
            }'::jsonb,
            TRUE
        WHERE NOT EXISTS (SELECT 1 FROM agent_skins WHERE name = 'default');
    """))

    conn.execute(sa.text("""
        INSERT INTO agent_skins (tenant_id, name, description, version, author, variables, is_approved)
        SELECT
            '00000000-0000-0000-0000-000000000000'::uuid,
            'midnight',
            'Dark midnight theme',
            '1.0.0',
            'SomaTech',
            '{
                "--bg-void": "#0f172a",
                "--glass-surface": "rgba(30, 41, 59, 0.85)",
                "--glass-border": "rgba(255, 255, 255, 0.05)",
                "--text-main": "#e2e8f0",
                "--text-dim": "#64748b",
                "--accent-slate": "#94a3b8"
            }'::jsonb,
            TRUE
        WHERE NOT EXISTS (SELECT 1 FROM agent_skins WHERE name = 'midnight');
    """))


def downgrade() -> None:
    """Drop agent_skins table and related objects."""
    conn = op.get_bind()

    # Drop trigger
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trigger_skins_updated_at ON agent_skins;"))
    conn.execute(sa.text("DROP FUNCTION IF EXISTS update_agent_skins_updated_at();"))

    # Drop table
    conn.execute(sa.text("DROP TABLE IF EXISTS agent_skins CASCADE;"))
