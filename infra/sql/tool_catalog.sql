-- S4 – Centralized tool catalog
CREATE TABLE IF NOT EXISTS tool_catalog (
    name                  TEXT PRIMARY KEY,
    description           TEXT NOT NULL,
    parameters_schema     JSONB NOT NULL,
    enabled               BOOLEAN DEFAULT TRUE,
    cost_impact           TEXT CHECK (cost_impact IN ('low','medium','high')) DEFAULT 'low',
    profiles              TEXT[] DEFAULT '{"standard"}',
    updated_at            TIMESTAMPTZ DEFAULT NOW()
);

-- Seed canonical tools
INSERT INTO tool_catalog (name, description, parameters_schema, cost_impact, profiles)
VALUES
('echo', 'Echoes input text back', '{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}', 'low', '{"standard","enhanced"}'),
('document_ingest', 'Extract text from uploaded document', '{"type":"object","properties":{"attachment_id":{"type":"string"}},"required":["attachment_id"]}', 'medium', '{"enhanced","max"}')
ON CONFLICT (name) DO NOTHING;

-- Tenant overrides (fail-closed)
CREATE TABLE IF NOT EXISTS tenant_tool_flags (
    tenant_id   TEXT NOT NULL,
    tool_name   TEXT NOT NULL REFERENCES tool_catalog(name) ON DELETE CASCADE,
    enabled     BOOLEAN NOT NULL,
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, tool_name)
);