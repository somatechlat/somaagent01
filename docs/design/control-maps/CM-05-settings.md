# CM-05 — Settings Control Map (all tabs)

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — Settings shell × tabs (Agent, Models, Voice, Interface, Tools, Integrations, SomaBrain, Connectivity, Advanced) |
| Document Identifier | SOMA-UI-CM-05 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `SOMA-01-UIUX-005.md` · `SOMA-SETTINGS-MODEL-001.md` · `SOMA-UI-BINDINGS-001.md` · `UI-S-50`…`UI-S-57` · `UI-S-49` · `UI-S-54` |
| Live sources | `webui/src/views/soma-settings.ts` · `soma-settings-models.ts` · `soma-settings-channels.ts` · `soma-settings-somabrain.ts` · `soma-multimodal-settings.ts` · `webui/src/components/settings-form.ts` · `soma-skin-gallery.ts` · `soma-form-field.ts` · `soma-toggle.ts` · `soma-select.ts` |
| Routes | `/settings` · `/settings/models` · `/settings/channels` · `/settings/somabrain` · `/settings/multimodal` · `/settings/tools` (nav) · `/settings/mfa` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Exhaustive settings control map for all 9 tabs + Models full screen + Channels + Multimodal + form primitives. |

---

## 1. ASCII wireframe — Settings shell

```
┌─ Settings ─────────────────────────────────────────────────────────────────────────────────────┐
│ ST-00 Back to chat                                                                               │
│ ST-01 tabs: [Agent][Models][Voice][Interface][Tools][Integrations][SomaBrain][Connectivity][Advanced] │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│  <active section>                                                                               │
│  ST-02 section fields…                                                                          │
│  ST-03 [Save]  ST-04 [Revert]  ST-05 dirty/saved/error banner                                   │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. ASCII wireframe — Models (full-screen section)

```
┌─ Settings › Models ────────────────────────────────────────────────────────────────────────────┐
│ MD-01 provider key strip (Vault status per provider)                                            │
│ MD-02 Model roles: Chat | Utility | Embedding | Vision | Decision(Clef)                         │
│ MD-03 Presets: [Save current as preset] [Restore bundled]  · preset cards Apply/Duplicate/Edit/Delete │
│ MD-04 toolbar: [Refresh] [Export config?] [Restore bundled] [Add model]  [Search models…] [filter] │
│ MD-05 model row: name · provider · type · active · [Activate][Edit][Delete]                     │
│ MD-06 editor drawer: provider, api_key (Vault), api_base, Load models, name, display, type,     │
│       ctx_length, max_tokens, timeout, ctx_history, max_embeds, limits, priority, cost_tier,    │
│       capabilities, domains, vision, kwargs, is_active · [Save][Test connection][Delete][Close] │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Control map — Settings shell

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| ST-00 | Back to chat | link | `/chat` | default | — | `link` | LIVE |
| ST-01a | Tab Agent | tabs | local `_setTab('agent')` | active, inactive | — | `tab` | LIVE |
| ST-01b | Tab Models | tabs | `_setTab('models')` → full-screen models section / `/settings/models` | active, inactive | — | `tab` | LIVE |
| ST-01c | Tab Voice | tabs | `_setTab('voice')` | active, inactive | — | `tab` | LIVE |
| ST-01d | Tab Interface | tabs | `_setTab('interface')` | active, inactive | — | `tab` | LIVE |
| ST-01e | Tab Tools | tabs | `_setTab('tools')` | active, inactive | — | `tab` | LIVE |
| ST-01f | Tab Integrations | tabs | `_setTab('external')` | active, inactive | — | `tab` | LIVE |
| ST-01g | Tab SomaBrain | tabs | `_setTab('somabrain')` / `/settings/somabrain` | active, inactive | — | `tab` | LIVE |
| ST-01h | Tab Connectivity | tabs | `_setTab('connectivity')` | active, inactive | — | `tab` | LIVE |
| ST-01i | Tab Advanced | tabs | `_setTab('system')` | active, inactive | — | `tab` | LIVE |
| ST-03 | Save settings | button | `_saveSettings` (per-section store) | default, dirty, saving, saved, error | — | `button` | LIVE |
| ST-04 | Revert | button | local revert | default, dirty | — | `button` | LIVE |
| ST-05 | Save/error banner | readout | — | idle, dirty, saving, saved, error | — | `status` / `alert` | LIVE |
| ST-06 | Export config | button | `_exportConfig` client export | default | — | `button` | LIVE |
| ST-07 | Form field label/helper/error | readout | `soma-form-field` | default, error, required | — | label + `aria-describedby` | LIVE |
| ST-08 | Permission guard | surface | `soma-permission-guard` | allowed, denied, unknown | Missing permission → lock + reason | `region` | LIVE |

