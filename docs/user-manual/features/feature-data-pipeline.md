# Feature: Data Pipeline

## Overview
The SomaAgent01 data pipeline handles real-time data propagation through Kubernetes & Kafka infrastructure.

## Key Components
- Kafka event bus for message streaming
- Redis for caching and session state
- PostgreSQL for durable storage
- SomaBrain for memory and recall

## Data Flow
1. User input → Gateway
2. Gateway → Conversation Worker
3. Worker → LLM Provider (via Gateway)
4. Worker → SomaBrain (memory persistence)
5. Response → User (via SSE stream)

## Configuration
See [Technical Manual - Architecture](../../technical-manual/architecture.md) for detailed configuration options.

## Monitoring
Pipeline metrics are exposed via Prometheus at the Gateway metrics endpoint.
