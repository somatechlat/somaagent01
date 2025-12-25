# SRS: Eye of God — Visual Infrastructure (The "God Canvas")

**Document ID:** SA01-SRS-VISUAL-INFRASTRUCTURE-2025-12
**Persona:** 🔴 SAAS SysAdmin (God Mode)
**Focus:** Spatial/Topological Management (Penpot-Style)
**Status:** CANONICAL DESIGN

---

## 1. The "Universe Canvas" Philosophy

The Eye of God is not just a spreadsheet of settings; it is a **Map of Creation**. The "God Canvas" allows the admin to see the platform as a living network of connected nodes, providing a spatial understanding of the infrastructure.

**Core Interaction:** Infinite Pan/Zoom Canvas (Nodes & Edges).
**Metaphor:** "Connecting Synapses of the Brain".

---

## 2. Views & Modes

The Canvas has differents "Lenses" to view the system.

### 2.1 🌐 The Integration Topology (`/saas/infrastructure/integrations`)

Visualizes how the Platform connects to the outside world.

*   **Nodes:**
    *   🔴 `SomaPlatform` (Hub)
    *   🔵 `Lago` (Billing)
    *   🟡 `Keycloak` (Auth)
    *   🟢 `OpenAI` (Model Provider)
    *   🟣 `SMTP` (Email)
*   **Edges:**
    *   Lines represent active connections.
    *   Color: Green (Healthy), Red (Error), Grey (Disabled).
    *   Interaction: Click line to see `Connection Details` (Latency, Error Rate).

**Penpot-Style Action:**
*   Drag a "Stripe" node from the palette onto the canvas.
*   Draw a line from `SomaPlatform` to `Stripe`.
*   Modal opens: "Configure API Keys".
*   Connection established.

### 2.2 🏘 The Tenant Constellation (`/saas/infrastructure/tenants`)

Visualizes tenants as solar systems.

*   **Center:** `Tenant: Acme Corp`.
*   **Orbiting Nodes:** `Agent: HR Bot`, `Agent: Sales Bot`, `User: John Doe`.
*   **Edges:** Represent Permission/Access relationships.

**Actions:**
*   "Lasso Select" a group of agents -> Right Click -> `Start/Stop`.
*   Drag `Agent: HR Bot` to `Tenant: Beta Inc` to "Migrate" (Move) the agent.

---

## 3. UI Specifications

### 3.1 Screen: The God Canvas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔴 GOD CANVAS: INTEGRATIONS                            [ Save Topology ]    │
├────────┬────────────────────────────────────────────────────────────────────┤
│ PALETTE│                                                                    │
│ ┌────┐ │           (Cloud: AWS US-East)                                     │
│ │ 💳 │ │                    │                                               │
│ │Stp │ │              ┌─────────────┐       ┌────────────┐                  │
│ ├────┤ │              │ 🔴 SOMA     │───────│ 🔐 Keycloak│                  │
│ │ 💰 │ │              │ Platform    │   ✅  │ (Auth)     │                  │
│ │Lgo │ │              └─────────────┘       └────────────┘                  │
│ ├────┤ │                     │  \                                           │
│ │ 🤖 │ │                  ✅ │   \ ❌ (401 Error)                           │
│ │GPT │ │           ┌────────────┐   \        ┌────────────┐                 │
│ ├────┤ │           │ 💰 LAGO    │    \       │ 📧 RESEND  │                 │
│ │ 📧 │ │           │ (Billing)  │     \      │ (Email)    │                 │
│ │Mail│ │           └────────────┘      \     └────────────┘                 │
│ └────┘ │                                \                                   │
│        │                                 \   <-- Drag to Reconnect          │
│ ZOOM   │                                                                    │
│ [+][-] │                                                                    │
└────────┴────────────────────────────────────────────────────────────────────┘
```

### 3.2 Interaction Details

*   **Hover Node:** Shows quick stats (Uptime, Latency).
*   **Click Node:** Opens `Inspector Panel` on the right (Configuration Form).
*   **Right Click:** Context Menu (`Restart Connection`, `View Logs`, `Delete`).
*   **Drag Wire:** Create new integrations or re-route (e.g., Switch Email from SendGrid to Resend visually).

---

## 4. Technical Implementation

This is a **Frontend-Heavy** implementation.

*   **Library:** `React Flow` or `xyflow` (wrapped in Lit via custom element).
*   **State:** Coordinates (x,y) stored in `platform_topology` JSONB.
*   **Sync:** WebSocket connection (`/ws/admin/topology`) for real-time health updates (lines turn red instantly).

---

## 5. Justification for "God Mode"

This view separates a "Manager" from an "Architect".
*   **Manager:** Uses tables/forms.
*   **God:** Uses the Canvas to see the "Big Picture" and design the universe.

This directly addresses the requirement for **"Penpot-like creation of existing servers"**.