---

## 4. Control map — Tab Agent

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| AG-01 | Persona / name fields | input.text | CapsuleConfig / agent settings | dirty | — | labelled | LIVE |
| AG-02 | Agent mode defaults | select | agent settings | dirty | — | `combobox` | LIVE |
| AG-03 | IQ knobs deep link | button | → capsule / SomaBrain (see CM-04) | default | — | `button` | LIVE |
| AG-04 | Open Models | button | `_openModels()` | default | — | `button` | LIVE |
| AG-05 | Agent list section | list-row | `GET /agents/` | loading, empty, populated | — | list | LIVE |
| AG-06 | Create agent | button | `POST /agents/` (when API mounted) | default | API absent → present-but-disabled | `button` | PLANNED |
| AG-07 | Persona library | surface | capsule versions | default | Not shipped → “Persona library ships with capsule version diff.” | region | PLANNED |

---

## 5. Control map — Tab Models (full screen)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| MD-01 | Provider key strip | readout | Vault key presence per provider (masked) | set / unset | Values never redisplayed | `region` “Provider key status” | LIVE |
| MD-02a | Role Chat | select | `/llm/roles` (or settings roles map) | dirty | — | `select` `#role-chat` | LIVE |
| MD-02b | Role Utility | select | same | dirty | — | `#role-utility` | LIVE |
| MD-02c | Role Embedding | select | same | dirty | — | `#role-embedding` | LIVE |
| MD-02d | Role Vision | select | same | dirty | — | `#role-vision` | LIVE |
| MD-02e | Role Decision (Clef) | select | same | dirty | — | `#role-decision` | LIVE |
| MD-03a | Save current as preset | button | preset store | default | — | `button` | LIVE |
| MD-03b | Restore bundled presets | button | bundled preset restore | default, confirm | — | `button` | LIVE |
| MD-03c | Preset name | input.text | preset draft | dirty | — | placeholder “Preset name” | LIVE |
| MD-03d | Preset notes | input.text | preset draft | dirty | — | placeholder “Notes” | LIVE |
| MD-03e | Save preset edit | button | preset save | default, busy | — | `button` | LIVE |
| MD-03f | Apply preset | button | apply roles/models | default, busy | — | `button` | LIVE |
| MD-03g | Duplicate preset | button | preset clone | default | — | `button` | LIVE |
| MD-03h | Edit preset | button | open editor | default | — | `button` | LIVE |
| MD-03i | Delete preset | button | preset delete (confirm) | default | — | `button` danger | LIVE |
| MD-03j | Preset visibility toggle | select | preset meta | default | — | `select` | LIVE |
| MD-03k | Preset scope select | select | preset meta | default | — | `select` | LIVE |
| MD-04a | Refresh | button | `_reload()` model list | default, busy | — | `button` | LIVE |
| MD-04b | Export / bulk action | button | client export | default | — | `button` | LIVE |
| MD-04c | Restore bundled | button | bundled models | default, confirm | — | `button` | LIVE |
| MD-04d | Add model | button | `_openCreate()` | default | — | `button` primary | LIVE |
| MD-04e | Search models | input.search | local filter | filled | — | placeholder “Search models…” | LIVE |
| MD-04f | Filter models | select | local filter | default | — | `combobox` | LIVE |
| MD-05a | Model row | list-row | model list API | loading, empty, error, populated | — | `row` clickable | LIVE |
| MD-05b | Activate | button | `_activate(m)` | default, busy | Already active → “Active” badge instead | `button` | LIVE |
| MD-05c | Edit | button | `_openEdit(m)` | default | — | `button` | LIVE |
| MD-05d | Delete | button | `_deleteModel()` | default, confirm | — | `button` danger | LIVE |
| MD-06a | Provider | select | draft `_bind('provider')` | dirty | — | `combobox` | LIVE |
| MD-06b | API key | input.password | Vault write via `_saveKey()` | masked set/unset | Never re-display value; placeholder shows saved-state text | `#` labelled | LIVE |
| MD-06c | Save to Vault | button | Vault write path | default, busy | — | `button` | LIVE |
| MD-06d | API base | input.text | draft `api_base` | dirty | — | placeholder “Optional provider base URL” | LIVE |
| MD-06e | Load models | button | provider catalog fetch | default, busy | — | `button` | LIVE |
| MD-06f | Model pick list | list-row | loaded catalog | empty: “No models loaded yet” (disabled row) | — | list | LIVE |
| MD-06g | Name | input.text | draft | dirty | — | labelled | LIVE |
| MD-06h | Display name | input.text | draft | dirty | — | labelled | LIVE |
| MD-06i | Model type | select | draft `model_type` | dirty | — | `combobox` | LIVE |
| MD-06j | Context length | input.number | draft `ctx_length` | dirty | — | spinbutton | LIVE |
| MD-06k | Max tokens | input.number | draft `max_tokens` | dirty | — | spinbutton | LIVE |
| MD-06l | Timeout | input.number | draft `timeout` | dirty | — | spinbutton | LIVE |
| MD-06m | Context history | input.number | draft `ctx_history` | dirty | — | spinbutton | LIVE |
| MD-06n | Max embeds | input.number | draft `max_embeds` | dirty | — | spinbutton | LIVE |
| MD-06o | Limit requests | input.number | draft `limit_requests` | dirty | — | spinbutton | LIVE |
| MD-06p | Limit input | input.number | draft `limit_input` | dirty | — | spinbutton | LIVE |
| MD-06q | Limit output | input.number | draft `limit_output` | dirty | — | spinbutton | LIVE |
| MD-06r | Priority | input.number | draft `priority` | dirty | — | spinbutton | LIVE |
| MD-06s | Cost tier | select | draft `cost_tier` | dirty | — | `combobox` | LIVE |
| MD-06t | Capabilities | input.text | draft (csv) | dirty | — | placeholder “chat, tools, reasoning” | LIVE |
| MD-06u | Domains | input.text | draft (csv) | dirty | — | placeholder “general, product” | LIVE |
| MD-06v | Vision capable | input.checkbox | draft `vision` | on/off | — | `checkbox` | LIVE |
| MD-06w | Kwargs | textarea | draft `kwargs_text` | dirty | — | labelled textarea | LIVE |
| MD-06x | Is active | input.checkbox | draft `is_active` | on/off | — | `checkbox` | LIVE |
| MD-06y | Save model | button | `_saveModel()` | default, busy, error | — | `button` primary | LIVE |
| MD-06z | Test connection | button | `_testConnection()` | default, busy, ok, fail | — | `button` | LIVE |
| MD-06α | Close editor | button | `_draft = null` | default | — | `button` | LIVE |
| MD-07 | Key missing notice | readout | Vault status | visible when unset | — | explains write-only key policy | LIVE |

