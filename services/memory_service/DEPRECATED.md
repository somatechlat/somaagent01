# Deprecated: gRPC Memory Service

This directory is retained temporarily for historical reference but is no longer used.

- All memory operations now use SomaBrain over HTTP on port 9696 via `python/integrations/soma_client.py`.
- Docker Compose services for `memory-service` have been removed.
- Helm deployment for `memoryService` is disabled by default.
- Code paths have been migrated off `services.common.memory_client`.

Action items before permanent deletion:
- Ensure no external consumers or downstream repos import these modules.
- Remove this directory in a follow-up cleanup PR once downstreams are updated.
