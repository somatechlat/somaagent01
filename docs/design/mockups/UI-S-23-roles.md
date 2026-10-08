# UI-S-23 — Roles

Screen UI-S-23 · Routes: **`/platform/roles`** · **`/platform/role-matrix`** · **`/soma/permissions`**
· **`/platform/permissions`** (all `main.ts:164-166` → `soma-admin-roles-list`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/soma-admin-roles-list.ts` (`soma-admin-roles-list`)

**Status: LIVE.** One roles screen. This file is the **role catalogue pane**; the permission matrix
is the secondary pane (**UI-S-24**) of the **same** screen — not a second destination (DUP-7).

---

## 1. ASCII wireframe — roles catalogue (primary pane)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  ROLES · PERMISSIONS                                        [Save matrix]  [⟳ Refresh]          │
│                                                                                                  │
│  ┌─ ROLE LIST ─────────────┐  ┌─ PERMISSION MATRIX (UI-S-24 pane) ──────────────────────────┐  │
│  │  ‹role.name›         ●  │  │  perm              ‹role.a›   ‹role.b›   ‹role.c›           │  │
│  │  ‹role.name›            │  │  ─────────────     ────────   ────────   ────────           │  │
│  │  ‹role.name›            │  │  ‹perm.name›         [x]        [ ]        [x]              │  │
│  │  ‹role.name›            │  │  ‹perm.name›         [x]        [x]        [ ]              │  │
│  │                         │  │  ‹perm.name›         [ ]        [ ]        [ ]              │  │
│  │  [+ New role]           │  │  (scroll)                                                    │  │
│  │  [Delete role…]         │  │                                                               │  │
│  └─────────────────────────┘  └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

| UI field | Source | Absent handling |
|---|---|---|
| Role name | role record | required |
| Permission name | permission record | required |
| Cell checked | role↔permission assignment | unchecked when not assigned |

One live view (`soma-admin-roles-list`) for all four aliases (`main.ts:164-166`).
Do not present the matrix as a separate nav destination (DUP-7).

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Role list | Roles as stored. Selecting one highlights its matrix column. | live |
| 2 | New role | Create via the roles admin API → row appears. | live |
| 3 | Delete role… | Destructive confirm (UI-M-03) → roles admin API. | live |
| 4 | Matrix cells | Toggle role↔permission assignment (UI-S-24 pane). | live |
| 5 | Save matrix | Persist all assignment edits. Disabled until dirty. | live |
| 6 | Refresh | Re-fetch roles + assignments. | live |

---

## 4. Numbered journey — create a role and assign a permission

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/platform/roles` | Screen loads | roles admin API | Role list + matrix panes. |
| **2** | list | Click **New role** → name it | roles admin API | New row in the list. |
| **3** | matrix | Toggle a permission cell for that role | — | Cell dirty → **Save matrix** enabled. |
| **4** | matrix | Click **Save matrix** | roles admin API | Assignments persisted. |
| **5** | list | **Delete role…** → confirm | UI-M-03 → roles admin API | Role removed; its column drops. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading roles…” — skeleton rows. |
| empty | “No roles defined yet. Create the first role to get started.” |
| error | “Roles could not be loaded. Retry, or check that the somaAgent01 API is reachable.” |
| dirty | **Save matrix** enabled. |
| save fail | “Matrix was not saved. Your edits are still here — try again.” |
| permission-denied | Read-only; “Role administration requires the platform-admin role.” |
| offline | “Role actions are unavailable offline.” |

---

## 6. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Delete role… | UI-M-03 | “Delete ‹role.name›? Assignments will be removed.” Cancel / Delete (destructive). |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

---

## 7. Honesty

Role and permission names come from the store. No invented permission sets or counts.
One surface for all four route aliases (DUP-7).

---

## 8. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:164-166` | `/platform/roles` · `/platform/role-matrix` · `/soma/permissions` · `/platform/permissions` → `soma-admin-roles-list` |
| `webui/src/views/soma-admin-roles-list.ts` | Live screen (catalogue + matrix panes) |
| `SOMA-UI-NAV-AUDIT-001.md` §3 DUP-7 | Roles/permissions are panes of one screen |

End of Document
