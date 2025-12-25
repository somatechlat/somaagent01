"""SomaBrain PyFlink SQL Jobs.

VIBE COMPLIANT - PyFlink SQL for processing agent events.
Processes Kafka events and persists to SomaBrain.

Architecture:
    Kafka → Flink → PostgreSQL/SomaBrain

7-Persona Implementation:
- PhD Dev: Stream processing theory
- DevOps: Flink job configuration
- ML Eng: Learning signal aggregation
"""

# =============================================================================
# FLINK SQL JOB DEFINITIONS
# =============================================================================

# Job 1: Agent Act Aggregation
AGENT_ACT_AGGREGATION_JOB = """
-- Agent Act Aggregation Job
-- Tumbling window: 1 minute
-- Aggregates all agent actions for cognitive learning

CREATE TABLE agent_acts (
    event_id STRING,
    timestamp TIMESTAMP(3),
    tenant_id STRING,
    agent_id STRING,
    user_id STRING,
    session_id STRING,
    input_text STRING,
    output_text STRING,
    salience DOUBLE,
    latency_ms DOUBLE,
    model_used STRING,
    degraded BOOLEAN,
    event_time AS timestamp,
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'soma.agent.act',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json',
    'scan.startup.mode' = 'latest-offset'
);

CREATE TABLE agent_act_metrics (
    tenant_id STRING,
    agent_id STRING,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    total_acts BIGINT,
    avg_salience DOUBLE,
    avg_latency_ms DOUBLE,
    degraded_count BIGINT,
    PRIMARY KEY (tenant_id, agent_id, window_start) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/somaagent',
    'table-name' = 'flink_agent_act_metrics',
    'driver' = 'org.postgresql.Driver'
);

INSERT INTO agent_act_metrics
SELECT
    tenant_id,
    agent_id,
    TUMBLE_START(event_time, INTERVAL '1' MINUTE) AS window_start,
    TUMBLE_END(event_time, INTERVAL '1' MINUTE) AS window_end,
    COUNT(*) AS total_acts,
    AVG(salience) AS avg_salience,
    AVG(latency_ms) AS avg_latency_ms,
    SUM(CASE WHEN degraded THEN 1 ELSE 0 END) AS degraded_count
FROM agent_acts
GROUP BY tenant_id, agent_id, TUMBLE(event_time, INTERVAL '1' MINUTE);
"""

# Job 2: Memory Queue Processing
MEMORY_QUEUE_JOB = """
-- Memory Queue Processing Job
-- Processes queued memories when SomaBrain is available

CREATE TABLE memory_queue (
    event_id STRING,
    timestamp TIMESTAMP(3),
    tenant_id STRING,
    agent_id STRING,
    user_id STRING,
    memory_type STRING,
    content STRING,
    metadata STRING,
    queued BOOLEAN,
    synced_to_brain BOOLEAN,
    event_time AS timestamp,
    WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'soma.memory.queue',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json',
    'scan.startup.mode' = 'earliest-offset'
);

-- Output to SomaBrain API (via HTTP sink or JDBC)
CREATE TABLE pending_memories (
    event_id STRING,
    tenant_id STRING,
    agent_id STRING,
    memory_type STRING,
    content STRING,
    queued_at TIMESTAMP(3),
    PRIMARY KEY (event_id) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/somaagent',
    'table-name' = 'flink_pending_memories',
    'driver' = 'org.postgresql.Driver'
);

INSERT INTO pending_memories
SELECT
    event_id,
    tenant_id,
    agent_id,
    memory_type,
    content,
    event_time AS queued_at
FROM memory_queue
WHERE queued = TRUE AND synced_to_brain = FALSE;
"""

# Job 3: Neuromodulator State Tracking
NEUROMODULATOR_TRACKING_JOB = """
-- Neuromodulator State Tracking Job
-- Tracks brain state changes for learning optimization

CREATE TABLE neuromodulator_events (
    event_id STRING,
    timestamp TIMESTAMP(3),
    tenant_id STRING,
    agent_id STRING,
    dopamine DOUBLE,
    serotonin DOUBLE,
    norepinephrine DOUBLE,
    acetylcholine DOUBLE,
    gaba DOUBLE,
    glutamate DOUBLE,
    event_time AS timestamp,
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'soma.neuromodulators.state',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
);

CREATE TABLE neuromodulator_trends (
    tenant_id STRING,
    agent_id STRING,
    window_start TIMESTAMP(3),
    avg_dopamine DOUBLE,
    avg_serotonin DOUBLE,
    avg_acetylcholine DOUBLE,
    dopamine_variance DOUBLE,
    PRIMARY KEY (tenant_id, agent_id, window_start) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/somaagent',
    'table-name' = 'flink_neuromodulator_trends',
    'driver' = 'org.postgresql.Driver'
);

INSERT INTO neuromodulator_trends
SELECT
    tenant_id,
    agent_id,
    TUMBLE_START(event_time, INTERVAL '5' MINUTE) AS window_start,
    AVG(dopamine) AS avg_dopamine,
    AVG(serotonin) AS avg_serotonin,
    AVG(acetylcholine) AS avg_acetylcholine,
    STDDEV(dopamine) AS dopamine_variance
FROM neuromodulator_events
GROUP BY tenant_id, agent_id, TUMBLE(event_time, INTERVAL '5' MINUTE);
"""

# Job 4: Salience Learning Signals
SALIENCE_LEARNING_JOB = """
-- Salience Learning Signals Job
-- Aggregates importance signals for cognitive optimization

CREATE TABLE salience_events (
    event_id STRING,
    timestamp TIMESTAMP(3),
    tenant_id STRING,
    agent_id STRING,
    salience DOUBLE,
    event_time AS timestamp,
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'soma.learning.salience',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
);

CREATE TABLE salience_aggregates (
    tenant_id STRING,
    agent_id STRING,
    window_start TIMESTAMP(3),
    avg_salience DOUBLE,
    max_salience DOUBLE,
    min_salience DOUBLE,
    salience_count BIGINT,
    PRIMARY KEY (tenant_id, agent_id, window_start) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/somaagent',
    'table-name' = 'flink_salience_aggregates',
    'driver' = 'org.postgresql.Driver'
);

INSERT INTO salience_aggregates
SELECT
    tenant_id,
    agent_id,
    TUMBLE_START(event_time, INTERVAL '1' HOUR) AS window_start,
    AVG(salience) AS avg_salience,
    MAX(salience) AS max_salience,
    MIN(salience) AS min_salience,
    COUNT(*) AS salience_count
FROM salience_events
GROUP BY tenant_id, agent_id, TUMBLE(event_time, INTERVAL '1' HOUR);
"""

# All jobs
SOMABRAIN_FLINK_JOBS = {
    "agent_act_aggregation": AGENT_ACT_AGGREGATION_JOB,
    "memory_queue": MEMORY_QUEUE_JOB,
    "neuromodulator_tracking": NEUROMODULATOR_TRACKING_JOB,
    "salience_learning": SALIENCE_LEARNING_JOB,
}
