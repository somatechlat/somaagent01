# CM-10 — Admin, Voice, Profiles, Entity Control Map

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — Admin, Voice, Profiles, Entity manager, Infra/Audit (remaining screens) |
| Document Identifier | SOMA-UI-CM-10 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `UI-S-22`…`UI-S-24` · `UI-S-34`…`UI-S-48` · `SOMA-UI-BINDINGS-001.md` |
| Live sources | `soma-admin-api-keys.ts` · `soma-admin-roles-list.ts` · `soma-role-matrix.ts` · `soma-user-detail.ts` · `soma-audit-dashboard.ts` · `soma-agent-metrics.ts` · `soma-infrastructure-dashboard.ts` · `soma-integrations-dashboard.ts` · `soma-platform-metrics-dashboard.ts` · `soma-personal-profile.ts` · `soma-platform-profile.ts` · `entity-manager.ts` · voice views/components · `soma-permission-guard.ts` · `soma-infra-*.ts` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Remaining screen control map: admin, voice, profiles, entity manager, infra/audit, notification center (planned). |

---

## 1. ASCII wireframe — Admin users / roles / keys (composite)

```
┌─ Admin ────────────────────────────────────────────────────────────────────────────────────────┐
│ AD-00 nav: Users | Roles | Permission matrix | API keys | Audit | Metrics | Infrastructure     │
│ AD-01 search   AD-02 filters   AD-03 [Refresh]   AD-04 [Export CSV]                            │
│ AD-05 table rows …  AD-06 pagination prev/next                                                  │
│ AD-07 create modal: name / tenant / expiry  [Generate Key] [Cancel]                             │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. ASCII wireframe — Voice + Profile (composite)

```
┌─ Voice chat ────────────────┐  ┌─ Personal profile ───────────────────────────────────────────┐
│ VC-01 session picker        │  │ PR-01 displayName  PR-02 phone                                │
│ VC-02 transcript list       │  │ PR-03 theme  PR-04 language  PR-05 timezone                   │
│ VC-03 mic / talk            │  │ PR-06 [Reconfigure MFA]                                        │
│ VC-04 persona card          │  │ PR-07 notify: agentReplies / activitySummary / productUpdates  │
│ VC-05 waveform / live text  │  │ PR-08 [Save profile]                                           │
└─────────────────────────────┘  └───────────────────────────────────────────────────────────────┘
```

---

## 3. Control map — Admin

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| AD-00 | Admin section nav | tabs | route/local section | active | Permission-guarded | `nav` | LIVE |
| AD-01 | Search | input.search | local/API filter | idle | — | `searchbox` | LIVE |
| AD-02 | Action / resource filter | select | audit log API filters | default | — | `combobox` | LIVE |
| AD-03 | Refresh | button | reload list/logs | default, busy | — | `button` | LIVE |
| AD-04 | Export CSV | button | client/API export | default | — | `button` | LIVE |
| AD-05 | Table row | list-row | entity APIs | loading, empty, error | — | `row` | LIVE |
| AD-06a | Prev page | button | page API | default, disabled on first page | First page | `button` | LIVE |
| AD-06b | Next page | button | page API | default, disabled on last | Last page | `button` | LIVE |
| AD-07a | Create API key | button | open create modal | default | — | `button` primary | LIVE |
| AD-07b | Key name | input.text | draft | dirty | — | placeholder “e.g. production-gateway” | LIVE |
| AD-07c | Tenant id | input.text | draft | dirty | — | placeholder “Leave blank for a platform-wide key” | LIVE |
| AD-07d | Expiry | input.text | draft | dirty | — | placeholder “Leave blank to never expire” | LIVE |
| AD-07e | Generate Key | button | create key API | default, busy | — | `button` | LIVE |
| AD-07f | Cancel create | button | close modal | default | — | `button` | LIVE |
| AD-07g | Copy created key / Done | button | clipboard + close | default | Secret shown once at creation | `button` | LIVE |
| AD-08 | Provider key chips | readout | Vault/provider key status | set/unset | Values never redisplayed | `region` “LLM provider keys” | LIVE |
| AD-09 | Permission matrix cell | button | role-permission toggle API | on/off, dirty | — | `checkbox`/`button` | LIVE |
| AD-10 | Save role matrix | button | save | dirty, busy | — | `button` | LIVE |
| AD-11 | Revert role matrix | button | local | dirty | — | `button` | LIVE |
| AD-12 | User tab Profile | tabs | local `activeTab` | active | — | `tab` | LIVE |
| AD-13 | User tab Agents | tabs | local | active | — | `tab` | LIVE |
| AD-14 | User tab Activity | tabs | local | active | — | `tab` | LIVE |
| AD-15 | User tab Sessions | tabs | local | active | — | `tab` | LIVE |
| AD-16 | Suspend user | button | user admin API | confirm, busy | — | `button` danger | LIVE |
| AD-17 | Change role | select | user PATCH role | default | — | `combobox` | LIVE |
| AD-18 | Back to users | link | history | default | — | `link` | LIVE |
| AD-20 | Agent metrics filter | select | metrics API | default | — | `combobox` | LIVE |
| AD-21 | Infra status card | surface | diagnostics / infra APIs | ok, degraded, error | — | `region` | LIVE |
| AD-22 | Infra alert list | list-row | alerts API | empty, populated | — | `list` | LIVE |
| AD-23 | Infra metrics chart | readout | metrics API | loading, empty, error | — | `img`/chart + text summary | LIVE |
| AD-24 | Platform metrics | stat | metrics API | default | — | labelled stats | LIVE |
| AD-25 | Integrations row | list-row | integrations API | default | — | `row` | LIVE |
| AD-30 | Notification center | surface | notifications/audit API | loading, empty, error, populated | Endpoint absent → present-but-disabled with reason (never “0 notifications”) | `region` + `button` bell | PLANNED |
| AD-30a | Mark read | button | mark-read API | default | — | `button` | PLANNED |
| AD-30b | Mark all | button | mark-all API | default | — | `button` | PLANNED |
| AD-30c | Dismiss | button | dismiss API | default | — | `button` | PLANNED |

---

## 4. Control map — Voice

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| VC-01 | Session picker | select | voice sessions API | default | — | `combobox` | LIVE |
| VC-02 | Transcript row | list-row | sessions/transcript API | loading, empty | — | `list` | LIVE |
| VC-03 | Talk / mic | button | voice chat WS / STT | idle, live | — | `button` | LIVE |
| VC-04 | Persona card | surface | voice personas API | default | — | `region` | LIVE |
| VC-05 | Waveform | readout | live audio level | live, idle | — | decorative + text status | LIVE |
| VC-06 | Transcript live text | readout | STT stream | streaming | — | `log` polite | LIVE |
| VC-07 | Create persona | button | personas POST | default | — | `button` | LIVE |
| VC-08 | Persona fields | input.text/select | personas config | dirty | — | labelled | LIVE |
| VC-09 | Save persona | button | personas save | dirty, busy | — | `button` | LIVE |
| VC-10 | Open voice config panel | button | settings voice | default | — | `button` | LIVE |
| VC-11 | Session export | button | client Blob | default | — | `button` | PLANNED |
| VC-12 | Live caption toggle | toggle | local | on/off | — | `switch` | PLANNED |
| VC-13 | Voice enable (global) | toggle | flags (see CM-05) | on/off | — | `switch` | LIVE |

---

## 5. Control map — Profiles

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| PR-01 | Display name | input.text | profile save | dirty | — | labelled | LIVE |
| PR-02 | Phone | input.text | profile save | dirty | — | labelled | LIVE |
| PR-03 | Theme | select | profile/interface | dirty | — | `combobox` | LIVE |
| PR-04 | Language | select | profile | dirty | — | `combobox` | LIVE |
| PR-05 | Timezone | select | profile | dirty | — | `combobox` | LIVE |
| PR-06 | Reconfigure MFA | button | navigate `/mfa/setup` | default | — | `button` | LIVE |
| PR-07a | Notify agent replies | toggle | profile notifications | on/off | — | `switch` | LIVE |
| PR-07b | Notify activity summary | toggle | profile notifications | on/off | — | `switch` | LIVE |
| PR-07c | Notify product updates | toggle | profile notifications | on/off | — | `switch` | LIVE |
| PR-08 | Save profile | button | profile save | default, disabled-while-saving | — | `button` primary | LIVE |
| PR-09 | Avatar upload | input.file | profile avatar API | default | Avatar API may be absent → disabled + reason | `button` | PLANNED |
| PR-10 | Platform profile fields | input.text | platform profile API | dirty | — | labelled | LIVE |
| PR-11 | Delete account | button | account deletion API | confirm | Destructive + permission | `button` danger | PLANNED |

---

## 6. Control map — Entity manager / permission guard / forms

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| EN-01 | Refresh | button | `fetchData()` | default, busy | — | `button` | LIVE |
| EN-02 | Create entity | button | create API | **disabled** in current config | `entity-manager` create is disabled when create route is not configured | `button` disabled | GATED |
| EN-03 | Search entities | input.search | local `searchQuery` | idle | — | `searchbox` | LIVE |
| EN-04 | Status filter | select | local `selectedStatus` | default | — | `combobox` | LIVE |
| EN-05 | Entity row | list-row | list API | loading, empty, error | — | `row` | LIVE |
| PG-01 | Permission guard children | surface | permission map | allowed | — | region | LIVE |
| PG-02 | Locked fallback | readout | — | denied | Missing permission + reason string | lock + reason | GATED |
| FM-01 | Action menu trigger | menu | `soma-action-menu` | open, closed | — | `button` aria-haspopup | LIVE |
| FM-02 | Action menu item | menu | dispatched action | default | — | `menuitem` | LIVE |

---

## 7. Honesty notes

1. API key secrets appear once at generation (AD-07g); stored values are never shown again.
2. Infra charts use server numbers only; empty chart = no data, not zero.
3. Notification center stays out of UI until its API is real (AD-30 GATED/PLANNED).
4. Entity create is honestly disabled when the create route is not configured.
5. Platform/SaaS root routes are refused in this standalone build (CM-07 G-04).

---

## 8. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-admin-*.ts` | Admin screens |
| `webui/src/views/soma-audit-dashboard.ts` | Audit log |
| `webui/src/views/soma-voice-*.ts` + `components/voice-*.ts` | Voice family |
| `webui/src/views/soma-personal-profile.ts` `soma-platform-profile.ts` | Profiles |
| `webui/src/components/entity-manager.ts` | Generic entity list/create |
| `webui/src/components/soma-permission-guard.ts` | Lock + reason |
| `webui/src/components/soma-infra-*.ts` | Infra cards/charts/alerts |

End of Document