---

## 6. Control map — Tab Interface (theme + skins + locale)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| IF-01 | Theme | select | `_setInterface('theme', e)` + `theme-boot` | default | — | `combobox` | LIVE |
| IF-02 | Language | select | `_setInterface('language', e)` | default | — | `combobox` | LIVE |
| IF-03 | Timezone | select | `_setInterface('timezone', e)` | default | — | `combobox` | LIVE |
| IF-04 | Skin gallery | surface | `soma-skin-gallery` (see CM-08) | populated, empty, error | — | `region` | LIVE |
| IF-05 | Density / motion prefs | toggle | interface settings | default | Not all prefs persisted → some GATED | `switch` | PLANNED |
| IF-06 | Reduced motion note | readout | `prefers-reduced-motion` | always | — | text | LIVE |

---

## 7. Control map — Tab Tools

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| TL-01 | Tool enable toggle (per tool) | toggle | `_toggleTool(t.name)` tool catalog | on, off, error | — | `switch` per tool name | LIVE |
| TL-02 | Tool catalog list | list-row | `GET /tools` | loading, empty, error | — | list | LIVE |
| TL-03 | Tier / approval badges | readout | `ToolInfo` / `ToolCatalogItem` | default | — | text | LIVE |
| TL-04 | Approval required toggle | toggle | `PUT /tools/catalog` policy | on, off | Catalog write API absent → disabled with reason | `switch` | PLANNED |
| TL-05 | Tier selector | select | catalog policy | default | same | `combobox` | PLANNED |
| TL-06 | Tool schema expand | button | local | collapsed | — | aria-expanded | LIVE |
| TL-07 | MCP enabled | toggle | `_toggleFlag('mcpEnabled')` | on, off | — | `switch` | LIVE |
| TL-08 | Open Models (from tools empty) | button | `_openModels()` | default | — | `button` | LIVE |
| TL-09 | Add model CTA | button | `_openModels()` | default | — | `button` | LIVE |

