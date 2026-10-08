# UI-S-54-settings-interface — Settings — Interface

**Settings — Interface** — section **Interface** inside the one Settings shell — route `/settings` (Interface tab).
Chrome abbreviated (UI-S-00). Left section nav (7) is visible; Interface is active.

**Field truth.** Persisted display preferences are only `UserPreferences` via `GET/PUT /aaas/admin/preferences` (`admin/aaas/api/users.py` 638–641, 669–674):
`theme` · `language` · `timezone` · `date_format` (GET only) · `notifications` (`agentReplies`, `activitySummary`).
Theme also boots from localStorage key `soma-theme` (`webui/src/services/theme-boot.ts:5`).
Rows in Screen 7D with no preferences column (density, 12h/24h, chrome toggles, right-panel default) are **GATED** — never given a fake API field name.

**Language law.** Binding copy is **Used for: Chat / Help / Memory**. The banned admin noun never appears in UI strings.
**Memory rule.** Memory is not a Settings section. Its only home is `/memory` (UI-S-04, left rail).

## Purpose

One place for how the shell looks and reads: theme, language, timezone, date format, notification prefs. Chrome toggles from Screen 7D appear only when a real binding exists; otherwise GATED with a reason.

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · Interface   [Search settings…]                         [Save] [Cancel]     │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  INTERFACE — how the app looks and reads for you                                  │
│  Agent       │  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  Models      │  │ Theme       [system ▼]  light | dark | system     ← theme                   │   │
│  Voice       │  │ Language    [en     ▼]                            ← language                │   │
│  Interface●  │  │ Timezone    [UTC    ▼]  effective timezone shown  ← timezone                │   │
│  Tools       │  │ Date format [YYYY-MM-DD]  (read-only today)       ← date_format             │   │
│  Integrations│  │                                                                             │   │
│  Advanced    │  │ NOTIFICATIONS (notification_prefs)                                          │   │
│              │  │   Agent replies      [● on]   ← notifications.agentReplies                  │   │
│              │  │   Activity summary   [○ off]  ← notifications.activitySummary               │   │
│              │  │                                                                             │   │
│              │  │ CHROME (Screen 7D) — GATED until a real binding exists                       │   │
│              │  │   Density            [Comfortable / Compact]  — no preferences field         │   │
│              │  │   Time format        [12h / 24h]              — no preferences field         │   │
│              │  │   Show project bar   [Mobile / Desktop]       — no preferences field         │   │
│              │  │   Show clock         [Mobile / Desktop]       — no preferences field         │   │
│              │  │   Show connection    [Mobile / Desktop]       — no preferences field         │   │
│              │  │   Right panel        [Mobile / Desktop]       — session only (see note)     │   │
│              │  └─────────────────────────────────────────────────────────────────────────────┘   │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: <load / save state> · permission: settings:edit → write, else read-only banner          │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Field table (API field)

| Human label | Control | API field | Notes | Evidence |
|---|---|---|---|---|
| Theme | select | `theme` | `light` \| `dark` \| `system` (`THEME_CHOICES`) | `profiles.py:281-295`; `users.py:638`, `697-700` |
| Language | select | `language` | UI language; default `en` | `profiles.py:296`; `users.py:639` |
| Timezone | select | `timezone` | default `UTC`; effective zone shown | `profiles.py:297`; `users.py:640` |
| Date format | read-only | `date_format` | returned by GET; **not** on `PreferencesUpdateRequest` | `users.py:672`, `638-641` |
| Agent replies | toggle | `notifications.agentReplies` | inside `notification_prefs` JSON | `profiles.py:301-325`; `users.py:641`, `705-706` |
| Activity summary | toggle | `notifications.activitySummary` | same JSON | same |
| Density | segmented | **—** | **GATED** — no preferences column. Reason: "Density is not persisted yet." |
| Time format (12h/24h) | segmented | **—** | **GATED** — `date_format` is date-only; no 12h/24h field. |
| Show project bar | per-device toggle | **—** | **GATED** — no API field. |
| Show clock | per-device toggle | **—** | **GATED** — no API field. |
| Show connection status | per-device toggle | **—** | **GATED** — no API field. |
| Right panel | per-device toggle | **—** | Session-only: `rightPanelOpen` in `workspace-store.ts:9`. Not a preferences field. |

## Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-100 | section nav (7) | Agent · Models · Voice · Interface · Tools · Integrations · Advanced. |
| 2 | UI-C-063 | theme / language / timezone selects | Options from `THEME_CHOICES` / real locale + tz lists. No invented option. |
| 3 | UI-C-065 | notification toggles | Bind `notifications.agentReplies` / `activitySummary` only. |
| 4 | UI-C-067 | Save (primary, header) | `PUT /aaas/admin/preferences`. disabled-while: request in flight. |
| 5 | UI-C-069 | Cancel (secondary, header) | Restores last saved values. |
| 6 | UI-C-096 | date format readout | Read-only. Never an input while the API has no write field. |
| 7 | — | GATED chrome block | Density / 12h-24h / project bar / clock / connection / right-panel default render disabled with the reason string inline. Never drawn as available. |
| 8 | — | permission banner | `settings:edit` absent → read-only banner, Save disabled-reason: "Requires settings edit permission." |

## States

- **Loading.** Skeleton field blocks. No counts or metrics while loading.
- **Empty.** "No interface preferences saved yet. Choose a theme and language to begin."
- **Error.** "Couldn't load interface preferences. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to settings. Requires settings edit permission."
- **Offline.** "You're offline. Changes will not be saved until the connection returns."
- **GATED.** Each chrome row prints its disabled-reason. No phantom values.

**Modal overlays.** None. Theme polarity also lives in the chrome toggle (`theme-boot.ts`); both must agree after save.

## Nav

Settings shell section nav = Agent · Models · Voice · **Interface** · Tools · Integrations · Advanced (UI-S-50). No Memory item.
Route stays `/settings` (in-page section). No separate Interface path in `main.ts`.

## Test clicks

| Click | Expect |
|---|---|
| Theme → `dark` → Save | `PUT /aaas/admin/preferences` `{theme:"dark"}` 200; chrome flips; `soma-theme` boot key follows |
| Language → `es` → Save | `PUT` `{language:"es"}` 200 |
| Timezone → `Europe/Madrid` → Save | `PUT` `{timezone:"Europe/Madrid"}` 200 |
| Toggle Agent replies → Save | `PUT` `{notifications:{agentReplies:true,…}}` 200 |
| Click Density / 12h / Show clock | Control disabled + reason; no network call |
| Save without edit permission | Save disabled + reason banner |

## file:line evidence

| Evidence | Path |
|---|---|
| Preferences request fields | `somaAgent01/admin/aaas/api/users.py:638-641` |
| Preferences GET payload | `somaAgent01/admin/aaas/api/users.py:669-674` |
| `THEME_CHOICES` · `date_format` · `notification_prefs` | `somaAgent01/admin/aaas/models/profiles.py:281-325` |
| Live profile prefs UI | `somaAgent01/webui/src/views/soma-personal-profile.ts:27-35`, `344-348` |
| Theme boot key `soma-theme` | `somaAgent01/webui/src/services/theme-boot.ts:5` |
| Right-panel session state | `somaAgent01/webui/src/stores/workspace-store.ts:9` |
| Screen 7D table | `somabrain/docs/project/SOMA-UI-MOCKUPS-001.md:595-608` |
| Nav shell | `somaAgent01/docs/design/mockups/UI-S-50-settings-agent.md:41-53` |
