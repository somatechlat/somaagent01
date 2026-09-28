# UI-S-32 — MFA setup

**MFA setup** — Authenticated workspace column (alias /settings/mfa) — route `/mfa/setup` — facet **Auth**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ capsule: <capsule.name>                                                                         │
│ version: <version>    lifecycle: <lifecycle>                                                    │
│ persona knobs: (IQ <val>)(auto <val>)(budget <val>)                                             │
│ derived AgentIQ RO (greyed, never inputs):                                                      │
│   temperature <v>  max_tokens <v>  rlm_iterations <v>                                           │
│   recall_limit <v>  model_tier <v>  brain_query_enabled <v>                                     │
│   require_hitl <v>  tool_approval <v>  egress_allowed <v>                                       │
│   token_limit <v>  cost_tier <v>  thinking_budget <v>                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ facet tabs x6:  [Soul][Brain][Hands][Memory][Body][Governance]                                  │
│ command palette: <Cmd-K>                                                                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ WORKSPACE  facet: Auth                                                 │ SURFACE RAIL x8        │
│  route: /mfa/setup                                                     │  [1] Files             │
│  MFA setup                                    [Save] [Cancel]          │  [2] Tools             │
│  Protect your account with a second factor.                            │  [3] Browser           │
│                                                                        │  [4] Editor            │
│  ┌── Authenticator app ────────────────────────────────┐               │  [5] Debug             │
│  │ 1. Scan the QR code (opens UI-M-02 full-screen)     │               │  [6] Capsule           │
│  │    ┌────────┐                                       │               │  [7] Brain             │
│  │    │ QR from <otpauth-uri>                          │               │  [8] Desktop           │
│  │    └────────┘                                       │               │       GATED (UI-X-08)  │
│  │ 2. Or enter the key (masked)                        │               │                        │
│  │    sk-***...aBcD   note: rotate in Vault            │               │                        │
│  │ 3. Enter the 6-digit code                           │               │                        │
│  │    ┌──────┐                                         │               │                        │
│  │    │ **** │                                         │               │                        │
│  │    └──────┘                                         │               │                        │
│  └─────────────────────────────────────────────────────┘               │                        │
│                                                                        │                        │
│  Recovery codes               [Generate new codes]                     │                        │
│  │ <recovery-code> [copy] │  shown once, then masked                   │                        │
│  │ <recovery-code> [copy] │                                            │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-119 | TOTP QR / secret display | QR opens in UI-M-02. Shared secret renders masked (`sk-••••••••aBcD`) with a "rotate in Vault" note — never a real value. |
| 2 | UI-C-061 | verification code input | 6 digits. Server-validated. |
| 3 | UI-C-067 | Save (primary) | disabled-until: a valid code is entered. |
| 4 | UI-C-085 | recovery codes block | Shown once at generation, then masked. [copy] writes to clipboard. |
| 5 | UI-C-068 | Generate new codes (secondary) | Invalidates prior codes. Confirmation via UI-M-03. |
| 6 | UI-C-069 | Disable MFA (destructive) | Opens UI-M-03. disabled-when: MFA not enabled — disabled-reason: "MFA is not enabled on this account." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No recovery codes generated yet. Generate codes and store them offline."
- **Error.** "Couldn't verify the code. ‹ reason from API ›"
- **Permission-denied.** "MFA setup requires an authenticated session. Sign in first."
- **Offline.** "You're offline. MFA setup needs a connection."

**Modal overlays.** UI-M-02 Full-screen — QR code for scanning (explicit dismiss only). UI-M-03 Dialog — "Disable MFA on this account?" (destructive) and "Regenerate recovery codes? Existing codes will stop working."
