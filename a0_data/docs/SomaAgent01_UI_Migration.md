⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 UI Migration

`services/ui/main.py` serves the legacy Agent Zero `webui/` assets via FastAPI. This keeps the identical layout while we transition the backend to SomaAgent 01 services.

## How to run locally
```bash
uvicorn services.ui.main:app --port 8080 --reload
```
Then browse to `http://localhost:8080` — the familiar UI will load, but API calls should point to the gateway exposed on `http://localhost:8010` (see `docker-compose.somaagent01.yaml`, service `gateway`). Client code that talks to JSON APIs uses relative paths, so in most cases no change is required; verify your reverse proxy forwards `/v1/*` to the gateway.

The capsule marketplace script (`webui/js/marketplace.js`) already targets the versioned gateway surface (`/v1/capsules`, `/v1/capsules/{id}`, `/v1/capsules/{id}/install`). Override `CAPSULE_REGISTRY_URL` in the runtime environment if your registry runs on a different host/port.

## Next Steps
1. Wire quick action buttons, telemetry badges, voice controls, and requeue notifications to the new endpoints.
2. Replace remaining legacy Flask assumptions (CSRF/auth) with the gateway’s auth model.
3. Eventually relocate the static assets to a dedicated frontend build system once feature parity is achieved.