---

## 8. Control map — Tab Integrations / external

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| IN-01 | Provider secret field | input.password | Vault write-only (`PUT /secrets/providers/{id}` target) | unset, set-masked | Value never redisplayed | masked + Test/Rotate/Revoke actions | LIVE (write-only) |
| IN-02 | Test connection | button | provider test | default, busy | — | `button` | LIVE |
| IN-03 | Rotate / Revoke | button | Vault ops | default | Vault path may be absent → reason | `button` | PLANNED |
| IN-04 | External tool keys | readout | integrations API | default | — | region | LIVE |
| IN-05 | Add integration | button | integrations create | default | API absent → disabled + reason | `button` | PLANNED |
| IN-06 | Voice enabled | toggle | `_toggleFlag('voiceEnabled')` | on, off | — | `switch` | LIVE |
| IN-07 | Memory enabled | toggle | `_toggleFlag('memoryEnabled')` | on, off | — | `switch` | LIVE |
| IN-08 | Tools enabled | toggle | `_toggleFlag('toolsEnabled')` | on, off | — | `switch` | LIVE |

---

## 9. Control map — Tab Voice / Multimodal / Channels / Advanced

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| VO-01 | Voice enable | toggle | voice settings / flags | on, off | — | `switch` | LIVE |
| VO-02 | Persona picker | select | voice personas API | default | — | `combobox` | LIVE |
| VO-03 | Open voice chat | button | `/voice/chat` | default | — | `button` | LIVE |
| MM-01 | Image quality | select | multimodal config | dirty | — | `combobox` | LIVE |
| MM-02 | Image style | select | config | dirty | — | `combobox` | LIVE |
| MM-03 | Image enabled | toggle | config | on/off | — | `switch` | LIVE |
| MM-04 | Diagram format | select | config | dirty | — | `combobox` | LIVE |
| MM-05 | Diagram theme | select | config | dirty | — | `combobox` | LIVE |
| MM-06 | Diagram enabled | toggle | config | on/off | — | `switch` | LIVE |
| MM-07 | Screenshot mode | select | config | default | — | `combobox` | LIVE |
| MM-08 | Screenshot full page | toggle | config | on/off | — | `switch` | LIVE |
| MM-09 | Screenshot enabled | toggle | config | on/off | — | `switch` | LIVE |
| MM-10 | Vision enabled | toggle | config | on/off | — | `switch` | LIVE |
| MM-11 | Chat model vision | toggle | config | on/off | — | `switch` | LIVE |
| MM-12 | Browser model vision | toggle | config | on/off | — | `switch` | LIVE |
| MM-13 | Image provider | select | config | default | — | `combobox` | LIVE |
| MM-14 | Diagram provider | select | config | default | — | `combobox` | LIVE |
| MM-15 | Screenshot provider | select | config | default | — | `combobox` | LIVE |
| MM-16 | Save config | button | `saveConfig()` | default, saving, disabled-while-saving | — | `button` | LIVE |
| CH-01 | Module enable (channels) | toggle | `_moduleToggle(m.name, !m.enabled)` | on/off | — | `switch` | LIVE |
| CH-02 | Channel kind | select | `_kind` draft | default | — | `combobox` | LIVE |
| CH-03 | Channel id / uuid | input.text | draft | dirty | — | placeholder “uuid” | LIVE |
| CH-04 | Channel mode | select | `_mode` | default | — | `combobox` | LIVE |
| CH-05 | Bot token | input.password | draft (Vault-bound write) | masked | Never re-display | masked | LIVE |
| CH-06 | Group mode | select | `_groupMode` | default | — | `combobox` | LIVE |
| CH-07 | Allow-list | input.text | draft | dirty | — | placeholder “empty = allow all” | LIVE |
| CH-08 | Create channel | button | `_createChannel()` | default, busy | — | `button` | LIVE |
| CH-09 | Test channel | button | `_lifecycle(c.id, 'test')` | default, busy | — | `button` | LIVE |
| CH-10 | Start channel | button | `_lifecycle(c.id, 'start')` | default, busy | — | `button` | LIVE |
| CH-11 | Stop channel | button | `_lifecycle(c.id, 'stop')` | default, busy | — | `button` | LIVE |
| CH-12 | Delete channel | button | `_deleteChannel(c.id)` | default, confirm | — | `button` danger | LIVE |
| SY-01 | Feature flags table | toggle | live flags | on/off | — | `switch` | LIVE |
| SY-02 | Backup export | button | settings export | default | — | `button` | LIVE |
| SY-03 | Backup restore | button | restore API | default | Restore API absent → “Restore needs the backup API.” | `button` | PLANNED |
| SY-04 | Dangerous reset | button | destructive reset | confirm | Permission-guarded | `button` danger | PLANNED |
| SY-05 | Advanced raw editor | textarea | `settings-form.ts` text/number/json fields | dirty, error | — | labelled fields | LIVE |

