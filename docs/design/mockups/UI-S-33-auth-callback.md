# UI-S-33 — Auth callback (Agent Soma)

Screen UI-S-33 · Route: `/auth/callback` · Facet: Auth · Public (transient)  
Live: `webui/src/views/soma-auth-callback.ts` · Router: `webui/src/main.ts`  
Success → **UI-S-07 State A welcome** (`/chat`). Failure → `/login` (UI-S-29).

**Product:** Agent Soma. Standalone transient auth screen.  
Forbidden on screen: the word "slot" · SaaS / Eye of God branding · fake metrics · facet tabs · surface rail · IQ knobs.

---

## 1. Purpose

Complete an OAuth/SSO exchange after the provider redirects back. Transient — resolves to `/chat` on success or `/login` on failure. No workspace chrome.

---

## 2. ASCII wireframe — `/auth/callback` (desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                              │
│                         ┌────────────────────────────────┐                                   │
│                         │                                │                                   │
│                         │           (spinner)            │                                   │
│                         │                                │                                   │
│                         │   Completing sign-in...        │                                   │
│                         │                                │                                   │
│                         │   provider: <oauth.provider>   │                                   │
│                         │   state: <auth.state>          │                                   │
│                         │                                │                                   │
│                         │   Do not close this window.    │                                   │
│                         │                                │                                   │
│                         │   [ Cancel → sign in ]         │                                   │
│                         │                                │                                   │
│                         └────────────────────────────────┘                                   │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Chrome law.** Standalone transient screen. No chat top, no left rail, no canvas, no facet tabs, no surface rail.

---

## 3. User journey (numbered clicks)

1. OAuth provider redirects to `/auth/callback?code=…&state=…`.
2. Screen shows spinner `Completing sign-in...` with live provider/state readout.
3. Exchange completes → navigate to **UI-S-07 State A welcome** (`/chat`): thin chat top, composer hero.
4. On failure → navigate to `/login` (UI-S-29) with error banner.
5. Click **Cancel → sign in** at any time → abort exchange → `/login`. No partial session minted.

---

## 4. Control map

| # | Control | Binding |
|---|---|---|
| 1 | Status progress panel | Non-interactive readout of the OAuth exchange. Values from the callback query — never fabricated. |
| 2 | Cancel → sign in | Aborts the exchange and routes to `/login`. Does not mint a partial session. |

---

## 5. Field / behavior

| Field | Source | Behavior |
|---|---|---|
| provider | callback query `provider` | Read-only label. |
| state | callback query `state` | Read-only. Short token. |
| exchange | `POST /api/v2/auth/callback` | Body: code + state. Server completes the OAuth exchange. |
| success | API `redirect_path` | Navigate to `redirect_path` or `/chat` → UI-S-07 State A. |
| failure | API error message | Navigate to `/login` with error banner. |

---

## 6. States (verbatim)

| State | Verbatim |
|---|---|
| loading | `Completing sign-in...` |
| loading | `Do not close this window.` |
| success | (navigates away — no success state on this screen) |
| error | `Sign-in was cancelled or failed. ‹ reason from API ›` |
| permission | `This sign-in method is not enabled for your account. ‹ reason from API ›` |
| offline | `You're offline. Sign-in needs a connection.` |

---

## 7. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/auth/callback` | OAuth/SSO provider redirect. |
| Out | `/chat` (UI-S-07 State A welcome) | After successful exchange. |
| Out | `/login` | On failure or Cancel. UI-S-29. |

---

## 8. Acceptance

- [ ] No facet tabs, surface rail, IQ knobs, or workspace chrome
- [ ] Transient — no interactive chrome beyond Cancel
- [ ] Success lands on UI-S-07 State A welcome (thin chat top, composer hero)
- [ ] All copy verbatim per §6

End of Document
