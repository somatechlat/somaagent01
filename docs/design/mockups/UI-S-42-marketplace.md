# UI-S-42 — Marketplace

Screen UI-S-42 · Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform

**Status: GATED / future — does not ship on this deployment.**

> **Blocking reason:** **`/platform/marketplace` is not a route in `main.ts`.** ORPH-M5
> (`SOMA-UI-NAV-AUDIT-001.md` §5). There is no marketplace view and no catalogue/browse API.

Also: `/themes` (`main.ts:361`) is a **present-but-disabled skins notice** — it is **not** a
marketplace and must not be documented as one (GAP-N3). Skins are specified in
`SOMA-UI-SKINS-001.md` and not implemented.

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
│  │   Marketplace is not available on this deployment.                                        │  │
│  │                                                                                           │  │
│  │   Blocking reason: /platform/marketplace is not a route in main.ts (ORPH-M5).             │  │
│  │   /themes is a disabled skins notice (GAP-N3) — not a marketplace.                        │  │
│  │                                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  (no listings · no install · no ratings)                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

**None.** No marketplace schema or endpoint exists. Any listing, price, or rating would be invented.

---

## 3. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Gated notice | Blocking reason verbatim. | live (notice) |
| — | Listings / install / ratings | **Not rendered** — no API, no route. | GATED |

---

## 4. Numbered journey (stops at the gate)

| Step | Where | Action | Result |
|---|---|---|---|
| **1** | anywhere | Look for a Marketplace nav entry | None — not in the nav. |
| **2** | (bookmark) | Navigate to `/platform/marketplace` | Not routed; fallthrough → `soma-chat`. |
| **3** | `/themes` | Navigate there | Disabled **skins** notice (not marketplace) — GAP-N3. |
| **4** | here | Read the blocking reason | Understands marketplace is unimplemented. |

---

## 5. States

| State | Behavior |
|---|---|
| default | GATED notice + blocking reason. |

---

## 6. Honesty

No invented listings, prices, ratings or install counts. `/themes` is **not** documented here as a
marketplace route (GAP-N3). This mock records the gap (ORPH-M5).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts` (no `/platform/marketplace`) | Route does not exist |
| `webui/src/main.ts:361` | `/themes` = disabled skins notice (GAP-N3) |
| `SOMA-UI-NAV-AUDIT-001.md` §5 ORPH-M5 · GAP-N3 | Marketplace has no route; `/themes` ≠ marketplace |

End of Document
