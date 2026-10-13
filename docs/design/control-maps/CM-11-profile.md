# CM-11 — User Profile Control Map (`/profile` · UI-S-34)

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — User Profile: Account / Security / Notifications / Sessions + Change-password modal |
| Document Identifier | SOMA-UI-CM-11 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 · ISO 9001:2015 clause 7.5 |
| Next Review | 2027-01-13 |
| Related | `UI-S-34` · `UI-M-01` · `UI-M-03` · `SOMA-UI-IA-001.md` · `SOMA-UI-BINDINGS-001.md` · `SOMA-UI-NAV-001.md` · `CM-07-auth.md` (MFA family) · `CM-10-admin-voice-profile.md` §5 (superseded for `/profile`) |
| Live sources | `webui/src/views/soma-personal-profile.ts` · `webui/src/services/api-client.ts` · `webui/src/main.ts` route `/profile` |
| API sources | `admin/auth/api.py` · `admin/platform/api/users.py` (`/profile`, `/preferences`) · `admin/platform/models/identity.py` · `services/common/identity/password.py` · `admin/common/session_manager.py` |
| Routes | `/profile` (also `/admin/profile`, `/platform/profile` → same view) · out: `/chat` `/mfa/setup` `/login` |
| Scope note | **Supersedes CM-10 §5 PR-01…PR-11 for `/profile`.** Platform profile (`UI-S-35`, `/admin/profile` platform-admin) stays in CM-10. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Profile screen ISO control map + wireframes: Account / Security / Notifications / Sessions, change-password modal (min 14), self-service role rules. LIVE vs PLANNED vs GATED from source, not aspiration. |

---

## 1. ASCII wireframe — `/profile` (desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ PG-10 [←]   SOMA · Profile                                      PG-11 [Save]  PG-12 [Cancel] │  ← thin top strip (PLANNED chrome;
│ PG-01 Personal profile                                                                        │     live chrome = page title + dirty save bar)
│ PG-02 error banner (only when load/save failed)                                               │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  ── Account ──────────────────────────────────────────────────────────────────────────────── │
│  AC-01 ┌── avatar ──┐   AC-02 [Upload avatar]          GATED: no avatar API                  │
│        │  <image /  │   AC-03 Display name   ┌──────────────────────────┐                    │
│        │  initials> │   AC-04 Email          ┌──────────────────────────┐ (read-only)        │
│        └────────────┘   AC-05 Phone          ┌──────────────────────────┐                    │
│                           AC-06 Tenant       ┌──────────────────────────┐ (read-only)        │
│                           AC-07 Tenant ID    ┌──────────────────────────┐ (read-only)        │
│  ── display prefs ────────────────────────────────────────────────────────────────────────── │
│                           AC-08 Theme  [System ▾]   AC-09 Language [English ▾]               │
│                           AC-10 Timezone [America/New_York ▾]                                │
│                                                                                              │
│  ── Security ─────────────────────────────────────────────────────────────────────────────── │
│  SC-01 Multi-Factor Authentication   SC-02 status: Enabled / Enrolled / Disabled             │
│                                    SC-03 [Reconfigure MFA → /mfa/setup]                      │
│  SC-04 Password   SC-05 Last changed <ts | never>                                            │
│            SC-06 notice: "Password change has no API on this deployment." (LIVE honest gate) │
│            SC-07 [Change password]  GATED until POST /auth/change-password mounts → UI-M-01  │
│                                                                                              │
│  ── Notifications ────────────────────────────────────────────────────────────────────────── │
│  NT-01 Agent replies to my conversations                          ( ●───○ toggle )           │
│  NT-02 Weekly activity summary                                    ( ●───○ toggle )           │
│  NT-03 Product updates and tips                                   ( ●───○ toggle )           │
│                                                                                              │
│  ── Sessions ─────────────────────────────────────────────────────────────────────────────── │
│  SS-01 Active sessions: <n>   SS-02 [Sign out everywhere]  (UI-M-03 confirm)                 │
│  ┌────────────────────────────────────────────────────────────────────────────┐              │
│  │ device │ ip │ last seen │ current │ revoke                                 │              │
│  │ SS-03 rows… (PLANNED — no self session list endpoint mounted today)        │              │
│  │ SS-04 [revoke] per row  (UI-M-03 confirm)                                  │              │
│  └────────────────────────────────────────────────────────────────────────────┘              │
│                                                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ PG-03 [Save Changes]  (rendered only when dirty · PG-04 disabled-while-saving)               │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

