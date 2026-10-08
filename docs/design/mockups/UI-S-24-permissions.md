# UI-S-24 — Permissions (matrix pane)

Screen UI-S-24 · Same route as UI-S-23: **`/platform/roles`** · **`/platform/role-matrix`** ·
**`/soma/permissions`** · **`/platform/permissions`** (`main.ts:164-166` → `soma-admin-roles-list`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/soma-admin-roles-list.ts` (`soma-admin-roles-list`)

**Status: LIVE — as a pane, not a destination.** The permission matrix is the **secondary pane**
of the same roles screen (UI-S-23 is the role catalogue pane). One live view serves every alias
(DUP-7). Do not present this as a second nav target.

---

## 1. ASCII wireframe — permission matrix (secondary pane)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  ROLES · PERMISSIONS                                        [Save matrix]  [⟳ Refresh]          │
│                                                                                                  │
│  ┌─ ROLE LIST (UI-S-23 pane) ───┐  ┌─ PERMISSION MATRIX (this pane) ────────────────────────┐  │
│  │  ‹role.name›              ●  │  │  perm              ‹role.a›   ‹role.b›   ‹role.c›      │  │
│  │  ‹role.name›                 │  │  ─────────────     ────────   ────────   ────────      │  │
│  │  ‹role.name›                 │  │  ‹perm.name›         [x]        [ ]        [x]         │  │
│  │  [+ New role]                │  │  ‹perm.name›         [x]        [x]        [ ]         │  │
│  └──────────────────────────────┘  │  ‹perm.name›         [ ]        [ ]        [ ]         │  │
│                                    │  ‹perm.name›         [x]        [ ]        [ ]         │  │
│                                    │  (scroll)                                                 │  │
│                                    │                                                             │  │
│                                    │  [ Save matrix ]  ← enabled while dirty                    │  │
│                                    └─────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

| UI field | Source | Absent handling |
|---|---|---|
| Permission name | permission record | required |
| Role column header | role record | required |
| Cell checked | role↔permission assignment | unchecked when not assigned |

Same `soma-admin-roles-list` view as UI-S-23 — no second endpoint, no second store.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Role columns | From the role list (UI-S-23 pane). | live |
| 2 | Permission rows | From the permission record set. | live |
| 3 | Cell toggle | Marks role↔permission assignment dirty. | live |
| 4 | Save matrix | Persist all assignment edits. Disabled until dirty. | live |
| 5 | Refresh | Re-fetch roles + assignments. | live |

---

## 4. Numbered journey — toggle a permission

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/platform/roles` | Screen loads | roles admin API | Matrix pane shows assignments. |
| **2** | matrix | Toggle a cell for the selected role | — | Cell dirty → **Save matrix** enabled. |
| **3** | matrix | Toggle more cells | — | All edits stay dirty. |
| **4** | matrix | Click **Save matrix** | roles admin API | Assignments persisted; dirty cleared. |
| **5** | matrix | **Refresh** | roles admin API | Server truth repainted. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading permissions…” — skeleton rows. |
| empty | “No permissions defined yet.” |
| error | “Permissions could not be loaded. Retry, or check that the somaAgent01 API is reachable.” |
| dirty | **Save matrix** enabled. |
| save fail | “Matrix was not saved. Your edits are still here — try again.” |
| permission-denied | Read-only toggles; “Role administration requires the platform-admin role.” |
| offline | “Permission changes are unavailable offline.” |

---

## 6. Honesty

Permission names and assignments come from the store. No invented permission catalogue, no
derived policy labels. This pane never appears as its own nav entry (DUP-7).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:164-166` | All four aliases → `soma-admin-roles-list` |
| `webui/src/views/soma-admin-roles-list.ts` | Live screen (catalogue + matrix panes) |
| `SOMA-UI-NAV-AUDIT-001.md` §3 DUP-7 | UI-S-23 + UI-S-24 are panes of one screen |

End of Document
