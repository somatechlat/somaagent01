# UI-S-11 — Capsule list

Screen UI-S-11 · Route: **`/admin/agents`** (`main.ts:258` → `soma-agents-view`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §3 Capsule
Live view: `webui/src/views/soma-entity-views.ts` (`soma-agents-view`)

**Status: LIVE.** Capsule is per-agent: `GET /api/v2/agents/{agent_id}/capsule`.
The list shows each agent’s primary capsule — **`CapsuleConfigOut` fields only**.

---

## 1. ASCII wireframe — capsule list (workspace)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  CAPSULES — agent primary capsules                                       [⟳ Refresh]            │
│  [Search agents…                    ]  status [all ▾]                                            │
│                                                                                                  │
│  ┌─ CAPSULE TABLE (server order) ─────────────────────────────────────────────────────────────┐  │
│  │ agent_id        capsule_id     name                 status        description              │  │
│  │ ‹agent_id›      ‹capsule_id›   ‹name›               ‹status›      ‹description | —›        │  │
│  │ ‹agent_id›      ‹capsule_id›   ‹name›               ‹status›      ‹description | —›        │  │
│  │ (scroll)                                                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  total: ‹n | —› agents                                                         [Open]          │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Columns are exactly the `CapsuleConfigOut` scalars (`admin/agents/api/schemas.py:75-87`).
No semver chip, no lifecycle chip, no IQ/AUTO/BUDGET knobs, no facet tabs, no instance strip —
those are not capsule fields and not enterprise chrome (`UI-S-00` §3).

---

## 2. Real data — `CapsuleConfigOut`

| UI column | API field | Notes |
|---|---|---|
| Agent | `agent_id` | path key of `GET /api/v2/agents/{agent_id}/capsule` |
| Capsule | `capsule_id` | `str(capsule.id)` |
| Name | `name` | |
| Status | `status` | as stored — no invented lifecycle enum |
| Description | `description` | `Optional` → `—` when null |

Route: `GET /api/v2/agents/{agent_id}/capsule` (one capsule per agent).
There is **no list-all-capsules endpoint** — the list is built from the agents view
(`/admin/agents` → `soma-agents-view`) and each row’s capsule read.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Search | Client filter over loaded agents. | live |
| 2 | Status filter | Filter on `status` as stored. | live |
| 3 | Capsule row | Shows `agent_id · capsule_id · name · status · description`. | live |
| 4 | Open | `router →` UI-S-12 for that `agent_id` (capsule editor). | live |
| 5 | Refresh | Re-fetch the agents + capsule reads. | live |
| 6 | Total | `—` until the server reports. Never `0` on failure. | live |

---

## 4. Numbered journey — find a capsule and open it

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/admin/agents` | Screen loads | agents view + `GET …/capsule` per agent | Table rows with real `CapsuleConfigOut` scalars. |
| **2** | list | Search `name` / filter `status` | client filter | Table narrows. |
| **3** | list | Click a row’s **Open** | `router →` UI-S-12 | Capsule editor for that `agent_id`. |
| **4** | list | Row with no capsule | `GET …/capsule` 404 | Row shows `—` / “No capsule”; Open disabled. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | Skeleton rows. “Loading capsules…” |
| empty | “No capsules yet. Open an agent to create its capsule.” |
| empty (filter) | “No capsules match this filter. Clear the filter to see all.” |
| error | “Capsules could not be loaded. Retry, or check that the somaAgent01 API is reachable.” |
| 404 (one agent) | That row: “No capsule” — other rows unaffected. |
| permission-denied | Read-only; “You do not have permission to manage capsules. Ask a platform admin for the capsule-editor role.” |
| offline | “Capsule actions are unavailable offline.” |

---

## 6. Honesty

Card values are `CapsuleConfigOut` fields only. No invented semver, lifecycle, or metric chips.
Totals are `—` until the server reports.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-entity-views.ts` | Live agents view |
| `GET /api/v2/agents/{agent_id}/capsule` | `CapsuleConfigOut` (`schemas.py:75-87`) |
| `SOMA-UI-CATALOG-001.md` §3 | Real capsule fields |

End of Document