Chrome law: own workspace chrome only. No chat left rail, no canvas, no surface rail, no facet tabs, no Models/Memory hero cards. Entry: chat left-rail 👤 → `/profile`.

---

## 2. ASCII wireframe — Change-password modal (UI-M-01)

```
┌─ UI-M-01 Drawer (420px, right) — Change password ─────────────────────────────┐
│  PW-01 header "Change password"                        PW-02 [×] close        │
│                                                                               │
│  PW-03 Current password   ●•••••••••••  PW-04 [show]                          │
│  PW-05 New password       ●•••••••••••  PW-06 [show]                          │
│  PW-07 Confirm new        ●•••••••••••  PW-08 [show]                          │
│                                                                               │
│  PW-09 policy readout: "Minimum 14 characters · max 128 · not your username   │
│                         or email · not whitespace-only · not a single         │
│                         repeated character. Length is the only composition    │
│                         rule."   (live counter: 0/14)                         │
│                                                                               │
│  PW-10 error banner (wrong current · policy fail · mismatch · server error)   │
│                                                                               │
│                    PW-11 [Cancel]   PW-12 [Change password]                   │
│                    (ESC closes · focus trapped · all three fields write-only)  │
└───────────────────────────────────────────────────────────────────────────────┘
```

On success: toast `Password changed.` · modal closes · SC-05 `last changed` refreshes · optional session-revocation offer (PLANNED: revoke other sessions).

---

## 3. Role rules — self-service only (non-negotiable)

| Rule | Enforcement | Evidence |
|---|---|---|
| **R-1 The screen only ever acts on the signed-in user.** | Every binding resolves `user_id` / `email` from the bearer principal (`request.auth.sub` / `request.auth.email`). No route param selects the subject. | `admin/platform/api/users.py` `get_profile` / `update_profile` / `get_preferences` / `update_preferences` |
| **R-2 No cross-user read or write.** | Admin user management is a different screen (`UI-S-22` Users, `UI-S-23` Roles, `soma-user-detail.ts`). Profile contains no `user_id` selector, no search, no suspend, no role edit. | `soma-personal-profile.ts` (no user-id input anywhere) |
| **R-3 Identity is IdP-owned.** | Email field is permanently read-only here. Email change is a separate verified flow (not drawn). Tenant / Tenant ID are read-only projections of the principal. | view `disabled` on email + tenant inputs; `ProfileOut` tenant from `request.auth.effective_tenant_id` |
| **R-4 Password change is self-only and write-only.** | `POST /api/v2/auth/change-password` (PLANNED) must authenticate the caller, verify **current** password, and never echo any candidate. Admin password reset for others is out of scope of this screen. | `services/common/identity/password.py` (`check_password_policy` message never contains the candidate) |
| **R-5 Session controls are self-only.** | Planned `GET/DELETE /auth/sessions…` and `POST /auth/logout-all` must scope to the caller's `user_id` only. The existing admin revoke (`DELETE /platform/admin/users/{user_id}/sessions/{session_id}`) is **not** a substitute — it authorizes `org:user_update` on `users` and targets an arbitrary user. | `admin/platform/api/users.py:497-510` vs `admin/common/session_manager.py` `list_sessions` / `delete_user_sessions` (real service methods, unmounted as self endpoints) |
| **R-6 Permission check honesty.** | Live `GET/PUT /platform/admin/profile` authorize `org:user_read` / `org:user_update` on resource `users` (admin-grade verbs) while the write target is always the caller's row. `GET/PUT …/preferences` authorize `identity:self`. This asymmetry is real and must not be papered over: the screen is self-service in data scope even when the verb is admin-grade. | `users.py` `authorize_sync(...)` call sites |
| **R-7 No privileged escalation on this screen.** | No role assignment, no impersonation (`POST /auth/impersonate` lives outside profile), no API-key minting, no tenant admin. Those are Admin screens (CM-10 AD-*). | CM-10; this map contains zero admin verbs |

