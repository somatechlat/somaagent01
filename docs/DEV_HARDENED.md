Dev‑Hardened Mode (near‑prod, local‑only)
========================================

Goals
- Mirror production auth/policy, memory pipeline, and metrics locally.
- Keep everything bound to localhost and safe for a single developer machine.
- Avoid env provider keys; use Gateway credentials store.

Quick Start
1) Copy env template and generate an admin JWT
   cp .env.devh.example .env.devh
   export $(grep -v '^#' .env.devh | xargs -I{} echo {})
   python3 scripts/gen_devh_jwt.py > /tmp/devh.jwt
   sed -i '' "s|^DEVH_ADMIN_JWT=.*|DEVH_ADMIN_JWT=$(cat /tmp/devh.jwt)|" .env.devh

2) Bring up the stack (local‑only binds)
   docker compose -f docker-compose.yaml -f docker-compose.devh.yaml --env-file .env.devh --profile core --profile devh up -d

3) Store your LLM provider key via Gateway credentials (admin JWT)
   curl -sS -X POST \
     -H "Authorization: Bearer $(cat /tmp/devh.jwt)" \
     -H 'Content-Type: application/json' \
     http://localhost:${GATEWAY_PORT:-20016}/v1/llm/credentials \
     -d '{"provider":"groq","secret":"REPLACE_WITH_YOUR_KEY"}'

4) Open the UI and chat
   open http://localhost:${AGENT_UI_PORT:-20015}/

5) Run Playwright smoke locally
   export RUN_PLAYWRIGHT=1
   export AGENT_UI_URL=http://127.0.0.1:${AGENT_UI_PORT:-20015}/
   pytest -q tests/playwright/test_ui_smoke.py

What’s Enabled
- Gateway auth required (HS256 JWT via header or cookie).
- OPA available; start in monitor (default) and flip to enforce by setting OPA policy URL/decision path.
- Write‑through to SomaBrain with WAL fallback and replica.
- Export jobs (async) with local file output.
- Full Prometheus metrics for Gateway/Replicator/OutboxSync.

Safety & Cleanup
- All ports are bound to 127.0.0.1.
- Volumes are local; to reset, stop and prune volumes as needed.

