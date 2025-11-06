# Quick Start Tutorial

This quick start gets you chatting with the agent on your local machine using a production-parity dev stack.

## Prerequisites

- Docker and Docker Compose v2
- Python 3.12 with virtualenv (optional for running tests locally)
- At least 8GB RAM for the stack

## Start the local stack

We run all core services (Kafka, Redis, Postgres, OPA) and the app services (Gateway, Conversation Worker, Tool Executor, Memory Replicator/Sync, Outbox Sync) with the correct profiles and ports.

1) Set the Gateway host port to 21016 and enable required profiles:

```
export GATEWAY_PORT=21016
docker compose --profile core --profile dev up -d
```

The UI will be available at: http://localhost:21016/ui/index.html

Notes:

- LLM/secrets are centralized in the Gateway; the Conversation Worker fetches credentials via an internal token.
- Attachments are stored in Postgres and referenced by ID; services fetch bytes via the internal endpoint.
- SomaBrain base URL is aligned to port 9696 for memory writes and WAL emission.

## Verify health

Open http://localhost:21016/v1/health and confirm component statuses are okay. If Kafka is still booting, give it ~30–60s.

## Configure the LLM (Groq by default)

1) Open Settings in the UI.
2) In the LLM Credentials section, select provider “groq” and paste your API key.
3) In the Model Profile section, set:
	- Model: `llama-3.1-8b-instant` (or another Groq model you have access to)
	- Base URL: `https://api.groq.com/openai/v1`
	- Temperature: `0.2`
4) Save. The Gateway will normalize and persist these values globally.

Verify from a terminal:
```bash
curl -s -X POST http://localhost:21016/v1/llm/test -H 'Content-Type: application/json' -d '{"role":"dialogue"}' | jq .
```

## Upload a file and send a message

1) In the UI, click the paperclip to upload a small text file. The UI posts to `/v1/uploads` and shows the file as an attachment.
2) Send a chat message and include the uploaded file if relevant. Small files are ingested inline.

## Run quick tests (optional)

- API smoke and gateway unit tests:

```
pytest -q tests/test_gateway_llm_audit.py
```

- Live E2E (requires running stack):

```
export GATEWAY_BASE_URL=http://localhost:21016
pytest -q tests/e2e/test_document_ingest_by_id.py
```

If you have Playwright installed and want to exercise the UI flow:

```
export GATEWAY_BASE_URL=http://localhost:21016
export E2E_LIVE=1
pytest -q tests/e2e/test_ui_chat_playwright.py
```

## Troubleshooting

- If the Gateway returns 5xx during first requests, Kafka metadata may still be warming up—retry once after ~10s.
- Ensure `GATEWAY_INTERNAL_TOKEN` is the same on Gateway and Worker/Tool containers (compose defaults to `dev-internal-token`).
- If `/v1/admin/memory` returns 401/403, your environment requires admin auth; E2E memory checks will be skipped.

**Standards**: ISO/IEC 29148§5.2

## Your First Conversation

### 1. Access the UI

Open your browser to: `http://localhost:21016/ui/index.html`

### 2. Login (if enabled)

If authentication is enabled, enter the password configured in `.env`. By default in local dev, auth is disabled.

### 3. Start a Conversation

Type in the chat input:
```
Hello! Can you help me understand what you can do?
```

**Expected**: The agent responds with its capabilities.

### 4. Execute Code

Try a simple task:
```
Create a Python script that prints the current date and time, then run it.
```

**Expected**: The agent writes Python code, executes it, and shows the output.

### 5. Use Memory

Ask the agent to remember something:
```
Remember that my favorite programming language is Python.
```

Then in a new session:
```
What's my favorite programming language?
```

**Expected**: The agent recalls the information from memory.

## Common Tasks

### File Operations

```
Create a file called test.txt with "Hello World" in it.
```

### Web Search

```
Search for the latest news about AI agents.
```

### Multi-Agent Delegation

```
I need to analyze a large dataset. Can you delegate this to a subordinate agent?
```

## Next Steps

- [Features Overview](./features.md)
- [FAQ](./faq.md)
- [Troubleshooting](./troubleshooting.md)
