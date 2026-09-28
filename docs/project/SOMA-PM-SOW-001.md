# SOMA COGNITIVE TRIAD — SCOPE OF WORK

## Document Control

| Field | Value |
|---|---|
| Document Title | Soma Cognitive Triad — Full Scope of Work |
| Document Identifier | SOMA-PM-SOW-001 |
| Version | 1.0.0 |
| Date | 2026-06-15 |
| Status | Approved |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Brought under ISO document control: Document Control block normalised and this Revision History added. |

## 1. OBJECTIVE

Build the **best AI agent in the world** — a modular, enterprise-grade cognitive agent platform with:
- Standalone mode: `docker run` one command, personal AI assistant (Agent Zero style)
- Enterprise mode: Multi-tenant, LDAP/SSO, billing, full observability
- Shared core: Chat, memory (SomaBrain + SFM), tools, plugins, canvas
- SomaTech brand identity (somatech.dev + yachaq.ai colors/fonts)

---

## 2. SCOPE — 7 SPRINTS

### Sprint 1: Core Agent (Week 1)
**Goal**: Standalone agent that chats, remembers, and executes tools.

| # | Task | Deliverable |
|---|------|-------------|
| 1.1 | Scaffold modular architecture (core/module.py, registry, loader) | Module system foundation |
| 1.2 | Create standalone settings (simple auth, SQLite ok, no Keycloak) | Standalone config |
| 1.3 | Wire Groq/OpenAI via LiteLLM with model selector | LLM works |
| 1.4 | Implement V3 orchestrator for standalone mode | Chat pipeline works |
| 1.5 | Create agent CRUD (name, model, prompt, tools) | Agent management |
| 1.6 | Build chat UI with SomaTech brand (colors, fonts, layout) | Chat page renders |
| 1.7 | Add show/hide password toggle | Login UX |
| 1.8 | Test: agent responds to chat message via Groq | E2E proof |

### Sprint 2: Tools & Canvas (Week 2)
**Goal**: Agent has tools and canvas panel.

| # | Task | Deliverable |
|---|------|-------------|
| 2.1 | Implement web search tool (DuckDuckGo) | Search works |
| 2.2 | Implement code execution tool (Python sandbox) | Code runs |
| 2.3 | Implement file operations tool (read/write/list) | File ops work |
| 2.4 | Implement git operations tool | Git works |
| 2.5 | Build canvas panel (right side, tabbed) | Canvas renders |
| 2.6 | Build code editor canvas | Code editor works |
| 2.7 | Build document editor canvas | Doc editor works |
| 2.8 | Build file browser canvas | File browser works |
| 2.9 | Test: agent searches web, writes code, creates file | E2E proof |

### Sprint 3: Settings & Modules (Week 3)
**Goal**: Settings UI with model config, tool toggles, module manager.

| # | Task | Deliverable |
|---|------|-------------|
| 3.1 | Build settings hub page | Settings page renders |
| 3.2 | Build model provider config (API key entry, model selection) | Model config works |
| 3.3 | Build agent settings (personality, prompt, tools) | Agent settings work |
| 3.4 | Build module manager (toggle on/off with dependency validation) | Module manager works |
| 3.5 | Implement module lifecycle (init, start, health, stop) | Module system works |
| 3.6 | Create billing module skeleton | Billing toggleable |
| 3.7 | Create auth.keycloak module skeleton | Keycloak toggleable |
| 3.8 | Test: enable/disable modules, configure model | E2E proof |

### Sprint 4: Welcome & UX Polish (Week 4)
**Goal**: Agent Zero quality UX — welcome screen, chat history, markdown, code blocks.

| # | Task | Deliverable |
|---|------|-------------|
| 4.1 | Build welcome screen (quick actions, recent chats) | Welcome renders |
| 4.2 | Build chat history sidebar (grouped by date) | Sidebar works |
| 4.3 | Implement markdown rendering (headings, lists, bold, links) | Markdown renders |
| 4.4 | Implement code syntax highlighting (with copy/run buttons) | Code blocks work |
| 4.5 | Implement tool call display (collapsible input/output) | Tool calls render |
| 4.6 | Implement file attachments (drag-and-drop) | Attachments work |
| 4.7 | Implement image display in chat | Images render |
| 4.8 | Add keyboard shortcuts (Ctrl+N, Ctrl+K, Ctrl+B, etc.) | Shortcuts work |
| 4.9 | Test: full chat UX flow | E2E proof |

