# SRS: Eye of God — SaaS-Wide Infrastructure & MCP Defaults

**Document ID:** SA01-SRS-INFRASTRUCTURE-DEFAULTS-2025-12
**Persona:** 🔴 SAAS SysAdmin (God Mode)
**Focus:** The "Nervous System" (Global Tools & MCP Servers)
**Status:** CANONICAL DESIGN

---

## 1. The "Global Nervous System" Philosophy

The Eye of God determines what the "System" *is*.
If the System has a "Long Term Memory", it is defined here.
If the System has "Web Access", it is defined here.

**Key Concept: The MCP Registry**
We move away from hardcoded `mcp_servers_config` strings to a dynamic **Global Registry** managed by the SysAdmin.

---

## 2. Core Modules

### 2.1 🔌 The Global MCP Registry (`/saas/infrastructure/mcp`)

**Route:** `/saas/infrastructure/mcp`

Allows the SAAS Admin to register "Official" MCP Servers that are available to the ecosystem.

#### Server Types
1.  **Local (StdIO):** Runs on the *same pod* as the agent (high security risk, admin only).
2.  **Remote (SSE/HTTP):** Runs on a separate microservice (preferred for SaaS).

#### Preconfigured "Golden" Servers (The User's Request)
The system comes with these "batteries included" servers defined in the Catalog:

| Server ID | Type | Description | Default Status |
|-----------|------|-------------|----------------|
| `brave-search` | Remote | Web Search Configured | **Optional** |
| `filesystem` | Local | SANDBOXED File Access | **Restricted** (Enterprise Only) |
| `soma-memory` | Remote | Vector/Graph Memory | **Mandatory** (Core OS) |
| `github-mcp` | Remote | Code Repo Access | **Optional** |
| `slack-mcp` | Remote | Chat Integration | **Optional** |

### 2.2 🧬 The Inheritance Logic (Global -> Tenant -> Agent)

How do these servers get to the user?

1.  **Global Defaults (God Layer):**
    *   Admin sets `soma-memory` as **Mandatory**.
    *   Admin sets `brave-search` as **Available**.

2.  **Tenant Provisioning (The "Hydration" Flow):**
    *   When Tenant `Acme` is created...
    *   System injects `soma-memory` config into their vault.
    *   System *offers* `brave-search` as an addon in their settings.

3.  **Agent Runtime:**
    *   Agent spins up.
    *   Loads **Mandatory** servers automatically.
    *   Loads **Enabled** optional servers.

---

## 3. UI Specifications

### 3.1 Screen: MCP Registry Manager

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔌 GLOBAL MCP SERVER REGISTRY                          [+ Add Server]       │
├─────────────────────────────────────────────────────────────────────────────┤
│  MANDATORY SERVERS (Injected into every Agent)                              │
│  ┌──────────────────────┐  ┌──────────────────────┐                         │
│  │ 🧠 SOMA Memory       │  │ 🛡 Audit Logger      │                         │
│  │ Type: Remote (SSE)   │  │ Type: Remote (SSE)   │                         │
│  │ URL: internal:9090   │  │ URL: internal:9091   │                         │
│  │ Status: 🟢 Healthy   │  │ Status: 🟢 Healthy   │                         │
│  └──────────────────────┘  └──────────────────────┘                         │
│                                                                             │
│  CATALOG (Available for Tenants to Enable)                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐ │
│  │ 🦁 Brave Search      │  │ 📁 Filesystem        │  │ 🐙 GitHub          │ │
│  │ Key: $ENV.BRAVE_KEY  │  │ Mode: Sandboxed      │  │ Auth: OAuth        │ │
│  │ [Edit] [Deprecate]   │  │ [Edit] [Deprecate]   │  │ [Edit] [Deprecate] │ │
│  └──────────────────────┘  └──────────────────────┘  └────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Screen: Server Configuration Modal

When clicking `[+ Add Server]`:

*   **Name:** `postgres-adapter`
*   **Transport:** `Remote (SSE)`
*   **URL:** `https://mcp.soma.tech/v1/postgres`
*   **Env Vars:**
    *   `DB_HOST` = `{{TENANT_DB_HOST}}` (Variable Injection)
    *   `DB_PASS` = `{{TENANT_DB_PASS}}`
*   **Availability:**
    *   [ ] Mandatory (All Agents)
    *   [x] Optional (Tenant Admin must enable)
    *   [ ] Restricted (Enterprise Tier Only)

---

## 4. The "Whole Flow" User Experience

**Scenario: A New User wants Web Search.**

1.  **God Mode:** SysAdmin installs `mcp-brave-search` server on the cluster.
    *   Registers it in **MCP Registry**.
    *   Sets API Key strategy: `Passthrough` (Tenant provides key) OR `Platform` (We provide key).

2.  **Tenant Mode:**
    *   Tenant Admin logs in.
    *   Goes to **Settings > Integrations**.
    *   Sees "Web Search" available.
    *   Clicks **[Enable]**.

3.  **Agent Mode:**
    *   User types: "Search for latest news".
    *   Agent sees tool `brave_search.search`.
    *   Executes successfully.

---

## 5. Security Architecture

*   **Sandboxing:** Local servers (`stdio`) are dangerous.
    *   **Rule:** Local servers ONLY run in **Ephemeral Firecracker VMs**.
    *   **Rule:** Remote servers are preferred.
*   **Header Injection:**
    *   The Platform injects `X-Tenant-ID` and `X-Agent-ID` into every MCP call.
    *   The MCP Server MUST validate these headers.

---

## 6. Implementation Plan

1.  **Backend:** Extend `MCPConfig` to read from DB (`GlobalMCPServer` model) instead of just single JSON.
2.  **Frontend:** Build the Registry UI using the existing Card/Table components.
3.  **Agent:** Update `AgentContext` to merge Mandatory + Tenant config at runtime.
