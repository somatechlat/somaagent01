# MCP & A2A Interaction

This diagram shows how a client talks to the **MCP** (Model‑Context‑Protocol) and
**A2A** (Agent‑to‑Agent) servers that are part of the Agent‑Zero stack.  The flow
mirrors the implementation in `python/helpers/mcp_handler.py` and
`python/helpers/fasta2a_server.py`.

```mermaid
sequenceDiagram
    participant C as Client (e.g., another Agent)
    participant P as Proxy (MCP/A2A Server)
    participant S as Service (e.g., tool‑executor, capsule‑registry)
    participant DB as Postgres
    participant T as Token Store (runtime env)

    C->>P: HTTP request with Authorization header
    P->>T: validate token (create_auth_token())
    alt token valid
        P->>S: forward request (SSE/HTTP)
        S->>DB: optional DB lookup
        S-->>P: response payload
        P-->>C: stream / JSON response
    else token invalid
        P-->>C: 401 Unauthorized
    end
```

**Key points**
* Tokens are generated from the persistent runtime ID plus optional auth login
  credentials (`settings.py`).
* The proxy re‑configures itself at runtime (`DynamicMcpProxy`, `DynamicA2AProxy`).
* All requests pass through the same FastAPI gateway, keeping the network surface
  minimal.