---

## 10. Settings form primitives (`settings-form.ts`, `soma-*` fields)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| FM-A | Text field | input.text | settings store | default, dirty, error | — | label + error | LIVE |
| FM-B | Number field | input.number | settings store | same | — | spinbutton | LIVE |
| FM-C | JSON field | textarea | settings store | same, parse error | — | labelled | LIVE |
| FM-D | Revert changes | button | local | default, dirty | — | `button` | LIVE |
| FM-E | Save settings | button | save | default, dirty, busy | — | `button` | LIVE |
| FM-F | Toggle component | toggle | `soma-toggle` `soma-change` | on/off/disabled | — | `switch` | LIVE |
| FM-G | Select component | select | `soma-select` | open/closed/error | — | `combobox` | LIVE |
| FM-H | Glass modal | modal | `soma-glass-modal` | open/closed | — | `dialog` aria-modal, close button | LIVE |

---

## 11. Honesty notes

1. Models are **full-screen inside Settings** — not a welcome card (A0 law).
2. API keys are Vault write-only; UI shows set/unset, never the secret.
3. AgentIQ derived settings are read-only next to the 3 knobs (REQ-UIXS-003).
4. Tools catalog toggles that lack a write API are GATED with the API name.
5. Save never claims success without a persistence response (REQ-UIXS-006).
6. L3/L4-owned values render read-only with disabled-reason (REQ-UIXS-002).

---

## 12. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-settings.ts` | Shell + tabs + flags + interface + tools toggles |
| `webui/src/views/soma-settings-models.ts` | Models full screen |
| `webui/src/views/soma-settings-channels.ts` | Channels lifecycle |
| `webui/src/views/soma-settings-somabrain.ts` | SomaBrain connection (see CM-04) |
| `webui/src/views/soma-multimodal-settings.ts` | Multimodal knobs |
| `webui/src/components/settings-form.ts` | Generic form fields |
| `webui/src/components/soma-form-field.ts` / `soma-toggle.ts` / `soma-select.ts` / `soma-glass-modal.ts` | Primitives |

End of Document
