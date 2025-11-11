CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS session_embeddings (
    id              BIGSERIAL PRIMARY KEY,
    session_id      UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    text            TEXT NOT NULL,
    vector          VECTOR(384),      -- 384-dim OpenAI small model
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(session_id, text)
);

CREATE INDEX IF NOT EXISTS ix_session_embeddings_vector
    ON session_embeddings USING ivfflat (vector vector_cosine_ops)
    WITH (lists = 100);