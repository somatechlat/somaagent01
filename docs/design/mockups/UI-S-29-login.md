# UI-S-29 — Login (Agent Soma)

Screen UI-S-29 · Route: `/login` · Facet: Auth · Public (no session)  
Live: `webui/src/views/soma-login.ts` · Router: `webui/src/main.ts:34-63`  
First screen after login: **UI-S-07 welcome empty chat** (`/chat`).

**Product:** Agent Soma. Standalone auth screen (not the signed-in workspace chrome).  
Forbidden on screen: the word “slot” · SaaS / Eye of God branding · fake metrics.

---

## 1. Purpose

Establish a session (email/password, Google, or configured SSO) and land the user on the chat
workspace in its welcome/empty state. No surface rail, no facet tabs, no Memory UI on this screen.

---

## 2. ASCII wireframe — `/login` (live `soma-login.ts`)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                              │
│                         ┌────────────────────────────────┐                                   │
│                         │  SOMA                          │                                   │
│                         │  Cognitive AI Agent            │                                   │
│                         │                                │                                   │
│                         │  [G] Continue with Google      │                                   │
│                         │  [SSO] Continue with SSO       │                                   │
│                         │  ------- or sign in -------    │                                   │
│                         │  Email                         │                                   │
│                         │  ┌──────────────────────────┐  │                                   │
│                         │  │ name@company.com         │  │                                   │
│                         │  └──────────────────────────┘  │                                   │
│                         │  Password          [show/hide] │                                   │
│                         │  ┌──────────────────────────┐  │                                   │
│                         │  │ ••••••••                 │  │                                   │
│                         │  └──────────────────────────┘  │                                   │
│                         │  [ ] Remember me    Forgot?    │                                   │
│                         │                                │                                   │
│                         │  [ Sign in                   ] │                                   │
│                         │  Don't have an account? Get started                                 │
│                         └────────────────────────────────┘                                   │
│                                                                                              │
│  SSO modal (on [SSO]): provider ▾ + provider fields + Test connection + Save                  │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### First screen after login — UI-S-07 State A (Welcome)

Canonical: `UI-S-07-chat-workspace.md` §1 (A0-merged: composer + banners + quick actions + **Connect Channels** + **System Resources**).

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ A  [≡] [S] SOMA          ‹clock›  ● Connected  🔔  ▢ ‹project› ▾                              │
├──────────────┬───────────────────────────────────────────────────────────────┬───────────────┤
│ B LEFT       │ C WELCOME                                                    │ D CANVAS 56px │
│ Search       │   Hello! I'm Soma 👋                                         │ Files/Tools/… │
│ + New chat   │   How can I help you today?                                  │ NO Memory tab │
│ chats        │   [ Message Soma…                                     ➤ ]    │               │
│ ──           │   banners (real /banners)                                    │               │
│ 🧠 Memory    │   [Memory][Files][Tasks][Modules][Settings]                  │               │
│ ⚙ Settings   │   Connect Channels: [Telegram][WhatsApp][Email]              │               │
│ 👤 user      │   System Resources: RAM · CPU · Disk (real API)              │               │
│ [Sign out]   │   SomaTech · Cognitive AI Agent                              │               │
├──────────────┴───────────────────────────────────────────────────────────────┴───────────────┤
│ E ready · recall — · model ‹live›                                                            │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Quick Actions:** New chat · Files · Agents · Settings · Voice · Brain.

---

## 3. Control map (UI-C / UI-A → live code)

| # | UI-C / UI-A | Control | Live binding |
|---|---|---|---|
| 1 | UI-C-083 | Continue with Google | `soma-login.ts:675` → `_handleGoogleSignIn` `889-895` |
| 2 | UI-C-083 | Continue with SSO | `soma-login.ts:685` → SSO modal (`_showSSOModal`) with real provider field sets `34-117` |
| 3 | UI-C-061 | Email input | `type=email` `soma-login.ts:700-706`; RFC 5322 check `600-640` |
| 4 | UI-C-062 | Password input | masked; `minlength=8`; show/hide `712-716`; never echoed back |
| 5 | UI-C-062 | Show / hide password toggle | `soma-login.ts:716` |
| 6 | UI-C-066 | Remember me | `soma-login.ts:725-728` (`_rememberMe`) |
| 7 | UI-C-076 | Forgot? | href `/forgot-password` `soma-login.ts:710` → UI-S-31 |
| 8 | UI-C-067 | Sign in (primary) | `_handleLogin` `835-883` → POST `/api/v2/auth/login` `857` |
| 9 | UI-C-076 | Get started | href `/register` `soma-login.ts:667` → UI-S-30 |
| 10 | — | Inline error banner | `soma-login.ts:671` (`_error`) |

**Post-login navigation (real):** `window.location.href = result.redirect_path || '/chat'` (`soma-login.ts:881`) → **UI-S-07 State A welcome** (thin chat top, composer hero).  
**Already signed-in:** `/login` redirects to `/chat` (`main.ts:54-57`).

