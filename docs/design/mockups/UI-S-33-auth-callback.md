# UI-S-33 — Auth callback

**Auth callback** — Public pre-auth workspace (chrome shown signed-out) — route `/auth/callback` — facet **Auth**.
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
│  route: /auth/callback                                                 │  [1] Files             │
│             ┌────────────────────────────────┐                         │  [2] Tools             │
│             │                                │                         │  [3] Browser           │
│             │           (spinner)            │                         │  [4] Editor            │
│             │                                │                         │  [5] Debug             │
│             │   Completing sign-in...        │                         │  [6] Capsule           │
│             │                                │                         │  [7] Brain             │
│             │   provider: <oauth.provider>   │                         │  [8] Desktop           │
│             │   state: <auth.state>          │                         │       GATED (UI-X-08)  │
│             │                                │                         │                        │
│             │   Do not close this window.    │                         │                        │
│             │                                │                         │                        │
│             │   [ Cancel -> sign in ]        │                         │                        │
│             └────────────────────────────────┘                         │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <signed out>                                               │
│ neuro meters x4 (RO): DA -  5-HT -  NE -  ACh -   synced -                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-086 | status progress panel | Non-interactive readout of the OAuth exchange. Values are `‹ live value ›` from the callback query — never fabricated. |
| 2 | UI-C-068 | Cancel and return to sign in | Aborts the exchange and routes to /login. Does not mint a partial session. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** Not applicable — this screen is transient.
- **Error.** "Sign-in was cancelled or failed. ‹ reason from API ›" with a route back to /login.
- **Permission-denied.** "This sign-in method is not enabled for your account. ‹ reason from API ›"
- **Offline.** "You're offline. Sign-in needs a connection."

**Modal overlays.** None. This screen opens no overlay.
