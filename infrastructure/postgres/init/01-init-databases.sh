#!/bin/sh
# PostgreSQL Multi-Database Initialization
# Creates additional databases for SomaStack services
#
# VIBE COMPLIANT: Real initialization script

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create additional databases
    CREATE DATABASE somabrain;
    CREATE DATABASE somamemory;
    
    -- Create event store tables with partitioning
    \c somaagent
    
    -- Agent events table (partitioned by month)
    -- Note: Primary key includes created_at for partitioning  
    CREATE TABLE IF NOT EXISTS agent_events (
        id UUID DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        event_type VARCHAR(100) NOT NULL,
        aggregate_id UUID NOT NULL,
        aggregate_type VARCHAR(100) NOT NULL,
        payload JSONB NOT NULL DEFAULT '{}',
        metadata JSONB DEFAULT '{}',
        version INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (id, created_at)
    ) PARTITION BY RANGE (created_at);
    
    -- Create partitions for current and next month
    CREATE TABLE IF NOT EXISTS agent_events_2024_12 PARTITION OF agent_events
        FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');
    CREATE TABLE IF NOT EXISTS agent_events_2025_01 PARTITION OF agent_events
        FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    
    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_agent_events_tenant ON agent_events(tenant_id);
    CREATE INDEX IF NOT EXISTS idx_agent_events_aggregate ON agent_events(aggregate_type, aggregate_id);
    
    -- Run receipts table for AgentIQ
    CREATE TABLE IF NOT EXISTS run_receipts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        conversation_id UUID NOT NULL,
        run_id VARCHAR(100) NOT NULL,
        model VARCHAR(100) NOT NULL,
        provider VARCHAR(50) NOT NULL,
        input_tokens INTEGER NOT NULL DEFAULT 0,
        output_tokens INTEGER NOT NULL DEFAULT 0,
        total_tokens INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
        latency_ms INTEGER NOT NULL,
        cost_usd DECIMAL(10, 6),
        status VARCHAR(20) NOT NULL DEFAULT 'success',
        error_message TEXT,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_run_receipts_tenant ON run_receipts(tenant_id);
    CREATE INDEX IF NOT EXISTS idx_run_receipts_conversation ON run_receipts(conversation_id);
    
    -- Grant permissions
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
    
    -- Setup somabrain
    \c somabrain
    
    CREATE TABLE IF NOT EXISTS memories (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        agent_id UUID NOT NULL,
        content TEXT NOT NULL,
        memory_type VARCHAR(50) NOT NULL DEFAULT 'episodic',
        importance FLOAT NOT NULL DEFAULT 0.5,
        last_accessed TIMESTAMPTZ DEFAULT NOW(),
        access_count INTEGER DEFAULT 0,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_memories_tenant ON memories(tenant_id);
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
    
    -- Setup somamemory
    \c somamemory
    
    CREATE TABLE IF NOT EXISTS fractal_nodes (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        parent_id UUID,
        node_type VARCHAR(50) NOT NULL,
        content TEXT,
        depth INTEGER NOT NULL DEFAULT 0,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_fractal_tenant ON fractal_nodes(tenant_id);
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
EOSQL

echo "PostgreSQL initialization complete!"