---

## 4. Control map — Page chrome

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| PG-01 | Personal profile (page title) | readout | static | always | — | `heading` level 1 | LIVE |
| PG-02 | Error banner | readout | `this.error` ← load/save failure | hidden, error | — | `alert` | LIVE |
| PG-03 | Save Changes | button | `_saveProfile()` → `PUT /platform/admin/preferences` + `PUT /platform/admin/profile` | default, disabled-while-saving, hidden when clean | — | `button` primary | LIVE |
| PG-04 | Saving… label | readout | `this.saving` | busy | — | `aria-live="polite"` on button | LIVE |
| PG-05 | Loading profile… | readout | `this.loading` | loading | — | `status` | LIVE |
| PG-06 | Failed to load profile | readout | `_loadProfile()` catch | error | — | `alert` (empty-vs-error distinct from PG-05) | LIVE |
| PG-10 | Back to chat | button | `history.back()` / `/chat` (UI-S-34 §2 top strip) | default | — | `button` | PLANNED |
| PG-11 | Save (header) | button | same as PG-03 | default, disabled-while-saving or when clean | — | `button` primary | PLANNED |
| PG-12 | Cancel (header) | button | restore last-saved snapshot | default, disabled when clean | — | `button` | PLANNED |
| PG-20 | Offline notice | readout | `navigator.onLine` (UI-S-34 §6: "You're offline. Changes will not be saved until the connection returns.") | offline | Save gated while offline | `status` | PLANNED |

---

## 5. Control map — Account

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| AC-01 | Avatar (image or initials fallback) | readout | `adminProfile.avatar_url \|\| me.avatar_url` via `GET /platform/admin/profile` + `GET /auth/me`; fallback `_getInitials` | image, initials | — | `img` with `alt` = display name (live) | LIVE |
| AC-02 | Avatar upload notice | readout | — | always | `Avatar upload has no API on this deployment.` (verbatim in `soma-personal-profile.ts:432`) | text | GATED |
| AC-02b | Upload avatar | button | target: avatar upload API writing `AdminProfile.avatar_url` / `UserPreferences.avatar_url` (`admin/platform/models/profiles.py`) | default, busy | `Avatar upload has no API on this deployment.` | `button` | PLANNED |
| AC-03 | Display name | input.text | `PUT /platform/admin/preferences` `{display_name}` + `PUT /platform/admin/profile` `{display_name}` | empty, filled, dirty | — | labelled | LIVE |
| AC-04 | Email | input.email | `GET /auth/me` (read) | filled | Permanently read-only — email is IdP-owned; change is a separate verified flow | labelled + `disabled` | LIVE |
| AC-05 | Phone | input.tel | `GET/PUT /platform/admin/profile` `{phone}` (server trims to 20 chars) | empty, filled, dirty | — | labelled | LIVE |
| AC-06 | Tenant | input.text (read-only) | `GET /platform/admin/profile` `tenant_name` ← `request.auth.effective_tenant_id` | filled, `—` | Read-only — tenant assignment is platform admin | labelled + `disabled` | LIVE |
| AC-07 | Tenant ID | input.text (read-only) | same, `tenant_id` | filled, `—` | Read-only — identifier, not editable here | labelled + `disabled` | LIVE |
| AC-08 | Theme | select | `PUT /platform/admin/preferences` `{theme}` ∈ `UserPreferences.THEME_CHOICES` (`system` \| `light` \| `dark`) | default, dirty | — | `combobox` | LIVE |
| AC-09 | Language | select | `PUT /platform/admin/preferences` `{language}` | default, dirty | — | `combobox` | LIVE |
| AC-10 | Timezone | select | `PUT /platform/admin/preferences` `{timezone}` | default, dirty | — | `combobox` | LIVE |

---

