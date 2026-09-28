# UI-S-31 — Forgot password

**Forgot password** — Public pre-auth workspace (chrome shown signed-out) — route `/forgot-password` — facet **Auth**.
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
│  route: /forgot-password                                               │  [1] Files             │
│             ┌────────────────────────────────┐                         │  [2] Tools             │
│             │  Reset your password           │                         │  [3] Browser           │
│             │                                │                         │  [4] Editor            │
│             │  Enter the email you signed up │                         │  [5] Debug             │
│             │  with. We'll send a reset link │                         │  [6] Capsule           │
│             │  if the account exists.        │                         │  [7] Brain             │
│             │                                │                         │  [8] Desktop           │
│             │  Email                         │                         │       GATED (UI-X-08)  │
│             │  ┌──────────────────────────┐  │                         │                        │
│             │  │ <user.email>              │  │                        │                        │
│             │  └──────────────────────────┘  │                         │                        │
│             │                                │                         │                        │
│             │  [ Send reset link           ] │                         │                        │
│             │                                │                         │                        │
│             │  Back to sign in               │                         │                        │
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
| 2 | UI-C-067 | Send reset link (primary) | Response is deliberately generic — the UI must not reveal whether the account exists. |
| 3 | UI-C-076 | Back to sign in link | Routes to /login (UI-S-29). |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** Not applicable — the form is always present.
- **Error.** "Couldn't send the reset link. ‹ reason from API ›"
- **Permission-denied.** "Password reset is disabled for this deployment. Contact your administrator."
- **Offline.** "You're offline. Password reset needs a connection."

**Modal overlays.** None. This screen opens no overlay.