**Not offered on this screen:** Microsoft / SAML one-click buttons (SSO goes through the configured provider modal only) · Memory UI · surface rail · metrics.

---

## 4. Field / behavior table

| Field | Source | Behavior |
|---|---|---|
| email | form state `_email` | Required. Inline “Please enter a valid email address” on blur (`638`). Cleared on retype (`627-629`). |
| password | `_password` | Required, min 8 (`854`). Write-only — never rendered back. |
| remember me | `_rememberMe` | Session persistence preference only. |
| sign-in request | POST `/api/v2/auth/login` | Body: email + password. Disabled while `_isLoading` (spinner + “Signing in...” `732`). |
| success | API `redirect_path` | Navigate to `redirect_path` or `/chat` (`881`). |
| failure | API error message | “Sign-in failed. ‹ reason from API ›” / `_error` (`883`). |
| Google | OAuth helper | Real flow or error “Google sign-in failed” (`895`). |
| SSO modal | provider catalog `34-117` | oidc · saml · ldap · ad · okta · azure · ping · onelogin. Fields are provider-specific. Test connection hits the real endpoint (`925-931`). |
| validation | `_validateEmail` | RFC 5322 regex, max 254 chars (`611-619`). |

---

## 5. States (verbatim copy)

| State | Verbatim |
|---|---|
| loading | “Signing in...” (`soma-login.ts:732`) |
| empty / default | Form always present — empty state N/A |
| field error | “Please enter a valid email address” |
| field error | “Password must be at least 8 characters” |
| field error | “Please enter both email and password” |
| error | “Sign-in failed. ‹ reason from API ›” |
| error (generic) | “Login failed” (`883`) |
| permission | “This account is not allowed to sign in. Contact your administrator.” |
| offline | “You're offline. Sign-in needs a connection.” |
| SSO test ok | (provider test success message from API) |
| SSO test fail | “Connection failed. Please verify your configuration.” / “Network error. Please check your connection and try again.” (`927`, `931`) |

### Welcome empty chat (first screen after login) — verbatim from UI-S-07 State A

Canonical: `mockups/UI-S-07-chat-workspace.md` §1. Thin chat top. Composer is the hero.

| State | Verbatim |
|---|---|
| welcome heading | `Welcome back, ‹first name›` (or `Welcome` if no name) |
| welcome sub | `What are we working on today?` |
| composer placeholder | `Message Soma…` |
| empty list | `No conversations yet. Start a new chat to begin.` |
| memory (C2) | `🧠 recall 0 · nothing this turn · [Open Memory]` |

**No Memory / Models / Channels / Settings / Brain cards on welcome.** Thin chat top (time · connection · notifications · project).

---

## 6. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/login` | Public path (`main.ts:35`). |
| In | `/logout` → `/login` | Session cleared server-side first (`soma-chat.ts:1846-1861`). |
| Out | `/chat` (UI-S-07 welcome) | After successful sign-in (`soma-login.ts:881`). |
| Out | `/forgot-password` | UI-S-31. |
| Out | `/register` | UI-S-30. |
| Out | `/auth/callback` | UI-S-33 (OAuth return). |
| — | `/memory` | Not reachable from this screen before auth. |

---

## 7. Test clicks

1. `/login` logged-out → form renders; no metrics, no surface rail, no Memory UI.
2. Invalid email blur → “Please enter a valid email address”.
3. Password &lt; 8 → “Password must be at least 8 characters”.
4. Valid credentials + **Sign in** → spinner "Signing in..." → land on **UI-S-07 State A welcome** (thin chat top, composer hero, no Memory/Models cards).
5. **Forgot?** → `/forgot-password`. **Get started** → `/register`.
6. **Continue with Google** → real OAuth or “Google sign-in failed”.
7. **Continue with SSO** → modal; **Test connection** returns the API result; Save writes config.
8. Revisit `/login` while signed-in → redirected to `/chat` (`main.ts:54-57`).
9. From UI-S-07 **logout** → `/login`.
10. Confirm welcome chat has **no Memory card** and no canvas Memory tab.

---

## 8. Code verified

| File:line | What |
|---|---|
| `webui/src/views/soma-login.ts:34-117` | SSO provider catalog + field sets |
| `webui/src/views/soma-login.ts:587-597` | form state |
| `webui/src/views/soma-login.ts:648-732` | render: OAuth, email, password, remember, submit |
| `webui/src/views/soma-login.ts:835-883` | `_handleLogin` → POST `/api/v2/auth/login` → `/chat` |
| `webui/src/views/soma-login.ts:889-895` | `_handleGoogleSignIn` |
| `webui/src/main.ts:34-63` | public paths, `/login` redirect when authed |
| `webui/src/views/soma-chat.ts:2270-2312` | welcome empty chat actions — **GAP**: code still shows Models/Channels; must be task starters only per IA |
| `webui/src/views/soma-chat.ts:1846-1861` | logout → `/login` |

End of Document
