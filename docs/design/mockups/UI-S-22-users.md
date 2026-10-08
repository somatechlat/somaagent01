# UI-S-22 — Users

Screen UI-S-22 · Routes: **`/admin/users`** (`main.ts:224` → `soma-entity-views` → `soma-users-view`)
· **`/admin/users/:id`** (`main.ts:231` → `soma-user-detail`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/soma-entity-views.ts` (`soma-users-view`)

**Status: LIVE.** Agent-admin user list + detail pane. No chat canvas, no facet tabs, no IQ knobs.

---

## 1. ASCII wireframe — users workspace

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  USERS                                                                  [⟳ Refresh]             │
│  [Search users…                     ]  role [all ▾]                                              │
│                                                                                                  │
│  ┌─ USER TABLE (server order) ───────────────────────────────────────────────────────────────┐  │
│  │ name              email                      role             status         [⋯]          │  │
│  │ ‹name›            ‹email›                    ‹role | —›       ‹status | —›                │  │
│  │ ‹name›            ‹email›                    ‹role | —›       ‹status | —›                │  │
│  │ (scroll)                                                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  total: ‹n | —› users                                                            [Open detail]  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Detail pane (`/admin/users/:id` → `soma-user-detail`) opens over the list:

```
┌─ USER DETAIL ──────────────────────────────────────────┐
│  name      ‹name›                                      │
│  email     ‹email›                                     │
│  role      ‹role | —›                                  │
│  status    ‹status | —›                                │
│  user_id   ‹id›                                        │
│                                                         │
│  [Save]  [Close]                       ← Back to list  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Real data

List from the users view (`soma-users-view`); detail from `soma-user-detail`
(`main.ts:224` and `main.ts:231`).

| UI field | Source | Absent handling |
|---|---|---|
| name | user record | required |
| email | user record | required |
| role | user record | `—` |
| status | user record | `—` |
| id | user record | read-only |

No invented plan/tier columns, no usage metrics, no MFA chips unless the record reports them.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Search | Client filter over loaded rows. | live |
| 2 | Role filter | Filter on `role` as stored. | live |
| 3 | User row | `name` · `email` · `role` · `status`. | live |
| 4 | Open detail | `router → /admin/users/{id}` (`soma-user-detail`). | live |
| 5 | Detail form | Edit → Save via the users admin API. | live |
| 6 | Refresh | Re-fetch the list. | live |
| 7 | Total | `—` until the server reports. | live |

---

## 4. Numbered journey — open and edit a user

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/admin/users` | Screen loads | users view | Table rows with real user fields. |
| **2** | list | Search `email` / filter `role` | client filter | Table narrows. |
| **3** | list | Click a row | `router → /admin/users/{id}` | Detail pane opens. |
| **4** | detail | Change `role` → **Save** | users admin API | Saved; list reflects the new role. |
| **5** | detail | Close | `router → /admin/users` | Back to the list. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading users…” — skeleton rows. |
| empty | “No users yet.” |
| empty (filter) | “No users match this filter. Clear the filter to see all.” |
| error | “Users could not be loaded. Retry, or check that the somaAgent01 API is reachable.” |
| not found (detail) | “User could not be loaded. They may have been deleted.” |
| permission-denied | “You do not have permission to manage users. Ask a platform admin for the platform-admin role.” |
| offline | “User actions are unavailable offline.” |

---

## 6. Honesty

Rows are real user-record fields only. Totals are `—` until the server reports. No fabricated
counts or metrics.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:224` | `/admin/users` → `soma-users-view` |
| `webui/src/main.ts:231` | `/admin/users/:id` → `soma-user-detail` |
| `webui/src/views/soma-entity-views.ts` | Live list |

End of Document
