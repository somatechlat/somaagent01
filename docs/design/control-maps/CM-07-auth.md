# CM-07 — Auth Family Control Map

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — Auth (login, register, forgot/reset, MFA setup, OAuth/SSO callback) |
| Document Identifier | SOMA-UI-CM-07 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `UI-S-29`…`UI-S-33` · `SOMA-UI-BINDINGS-001.md` · `admin/auth/api.py` |
| Live sources | `webui/src/views/soma-login.ts` · `soma-register.ts` · `soma-forgot-password.ts` · `soma-mfa-setup.ts` · `soma-auth-callback.ts` · `webui/src/main.ts` route guards |
| Routes | `/login` `/register` `/forgot-password` `/reset-password` `/verify-email` `/auth/callback` `/mfa/setup` `/logout` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Auth family control map with OAuth/SSO/MFA honesty gates. |

---

## 1. ASCII wireframe — Login

```
┌─ Login ────────────────────────────────────────────────────────────────────┐
│  A-01 [Continue with Google]   A-02 [SSO…]                                │
│  ── or ──                                                                  │
│  A-03 email    A-04 password    A-05 show/hide password                    │
│  A-06 [x] Remember me          A-07 [Sign in]                             │
│  A-08 Forgot password?  A-09 Create account                               │
│  ┌─ SSO modal ──────────────────────────────────────────────┐             │
│  │ A-10 close  A-11 provider list  A-12 dynamic fields      │             │
│  │ A-13 [Test connection]  A-14 [Cancel]  A-15 [Save & Connect] │         │
│  └──────────────────────────────────────────────────────────┘             │
└────────────────────────────────────────────────────────────────────────────┘
```

## 2. ASCII wireframe — Register / Forgot / MFA / Callback

```
Register:  A-20 name  A-21 email  A-22 password  A-23 [x] terms  A-24 [Create account]
Forgot:    A-30 email  A-31 [Send reset] (disabled until valid email)
MFA:       A-40 [Start setup]  A-41 secret key (copy)  A-42 [Continue→verify]
           A-43 code  A-44 [Verify]  A-45 [Back]  A-46 [Download recovery codes]  A-47 [Done→settings]
Callback:  A-50 status spinner  A-51 [Retry]  A-52 error panel
Reset/Verify email route: A-60 honest mounted-route notice + Back to login
```

---

