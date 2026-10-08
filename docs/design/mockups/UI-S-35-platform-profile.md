# UI-S-35 — Platform profile (Agent Soma)

Screen UI-S-35 · Route: `/admin/profile` (same view as `/platform/profile`) · Platform-admin only  
Live: `webui/src/views/soma-platform-profile.ts` · Router: `webui/src/main.ts`  
Entry: platform admin nav → `/admin/profile`. Not a Settings section.

**Product:** Agent Soma platform identity. Thin workspace chrome.  
Forbidden on screen: the word "slot" · SaaS / Eye of God branding · fake metrics · facet tabs · surface rail · IQ knobs · chat left rail · canvas.

---

## 1. Purpose

Manage platform-level identity (name, support contact) and the platform signing key. Platform-admin only. Own workspace chrome — no chat rail.

---

## 2. ASCII wireframe — `/admin/profile` (desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ [←]  SOMA · Platform profile                           [Save] [Cancel]                        │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  Platform profile                                                                            │
│                                                                                              │
│  Platform identity                                                                           │
│  Name            ┌──────────────────────────┐                                                 │
│                  │ <platform.name>          │                                                 │
│  Support contact └──────────────────────────┘                                                 │
│                  │ <platform.support_email> │                                                 │
│                  ┌──────────────────────────┐                                                 │
│                                                                                              │
│  Operator identity (this account)                                                            │
│  Role chips: <role>  <role>   Display name ┌────────────────┐                                 │
│                                 │ <user.name>    │                                          │
│                                 ┌────────────────┘                                          │
│                                                                                              │
│  Danger zone                                                                                 │
│  [Rotate platform signing key]  (opens UI-M-03)                                              │
│  secrets render masked ••••••••••••aBcD  note: rotate in Vault                               │
│                                                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ status: <save state> · permission: platform-admin required                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Chrome law.** Thin workspace top ([←] back · brand · Save/Cancel). No chat left rail, no canvas, no facet tabs, no surface rail.

---

## 3. User journey (numbered clicks)

1. Platform admin nav → `/admin/profile`.
2. Edit **Name** and **Support contact**.
3. Click **Save** → spinner `Saving...` → confirmation.
4. Click **Rotate platform signing key** → UI-M-03 confirm dialog → key rotated (new key shown masked once).
5. Click **[←]** → back to platform admin nav.

---

## 4. Control map

| # | Control | Binding |
|---|---|---|
| 1 | Platform name input | Platform display name. No default value invented. |
| 2 | Support contact input | `type=email`. |
| 3 | Operator identity display | Current account; role chips from the session. |
| 4 | Save (primary, header) | Saves platform identity fields. disabled-while: request in flight. |
| 5 | Cancel (secondary, header) | Restores last saved values. |
| 6 | Signing key readout (masked) | Renders `••••••••••••aBcD` with "rotate in Vault" note. Never a real value, never editable. |
| 7 | Rotate platform signing key (destructive) | Opens UI-M-03. disabled-when: not platform admin — disabled-reason: `Requires the platform-admin role.` |

---

## 5. Field / behavior

| Field | Source | Behavior |
|---|---|---|
| platform name | `GET/PUT /api/v2/platform/profile` | Editable. |
| support contact | `GET/PUT /api/v2/platform/profile` | `type=email`. Editable. |
| operator roles | session / `GET /api/v2/auth/me` | Read-only chips. |
| signing key | Vault | Always masked. Rotate via UI-M-03 confirm. |

---

## 6. States (verbatim)

| State | Verbatim |
|---|---|
| loading | `Loading platform profile...` |
| empty | `No platform profile stored yet. Fill in the name and support contact.` |
| error | `Couldn't load the platform profile. ‹ reason from API ›` |
| permission | `You don't have access to platform profile. Requires the platform-admin role.` |
| offline | `You're offline. Changes will not be saved until the connection returns.` |
| save ok | `Platform profile updated.` |

---

## 7. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/admin/profile` | Platform admin nav. Alias: `/platform/profile`. |
| Out | platform admin nav | [←] back. |
| Out | `/login` | If session expired. |

---

## 8. Modal overlays

- **UI-M-03** Dialog — `Rotate the platform signing key? Existing signatures will need re-signing.` (destructive).

---

## 9. Acceptance

- [ ] No facet tabs, surface rail, IQ knobs, chat left rail, or canvas
- [ ] Real routes: `/admin/profile` · `/platform/profile`
- [ ] Signing key always masked — never a real value
- [ ] All copy verbatim per §6

End of Document
