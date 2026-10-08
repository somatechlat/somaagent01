# UI-S-36 — Mode selection

Screen UI-S-36 · Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform

**Status: GATED / future — does not ship on this deployment.**

> **Blocking reason:** **`/mode-select` is not a route in `main.ts`.** ORPH-M3
> (`SOMA-UI-NAV-AUDIT-001.md` §5). There is no mode-selection view and no role-gated “God Mode /
> Enter Tenant” picker — this is a **standalone agent** (`main.ts:131-132`), so the whole
> God-Mode/tenant choice is out of scope.

Unknown paths fall through to `soma-chat` (`main.ts:408`) — never to this screen.

---

## 1. ASCII wireframe — future sketch (not routable)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ┌─ GATED ───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                           │  │
│  │   Mode selection is not available on this deployment.                                     │  │
│  │                                                                                           │  │
│  │   Blocking reason: /mode-select is not a route in main.ts (ORPH-M3).                       │  │
│  │   Standalone agent — no God Mode / tenant picker (main.ts:131-132).                        │  │
│  │                                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  (no mode cards · no tenant picker · no Continue)                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

**None.** No mode-selection API. Any role card or tenant row would be invented.

---

## 3. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Gated notice | Blocking reason verbatim. | live (notice) |
| — | Mode cards / tenant picker / Continue | **Not rendered** — no API, no route. | GATED |

---

## 4. Numbered journey (stops at the gate)

| Step | Where | Action | Result |
|---|---|---|---|
| **1** | after login | Land on `/chat` welcome | `soma-chat` — the real post-auth home (`main.ts:54` → `/chat`). |
| **2** | (bookmark) | Navigate to `/mode-select` | Not routed; fallthrough → `soma-chat`. |
| **3** | here | Read the blocking reason | Understands mode selection is unimplemented. |

---

## 5. States

| State | Behavior |
|---|---|
| default | GATED notice + blocking reason. |

---

## 6. Honesty

No invented mode names, role cards, or tenant rows. This mock records the gap (ORPH-M3).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts` (no `/mode-select`) | Route does not exist |
| `webui/src/main.ts:131-132` | Standalone agent |
| `SOMA-UI-NAV-AUDIT-001.md` §5 ORPH-M3 | Mode-selection mock has no route |

End of Document
