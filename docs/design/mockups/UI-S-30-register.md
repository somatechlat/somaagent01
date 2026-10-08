# UI-S-30 — Register (Agent Soma)

Screen UI-S-30 · Route: `/register` · Facet: Auth · Public (no session)  
Live: `webui/src/views/soma-register.ts` · Router: `webui/src/main.ts`  
Post-register land: **UI-S-07 State A welcome** (`/chat`) — thin chat top, composer hero.

**Product:** Agent Soma. Standalone auth screen (not the signed-in workspace chrome).  
Forbidden on screen: the word "slot" · SaaS / Eye of God branding · fake metrics · facet tabs · surface rail · IQ knobs · Memory/Models/Channels cards.

---

## 1. Purpose

Create an account (email + password) and land on the chat workspace welcome state. No workspace chrome, no surface rail, no facet tabs on this screen.

---

## 2. ASCII wireframe — `/register` (desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                              │
│                         ┌────────────────────────────────┐                                   │
│                         │  SOMA                          │                                   │
│                         │  Cognitive AI Agent            │                                   │
│                         │                                │                                   │
│                         │  Create your account           │                                   │
│                         │                                │                                   │
│                         │  Display name                  │                                   │
│                         │  ┌──────────────────────────┐  │                                   │
│                         │  │ <user.name>              │  │                                   │
│                         │  └──────────────────────────┘  │                                   │
│                         │  Email                         │                                   │
│                         │  ┌──────────────────────────┐  │                                   │
│                         │  │ name@company.com         │  │                                   │
│                         │  └──────────────────────────┘  │                                   │
│                         │  Password          [show/hide] │                                   │
│                         │  ┌──────────────────────────┐  │                                   │
│                         │  │ ••••••••                 │  │                                   │
│                         │  └──────────────────────────┘  │                                   │
│                         │  Confirm password              │                                   │
│                         │  ┌──────────────────────────┐  │                                   │
│                         │  │ ••••••••                 │  │                                   │
│                         │  └──────────────────────────┘  │                                   │
│                         │  [ ] I accept the terms        │                                   │
│                         │                                │                                   │
│                         │  [ Create account            ] │                                   │
│                         │  Already have an account? Sign in                                  │
│                         └────────────────────────────────┘                                   │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Chrome law.** Standalone auth screen. No chat top, no left rail, no canvas, no facet tabs, no surface rail. See UI-S-00 §2 (auth routes are public).

---

## 3. User journey (numbered clicks)

1. `/register` (logged-out) → form renders, Display name focused.
2. Type display name → Email → Password → Confirm password.
3. Check **I accept the terms**.
4. Click **Create account** → spinner `Creating account...`.
5. Success → land on **UI-S-07 State A welcome** (`/chat`): thin chat top, composer hero, no Memory/Models cards.
6. Click **Sign in** link → `/login` (UI-S-29).

---

## 4. Control map

| # | Control | Binding |
|---|---|---|
| 1 | Display name input | form state `_displayName`. Required. Trimmed. |
| 2 | Email input | `type=email`. Required. RFC 5322 check. |
| 3 | Password input | Masked. `minlength=8`. Password rules render as server-provided text — never invented locally. |
| 4 | Confirm password input | Must match password. |
| 5 | Show / hide password toggle | toggles `type` on both password fields. |
| 6 | Terms checkbox | Required to submit. |
| 7 | Create account (primary) | `POST /api/v2/auth/register` → `redirect_path` or `/chat`. disabled-until: all required fields valid and terms accepted. |
| 8 | Sign in link | href `/login` → UI-S-29. |

---

## 5. Field / behavior

| Field | Source | Behavior |
|---|---|---|
| display name | `_displayName` | Required. Trimmed. Inline error on blur. |
| email | `_email` | Required. Inline "Please enter a valid email address" on blur. |
| password | `_password` | Required, min 8. Write-only — never rendered back. |
| confirm password | `_confirmPassword` | Must match `_password`. |
| terms | `_termsAccepted` | Required boolean. |
| register request | `POST /api/v2/auth/register` | Body: display name + email + password. Disabled while `_isLoading`. |
| success | API `redirect_path` | Navigate to `redirect_path` or `/chat` → UI-S-07 State A. |
| failure | API error message | Inline banner. Never a fabricated reason. |

---

## 6. States (verbatim)

| State | Verbatim |
|---|---|
| loading | `Creating account...` |
| default | Form always present — empty state N/A |
| field error | `Please enter a valid email address` |
| field error | `Password must be at least 8 characters` |
| field error | `Passwords do not match` |
| field error | `Please accept the terms to continue` |
| error | `Couldn't create the account. ‹ reason from API ›` |
| permission | `Self-registration is disabled for this deployment. Ask your administrator for an invitation.` |
| offline | `You're offline. Registration needs a connection.` |

---

## 7. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/register` | Public path. |
| Out | `/chat` (UI-S-07 State A welcome) | After successful registration. |
| Out | `/login` | UI-S-29. Already have an account? Sign in. |
| — | `/memory` | Not reachable from this screen before auth. |

---

## 8. Acceptance

- [ ] No facet tabs, surface rail, IQ knobs, or workspace chrome
- [ ] No Memory / Models / Channels / Settings cards
- [ ] Post-register lands on UI-S-07 State A welcome (thin chat top, composer hero)
- [ ] All copy verbatim per §6

End of Document
