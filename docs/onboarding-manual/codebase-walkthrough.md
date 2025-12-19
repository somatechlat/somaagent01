# Codebase Walkthrough

## Overview
This document provides a guided tour through the SomaAgent01 codebase.

## Directory Structure
See [Project Context](./project-context.md) for the complete structure.

## Key Files
- `services/gateway/main.py` - API gateway entry point
- `services/conversation_worker/main.py` - Message processing worker
- `python/integrations/somabrain_client.py` - SomaBrain HTTP client
- `webui/index.html` - Main UI entry point

## Code Flow
1. User sends message via UI
2. Gateway receives POST `/v1/sessions/message`
3. Message published to Kafka
4. Conversation worker processes message
5. LLM invoked via Gateway
6. Response streamed back via SSE

## Next Steps
- [First Contribution](./first-contribution.md)
- [Team Collaboration](./team-collaboration.md)
