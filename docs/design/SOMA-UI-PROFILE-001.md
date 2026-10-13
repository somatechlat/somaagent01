# SOMA-UI-PROFILE-001 — User Profile Window (Design Spec)

## Document Control

| Field | Value |
|---|---|
| Document Title | User Profile Window — Design & Control Spec |
| Document Identifier | SOMA-UI-PROFILE-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 · ISO 9001:2015 clause 7.5 · WCAG 2.1 AA |
| Next Review | 2027-01-13 |
| Source of truth | `webui/src/components/soma-profile-modal.ts` · `soma-personal-profile.ts` · CM-11 |
| Related | `SOMA-01-UIUX-001` · `SOMA-UI-I18N-001` · `SOMA-UI-CONTROL-MAPS-001` |
| Law | Soma law: NO SHIMS/FAKES/MOCKS/STUBS. Honest GATED with reason. No emojis. Material Symbols. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | SomaTech Engineering | Initial design: full profile window, channels, one-click Display, I18N contract. |

---

## 1. Purpose

One **Profile window** for the signed-in user: identity, photo, email/WhatsApp channels (for later modules), chat display settings in **one click**, password, sign-out. Enterprise modal (glass), not a thin stub.

## 2. Soma law (non-negotiable)

1. NO SHIMS · FAKES · MOCKS · STUBS · PLACEHOLDERS · TODO passes  
2. Real handlers or **GATED + verbatim blocking reason**  
3. Product names: **Profile / Channels / Display / Security** — never “Capsule” in UI  
4. **No emojis** — Material Symbols only  
5. **I18N** — all strings via message catalog (see SOMA-UI-I18N-001)  
6. Secrets never re-displayed; Vault write-only  

## 3. Window anatomy (wireframe)

```
┌─ Profile ──────────────────────────────────────────────────────────┐
│  (avatar + camera)   Name                                    [×]  │
│                      primary email                                │
│                      [role]                                       │
├─ Account │ Channels │ Display │ Security ─────────────────────────┤
│                                                                  │
│  Account: display name · primary email (ro) · role (ro) [Save]   │
│  Channels: email accounts[] · WhatsApp numbers[] · Add · Save     │
│  Display:  [Chat settings] one click · [Full profile page]        │
│  Security: [Change password] · [Sign out]                        │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  [Sign out]                                    [Close]            │
└──────────────────────────────────────────────────────────────────┘
```

## 4. Control map (PF-*)

| ID | Label | Type | Binding | States | Status |
|---|---|---|---|---|---|
| PF-01 | Dialog | modal | — | open/closed | LIVE |
| PF-02 | Avatar | img/initials | local `soma_profile_avatar` + `/auth/me` | loaded/initials | PLANNED server |
| PF-03 | Camera / Upload photo | file input | FileReader → preview | idle/error | PLANNED API upload |
| PF-04 | Display name | input | local + future PATCH profile | dirty/saved | PLANNED API |
| PF-05 | Primary email | input readonly | `/auth/me` | — | LIVE |
| PF-06 | Role | input readonly | `/auth/me` | — | LIVE |
| PF-07 | Save profile | button | local / PATCH | dirty/saving/error | PLANNED API |
| PF-08 | Email account row | row | channels store | — | LIVE local |
| PF-09 | Add email | input+button | validate + append | error | LIVE local |
| PF-10 | WhatsApp row | row | channels store | — | LIVE local |
| PF-11 | Add WhatsApp | input+button | validate + append | error | LIVE local |
| PF-12 | Save channels | button | `localStorage soma_profile_channels` | dirty/saved | LIVE local |
| PF-13 | **Chat settings** | panel action | opens `soma-chat-settings` **in this window** | — | LIVE |
| PF-14 | Full profile page | panel action | navigate `/profile` | — | LIVE |
| PF-15 | Change password | panel action | `soma-password-modal` | GATED if no API | LIVE gate |
| PF-16 | Sign out | button | `POST /auth/logout` | — | LIVE |
| PF-17 | Close / scrim / ESC | button | close | — | LIVE |

**One-click rule:** topbar **Display** OR profile tab **Display → Chat settings** opens prefs **without** a second hunt.

## 5. Channels (why)

Later modules need contact routes: email bridge, WhatsApp bridge. Profile stores **operator-owned** addresses/numbers (not secrets). Verified flags only when a real verification API exists — never fake “verified”.

## 6. I18N contract

Every user-visible string uses `t('key')` from `webui/src/i18n/`. Locales: `en` (default), `es`. No hardcoded English in templates. Date/number via `Intl`.

## 7. Acceptance (Playwright)

| AC | Proof |
|---|---|
| PF-AC-01 | User chip opens Profile modal (glass) |
| PF-AC-02 | Display tab opens Chat settings in ≤1 click from chip |
| PF-AC-03 | Photo picker updates avatar (local until upload API) |
| PF-AC-04 | Add email/WhatsApp · Save persists across reload |
| PF-AC-05 | Invalid email shows error · no fake success |
| PF-AC-06 | All labels switch with locale |
| PF-AC-07 | No emoji in window |

## 8. Implementation notes (after GO)

- `soma-profile-modal.ts` (this design)  
- i18n catalog keys `profile.*` · `channels.*` · `display.*`  
- Channel API `GET/PUT /user/channels` when mounted — until then **local-only status string**  

---

## 9. Out of scope

| Excluded | Where |
|---|---|
| Admin user CRUD | `/admin` users |
| Org roles matrix | Settings › Roles |
| OAuth account linking | auth providers |

**End of Design Spec.**