## 6. Control map — Security

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| SC-01 | Multi-Factor Authentication (row) | surface | `GET /platform/admin/profile` | enabled, enrolled, disabled | — | `region` | LIVE |
| SC-02 | MFA status value | readout | `mfa_enabled` (server hardcodes `False` — TOTP enable path fails closed) / `mfa_enrolled` (`LocalIdentity.mfa_enrolled`) | `Enabled (TOTP)` · `Enrolled (TOTP not yet active)` · `Disabled` | — | text + icon (`check_circle` / `cancel`) | LIVE |
| SC-03 | Reconfigure MFA | button | `soma-navigate` → `/mfa/setup` (UI-S-32, CM-07 A-40…A-48) | default | — | `button` | LIVE |
| SC-04 | Password (row label) | readout | static | always | — | text | LIVE |
| SC-05 | Last changed `<ts>` | readout | target `LocalIdentity.password_changed_at` (`admin/platform/models/identity.py:63,137`) | unknown → renders `never` | `ProfileOut` does not expose `last_password_change` — value is unbound until the API surfaces it | text | PLANNED |
| SC-06 | Password-change absence notice | readout | — | always | `Password change has no API on this deployment.` (verbatim, `soma-personal-profile.ts:527`) | text | GATED |
| SC-07 | Change password | button | opens UI-M-01 (PW-*); target `POST /api/v2/auth/change-password` | default, busy, error | `Password change has no API on this deployment.` — button must stay disabled-with-reason until the route is mounted in `admin/auth/api.py` (today's mounted auth routes: `/token` `/refresh` `/me` `/logout` `/login` `/register` `/impersonate` + `/sso` `/oauth` `/mfa`) | `button` | PLANNED |
| SC-08 | Delete account | button | target: account deletion API (destructive, UI-M-03) | default, confirm | Destructive + API absent on this deployment | `button` danger | PLANNED |

---

## 7. Control map — Notifications

Saved with the same `PUT /platform/admin/preferences` payload as Account fields (`notifications` object). Key names in the wire are the server `UserPreferences.notification_prefs` keys as the view persists them (`agentReplies`, `activitySummary`, `productUpdates`).

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| NT-01 | Agent replies to my conversations | toggle | `PUT /platform/admin/preferences` `notifications.agentReplies` | on, off, dirty | — | `switch` | LIVE |
| NT-02 | Weekly activity summary | toggle | `notifications.activitySummary` | on, off, dirty | — | `switch` | LIVE |
| NT-03 | Product updates and tips | toggle | `notifications.productUpdates` | on, off, dirty | — | `switch` | LIVE |
| NT-04 | Critical alerts (server default `true`) | toggle | `UserPreferences` default key `criticalAlerts` | on, off | Not drawn in the live view — shown here only so the server default is not mistaken for a missing control | `switch` | PLANNED |

Note: `ProfileOut.notifications` also carries `AdminProfile.notification_prefs` (`criticalAlerts` / `weeklyDigest` / `marketing`). The live view writes the prefs object, not the admin-profile object. Do not double-bind one toggle to two stores.

---

## 8. Control map — Sessions

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| SS-01 | Active sessions: `<n>` | stat | `GET /platform/admin/profile` `active_sessions` = `UserSession.objects.filter(user_id=caller).count() or 1` | number | — | labelled stat | LIVE |
| SS-02 | Sessions table | surface | target `GET /api/v2/auth/sessions` (rows: device · ip · last seen · current) | loading, empty (`No active sessions to show.`), error, populated | Endpoint not mounted. Service layer is real: `admin/common/session_manager.py` `list_sessions(user_id)` is used today only by admin user-detail | `table` | PLANNED |
| SS-03 | Session row | list-row | same | current, foreign | — | `row` | PLANNED |
| SS-04 | Revoke (per row) | button | target `DELETE /api/v2/auth/sessions/{id}` scoped to caller; confirm UI-M-03 | default, busy | Not mounted. The only revoke today is admin `DELETE /platform/admin/users/{user_id}/sessions/{session_id}` (`org:user_update`) — wrong scope for this screen (R-5) | `button` danger | PLANNED |
| SS-05 | Sign out everywhere | button | target `POST /api/v2/auth/logout-all`; confirm UI-M-03 (`Sign out of all sessions, including this one?`) → `/login` | default, busy, confirm | Not mounted. Service layer real: `SessionManager.delete_user_sessions(user_id)` (`admin/common/session_manager.py:203-217`) | `button` danger | PLANNED |
| SS-06 | Revoke / sign-out confirm dialog | modal | UI-M-03 | open, cancel, confirm | — | `dialog` destructive | PLANNED |
| SS-07 | Empty sessions state | readout | SS-02 | empty | Must say `No active sessions to show.` — never invent rows, never impersonate error (UI-S-34 §6) | `status` | PLANNED |

---

## 9. Control map — Change-password modal (UI-M-01)

Target route (PLANNED): `POST /api/v2/auth/change-password` · body `{current_password, new_password}` · auth: bearer of the caller. No password value is ever echoed in the response.

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| PW-01 | Change password (modal header) | readout | static | open | — | `heading` level 2 | PLANNED |
| PW-02 | Close | button | close UI-M-01 | default | — | aria-label “Close” | PLANNED |
| PW-03 | Current password | input.password | local `currentPassword` (write-only) | empty, filled, invalid | — | labelled password | PLANNED |
| PW-04 | Show/hide current | button | local reveal (CM-07 A-05 pattern: `tabindex="-1"`) | default | — | aria-label toggle visibility | PLANNED |
| PW-05 | New password | input.password | local `newPassword` (write-only) | empty, filled, policy-fail | — | labelled password | PLANNED |
| PW-06 | Show/hide new | button | local reveal | default | — | aria-label toggle visibility | PLANNED |
| PW-07 | Confirm new password | input.password | local `confirmPassword` (write-only) | empty, filled, mismatch | — | labelled password | PLANNED |
| PW-08 | Show/hide confirm | button | local reveal | default | — | aria-label toggle visibility | PLANNED |
| PW-09 | Policy readout + live counter | readout | static policy text + `newPassword.length` | under, met | — | `status` polite | PLANNED |
| PW-10 | Modal error banner | readout | server error / local validation | hidden, error | — | `alert` | PLANNED |
| PW-11 | Cancel | button | close UI-M-01 | default | — | `button` | PLANNED |
| PW-12 | Change password (submit) | button | `POST /api/v2/auth/change-password` | default, busy, error | Disabled until: current non-empty ∧ new ≥ 14 ∧ confirm === new ∧ new ≠ current. Server re-checks policy regardless. | `button` primary submit | PLANNED |
| PW-13 | Post-success toast | readout | `show-toast` success `Password changed.` | transient | — | `status` | PLANNED |
| PW-14 | Offer “sign out other sessions” | checkbox | after success → SS-05 | on, off | — | `checkbox` | PLANNED |

### 9.1 Modal validation order (local, then server)

1. `current_password` non-empty.
2. `new_password` length ≥ **14** (see §10) and ≤ 128.
3. `new_password` !== `current_password`.
4. `confirm_password` === `new_password`.
5. Client-side policy parity (whitespace-only, single repeated character, ≠ username/email casefolded) mirrors `check_password_policy` — the server is still the authority.

Failure copy is server- or rule-derived; never reveal whether the account exists (CM-07 uniform-401 law applies to change-password too: wrong current password and unknown account are the same body).

---

## 10. Password policy (server-backed, not invented in the UI)

Source of truth: `services/common/identity/password.py`.

| Constant | Value | Meaning |
|---|---|---|
| `MIN_PASSWORD_LENGTH` | **12** | Member floor |
| `PRIVILEGED_MIN_PASSWORD_LENGTH` | **14** | Privileged floor (anyone who can change who holds what) |
| `MAX_PASSWORD_LENGTH` | **128** | Upper bound |
| Hash | Argon2id (`t=3, m=64MiB, p=4, h=32, s=16`) | `hash_password` / `verify_password` / `needs_rehash` |
| Pepper | HMAC key from Vault (`get_password_pepper`) | Hash without pepper is inert |

**This modal's gate is min 14 characters** (the privileged floor). Rationale for the UI gate: a self-service password change must not weaken a privileged account below 14; the server call is `check_password_policy(..., privileged=True)` for privileged principals and `privileged=False` (floor 12) otherwise — the UI always shows the stricter 14 and lets the server raise/keep the bar.

Composition rules (from `check_password_policy`, `password.py:219-269`):

- Length is the control. **No** upper/lower/digit/symbol composition requirements (they push predictable substitutions).
- Rejects: empty · whitespace-only · single repeated character · password equal to the username or email (casefolded compare).
- The exception message names the rule and **never contains the candidate**.

---

## 11. Honesty notes

1. **Password change is honestly absent, not faked.** The live screen ships SC-06 `Password change has no API on this deployment.` — there is no `change-password` route in `admin/auth/api.py` (mounted: `/token` `/refresh` `/me` `/logout` `/login` `/register` `/impersonate` + `/sso` `/oauth` `/mfa`). SC-07 and PW-* are PLANNED against `POST /api/v2/auth/change-password` and must stay disabled-with-reason until it exists. (CM-07's middleware allowlist mentions `/api/v2/auth/password/reset|forgot`; neither is mounted — CM-07 A-60 covers that honest notice.)
2. **`Last changed` is not allowed to lie.** SC-05 currently renders `never` unconditionally because `ProfileOut` omits `last_password_change`. Until the API exposes `LocalIdentity.password_changed_at`, the readout must show `unknown`, not `never` (empty-vs-error law). `never` is only correct when the field is present and null.
3. **Avatar upload is a notice, not a dead button.** AC-02 is a gated notice with the blocking reason; AC-02b stays disabled until a real upload endpoint writes `avatar_url`. Letter fallback (AC-01) is real — never a stock image.
4. **Sessions table refuses to invent rows.** SS-02/SS-07 stay PLANNED/GATED. Today only the count (SS-01) is real. No device/IP/last-seen row may appear without `GET /api/v2/auth/sessions`.
5. **Admin revoke ≠ self revoke.** SS-04 must not quietly call `DELETE /platform/admin/users/{user_id}/sessions/{session_id}` — that endpoint authorizes `org:user_update` and takes an arbitrary `user_id` (R-5/R-7).
6. **MFA status is honest about the fail-closed enable path.** `mfa_enabled` is server-hardcoded `False` (TOTP secret persistence unimplemented); `mfa_enrolled` is real from `LocalIdentity`. SC-02 shows three distinct strings (Enabled / Enrolled / Disabled) — never collapse Enrolled into Enabled.
7. **Write payload split is real.** `_saveProfile` writes display prefs + notifications to `UserPreferences` (`PUT /platform/admin/preferences`) and display_name + phone to `AdminProfile` (`PUT /platform/admin/profile`). One toggle never writes both stores (§7 note).
8. **Failure → visible error.** Load failure renders PG-06 (`Failed to load profile`), save failure sets PG-02 + `show-toast` error. Neither path renders a silent empty form (contrast cognitive-panel `_loadFailed` pattern).
9. **No dead CTA on this screen.** Every row above is either LIVE with a handler, PLANNED with a named target API, or GATED with a verbatim blocking reason.

---

## 12. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-personal-profile.ts` | PG-01…PG-06, AC-01…AC-10, SC-01…SC-06, NT-01…NT-03, SS-01 (live) |
| `webui/src/services/api-client.ts` | base `/api/v2`; `get`/`put` used by the view |
| `webui/src/main.ts` | route `/profile` (and `/admin/profile`, `/platform/profile` aliasing) |
| `admin/auth/api.py` | mounted auth routes (proof that change-password / sessions are absent) |
| `admin/platform/api/users.py` | `GET/PUT /platform/admin/profile`, `GET/PUT /platform/admin/preferences`, admin session revoke (out of scope), `ProfileOut` |
| `admin/platform/models/profiles.py` | `AdminProfile`, `UserPreferences` (incl. `avatar_url`, `notification_prefs`) |
| `admin/platform/models/identity.py` | `LocalIdentity.password_changed_at`, `set_password`, `mfa_enrolled` |
| `services/common/identity/password.py` | `check_password_policy`, min 12 / privileged 14 / max 128, Argon2id + pepper |
| `admin/common/session_manager.py` | `list_sessions`, `delete_user_sessions`, `count_user_sessions` (service layer for SS-02…SS-05) |
| `docs/design/mockups/UI-S-34-personal-profile.md` | target wireframe, UI-M-01 / UI-M-03, state copy (§6) |
| `docs/design/SOMA-UI-IDREG-001.md` | UI-S-34, UI-M-01 (Drawer), UI-M-03 (Dialog) |
| `docs/design/SOMA-UI-IA-001.md` | A0 chrome law, thin top strip, 👤 → `/profile` |

End of Document
