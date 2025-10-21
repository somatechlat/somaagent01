# Environment files — how to use

This folder contains example environment files used as an environment contract for local development and shared infra.

- `.env.shared.example` — shared infra example. Copy to `infra/env/.env.shared` (or place values into your secrets manager) for local setups where multiple services communicate on specific ports.

Top-level `.env.example` in the repo root is a simpler, developer-focused template you can copy to `.env` in the repository root for a single-node local docker-compose run.

Usage:

1. Copy the example to a real env file locally:

```bash
cp .env.example .env
# or for shared infra
cp agent-zero/infra/env/.env.shared.example agent-zero/infra/env/.env.shared
```

2. Edit `.env` and fill in secrets (do NOT commit `.env`):

```bash
open .env    # or use your editor
# fill GROQ_API_KEY, OPENROUTER_API_KEY, AUTH_PASSWORD, etc.
```

3. Start the stack:

```bash
docker compose up -d
```

4. If you change the env file while containers are running, restart the services that need the new variables (gateway, conversation-worker):

```bash
docker compose restart gateway conversation-worker
```

Security:
- Never commit `.env` with real secrets. Use `.env.example` for placeholders and share real secrets via secured channels or secret stores.
