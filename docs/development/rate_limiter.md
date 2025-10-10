# Rate Limiter

Agent‑Zero limits the number of requests and tokens sent to each LLM model.  The
logic lives in `python/helpers/rate_limiter.py` and is used by the chat, utility
and embedding models.

```mermaid
graph LR
    subgraph Config
        R1[chat_model_rl_requests]
        R2[chat_model_rl_input]
        R3[chat_model_rl_output]
        U1[util_model_rl_requests]
        U2[util_model_rl_input]
        U3[util_model_rl_output]
        E1[embed_model_rl_requests]
        E2[embed_model_rl_input]
    end

    R1 -->|rate limit| LLM1[Chat Model]
    R2 -->|token limit| LLM1
    R3 -->|token limit| LLM1
    U1 -->|rate limit| LLM2[Utility Model]
    U2 -->|token limit| LLM2
    U3 -->|token limit| LLM2
    E1 -->|rate limit| LLM3[Embedding Model]
    E2 -->|token limit| LLM3

    LLM1 -->|calls| API1[OpenAI / Azure / ...]
    LLM2 -->|calls| API2[OpenAI / Azure / ...]
    LLM3 -->|calls| API3[OpenAI / Azure / ...]
```

**How it works**
1. The `RateLimiter` object tracks a sliding‑window of timestamps for each
   limit type.
2. Before each LLM call the engine asks the limiter whether the request can
   proceed (`allow`).
3. If the limit is exceeded the request is delayed (`await asyncio.sleep`).
4. The UI displays a progress bar (`AgentContext.log.set_progress`).

All limits are configurable via the `settings.py` fields (`*_rl_requests`,
`*_rl_input`, `*_rl_output`).
