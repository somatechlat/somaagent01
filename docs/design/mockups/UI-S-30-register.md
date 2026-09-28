# UI-S-30 — Register

**Register** — Public pre-auth workspace (chrome shown signed-out) — route `/register` — facet **Auth**.
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
│  route: /register                                                      │  [1] Files             │
│             ┌────────────────────────────────┐                         │  [2] Tools             │
│             │  Create your account           │                         │  [3] Browser           │
│             │                                │                         │  [4] Editor            │
│             │  Display name                  │                         │  [5] Debug             │
│             │  ┌──────────────────────────┐  │                         │  [6] Capsule           │
│             │  │ <user.name>               │  │                        │  [7] Brain             │
│             │  └──────────────────────────┘  │                         │  [8] Desktop           │
│             │  Email                       │                           │       GATED (UI-X-08)  │
│             │  ┌──────────────────────────┐  │                         │                        │
│             │  │ <user.email>              │  │                        │                        │
│             │  └──────────────────────────┘  │                         │                        │
│             │  Password                    │                           │                        │
│             │  ┌──────────────────────────┐  │                         │                        │
│             │  │ ********                   │  │                       │                        │
│             │  └──────────────────────────┘  │                         │                        │
│             │  Confirm password            │                           │                        │
│             │  ┌──────────────────────────┐  │                         │                        │
│             │  │ ********                   │  │                       │                        │
│             │  └──────────────────────────┘  │                         │                        │
│             │  [ ] I accept the terms        │                         │                        │
│             │  [ Create account            ] │                         │                        │
│             │  Already have an account? Sign in                        │                        │
│             └────────────────────────────────┘                         │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <signed out>                                               │
│ neuro meters x4 (RO): DA -  5-HT -  NE -  ACh -   synced -                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-061 | display name input | Required. Trimmed. |
| 2 | UI-C-061 | email input | type=email. Required. |
| 3 | UI-C-062 | password input | Masked. Password rules render as server-provided text — never invented locally. |
| 4 | UI-C-062 | confirm password input | Must match password. |
| 5 | UI-C-066 | terms checkbox | Required to submit. |
| 6 | UI-C-067 | Create account (primary) | disabled-until: all required fields valid and terms accepted. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** Not applicable — the form is always present.
- **Error.** "Couldn't create the account. ‹ reason from API ›"
- **Permission-denied.** "Self-registration is disabled for this deployment. Ask an admin for an invitation."
- **Offline.** "You're offline. Registration needs a connection."

**Modal overlays.** None. This screen opens no overlay.
