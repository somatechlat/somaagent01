# UI-S-29 — Login

**Login** — Public pre-auth workspace (chrome shown signed-out) — route `/login` — facet **Auth**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ capsule: <capsule.name>                                                                         │
│ version: <version>    lifecycle: <lifecycle>                                                    │
│ persona knobs: (IQ -)(auto -)(budget -)   [signed out]                                          │
│ derived AgentIQ RO: -   (no session)                                                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ facet tabs x6:  [Soul][Brain][Hands][Memory][Body][Governance]                                  │
│ command palette: <Cmd-K>                                                                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ WORKSPACE  facet: Auth                                                 │ SURFACE RAIL x8        │
│  route: /login                                                         │  [1] Files             │
│             ┌────────────────────────────────┐                         │  [2] Tools             │
│             │  SOMA                          │                         │  [3] Browser           │
│             │  Cognitive AI Agent            │                         │  [4] Editor            │
│             │                                │                         │  [5] Debug             │
│             │  Email                         │                         │  [6] Capsule           │
│             │  ┌──────────────────────────┐  │                         │  [7] Brain             │
│             │  │ <user.email>              │  │                        │  [8] Desktop           │
│             │  └──────────────────────────┘  │                         │       GATED (UI-X-08)  │
│             │  Password          [show/hide] │                         │                        │
│             │  ┌──────────────────────────┐  │                         │                        │
│             │  │ ********                   │  │                       │                        │
│             │  └──────────────────────────┘  │                         │                        │
│             │  [ ] Remember me  Forgot password?                       │                        │
│             │                                │                         │                        │
│             │  [ Sign in                   ] │                         │                        │
│             │  ------- or continue with ----- │                        │                        │
│             │  [G] Google [M] Microsoft [S] SAML                       │                        │
│             │  Don't have an account? Sign up │                        │                        │
│             └────────────────────────────────┘                         │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <signed out>                                               │
│ neuro meters x4 (RO): DA -  5-HT -  NE -  ACh -   synced -                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-061 | email input | type=email. Required. |
| 2 | UI-C-062 | password input | Masked. Write-only. Never echoed back. |
| 3 | UI-C-066 | Remember me checkbox | Session persistence preference only. |
| 4 | UI-C-076 | Forgot password? link | Routes to /forgot-password (UI-S-31). |
| 5 | UI-C-067 | Sign in (primary) | disabled-while: request in flight. |
| 6 | UI-C-083 | OAuth provider buttons | Google / Microsoft / SAML. Rendered only when the provider is actually configured — omitted otherwise, never faked. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** Not applicable — the form is always present.
- **Error.** "Sign-in failed. ‹ reason from API ›"
- **Permission-denied.** "This account is not allowed to sign in. Contact your administrator."
- **Offline.** "You're offline. Sign-in needs a connection."

**Modal overlays.** None. This screen opens no overlay.
