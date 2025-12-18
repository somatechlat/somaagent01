-- Migration: 018_prompts.sql
-- Description: Create prompts table for dynamic prompt management.

CREATE TABLE IF NOT EXISTS prompts (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    version INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed multimodal_critic prompt
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
