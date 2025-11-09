# Config Registry Plan

## Intent
Centralize runtime configuration with validation, layering, and safe rollouts.

## Interface
- `ConfigRegistry(schema)`: holds a validated snapshot (`version`, `checksum`, `payload`).
- `load_defaults(payload)`: initialize from defaults (files/env-derived), validates against schema.
- `apply_update(payload)`: validate and apply remote update; notifies subscribers.
- `subscribe(callback)`: receive applied snapshots.
- `build_ack(result, error=None)`: helper to emit ack events (published by caller).

## Schema
- JSON Schema at `schemas/config/registry.v1.schema.json` defines overlays for `uploads`, `antivirus`, `speech`, plus `secrets` (reference keys) and `feature_flags`.

## Transport & Rollout
- Publisher: gateway admin tool or CI job posts config to topic `config_updates`.
- Consumer: gateway `_config_update_listener` parses event and calls `ConfigRegistry.apply_update` then publishes ack to `config_updates.ack`.
- Rollback: re-publish prior `version` snapshot.

## Metrics
- `config_update_apply_total{result}`: ok|rejected|error.
- `config_update_version_info`: gauge label for current version.

## Next Steps
1. Wire `ConfigRegistry` into gateway startup; store at `app.state.config_registry`.
2. Expand schema as more overlays are standardized (rate limit, realtime, tools).
3. Add admin endpoint `POST /v1/admin/config/apply` (authz guarded) to trigger updates in dev.
