# UI-S-34 — Personal profile (Agent Soma)

Screen UI-S-34 · Route: `/profile` · Authenticated  
Live: `webui/src/views/soma-personal-profile.ts` · Router: `webui/src/main.ts`  
Entry: chat left rail → **👤 user** → `/profile`. Not a Settings section.

**Product:** Agent Soma account profile. Thin workspace chrome.  
Forbidden on screen: the word "slot" · SaaS / Eye of God branding · fake metrics · facet tabs · surface rail · IQ knobs · chat left rail · canvas.

---

## 1. Purpose

View and edit the signed-in user's identity, manage account security (password, MFA), and review active sessions. Own workspace chrome — no chat rail (only `/chat` mounts the chat rail).

---

## 2. ASCII wireframe — `/profile` (desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ [←]  SOMA · Profile                                    [Save] [Cancel]                        │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  Personal profile                                                                            │
│                                                                                              │
│  Identity                                                                                    │
│  ┌── avatar ──┐  Display name  ┌─────────────────────┐                                        │
│  │  <avatar>  │  │ <user.name>    │                                       │
│  └────────────┘  └─────────────────────┘                                        │
│  [Upload avatar]  Email  <user.email>  (read-only)                                          │
│                                                                                              │
│  Security                                                                                    │
│  [Change password]  [Manage MFA → /mfa/setup]  [Sign out everywhere]                         │
│                                                                                              │
│  Active sessions                                                                             │
│  | device | ip | last seen | current | [revoke] |                                            │
│  | <ua>   | <ip> | <ts>    | yes/no  | [revoke] |                                            │
│  | <ua>   | <ip> | <ts>    | yes/no  | [revoke] |                                            │
│                                                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ status: <save state> · permission: own account only                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Chrome law.** Thin workspace top ([←] back · brand · Save/Cancel). No chat left rail, no canvas, no facet tabs, no surface rail. Only `/chat` mounts the chat rail.

---

## 3. User journey (numbered clicks)

1. In chat (UI-S-07) → click **👤 user** in left rail → `/profile`.
2. Edit **Display name**.
3. Click **Upload avatar** → pick image → avatar previews.
4. Click **Save** → spinner `Saving...` → confirmation.
5. Click **Manage MFA** → `/mfa/setup` (UI-S-32).
6. Click **Change password** → password dialog → current + new + confirm → Save.
7. In **Active sessions** → click **[revoke]** on a row → confirm dialog → session revoked.
8. Click **Sign out everywhere** → confirm dialog → all sessions revoked → `/login`.
9. Click **[←]** → back to `/chat`.

---

## 4. Control map

| # | Control | Binding |
|---|---|---|
| 1 | Avatar display / Upload avatar | Real upload or letter fallback — never a stock image. |
| 2 | Display name input | Editable. `PUT /api/v2/auth/me` or profile endpoint. |
| 3 | Email readout | Read-only. Email change is a separate verified flow — never drawn as editable here. |
| 4 | Save (primary, header) | Saves identity fields. disabled-while: request in flight. |
| 5 | Cancel (secondary, header) | Restores last saved values. |
| 6 | Change password | Opens password dialog (UI-M-01). |
| 7 | Manage MFA | href `/mfa/setup` → UI-S-32. |
| 8 | Active sessions list | `GET /api/v2/auth/sessions`. No session rows invented. |
| 9 | [revoke] (per row) | `DELETE /api/v2/auth/sessions/{id}` via UI-M-03 confirm. |
| 10 | Sign out everywhere (destructive) | `POST /api/v2/auth/logout-all`. Opens UI-M-03. |

---

## 5. Field / behavior

| Field | Source | Behavior |
|---|---|---|
| avatar | upload / letter fallback | Real upload or first-letter fallback. Never a stock image. |
| display name | `_displayName` | Editable. Required. |
| email | `GET /api/v2/auth/me` | Read-only on this screen. |
| sessions | `GET /api/v2/auth/sessions` | Rows: device · ip · last seen · current. |
| password change | `POST /api/v2/auth/change-password` | Current + new + confirm. Write-only. |

---

## 6. States (verbatim)

| State | Verbatim |
|---|---|
| loading | `Loading profile...` |
| empty | `No active sessions to show.` |
| error | `Couldn't load your profile. ‹ reason from API ›` |
| permission | `You don't have access to this profile. Sign in with your own account.` |
| offline | `You're offline. Changes will not be saved until the connection returns.` |
| save ok | `Profile updated.` |

---

## 7. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/profile` | From chat left rail 👤 user chip. |
| Out | `/chat` | [←] back. |
| Out | `/mfa/setup` | Manage MFA → UI-S-32. |
| Out | `/login` | Sign out everywhere / session revoked. |

---

## 8. Modal overlays

- **UI-M-01** Drawer — Change password (current + new + confirm, all write-only).
- **UI-M-03** Dialog — `Sign out of all sessions, including this one?` (destructive). Per-row [revoke] uses the same dialog pattern.

---

## 9. Acceptance

- [ ] No facet tabs, surface rail, IQ knobs, chat left rail, or canvas
- [ ] Real routes: `/profile`, `/mfa/setup`
- [ ] Email is read-only on this screen
- [ ] Sessions list from real API — no invented rows
- [ ] All copy verbatim per §6

End of Document
