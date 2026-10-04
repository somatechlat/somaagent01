# SOMA-RAPID-DEVELOPMENT-001 — Rapid Development Plan + The Rules

**Status:** ACTIVE. Every agent working on this triad reads this file first and obeys it.
**Owner standing order:** *"do not fucking violate the rules … feed the rules to every agent."*

---

## THE RAPID PLAN

**Done means:** `tests/e2e/test_human_chat_session.spec.js` passes in the UI, covering
**chatting, changing settings, creating models, and every user action.** Nothing is done
until a human-like Playwright run proves it.

### Wave 1 — unblock the product *(no parallelism, must land first)*
| # | Task | Owner | Gate |
|---|---|---|---|
| W1.1 | Shared agent↔brain credential seeded **merge-safe**, read-back asserted | memory | remember → recall round-trips |
| W1.2 | Agent↔brain transport reachable (clean RFC 1035 service name) | memory | no DisallowedHost, no 401 |
| W1.3 | Chat save→recall through SomaBrain+SFM | memory | `"What codeword did I ask you to remember?"` answers correctly |

### Wave 2 — the UI does real work *(parallel)*
| # | Task | Gate |
|---|---|---|
| W2.1 | Settings surface: every service URL + knob editable live | edit `SOMABRAIN_URL` in UI → memory lane repoints, no rebuild |
| W2.2 | Models: create / edit / delete a model; key↔model relation both ways | create a model in the UI, it appears and is usable |
| W2.3 | AgentIQ: knobs editable, derived values from the server only | change IQ → behaviour changes; no client-side derivation |

### Wave 3 — chat perfection + actions *(parallel)*
| # | Task | Gate |
|---|---|---|
| W3.1 | Stream latency + tool timeline + lanes visible | Playwright chat spec green |
| W3.2 | Roles gate the UI correctly | settings-by-role spec green |
| W3.3 | Every control has a handler; zero dummies | no dead button in the UI |

### Wave 4 — capacity + hardening *(parallel)*
| # | Task | Gate |
|---|---|---|
| W4.1 | Capsule-owned, permission-filtered tools | two capsules, different tool sets |
| W4.2 | One role store (Django + SpiceDB), zero-trust | `sysadmin` can chat **and** configure |
| W4.3 | SomaBrain/SFM/Temporal at 100% or explicitly out of scope | each capability live or documented |

**Final gate:** the full human Playwright suite, in the UI, green.

---

## THE RULES — non-negotiable, on every line

Authority: `docs/standards/SOMA-STD-CODING-001.md` (VIBE). These are the load-bearing ones.

### 1. NO HARDCODED VALUES — ever, in any file
No literal URL, host, port, path, or number in application code, bootstrap scripts,
compose, tests or docs. **A default IS a hardcoded value.**

| Forbidden | Write instead |
|---|---|
| `http://localhost:20882`, `:30101` | required env / setting — no default |
| `os.environ.get("X", "default")` | `require_env("X")` that raises |
| `${VAR:-somabrain}` | `${VAR:?set VAR}` |
| `getattr(settings, X, "http://…")` | resolve through the chain or raise |
| `timeout=15`, `TTL=768`, `dim=512` | a named setting |

**After every edit, run this and it must return nothing:**
```bash
grep -rnE 'https?://|localhost|127\.0\.0\.1|host\.docker\.internal|:[0-9]{4,5}' <files touched> | grep -v '^\s*#'
grep -rnE 'os\.environ\.get\([^)]*,[^)]+\)|\$\{[A-Z0-9_]+:-|getattr\([^,]+,[^,]+,\s*["\x27]http' <files touched>
```

### 2. NO FALLBACKS
A value comes from a real setting or the call **refuses**. No "or localhost", no
default, no substitute. Deleting a fallback is always correct; replacing one is not.

### 3. SETTINGS CHAIN — one, already decided
`Capsule > AgentSetting > InfrastructureConfig (operator editor) > SettingsModel > schema default (EMPTY)`
- **ENV = bootstrap only**, each **required**, never defaulted:
  `SA01_DEPLOYMENT_MODE`, `VAULT_ADDR`, `VAULT_TOKEN_FILE`, `POSTGRES_HOST`, `POSTGRES_PORT`.
- **Every service URL is an administrator parameter**, edited from the UI. Not an ENV contract.

