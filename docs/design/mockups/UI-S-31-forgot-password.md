# UI-S-31 — Forgot password (Agent Soma)

Screen UI-S-31 · Route: `/forgot-password` · Facet: Auth · Public (no session)  
Live: `webui/src/views/soma-forgot-password.ts` · Router: `webui/src/main.ts`  
Next: email link → `/reset-password` → `/login` (UI-S-29).

**Product:** Agent Soma. Standalone auth screen (not the signed-in workspace chrome).  
Forbidden on screen: the word "slot" · SaaS / Eye of God branding · fake metrics · facet tabs · surface rail · IQ knobs.

---

## 1. Purpose

Request a password-reset link by email. Response is deliberately generic — the UI must not reveal whether the account exists.

---

## 2. ASCII wireframe — `/forgot-password` (desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                              │
│                         ┌────────────────────────────────┐                                   │
│                         │  SOMA                          │                                   │
│                         │  Cognitive AI Agent            │                                   │
│                         │                                │                                   │
│                         │  Reset your password           │                                   │
│                         │                                │                                   │
│                         │  Enter the email you signed up │                                   │
│                         │  with. We'll send a reset link │                                   │
│                         │  if the account exists.        │                                   │
│                         │                                │                                   │
│                         │  Email                         │                                   │
│                         │  ┌──────────────────────────┐  │                                   │
│                         │  │ name@company.com         │  │                                   │
│                         │  └──────────────────────────┘  │                                   │
│                         │                                │                                   │
│                         │  [ Send reset link           ] │                                   │
│                         │                                │                                   │
│                         │  Back to sign in               │                                   │
│                         └────────────────────────────────┘                                   │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Chrome law.** Standalone auth screen. No chat top, no left rail, no canvas, no facet tabs, no surface rail.

---

## 3. User journey (numbered clicks)

1. `/forgot-password` (logged-out) → form renders, Email focused.
2. Type email address.
3. Click **Send reset link** → spinner `Sending...`.
4. Success → generic confirmation `If that email is registered, a reset link is on its way.` (never reveals account existence).
5. Click **Back to sign in** → `/login` (UI-S-29).
6. (Off-screen) User opens email link → `/reset-password` → sets new password → `/login`.

---

## 4. Control map

| # | Control | Binding |
|---|---|---|
| 1 | Email input | `type=email`. Required. RFC 5322 check. |
| 2 | Send reset link (primary) | `POST /api/v2/auth/forgot-password`. Response is deliberately generic. disabled-while: request in flight. |
| 3 | Back to sign in link | href `/login` → UI-S-29. |

---

## 5. Field / behavior

| Field | Source | Behavior |
|---|---|---|
| email | `_email` | Required. Inline "Please enter a valid email address" on blur. |
| request | `POST /api/v2/auth/forgot-password` | Body: email. Response is generic regardless of account existence. |
| success | generic copy | `If that email is registered, a reset link is on its way.` |
| failure | API error message | Inline banner. Never a fabricated reason. |

---

## 6. States (verbatim)

| State | Verbatim |
|---|---|
| loading | `Sending...` |
| default | Form always present — empty state N/A |
| field error | `Please enter a valid email address` |
| success (generic) | `If that email is registered, a reset link is on its way.` |
| error | `Couldn't send the reset link. ‹ reason from API ›` |
| permission | `Password reset is disabled for this deployment. Contact your administrator.` |
| offline | `You're offline. Password reset needs a connection.` |

---

## 7. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/forgot-password` | Public path. From UI-S-29 "Forgot?" link. |
| Out | `/login` | UI-S-29. Back to sign in. |
| Out | `/reset-password` | Via email link (off-screen). |
| — | `/memory` | Not reachable from this screen before auth. |

---

## 8. Acceptance

- [ ] No facet tabs, surface rail, IQ knobs, or workspace chrome
- [ ] Generic success copy — never reveals account existence
- [ ] All copy verbatim per §6

End of Document
