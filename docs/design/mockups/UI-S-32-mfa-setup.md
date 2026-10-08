# UI-S-32 — MFA setup (Agent Soma)

Screen UI-S-32 · Route: `/mfa/setup` (alias `/settings/mfa`) · Authenticated  
Live: `webui/src/views/soma-mfa-setup.ts` · Router: `webui/src/main.ts`  
Entry: UI-S-34 personal profile → **Manage MFA**. After save → back to `/profile`.

**Product:** Agent Soma account security. Thin workspace chrome. Not a Settings section.  
Forbidden on screen: the word "slot" · SaaS / Eye of God branding · fake metrics · facet tabs · surface rail · IQ knobs · chat left rail.

---

## 1. Purpose

Enroll a second factor (TOTP authenticator app), verify a code, and manage recovery codes. This is account security — not agent configuration. Not one of the 7 Settings sections.

---

## 2. ASCII wireframe — `/mfa/setup` (desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ [←]  SOMA · Account security                          [Save] [Cancel]                         │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  MFA setup                                                                                   │
│  Protect your account with a second factor.                                                  │
│                                                                                              │
│  ┌── Authenticator app ──────────────────────────────────────────────┐                        │
│  │ 1. Scan the QR code                                              │                        │
│  │    ┌────────┐                                                     │                        │
│  │    │ QR from <otpauth-uri>                                        │                        │
│  │    └────────┘                                                     │                        │
│  │ 2. Or enter the key (masked)                                     │                        │
│  │    ••••••••••••aBcD   note: rotate in Vault                       │                        │
│  │ 3. Enter the 6-digit code                                        │                        │
│  │    ┌──────┐                                                       │                        │
│  │    │ **** │                                                       │                        │
│  │    └──────┘                                                       │                        │
│  └────────────────────────────────────────────────────────────────────┘                        │
│                                                                                              │
│  Recovery codes                              [Generate new codes]                             │
│  │ <recovery-code> [copy] │  shown once, then masked                                          │
│  │ <recovery-code> [copy] │                                                                  │
│                                                                                              │
│  [Disable MFA]  (destructive — opens confirm dialog)                                         │
│                                                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ status: <save state> · permission: authenticated session required                             │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Chrome law.** Thin workspace top ([←] back · brand · Save/Cancel). No chat left rail, no canvas, no facet tabs, no surface rail, no Settings section nav. MFA is account security, not a Settings section.

---

## 3. User journey (numbered clicks)

1. `/profile` (UI-S-34) → click **Manage MFA** → `/mfa/setup`.
2. Scan QR with authenticator app (or copy masked key).
3. Enter the 6-digit code from the app.
4. Click **Save** → spinner `Verifying...`.
5. Success → recovery codes shown once → **[copy]** each → store offline.
6. Click **Generate new codes** (if needed) → confirm dialog → new codes shown once.
7. Click **Cancel** or **[←]** → back to `/profile`.

---

## 4. Control map

| # | Control | Binding |
|---|---|---|
| 1 | TOTP QR display | QR from `<otpauth-uri>`. Full-screen on click (UI-M-02). |
| 2 | Shared secret (masked) | Renders `••••••••••••aBcD` with "rotate in Vault" note — never a real value. |
| 3 | Verification code input | 6 digits. Server-validated. |
| 4 | Save (primary, header) | `POST /api/v2/auth/mfa/verify`. disabled-until: a valid code is entered. |
| 5 | Cancel (secondary, header) | Back to `/profile`. Does not mint a partial enrollment. |
| 6 | Recovery codes block | Shown once at generation, then masked. [copy] writes to clipboard. |
| 7 | Generate new codes (secondary) | `POST /api/v2/auth/mfa/recovery-codes`. Invalidates prior codes. Confirmation via UI-M-03. |
| 8 | Disable MFA (destructive) | `DELETE /api/v2/auth/mfa`. Opens UI-M-03. disabled-when: MFA not enabled — disabled-reason: `MFA is not enabled on this account.` |

---

## 5. Field / behavior

| Field | Source | Behavior |
|---|---|---|
| otpauth URI | `GET /api/v2/auth/mfa/setup` | Generates QR. Secret renders masked only. |
| verification code | `_code` | 6 digits. Required to Save. |
| recovery codes | API response | Shown once at generation, then masked. |
| MFA status | `GET /api/v2/auth/me` | `mfa_enabled: bool`. Drives Disable button state. |

---

## 6. States (verbatim)

| State | Verbatim |
|---|---|
| loading | `Verifying...` |
| empty | `No recovery codes generated yet. Generate codes and store them offline.` |
| field error | `Enter the 6-digit code from your authenticator app` |
| error | `Couldn't verify the code. ‹ reason from API ›` |
| permission | `MFA setup requires an authenticated session. Sign in first.` |
| offline | `You're offline. MFA setup needs a connection.` |
| already enabled | `MFA is already enabled on this account.` |

---

## 7. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/mfa/setup` | From UI-S-34 **Manage MFA**. |
| In | `/settings/mfa` | Alias route. Same view. |
| Out | `/profile` | Cancel / [←] / after successful save. |
| Out | `/login` | If session expired. |

---

## 8. Modal overlays

- **UI-M-02** Full-screen — QR code for scanning (explicit dismiss only).
- **UI-M-03** Dialog — `Disable MFA on this account?` (destructive) and `Regenerate recovery codes? Existing codes will stop working.`

---

## 9. Acceptance

- [ ] No facet tabs, surface rail, IQ knobs, chat left rail, or Settings section nav
- [ ] Secret always masked — never a real value on screen
- [ ] Recovery codes shown once, then masked
- [ ] All copy verbatim per §6

End of Document
