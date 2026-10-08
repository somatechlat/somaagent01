# UI-S-13 — Version rail & diff

Screen UI-S-13 · Subview of **`/admin/agents`** (from UI-S-12) · Chrome: **UI-S-00 thin** (abbrev)
Catalog: `SOMA-UI-CATALOG-001.md` §3 Capsule

**Status: GATED / future.** `CapsuleConfigOut` has **no version fields** — `version`, `deployed_at`
and `deployed_by` were removed from the agent schemas as the wrong schema’s fields
(`admin/agents/api/schemas.py:46-49`). There is **no version-history endpoint**.

> **Blocking reason:** Capsule versioning is not implemented. `GET/PATCH /api/v2/agents/{agent_id}/capsule`
> returns a single live config with no version list, no author, and no diff base. This screen cannot
> show real data until a version API ships.

Do not invent semver chips, author rows, or diff lines. **`CapsuleConfigOut` fields only** — and it
has none of the above.

---

## 1. ASCII wireframe — gated surface

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  CAPSULE · VERSIONS   ‹name› · ‹capsule_id›                            ← Back to editor         │
│                                                                                                  │
│  ┌─ GATED ───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                           │  │
│  │   Version history is not available on this deployment.                                    │  │
│  │                                                                                           │  │
│  │   Blocking reason: Capsule versioning is not implemented. The capsule API                  │  │
│  │   returns one live configuration (GET /api/v2/agents/{agent_id}/capsule) with             │  │
│  │   no version list, no author, and no diff base.                                           │  │
│  │                                                                                           │  │
│  │   [ Back to editor ]                                                                     │  │
│  │                                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  (no version rail · no diff pane · no Restore)                                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

**None.** There is no version endpoint and `CapsuleConfigOut` carries no version fields:

| Concept a version screen would need | Real field? | Handling |
|---|---|---|
| version id / semver | **not in schema** | not drawn |
| author / deployed_by | **removed** (`schemas.py:46-49`) | not drawn |
| timestamp | **not in schema** | not drawn |
| diff base document | **not in schema** | not drawn |

The only capsule read is `GET /api/v2/agents/{agent_id}/capsule` → the **live** config (UI-S-12).

---

## 3. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Gated notice | Blocking reason verbatim above. | live (notice) |
| 2 | Back to editor | `router →` UI-S-12. | live |
| — | Version rail / Diff / Restore | **Not rendered** — no API. | GATED |

---

## 4. Numbered journey (stops at the gate)

| Step | Where | Action | Result |
|---|---|---|---|
| **1** | UI-S-12 | Look for “History / Versions” | No such control — versioning is not offered on this deployment. |
| **2** | UI-S-12 | (if surfaced) click Versions | This screen opens with the GATED notice. |
| **3** | here | Read the blocking reason | Understands versioning is unimplemented. |
| **4** | here | **Back to editor** | `router →` UI-S-12 (live config). |

There is no step 5 — nothing to diff, nothing to restore.

---

## 5. States

| State | Behavior |
|---|---|
| default | GATED notice + blocking reason. |
| offline | Same notice (the gate is not network-dependent). |

No loading, no empty rail, no error — the feature does not reach the API.

---

## 6. Honesty

- No invented semver strings, authors, timestamps, or diff lines.
- The gate reason names the real API shape (`GET …/capsule` returns one live config).
- When a version API ships, this screen fills from **that** API — never from placeholders.

---

## 7. Source map

| Source | Role |
|---|---|
| `admin/agents/api/schemas.py:46-49` | `version` / `deployed_at` / `deployed_by` removed |
| `GET /api/v2/agents/{agent_id}/capsule` | Single live config (UI-S-12) |
| `SOMA-UI-CATALOG-001.md` §3 | Capsule fields = `CapsuleConfigOut` only |

End of Document
