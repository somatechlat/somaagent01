# UI-S-14 — Capsule instances

Screen UI-S-14 · Subview of **`/admin/agents`** (from UI-S-11/12) · Chrome: **UI-S-00 thin** (abbrev)
Catalog: `SOMA-UI-CATALOG-001.md` §3 Capsule

**Status: GATED / future.** `CapsuleConfigOut` has **no instance fields** and there is **no
instance-management endpoint**. The live capsule read returns one configuration per agent
(`GET /api/v2/agents/{agent_id}/capsule`) — not a set of running instances.

> **Blocking reason:** Capsule instance management is not implemented. There is no instance list
> API, no instance id field on `CapsuleConfigOut`, and no restart/stop route. This screen cannot
> show real data until an instance API ships.

**`CapsuleConfigOut` fields only** — it contains none of `instance.id`, `instance.status`,
`started_at`. Do not draw them.

---

## 1. ASCII wireframe — gated surface

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  CAPSULE · INSTANCES   ‹name› · ‹capsule_id›                              ← Back to list        │
│                                                                                                  │
│  ┌─ GATED ───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                           │  │
│  │   Instance management is not available on this deployment.                                │  │
│  │                                                                                           │  │
│  │   Blocking reason: Capsule instance management is not implemented. There is no            │  │
│  │   instance list API and no instance fields on CapsuleConfigOut                            │  │
│  │   (GET /api/v2/agents/{agent_id}/capsule returns one configuration per agent).            │  │
│  │                                                                                           │  │
│  │   [ Back to list ]                                                                       │  │
│  │                                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  (no instance table · no Restart / Stop · no instance strip)                                     │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

There is no chrome instance strip either — UI-S-00 forbids an instance strip on chrome (§3).

---

## 2. Real data

**None.** No instance schema exists on the capsule API:

| Concept an instance screen would need | Real field? | Handling |
|---|---|---|
| instance id | **not in `CapsuleConfigOut`** | not drawn |
| instance status | **not in schema** | not drawn |
| started_at / session | **not in schema** | not drawn |
| restart / stop | **no route** | not drawn |

The only capsule read is `GET /api/v2/agents/{agent_id}/capsule` → live config scalars
(`agent_id` · `capsule_id` · `name` · `description` · `status` · `system_prompt` ·
`personality_traits` · `neuromodulator_baseline` · `learning_config`).

Note: `status` here is the **capsule’s** status, not an instance state.

---

## 3. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Gated notice | Blocking reason verbatim above. | live (notice) |
| 2 | Back to list | `router →` UI-S-11. | live |
| — | Instance table / Restart / Stop | **Not rendered** — no API. | GATED |

---

## 4. Numbered journey (stops at the gate)

| Step | Where | Action | Result |
|---|---|---|---|
| **1** | UI-S-11 | Look for “Instances” | No such control — instance management is not offered on this deployment. |
| **2** | UI-S-11/12 | (if surfaced) click Instances | This screen opens with the GATED notice. |
| **3** | here | Read the blocking reason | Understands instance management is unimplemented. |
| **4** | here | **Back to list** | `router →` UI-S-11. |

There is no step 5 — nothing to restart or stop.

---

## 5. States

| State | Behavior |
|---|---|
| default | GATED notice + blocking reason. |
| offline | Same notice (the gate is not network-dependent). |

No loading, no empty table, no error — the feature does not reach the API.

---

## 6. Honesty

- No invented instance ids, statuses, timestamps, or counts.
- No chrome instance strip (UI-S-00 §3 forbids it).
- The gate reason names the real API shape (one capsule config per agent).

---

## 7. Source map

| Source | Role |
|---|---|
| `admin/agents/api/schemas.py:75-97` | `CapsuleConfigOut` — no instance fields |
| `GET /api/v2/agents/{agent_id}/capsule` | Single live config (UI-S-12) |
| `UI-S-00-chrome.md` §3 | No instance strip on chrome |

End of Document