## 3. Control map

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| A-01 | Continue with Google | button | `GET /auth/oauth/{provider}` (browser never holds client id) | default, busy, error | — | `button` | LIVE |
| A-02 | SSO… | button | opens `_showSSOModal` | default | — | `button` | LIVE |
| A-03 | Email | input.email | local `_handleEmailInput` | empty, filled, invalid | — | labelled email | LIVE |
| A-04 | Password | input.password | local `_password` | empty, filled | — | labelled password | LIVE |
| A-05 | Show/hide password | button | local `_showPassword` | default (`tabindex="-1"`) | — | aria-label toggle visibility | LIVE |
| A-06 | Remember me | input.checkbox | local `_rememberMe` | on/off | — | `checkbox` `#remember` | LIVE |
| A-07 | Sign in | button | `POST /auth/login` | default, disabled-while-loading | — | `button` submit | LIVE |
| A-08 | Forgot password? | link | `/forgot-password` | default | — | `link` | LIVE |
| A-09 | Create account | link | `/register` | default | — | `link` | LIVE |
| A-10 | SSO modal close | button | local `_showSSOModal = false` | default | — | aria-label “Close” | LIVE |
| A-11 | SSO provider option | list-row | local `_selectedProvider` | selected | — | `radio` / list | LIVE |
| A-12 | SSO dynamic field | input.text | provider field schema | dirty | — | labelled (placeholder from schema) | LIVE |
| A-13 | Test connection | button | `_testConnection()` | default, busy, ok, fail | — | `button` | LIVE |
| A-14 | Cancel | button | close modal | default | — | `button` | LIVE |
| A-15 | Save & Connect | button | `_saveAndConnect()` | default, busy | — | `button` primary | LIVE |
| A-20 | Full name | input.text | local `_name` | empty, filled | — | labelled | LIVE |
| A-21 | Email | input.email | local `_email` | empty, filled | — | labelled | LIVE |
| A-22 | Password | input.password | local `_password` | empty, filled | — | labelled | LIVE |
| A-23 | Accept terms | input.checkbox | `_termsAccepted` | on/off | Submit disabled until terms accepted | `checkbox` `#terms` | LIVE |
| A-24 | Create account | button | `POST /auth/register` | default, disabled-while-loading or !terms | — | `button` submit | LIVE |
| A-30 | Email | input.email | local | empty, filled | — | `#forgot-email` | LIVE |
| A-31 | Send reset | button | forgot-password API | default, disabled until valid email | Invalid/empty email | `button` submit | LIVE |
| A-40 | Start setup | button | MFA setup start | default | — | `button` | LIVE |
| A-41 | Secret key (copy) | button | `navigator.clipboard` (`_copySecretKey`) | default | Secret shown once during setup; not re-fetched later | `button` on code block | LIVE |
| A-42 | Continue to verify | button | step = 'verify' | default | — | `button` | LIVE |
| A-43 | Verification code | input.text | local `verificationCode` (placeholder “000000”) | empty, filled | — | labelled code | LIVE |
| A-44 | Verify code | button | `_verifyCode()` | default, busy, error | — | `button` | LIVE |
| A-45 | Back to scan | button | step = 'scan' | default | — | `button` | LIVE |
| A-46 | Download recovery codes | button | `_downloadRecoveryCodes()` Blob | default | — | `button` | LIVE |
| A-47 | Done → Settings | button | `/settings` | default | — | `button` | LIVE |
| A-48 | Cancel / history back | button | `history.back()` | default | — | `button` | LIVE |
| A-50 | Callback spinner | readout | OAuth/OIDC return handling | loading | — | `status` | LIVE |
| A-51 | Retry | button | `_retry()` | error | — | `button` | LIVE |
| A-52 | Error panel | readout | — | error | — | `alert` | LIVE |
| A-60 | Reset-password / verify-email honest notice | readout | — | always on those paths | Routes mounted in `admin/auth/api.py`; SPA explains mount and links `/login` | text + `link` “Back to login” | GATED (honest notice) |
| A-61 | Onboarding / invite redirect | readout | `main.ts` redirects `/onboarding/*`, `/invite/*` → `/register` | default | No separate invitation router on this deployment | `status` | GATED |
| A-70 | Logout | button | `POST /auth/logout` then `/login` | default, busy | — | `button` | LIVE |

---

## 4. Route guard controls (`main.ts`)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| G-01 | Session probe | readout | `GET /api/v2/auth/me` | ok, anonymous | — | — | LIVE |
| G-02 | Redirect anonymous → `/login` | link | `history.replaceState` | default | — | — | LIVE |
| G-03 | Redirect authed `/login` → `/chat` | link | same | default | — | — | LIVE |
| G-04 | Platform route refusal notice | readout | `/soma/*` `/platform/*` paths | visible | Standalone agent: no Soma/billing platform routes in this build | text + exit | GATED |

---

## 5. Honesty notes

1. Browser never holds OAuth issuer/client id (`GET /auth/oauth/{provider}` server-side).
2. Password field default type is password; reveal is explicit and tab-skipped.
3. Terms gate is real: submit stays disabled until accepted.
4. Reset-password and verify-email render an honest mount notice instead of a fake form.
5. Onboarding/invite paths redirect to register; no phantom invite router.

---

## 6. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-login.ts` | A-01…A-15 |
| `webui/src/views/soma-register.ts` | A-20…A-24 |
| `webui/src/views/soma-forgot-password.ts` | A-30…A-31 |
| `webui/src/views/soma-mfa-setup.ts` | A-40…A-48 |
| `webui/src/views/soma-auth-callback.ts` | A-50…A-52 |
| `webui/src/main.ts` | Route guards + honest notices |
| `webui/src/services/api-client.ts` | `logout` POSTs `/auth/logout` |

End of Document
