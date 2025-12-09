# Configuration

This document outlines the configuration options for the Agent Zero application, including environment variables and Pydantic settings.

## Environment Variables

Environment variables are used to configure the application at a high level. They are typically defined in a `.env` file in the root of the repository.

### Memory Configuration (`.env.memory`)

The `.env.memory` file defines memory limits for the various services in the Docker Compose setup. These are particularly useful for development environments to prevent services from consuming too many resources.

| Variable | Description |
|---|---|
| `KAFKA_HEAP_OPTS` | JVM heap options for Kafka. |
| `KAFKA_MEM_LIMIT` | The maximum amount of memory Kafka can use. |
| `KAFKA_MEM_RESERVATION` | The amount of memory reserved for Kafka. |
| `REDIS_MEM_LIMIT` | The maximum amount of memory Redis can use. |
| `REDIS_MEM_RESERVATION` | The amount of memory reserved for Redis. |
| `POSTGRES_MEM_LIMIT` | The maximum amount of memory PostgreSQL can use. |
| `POSTGRES_MEM_RESERVATION` | The amount of memory reserved for PostgreSQL. |
| `POSTGRES_SHARED_BUFFERS` | The amount of memory to be used for shared memory buffers by PostgreSQL. |
| `GATEWAY_MEM_LIMIT` | The maximum amount of memory the Gateway service can use. |
| `GATEWAY_MEM_RESERVATION` | The amount of memory reserved for the Gateway service. |
| `CONVERSATION_WORKER_MEM_LIMIT` | The maximum amount of memory the Conversation Worker can use. |
| `CONVERSATION_WORKER_MEM_RESERVATION` | The amount of memory reserved for the Conversation Worker. |
| `TOOL_EXECUTOR_MEM_LIMIT` | The maximum amount of memory the Tool Executor can use. |
| `TOOL_EXECUTOR_MEM_RESERVATION` | The amount of memory reserved for the Tool Executor. |
| `MEMORY_REPLICATOR_MEM_LIMIT` | The maximum amount of memory the Memory Replicator can use. |
| `MEMORY_REPLICATOR_MEM_RESERVATION` | The amount of memory reserved for the Memory Replicator. |
| `MEMORY_SYNC_MEM_LIMIT` | The maximum amount of memory the Memory Sync service can use. |
| `MEMORY_SYNC_MEM_RESERVATION` | The amount of memory reserved for the Memory Sync service. |
| `OUTBOX_SYNC_MEM_LIMIT` | The maximum amount of memory the Outbox Sync service can use. |
| `OUTBOX_SYNC_MEM_RESERVATION` | The amount of memory reserved for the Outbox Sync service. |
| `JAVA_OPTS` | Default JVM options for services running on the JVM. |

## Pydantic Settings

The Agent Zero application uses Pydantic for settings management. The main settings are defined in the `python/helpers/settings.py` and `python/helpers/settings_model.py` files. These settings can be overridden by environment variables.