### 4. NO STUBS, MOCKS, SHIMS, TODOs, PLACEHOLDERS
No "temporary", no "later", no "deprecated shim", no fabricated return. A shim is a
bypass. **Fix the consumer**; never keep the old path alive.

### 5. SECRETS — Vault only
- Vault owns every secret at `secret/agent/api_keys/{provider}_api_key` and
  `secret/agent/credentials/{key}`.
- **ENV never carries keys, tokens, passwords or DSNs.**
- **Never write a secret to any file, including `/tmp` — pass it in-process only.**
- **Vault KV v2 `POST` REPLACES the whole document.** A one-key write deletes every
  sibling key. Read → merge → write the full object → **read back and assert every
  expected key is present**. This has already caused real data loss.
- No root Vault token in a running service. Scoped, TTL-bound tokens only.

### 6. FAIL-CLOSED (Rule 91)
A missing required value is a refusal naming the setting. Never guess a host.

### 7. NEVER WEAKEN A GATE TO PASS A TEST
If a test needs a real credential and it is absent, the honest outcome is a failure
naming the missing secret. No dummy credential, no skipped assertion, no fake state.

### 8. CHECK FIRST, CODE SECOND
Read the architecture and the files before writing anything. Understand data flow, who
calls this, what it calls, and the impact. If context is missing, **ask**.

### 9. NO UNNECESSARY FILES
Modify existing files. A new file only when unavoidable — say why.

### 10. DOCUMENTATION = TRUTH
Docs describe what the code does. No invented APIs or routes. If you cannot verify it,
say so.

### 11. COMMITS
User's own git identity. **No AI attribution of any kind** — no `Co-Authored-By`, no
"Generated with Claude Code", no session links. Small coherent chunks.

### 12. DESIGN CRITERIA ON EVERY DECISION
**the rules · millions of transactions · security · speed · latency · thin.**

---

## REPORTING

Every agent reports, honestly:
- what changed (file:line) and where each value now comes from
- every hardcoded value found and every fallback deleted
- real test results — never claim a pass that did not happen
- anything blocked, and the exact reason

---

## THE ONE PATH — connect through the infrastructure, never around it

**Owner's standing order:** *"TELL THE AGENTS TO CONNECT VIA THE WHOLE INFRASTRUCTURE
OTHERWISE SOMETIMES THE AGENT JUST FUCKS UP THE CODE AND CREATES THEIR OWN LANES TO
CONNECT THE CHAT."*

If you are about to create any of these, **stop — you are doing it wrong**:

- a new WebSocket route or a second chat consumer
- a new orchestrator / chat pipeline / "just call the LLM directly" path
- a new memory client, a direct SFM connection, or a second write path
- a new auth check, a new role store, a new settings resolver
- a "temporary" endpoint so a test can pass
- a parallel config file, an .env-only path, or a hardcoded URL
- a test-only settings override, a fake Vault, or a dummy credential so a suite boots

**The one path, end to end:**

```
browser → WS /ws/v2/chat/{capsule_id}
        → services/gateway/consumers/chat.py::ChatConsumer
        → admin/core/chat_orchestrator.py::V3ChatOrchestrator.process_turn|stream_turn
        → admin/core/tool_calling.py::run_tool_loop        (native function-calling only)
        → services/common/memory_gateway.py::FanoutMemoryGateway
        → services/common/adapters/somabrain_adapter.py::SomaBrainAdapter
        → SomaBrain  →  somafractalmemory
```

| Concern | The only way |
|---|---|
| Permissions | `admin/core/agentiq/unified_gate.py`, `admin/core/authz.py` |
| Service URLs | `admin/core/helpers/service_urls.require_service_url` (`Capsule > AgentSetting > InfrastructureConfig > SettingsModel`) |
| Secrets | `services/common/unified_secret_manager.py` / `vault_secrets.py` — Vault only |
| Tools | the per-capsule `ToolRegistry` |
| Settings | `admin/core/helpers/settings.py`, `capsule_settings.py` |

**A bypass is the same violation as a mock.** Routing around a broken hop leaves the real
consumer broken and the architecture rotting. **Fix the hop.**

Every agent must end its report with: *"I connected via the existing chain, and did not
create a new lane."* If one was created, say so and revert it.