### Sprint 5: Enterprise Modules (Week 5-6)
**Goal**: Enterprise mode with Keycloak, billing, audit.

| # | Task | Deliverable |
|---|------|-------------|
| 5.1 | Implement auth.keycloak module (OIDC, realm, login) | Keycloak auth works |
| 5.2 | Implement auth.ldap module (LDAP bind, search) | LDAP auth works |
| 5.3 | Implement billing module (Lago integration, usage tracking) | Billing works |
| 5.4 | Implement audit module (event logging, log viewer) | Audit works |
| 5.5 | Implement secrets.vault module (read/write secrets) | Vault works |
| 5.6 | Build admin dashboard (tenants, users, agents, billing) | Admin page renders |
| 5.7 | Implement multi-tenancy (tenant isolation, user roles) | Tenancy works |
| 5.8 | Test: enterprise deploy with Keycloak + billing | E2E proof |

### Sprint 6: Plugin & Skills System (Week 7-8)
**Goal**: Extensible agent with plugins and skills.

| # | Task | Deliverable |
|---|------|-------------|
| 6.1 | Design plugin architecture (hooks, lifecycle) | Plugin system works |
| 6.2 | Build plugin installer UI (browse, install, configure) | Plugin UI works |
| 6.3 | Create 5 starter plugins (email, telegram, tts, stt, scheduler) | Plugins work |
| 6.4 | Design skills system (import, export, compose) | Skills system works |
| 6.5 | Build skills management UI | Skills UI works |
| 6.6 | Create 5 starter skills (code review, research, writing, analysis, planning) | Skills work |
| 6.7 | Implement MCP integration (connect MCP servers) | MCP works |
| 6.8 | Test: install plugin, use skill, connect MCP server | E2E proof |

### Sprint 7: Polish & Release (Week 9-10)
**Goal**: Production-ready release.

| # | Task | Deliverable |
|---|------|-------------|
| 7.1 | Docker standalone image (`docker run soma/agent`) | One-command start |
| 7.2 | Docker enterprise image (full stack compose) | Enterprise deploy works |
| 7.3 | K8s manifests (probes, limits, HPA) | K8s ready |
| 7.4 | CI/CD pipeline (GitHub Actions) | CI green |
| 7.5 | Load testing (100 concurrent users) | Performance baseline |
| 7.6 | Security audit (Bandit, pentest checklist) | Security clean |
| 7.7 | Documentation (user guide, admin guide, API docs) | Docs complete |
| 7.8 | Release v1.0.0 | Shipped |

---

## 3. TECHNICAL STACK

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.1 + Django Ninja |
| Frontend | Lit 3.x Web Components |
| Database | PostgreSQL (enterprise) / SQLite (standalone) |
| Cache | Redis |
| LLM | LiteLLM (Groq, OpenAI, Anthropic, Ollama) |
| Memory | SomaBrain + SomaFractalMemory |
| Auth | Email/password (standalone) / Keycloak (enterprise) |
| Build | Docker + docker-compose |
| CI/CD | GitHub Actions |
| K8s | Production manifests with HPA, PDB, probes |

---

## 4. BRAND

| Element | Value |
|---------|-------|
| Primary BG | #0A0A0A (Soma Black) |
| Surface | #1A1A1A |
| Text | #E5E5E5 |
| Accent | #3B82F6 → #8B5CF6 (gradient) |
| Font | Inter (body), JetBrains Mono (code) |
| Logo | SOMA wordmark |

---

## 5. ACCEPTANCE CRITERIA

### Standalone Mode
- [ ] `docker run -p 80:80 soma/agent` starts everything
- [ ] User creates account, configures model, creates agent
- [ ] Agent responds to chat messages via configured LLM
- [ ] Agent uses tools (search, code, files)
- [ ] Canvas shows tool outputs
- [ ] Settings page shows modules with toggles

### Enterprise Mode
- [ ] `docker compose up -d` starts full stack
- [ ] Keycloak SSO login works
- [ ] Multi-tenant isolation verified
- [ ] Billing metering active
- [ ] Audit logging complete
- [ ] Admin dashboard shows all tenants/users/agents

---

End of Document
