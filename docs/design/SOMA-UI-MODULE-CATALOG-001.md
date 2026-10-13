# SOMA-UI-MODULE-CATALOG-001 — Reusable module/component catalog (skinnable agent UI)

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent Soma — reusable UI module catalog (Lit 3.x, skinnable) |
| Document Identifier | SOMA-UI-MODULE-CATALOG-001 |
| Version | 1.0.0 |
| Date | 2026-10-12 |
| Status | Draft |
| Classification | Internal |
| Author | SomaTech Engineering |
| Approver | — |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-12 |
| Source of truth | Live `webui/src/` inventory · `SOMA-RPT-FEATMATRIX-001` §2.3/§3 · `SOMA-UI-CATALOG-001` · `SOMA-UI-SKINS-001` §3.2–3.3 · `SOMA-PM-PLAN-TRIAD-001` WAVE 4 |
| Stack law | Lit 3.x only · no React/Alpine · no shims/fakes/mocks/stubs · real REST/WS only |
| Build order | Primitives → Shell → Workspace → Chat → Admin (dependency order below) |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | SomaTech Engineering | Initial module catalog. File Manager first-class. NEW vs EXISTS. Props/slots/events/states/skin surfaces per module. |

---

## 0. How to read this catalog

| Rule | Meaning |
|---|---|
| **Order = build order** | L0 primitives first; nothing higher-layer may redefine a lower-layer token or DOM contract. |
| **Status** | `NEW` = build from zero. `EXISTS` = current tag stays, contract is **refactored** to this catalog. `GATED` = UI present-but-disabled with a real blocking reason (never a placeholder). |
| **Skin surface** | Every module declares which `surfaces` key(s) of `SOMA-UI-SKINS-001` §3.3 it consumes. Values come from the closed `--skin-*` vocabulary. |
| **States** | Every data-bearing module MUST implement `loading` / `empty` / `error`. Empty ≠ error (`_loadFailed` pattern). |
| **No invented fields** | Domain fields come only from live schemas: `filesv2`, `ToolInfo`/`ToolCatalogItem`, `ModelIn`, WS `/ws/v2/chat/{id}`, CapsuleConfig, cognitive state. |
| **Events** | All DOM events are `CustomEvent` with `bubbles: true, composed: true` and a typed `detail`. No silent dead controls. |

### Skin surface map (`SOMA-UI-SKINS-001` §3.3)

| Surface key | Covers | Primary host module |
|---|---|---|
| `chrome` | top strip, facet tabs, instance strip | `soma-app-shell`, `soma-topbar` |
| `sidebar` | left rail, chat list, nav | `soma-sidebar` |
| `chat` | message list, bubbles, streaming | `soma-message-list`, `soma-message` |
| `composer` | input, attach menu, send | `soma-composer` |
| `tool_timeline` | tool-call rows | `soma-tool-timeline` |
| `right_panel` | canvas hosts + File Manager | `soma-right-panel`, `soma-file-manager` |
| `login` | auth screens | `soma-login` family |

**Token contract:** modules read **only** `var(--skin-*)` (closed vocabulary of SKINS-001 §3.2). Until the `--platform-*` → `--skin-*` rename ships in `tokens.css`, `theme-boot` / skin-applier provides the alias map; **no component may hardcode hex colours** (today’s 1575 literals are a defect to burn down during EXISTS refactor).

---

## L0 — Shared DS primitives

Built first. Used by every higher module. Path: `webui/src/components/`.

### M-001 `soma-button` · EXISTS (refactor)

| | |
|---|---|
| **Purpose** | Primary action control. |
| **Props** | `variant: 'primary' \| 'secondary' \| 'ghost' \| 'danger'` · `type: 'button' \| 'submit' \| 'reset'` · `disabled: boolean` · `loading: boolean` (NEW) · `size: 'sm' \| 'md' \| 'lg'` (NEW) · `icon?: string` (Material Symbols name) · `label?: string` (or slotted) · `fullWidth: boolean` |
| **Slots** | `default` (label) · `icon` (custom icon) |
| **Events** | `soma-click` `{ original: MouseEvent }` — never swallow submit |
| **States** | `disabled`, `loading` (spinner in-place, `aria-busy`) |
| **Reuse** | every module |
| **Skin** | core tokens only: `--skin-color-accent`, `-hover`, `-text`, `--skin-color-danger`, `--skin-color-border`, `--skin-radius-md`, `--skin-space-sm/md`, `--skin-motion-fast` |

**Refactor debt:** replace `--soma-*` fallbacks + `width: 100%` default with `--skin-*` + `fullWidth` opt-in.

### M-002 `soma-input` · NEW

| | |
|---|---|
| **Purpose** | Text / search / textarea field. Extracted so form-field is pure layout (M-007). |
| **Props** | `type: 'text' \| 'password' \| 'search' \| 'textarea' \| 'email' \| 'number'` · `value: string` · `placeholder` · `disabled` · `required` · `readonly` · `error: string` · `helper: string` · `rows?: number` · `maxLength?: number` · `autocomplete?: string` |
| **Slots** | `prefix` · `suffix` (buttons/meters) |
| **Events** | `soma-input` `{ value }` · `soma-change` `{ value }` · `soma-enter` `{ value }` · `soma-clear` |
| **States** | empty · focused · filled · error (`aria-invalid`) · disabled · readonly |
| **Reuse** | forms, search, composer internals, secrets manager |
| **Skin** | `--skin-color-bg-base`, `--skin-color-border`, `-hover`, `--skin-color-text-primary/muted`, `--skin-color-danger`, `--skin-radius-md`, `--skin-font-sans`, `--skin-text-base`, `--skin-space-sm` |

### M-003 `soma-select` · EXISTS (refactor)

| | |
|---|---|
| **Purpose** | Single/multi select with optional search. |
| **Props** | `options: SelectOption[]` (`{ value, label, disabled?, group?, meta? }`) · `value: string \| string[]` · `multiple: boolean` (NEW) · `searchable` · `placeholder` · `disabled` · `error` · `clearable: boolean` (NEW) |
| **Slots** | `option` (custom row template via render prop alternative: `optionTemplate`) |
| **Events** | `soma-select` `{ value, option }` · `soma-open` · `soma-close` |
| **States** | closed · open · empty-options · error · disabled · loading (`loading` prop for async options) |
| **Reuse** | settings, model picker, filters |
| **Skin** | same field tokens as M-002 + `--skin-z-dropdown` |

### M-004 `soma-toggle` · EXISTS (refactor)

| | |
|---|---|
| **Purpose** | Boolean switch with label + description. |
| **Props** | `checked` · `disabled` · `label` · `description` · `name?` · `indeterminate?: boolean` |
| **Slots** | — |
| **Events** | `soma-change` `{ checked }` |
| **States** | off · on · disabled · focus |
| **Reuse** | settings, secrets, tool catalog enable |
| **Skin** | `--skin-color-accent`, `--skin-color-border`, `--skin-radius-full`, `--skin-motion-fast` |

### M-005 `soma-modal` · EXISTS (`soma-glass-modal` → refactor/rename)

| | |
|---|---|
| **Purpose** | Focused dialog. |
| **Props** | `open` · `title` · `subtitle?` · `size: 'sm' \| 'md' \| 'lg' \| 'full'` · `closeOnBackdrop` · `closeOnEscape` · `showClose` · `noPadding` · `busy?: boolean` |
| **Slots** | `default` · `footer` · `header` |
| **Events** | `soma-close` `{ reason: 'backdrop' \| 'escape' \| 'button' \| 'programmatic' }` · `soma-confirm` |
| **States** | closed · open · busy |
| **Reuse** | model card edit, confirm destructive, message inspect |
| **Skin** | `--skin-color-bg-card`, `--skin-glass-bg`, `--skin-glass-border`, `--skin-shadow-overlay`, `--skin-radius-xl`, `--skin-z-modal` |
| **A11y** | `role="dialog"` `aria-modal` focus trap, restore focus on close |

### M-006 `soma-drawer` · NEW

| | |
|---|---|
| **Purpose** | Edge panel for secondary flows (filters, detail, secrets edit) without losing workspace. |
| **Props** | `open` · `side: 'left' \| 'right'` · `width: string` (default `420px`) · `title` · `modal: boolean` · `closeOnBackdrop` |
| **Slots** | `default` · `footer` |
| **Events** | `soma-close` · `soma-open` |
| **States** | closed · open · modal |
| **Reuse** | secrets manager, file metadata, notification detail |
| **Skin** | `--skin-color-bg-sidebar`, `--skin-color-border`, `--skin-shadow-lg`, `--skin-z-overlay`, `--skin-motion-normal` |

### M-007 `soma-form-field` · EXISTS (refactor)

| | |
|---|---|
| **Purpose** | Label + control + helper/error layout only (control via slot). |
| **Props** | `label` · `required` · `error` · `helper` · `for?: string` |
| **Slots** | `default` (the control) · `label-action` (e.g. “Test”) · `hint-right` |
| **Events** | — (delegates control events) |
| **States** | default · error · required |
| **Reuse** | all forms |
| **Skin** | type tokens (`--skin-text-sm`, `--skin-weight-medium`), `--skin-color-text-secondary`, `--skin-color-danger`, `--skin-space-xs` |
| **Refactor debt** | today embeds its own input + `soma-input` event; split to slot-based so M-002/M-003/M-004 compose cleanly |

### M-008 `soma-toast` · NEW

| | |
|---|---|
| **Purpose** | Transient success/error/info/warning feedback (global host). |
| **Props** | (host) `soma-toast-host` manages queue; individual toast via API not markup |
| **API** | `toast.success(msg, opts)` · `toast.error` · `toast.warn` · `toast.info` — `opts: { timeout, actionLabel, actionEvent, id }` |
| **Events** | `soma-toast-action` `{ id, actionLabel }` · `soma-toast-dismiss` `{ id }` |
| **States** | visible · auto-dismiss · sticky error (errors default sticky until dismissed) |
| **Reuse** | every async action (upload, save, revoke) |
| **Skin** | `--skin-color-bg-card`, semantic colours, `--skin-z-toast`, `--skin-shadow-md`, `--skin-radius-md` |

### M-009 `soma-table` · EXISTS (`soma-data-table` → refactor)

| | |
|---|---|
| **Purpose** | Sortable data table. |
| **Props** | `columns: TableColumn[]` · `data: Record<string, unknown>[]` · `rowKey` · `clickable` · `emptyMessage` · `loading?: boolean` (NEW) · `error?: string` (NEW) · `selectable?: boolean` (NEW) · `sortBy?` / `sortDir?` (controlled, NEW) |
| **Slots** | `cell:{columnId}` (renderer) · `empty` · `error` |
| **Events** | `soma-row-click` `{ row, key }` · `soma-sort` `{ column, dir }` · `soma-selection-change` `{ keys }` |
| **States** | loading · empty · error · populated · sorted |
| **Reuse** | secrets, models, plugins, skills, audit, users |
| **Skin** | `--skin-color-bg-base/card`, `--skin-color-border`, `--skin-color-bg-hover/active`, `--skin-text-sm` |

### M-010 `soma-tabs` · NEW

| | |
|---|---|
| **Purpose** | Horizontal/vertical tab switcher. |
| **Props** | `tabs: { id, label, icon?, badge?, disabled?, reason? }[]` · `active: string` · `orientation: 'horizontal' \| 'vertical'` · `fill: boolean` |
| **Slots** | `panel:{tabId}` |
| **Events** | `soma-tab-change` `{ id }` |
| **States** | default · active · disabled-present-but-disabled (shows `reason`) · overflow scroll |
| **Reuse** | settings sections, canvas surface bar, message detail |
| **Skin** | `--skin-color-accent`, `--skin-color-border`, `--skin-color-bg-hover`, `--skin-radius-md` |

### M-011 `soma-badge` · EXISTS (`soma-status-badge` → rename/align)

| | |
|---|---|
| **Purpose** | Status / count chip. |
| **Props** | `variant: 'success' \| 'warning' \| 'danger' \| 'info' \| 'neutral' \| 'accent'` · `size: 'sm' \| 'md'` · `showDot` · `label` · `count?: number` |
| **Slots** | `default` |
| **Events** | — |
| **States** | variant colour only |
| **Reuse** | nav, tables, gated surfaces, tool status |
| **Skin** | semantic colours + `--skin-radius-full` |

### M-012 `soma-card` · NEW

| | |
|---|---|
| **Purpose** | Surface container (stat, module, provider). |
| **Props** | `variant: 'default' \| 'outlined' \| 'glass'` · `hoverable` · `selected` · `padding: 'sm' \| 'md' \| 'lg'` · `disabled` · `disabledReason?` |
| **Slots** | `default` · `header` · `footer` · `media` |
| **Events** | `soma-card-click` (only if `hoverable` and not disabled) |
| **States** | default · hover · selected · disabled+reason |
| **Reuse** | model cards, plugin cards, skill cards, welcome quick actions |
| **Skin** | `--skin-color-bg-card`, `--skin-color-border`, `--skin-glass-bg`, `--skin-shadow-sm/md`, `--skin-radius-lg` |

### M-013 `soma-dropdown` · NEW (absorb `soma-action-menu`)

| | |
|---|---|
| **Purpose** | Menu / action list anchored to a trigger. |
| **Props** | `items: { id, label, icon?, danger?, disabled?, reason?, separator? }[]` · `placement: 'bottom-start' \| 'bottom-end' \| 'top-start'` · `open` (controlled) |
| **Slots** | `trigger` |
| **Events** | `soma-action` `{ id }` · `soma-open` · `soma-close` |
| **States** | closed · open · empty · disabled items with reason |
| **Reuse** | conversation ⋮, message actions, file row actions |
| **Skin** | `--skin-color-bg-card`, `--skin-color-border`, `--skin-z-dropdown`, `--skin-shadow-md` |

### M-014 `soma-empty-state` · NEW

| | |
|---|---|
| **Purpose** | Honest empty vs “nothing yet” vs gated. |
| **Props** | `kind: 'empty' \| 'gated' \| 'unavailable'` · `icon` · `title` · `description` · `actionLabel?` · `actionHref?` · `reason?` (for gated) |
| **Slots** | `default` · `actions` |
| **Events** | `soma-empty-action` |
| **States** | three kinds above — never a lying spinner |
| **Reuse** | all lists |
| **Skin** | `--skin-color-text-muted`, `--skin-color-warning` (gated), core spacing |

### M-015 `soma-error-state` · NEW

| | |
|---|---|
| **Purpose** | Load/API failure with retry. Distinct from empty. |
| **Props** | `title` · `detail` · `status?: number` · `retryable: boolean` · `busy?: boolean` |
| **Slots** | `actions` |
| **Events** | `soma-retry` |
| **States** | error · retrying |
| **Reuse** | every fetch surface (memory, files, settings, cognitive) |
| **Skin** | `--skin-color-danger`, `--skin-color-bg-card`, core type |

### M-016 `soma-skeleton` · NEW

| | |
|---|---|
| **Purpose** | Loading placeholder (text/row/card shapes). |
| **Props** | `variant: 'text' \| 'row' \| 'card' \| 'tree'` · `lines?: number` · `height?: string` |
| **Slots** | — |
| **Events** | — |
| **States** | shimmering · `prefers-reduced-motion` → static |
| **Reuse** | all lists/tables before data |
| **Skin** | `--skin-color-bg-hover`, `--skin-radius-md`, `--skin-motion-slow` |

### M-017 `soma-avatar` · NEW

| | |
|---|---|
| **Purpose** | User/agent identity chip. |
| **Props** | `src?` · `initials?` · `icon?` · `size: 'xs' \| 'sm' \| 'md' \| 'lg'` · `status?: 'online' \| 'busy' \| 'offline'` |
| **Slots** | — |
| **Events** | — |
| **States** | image · fallback initials · icon |
| **Reuse** | sidebar user, message headers, agent pickers |
| **Skin** | `--skin-color-accent`, `--skin-color-bg-hover`, `--skin-radius-full` |

**L0 exit gate:** `npx tsc` + `vite build` green; Story-style `soma-kitchen-sink` route (optional, dev-only) mounting each primitive in all states.

---

## L1 — Core shell modules

### M-018 `soma-app-shell` · NEW

| | |
|---|---|
| **Purpose** | Single chrome host: thin top strip + left rail + main + optional right rail. A0 chrome law: composer is hero; left rail = **Memory + Settings only** (plus chat list / search / new chat / profile). |
| **Props** | `sessionReady: boolean` · `route: string` · `rightRailOpen: boolean` · `sidebarCollapsed: boolean` · `skinId?: string` (Capsule skin host — sets `--skin-*` on `:host`) |
| **Slots** | `top` · `rail` · `main` · `right` · `overlays` (toasts, palette, drawers) |
| **Events** | `soma-shell-toggle-rail` · `soma-shell-toggle-sidebar` · `soma-shell-navigate` `{ path }` |
| **States** | booting · ready · session-missing (route to `/login`) · offline (WS down banner) |
| **Reuse** | all non-auth routes |
| **Skin** | `chrome` + container layout tokens (`--skin-sidebar-width`, `--skin-header-height`) |

### M-019 `soma-topbar` · NEW (replaces inline strips; keep `soma-chat-topbar` as chat-specific sibling)

| | |
|---|---|
| **Purpose** | Thin global strip: brand, ambient status (Brain ◉ · Sync ○ · Memory ◌), notifications, project chip, profile. |
| **Props** | `brainState?: { online: boolean, detail?: string }` · `syncState?: { online: boolean }` · `memoryState?: { online: boolean }` · `notificationsUnread: number` · `projectLabel?: string` · `user?: { name, avatar? }` |
| **Slots** | `actions` (extra) · `center` (chat title overrides) |
| **Events** | `soma-open-notifications` · `soma-open-profile` · `soma-open-command-palette` · `soma-status-click` `{ kind: 'brain' \| 'sync' \| 'memory' }` |
| **States** | connected · degraded (per indicator) · unknown (hidden, not fake) |
| **Reuse** | all shell routes |
| **Skin** | `chrome` surface tokens |
| **Law** | status is 12px ambient (IA-001); Memory click → `/memory` only (never canvas tab) |

### M-020 `soma-sidebar` · EXISTS (refactor → dual profile)

| | |
|---|---|
| **Purpose** | Two nav profiles in one component: `profile: 'chat' \| 'admin'`. |
| **Props** | `profile` · `sections?: NavSection[]` (admin default = `ADMIN_NAV`) · `collapsed` · `activeRoute` · `conversations?: ConversationLite[]` (chat profile) · `searchQuery?: string` · `unreadMap?: Record<string, number>` |
| **Slots** | `header` · `footer` · `user-block` |
| **Events** | `soma-nav` `{ route }` · `soma-new-chat` · `soma-conversation-select` `{ id }` · `soma-conversation-action` `{ id, action: 'rename' \| 'export' \| 'delete' }` · `soma-chat-search` `{ query }` · `soma-collapse` `{ collapsed }` |
| **States** | loading list · empty list · error (`_loadFailed`) · grouped by day |
| **Reuse** | chat workspace (profile=`chat`), settings/admin (profile=`admin`) |
| **Skin** | `sidebar` surface (`--skin-color-bg-sidebar`, …) |
| **Refactor debt** | strip Models/Channels from chat rail (IA law); keep only Search · New chat · chat list · **Memory** · **Settings** · profile |

### M-021 `soma-command-palette` · NEW

| | |
|---|---|
| **Purpose** | ⌘K / Ctrl-K command hub over routes + actions (open memory, settings, new chat, open file, run tool). |
| **Props** | `open` · `providers: PaletteProvider[]` (`{ id, kind: 'route' \| 'action' \| 'file' \| 'conversation', search(), execute() }`) · `placeholder` · `recentIds?: string[]` |
| **Slots** | `footer` |
| **Events** | `soma-palette-open/close` · `soma-palette-execute` `{ id, kind }` · `soma-palette-query` `{ query }` |
| **States** | closed · searching · results · empty · provider-error (partial results + banner) |
| **Reuse** | global (shell `overlays` slot) |
| **Skin** | `--skin-color-bg-card`, `--skin-z-modal`, `--skin-shadow-overlay` |
| **Law** | Memory/Settings entries navigate to their **single home**; no duplicate destinations |

### M-022 `soma-notification-center` · NEW

| | |
|---|---|
| **Purpose** | Bell + panel for agent/platform notifications (real API only). |
| **Props** | `unreadCount` · `items: NotificationItem[]` · `loading` · `error` · `filter: 'all' \| 'unread'` |
| **Slots** | `empty` · `item` |
| **Events** | `soma-notifications-mark-read` `{ ids }` · `soma-notifications-mark-all` · `soma-notification-open` `{ id, href? }` · `soma-notification-dismiss` `{ id }` |
| **States** | loading · empty · error · populated |
| **Reuse** | topbar bell |
| **Skin** | `chrome` + card tokens |
| **Binding** | live notifications/audit API when mounted; if endpoint absent → present-but-disabled with reason (never empty list that pretends “0 notifications”) |

### M-023 `soma-permission-guard` · EXISTS

| | |
|---|---|
| **Purpose** | Wrap children; if missing permission render locked + reason. |
| **Props** | `permission: string` · `fallback?: 'hide' \| 'lock'` · `reason?` |
| **Slots** | `default` · `locked` |
| **Events** | — |
| **States** | allowed · denied (lock + reason) · unknown (loading) |
| **Reuse** | admin routes, destructive actions |
| **Skin** | `--skin-color-warning`, muted text |

---

## L2 — Workspace modules (File Manager first-class)

### M-024 `soma-file-manager` · NEW · **first-class module**

| | |
|---|---|
| **Purpose** | Full work-directory browser: tree + list + preview + upload/download + breadcrumb. Single reusable module for canvas UI-X-01, composer “insert file”, settings backups, capsule knowledge files. |
| **Props** | `rootId?: string` · `path: string` (controlled breadcrumb path) · `selection: string[]` (file ids) · `mode: 'browse' \| 'select' \| 'manage'` · `showPreview: boolean` · `showUpload: boolean` · `showToolbar: boolean` · `pageSize?: number` · `accept?: string[]` (mime/extension filter) · `maxUploadBytes?: number` |
| **Slots** | `toolbar-extra` · `preview` (override preview host) · `empty` · `footer` |
| **Events** | `soma-path-change` `{ path, node }` · `soma-file-open` `{ fileId, name, mime, path }` · `soma-file-select` `{ fileIds }` · `soma-file-download` `{ fileId, name }` · `soma-upload-start` `{ files }` · `soma-upload-progress` `{ fileId, loaded, total, name }` · `soma-upload-complete` `{ fileId, name }` · `soma-upload-error` `{ name, error }` · `soma-file-delete` `{ fileId, name }` · `soma-file-rename` `{ fileId, name, newName }` · `soma-refresh` |
| **States** | `loading` (tree skeleton) · `empty` (dir has no children) · `error` (`soma-error-state` + retry) · `uploading` (per-file progress rows) · `partial` (list ok, tree failed → banner) |
| **Reuse** | canvas UI-X-01 · chat attachments picker · document/code editors source · backup/restore file list |
| **Skin** | `right_panel` surface: `--skin-color-bg-base`, `--skin-color-bg-sidebar`, `--skin-color-border`, `--skin-color-bg-hover/active`, `--skin-font-mono` (paths), `--skin-text-sm` |

**Internal composition (not independently shippable without the parent):**

| Sub-tag | Role | Props (delta) | Events (delta) |
|---|---|---|---|
| `soma-file-breadcrumb` | path bar | `path`, `rootLabel`, `readonly?` | `soma-path-change` |
| `soma-file-tree` | lazy tree | `nodes: TreeNode[]`, `expandedIds`, `loadingIds`, `selectedId` | `soma-expand`, `soma-collapse`, `soma-select`, `soma-file-open` |
| `soma-file-list` | dense list/table | `rows: FileRow[]`, `sort`, `columns: 'name' \| 'detail' \| 'compact'` | `soma-sort`, `soma-row-actions`, `soma-file-open`, `soma-file-select` |
| `soma-file-preview` | right/inline preview | `fileId`, `mime`, `name`, `size`, `editable?: boolean` | `soma-download`, `soma-edit-request` |
| `soma-file-upload-tray` | upload queue | `items: UploadItem[]` | `soma-cancel`, `soma-retry`, `soma-clear` |
| `soma-file-toolbar` | actions | `selection`, `canUpload`, `canDelete`, `canDownload` | `soma-upload-click`, `soma-download-click`, `soma-new-folder`, `soma-refresh` |

**Preview policy (real, no fake renderers):**

| Mime | Preview |
|---|---|
| `text/*`, `application/json`, source code | `soma-code-editor` in `readonly` |
| `image/*` | `<img>` from signed/authorized URL |
| `application/pdf` | iframe object from authorized URL |
| markdown | `soma-doc-viewer` |
| binary/unknown | metadata card + Download only (honest) |

**Binding (no mocks):** `GET /api/v2/filesv2/` for list · `POST /api/v2/filesv2/upload` → `upload_url` (S3 presign or `/upload-local/{file_id}`) as in `webui/src/services/file-upload.ts` · download via authorized URL endpoint; if a method is missing on the deployment, that control is present-but-disabled with reason.

### M-025 `soma-right-panel` · EXISTS (refactor → canvas host)

| | |
|---|---|
| **Purpose** | Right-rail surface registry host (UI-X-01…08). |
| **Props** | `active: SurfaceKey` · `available: Record<SurfaceKey, { available: boolean, reason?: string }>` · `fileContext?: FileRow` · `agentId` |
| **Slots** | `surface:{key}` (override) · `tabs` |
| **Events** | `soma-surface-change` `{ key }` · `soma-gated-explain` `{ key, reason }` |
| **States** | loading surface · error · gated (reason string) · open/collapsed |
| **Reuse** | chat workspace only (one host) |
| **Skin** | `right_panel` |
| **Refactor debt** | extract tab bar to `soma-tabs`; mount M-024 as `files` surface; keep GATED honesty for Browser/Desktop |

### M-026 `soma-canvas-browser` · NEW · GATED

| | |
|---|---|
| **Purpose** | Embedded browser surface (UI-X-03). |
| **Props** | `sessionId?` · `url?` · `readonly?: boolean` |
| **Slots** | `fallback` |
| **Events** | `soma-browser-ready` · `soma-browser-error` |
| **States** | gated (`Bind a browser model on UI-S-02 first`) · live session · error |
| **Reuse** | canvas only |
| **Skin** | `right_panel` |

### M-027 `soma-desktop-surface` · NEW · GATED

| | |
|---|---|
| **Purpose** | Remote desktop / VNC host (UI-X-08). |
| **Props** | `endpoint?` · `sessionId?` |
| **Slots** | `fallback` |
| **Events** | `soma-desktop-ready` / `error` |
| **States** | gated (fixed reason) · connected · disconnected |
| **Skin** | `right_panel` |

### M-028 `soma-code-editor` · NEW (UI-X-04)

| | |
|---|---|
| **Purpose** | Code editing surface (RO until save API is real). |
| **Props** | `value: string` · `language: string` · `readonly: boolean` · `path?: string` · `dirty: boolean` · `minimap: boolean` |
| **Slots** | `actions` (Save, Download) · `status` (Ln/Col, language chip) |
| **Events** | `soma-editor-input` `{ value }` · `soma-editor-save` `{ value, path }` · `soma-editor-download` · `soma-editor-language` `{ language }` |
| **States** | loading · readonly · dirty · save-error · unsupported-language (plain text) |
| **Reuse** | canvas editor, file preview, doc code blocks |
| **Skin** | `--skin-font-mono`, `--skin-color-bg-base`, `--skin-color-text-primary`, `--skin-color-border` |
| **Note** | real editor engine (CodeMirror 6 or Monaco) — not a textarea with a fake “IDE” chrome |

### M-029 `soma-code-block` · NEW

| | |
|---|---|
| **Purpose** | Syntax-highlighted code block for chat/docs with copy/download. |
| **Props** | `code: string` · `language: string` · `showLineNumbers?: boolean` · `title?: string` · `collapsed?: boolean` |
| **Slots** | `actions` |
| **Events** | `soma-code-copy` · `soma-code-insert` · `soma-code-download` |
| **States** | plain (unknown lang) · highlighted · collapsed |
| **Reuse** | `soma-message`, `soma-doc-viewer` |
| **Skin** | `--skin-font-mono`, card tokens |
| **Gap closed** | FEATMATRIX U-03 |

### M-030 `soma-doc-viewer` · NEW

| | |
|---|---|
| **Purpose** | Read-only document surface (markdown, exported docs) with optional editable mode later. |
| **Props** | `content: string` · `format: 'markdown' \| 'text'` · `editable: boolean` · `fileId?: string` |
| **Slots** | `toolbar` |
| **Events** | `soma-doc-save` `{ content }` · `soma-doc-download` · `soma-doc-edit-request` |
| **States** | loading · rendered · error · dirty (when editable) |
| **Reuse** | canvas docs, backups restore notes, skills/prompt preview |
| **Skin** | `chat` type scale + `--skin-color-text-link` |
| **Gap closed** | FEATMATRIX U-14 (viewer); editor phases behind real save API |

### M-031 `soma-markdown` · NEW (extract/replace `utils/markdown.ts` render path)

| | |
|---|---|
| **Purpose** | Safe markdown renderer as a Lit module (tables, lists, links, code → M-029). |
| **Props** | `source: string` · `safe: true` (always) · `linkPolicy: 'allow' \| 'nofollow'` · `onCopyCode?: boolean` |
| **Slots** | — |
| **Events** | `soma-md-link-click` `{ href, external }` (never `window.open` blindly) · `soma-code-copy` (bubbled from code blocks) |
| **States** | empty source · rendered |
| **Reuse** | message content, doc viewer, plugin/skill readme |
| **Skin** | type tokens, `--skin-color-text-link`, `--skin-color-border` |
| **Gap closed** | FEATMATRIX U-04 |

---

## L3 — Chat modules

### M-032 `soma-message-list` · NEW

| | |
|---|---|
| **Purpose** | Virtualized scroll container + branch context. |
| **Props** | `messages: ChatMessage[]` · `streamingId?: string` · `autoScroll: boolean` · `branch?: { parentId, branchId, count, index }` · `groupTools: boolean` |
| **Slots** | `message` (row template override) · `loading` · `empty` |
| **Events** | `soma-scroll-bottom` · `soma-branch-switch` `{ branchId, index }` · `soma-message-action` `{ id, action }` |
| **States** | loading · empty (welcome) · error · streaming (live tail) |
| **Reuse** | `/chat`, voice chat transcription history (alternate template) |
| **Skin** | `chat` surface |
| **Gap** | FEATMATRIX U-08 (branch UI host) |

### M-033 `soma-message` · EXISTS (refactor)

| | |
|---|---|
| **Purpose** | Single turn bubble (user/assistant/tool). |
| **Props** | `messageRole: 'user' \| 'assistant' \| 'system'` · `text` · `timestamp` · `tools: ToolCallStep[]` · `streaming` · `thinking` · `stopped` · `confidence?` · `error` · `attachments: AttachmentMeta[]` · `turnMeta?` · `branchIndex?` / `branchCount?` (NEW) |
| **Slots** | `actions` · `footer` |
| **Events** | `soma-message-copy` · `soma-message-regenerate` · `soma-message-branch` `{ direction: 'prev' \| 'next' \| 'create' }` · `soma-attachment-open` `{ fileId }` · `soma-tool-approval` `{ toolCallId, decision, reason? }` |
| **States** | draft · streaming · complete · stopped · error · thinking |
| **Reuse** | message list |
| **Skin** | `chat` |
| **Refactor debt** | body renders via M-031; code via M-029; tool rows stay M-034 |

### M-034 `soma-tool-timeline` · EXISTS (refactor)

| | |
|---|---|
| **Purpose** | Collapsible tool-call steps with HITL approve/reject. |
| **Props** | `steps: ToolCallStep[]` · `expanded: boolean` · `approvalEnabled: boolean` |
| **Slots** | `step` · `approval` |
| **Events** | `soma-tool-toggle` `{ id }` · `soma-tool-approval` `{ toolCallId, decision: 'approve' \| 'reject', reason }` |
| **States** | pending · running · success · failed · awaiting-approval · rejected |
| **Reuse** | message, debug surface (UI-X-05 read path) |
| **Skin** | `tool_timeline` surface |
| **Law** | never claim allow when OPA denied; show denial reason |

### M-035 `soma-composer` · EXISTS (refactor)

| | |
|---|---|
| **Purpose** | Hero input: text + attach + voice + send + queue. |
| **Props** | `busy` · `placeholder` · `disabledReason?` · `attachEnabled` · `voiceEnabled` · `queueDepth` · `modelLabel?` (display only) |
| **Slots** | `prefix` · `suffix` · `menu` |
| **Events** | `soma-send` `{ text, attachments: AttachmentMeta[], enqueue?: boolean }` · `soma-stop` · `soma-voice-toggle` · `soma-attach-request` · `soma-queue-clear` |
| **States** | idle · busy · recording · mic-error · upload-error (non-blocking for text) · disabled+reason |
| **Reuse** | `/chat` hero (welcome + active) |
| **Skin** | `composer` surface |
| **Gap** | FEATMATRIX U-05 attachments (pipeline via `file-upload.ts`) |

### M-036 `soma-attachment-chip` · NEW

| | |
|---|---|
| **Purpose** | Per-file chip in composer/messages with upload state and open/remove. |
| **Props** | `name` · `mime` · `size` · `fileId?` · `state: 'uploading' \| 'ready' \| 'failed'` · `progress?: number` · `error?` · `removable: boolean` |
| **Slots** | — |
| **Events** | `soma-attachment-remove` · `soma-attachment-retry` · `soma-attachment-open` `{ fileId }` |
| **States** | uploading · ready · failed (message still sendable without `file_id`) |
| **Skin** | `composer` + card tokens |

### M-037 `soma-attachment-picker` · NEW

| | |
|---|---|
| **Purpose** | Modal hosting M-024 in `mode: 'select'` + local file picker tab. |
| **Props** | `open` · `accept?: string[]` · `maxBytes?: number` · `multiple: boolean` · `maxCount?: number` |
| **Slots** | `tabs` |
| **Events** | `soma-attachments-selected` `{ files: { file?: File, fileMeta?: AttachmentMeta }[] }` · `soma-close` |
| **States** | loading files · empty · upload error · over-limit (honest client message) |
| **Skin** | modal tokens |

### M-038 `soma-chat-topbar` · EXISTS (refactor)

| | |
|---|---|
| **Purpose** | Chat-local strip: title, rename, export, delete, model chip, canvas toggle. |
| **Props** | `title` · `conversationId` · `canRename` · `canvasOpen` · `modelLabel` |
| **Slots** | `center` · `actions` |
| **Events** | `soma-conversation-rename` · `soma-conversation-export` · `soma-conversation-delete` · `soma-toggle-canvas` · `soma-open-models` |
| **States** | ready · busy (rename) · error |
| **Skin** | `chrome` |
| **Gap** | FEATMATRIX U-09 export (JSON already in `soma-chat` — keep real handler) |

### M-039 `soma-chat-search` · NEW

| | |
|---|---|
| **Purpose** | Search conversations + in-thread messages. |
| **Props** | `scope: 'conversations' \| 'thread' \| 'all'` · `query` · `results` · `loading` · `error` |
| **Slots** | `result` · `empty` |
| **Events** | `soma-chat-search` `{ query, scope }` · `soma-chat-search-open` `{ conversationId, messageId? }` |
| **States** | idle · loading · empty · error · results |
| **Reuse** | sidebar search box, ⌘K provider |
| **Gap** | FEATMATRIX U-10 |

### M-040 `soma-branch-indicator` · NEW

| | |
|---|---|
| **Purpose** | Prev/next/create branch controls on a message. |
| **Props** | `index` · `count` · `enabled` |
| **Slots** | — |
| **Events** | `soma-message-branch` `{ direction }` |
| **States** | single · multi · disabled (no branch API yet → hide create, keep navigate when server provides) |
| **Skin** | `chat` |
| **Gap** | FEATMATRIX U-08 |

### M-041 `soma-welcome` · EXISTS (`soma-welcome-dashboard` → refactor to IA law)

| | |
|---|---|
| **Purpose** | Empty-chat hero: greeting + **composer hero** + real warnings + Quick Actions (Files, Modules, New chat only) + channels CTA if unconfigured + system resources if API up. |
| **Props** | `userName?` · `warnings: RealWarning[]` · `channelsUnconfigured: string[]` · `system?: { ram, cpu, disk }` · `composerSlotHost` |
| **Slots** | `composer` · `warnings` |
| **Events** | `soma-quick-action` `{ id: 'files' \| 'modules' \| 'new-chat' }` · `soma-channel-connect` `{ channel }` · `soma-dismiss-warning` `{ id }` |
| **States** | default · warnings present · diagnostics-down (hide system panel) |
| **Law** | **No** Memory/Settings/Models/Brain hero cards (IA-001). |

---

## L4 — Admin / settings modules

### M-042 `soma-settings-shell` · NEW (extract from `soma-settings.ts`)

| | |
|---|---|
| **Purpose** | One settings chrome: nav + section host + dirty/save bar. |
| **Props** | `sections: SettingsSection[]` · `activeSection` · `dirty: boolean` · `saving: boolean` · `saveError?: string` |
| **Slots** | `section:{id}` · `save-bar` |
| **Events** | `soma-section-change` `{ id }` · `soma-settings-save` · `soma-settings-reset` · `soma-settings-dirty` `{ dirty }` |
| **States** | loading · dirty · saving · save-error · saved |
| **Reuse** | all `/settings/*` |
| **Skin** | `chrome` + form tokens |
| **Law** | Models live **inside** Settings (full-screen section, not welcome card). |

### M-043 `soma-settings-nav` · NEW

| | |
|---|---|
| **Purpose** | Section list with icons + lock reasons. |
| **Props** | `sections` · `active` · `permissionMap` |
| **Events** | `soma-section-change` |
| **States** | default · active · locked+reason |
| **Skin** | `sidebar` |

### M-044 `soma-settings-section` · NEW

| | |
|---|---|
| **Purpose** | Section wrapper: title, description, fields grid, danger zone. |
| **Props** | `title` · `description` · `id` · `collapsed?` |
| **Slots** | `default` · `actions` · `danger` |
| **Events** | — |
| **Reuse** | every settings page |

### M-045 `soma-secret-field` · NEW

| | |
|---|---|
| **Purpose** | Masked secret input with reveal/hint-not-value policy. |
| **Props** | `name` · `hasValue: boolean` · `providerId` · `helper` · `readOnly` |
| **Slots** | `actions` (Test, Rotate, Revoke) |
| **Events** | `soma-secret-set` `{ name, value }` · `soma-secret-reveal` · `soma-secret-revoke` · `soma-secret-test` |
| **States** | unset · set-hidden · editing · testing · error · revoked |
| **Reuse** | secrets manager, model provider config |
| **Law** | values never re-displayed after set; write path `PUT /secrets/providers/{id}` (Vault) |

### M-046 `soma-secrets-manager` · NEW

| | |
|---|---|
| **Purpose** | Per-provider secret inventory + set/test/revoke. |
| **Props** | `providers: { id, name, secrets: { name, hasValue, updatedAt? }[] }[]` · `loading` · `error` · `tenantId` |
| **Slots** | `provider` · `empty` |
| **Events** | `soma-secret-set` · `soma-secret-revoke` · `soma-secret-test` · `soma-refresh` |
| **States** | loading · empty · error · populated · test-result banner |
| **Reuse** | Settings · Integrations |
| **Gap** | FEATMATRIX U-20 / GAP-H02 |

### M-047 `soma-model-provider-config` · NEW

| | |
|---|---|
| **Purpose** | Provider/model setup UI against real `ModelIn` (16 fields) + Vault key binding. |
| **Props** | `models: ModelOut[]` · `providers: ProviderLite[]` · `loading` · `error` · `selectedId?` |
| **Slots** | `card` · `form` · `empty` |
| **Events** | `soma-model-create` `{ payload: ModelIn }` · `soma-model-update` `{ id, payload }` · `soma-model-activate` `{ id, active }` · `soma-model-test` `{ id }` · `soma-model-delete` `{ id }` |
| **States** | loading · empty · error · form-dirty · testing · invalid-schema (field errors) |
| **Reuse** | Settings · Models (UI-S-51), chat model chip deep-link |
| **Fields** | name · display_name · model_type · provider · api_base · capabilities · priority · cost_tier · domains · ctx_length · limit_requests · limit_input · limit_output · vision · kwargs · is_active — **no invented fields**; API keys via M-045 only |
| **Gap** | FEATMATRIX U-17 / GAP-C02 |

### M-048 `soma-plugin-manager` · NEW

| | |
|---|---|
| **Purpose** | Installed plugin list + enable/disable + inspect + install/remove when backend plugin API ships. |
| **Props** | `plugins: PluginRow[]` · `catalog?: PluginRow[]` · `loading` · `error` · `canInstall: boolean` |
| **Slots** | `card` · `detail` · `empty` · `gated` |
| **Events** | `soma-plugin-enable` `{ id, enabled }` · `soma-plugin-install` `{ id }` · `soma-plugin-remove` `{ id }` · `soma-plugin-inspect` `{ id }` |
| **States** | loading · empty · error · gated (backend plugin API missing → reason) · busy |
| **Reuse** | Settings · Advanced / Plugins |
| **Gap** | FEATMATRIX U-18 / P-01…P-04 |
| **Honesty** | UI may ship gated first; **no fake plugin rows** |

### M-049 `soma-skills-manager` · NEW

| | |
|---|---|
| **Purpose** | Skills catalog: list, enable, import/export, read SKILL.md. |
| **Props** | `skills: SkillRow[]` · `loading` · `error` · `selectedSkill?: SkillDetail` |
| **Slots** | `card` · `detail` · `empty` |
| **Events** | `soma-skill-enable` · `soma-skill-import` `{ file }` · `soma-skill-export` `{ id }` · `soma-skill-select` `{ id }` |
| **States** | loading · empty · error · detail-loading · import-error |
| **Reuse** | Settings · Skills / Modules |
| **Gap** | FEATMATRIX U-19 / P-06…P-07 |

### M-050 `soma-agent-profile-editor` · NEW (partially EXISTS in `soma-settings` + `soma-capsule-editor`)

| | |
|---|---|
| **Purpose** | Agent persona/prompt/limits editor bound to Capsule + agent settings. |
| **Props** | `agentId` · `capsule: CapsuleConfigOut` · `persona` · `limits` · `dirty` · `loading` · `error` · `readonly` |
| **Slots** | `identity` · `prompt` · `limits` · `knowledge` |
| **Events** | `soma-profile-save` `{ patch }` · `soma-profile-reset` · `soma-knowledge-open` |
| **States** | loading · dirty · saving · error · readonly (permission) |
| **Reuse** | Settings · Agent, capsule surface (UI-X-06 wraps `soma-capsule-editor`) |
| **Gap** | FEATMATRIX U-22 / GAP-H03 |

### M-051 `soma-backup-restore` · NEW

| | |
|---|---|
| **Purpose** | Backup create/list/download + restore with confirm. |
| **Props** | `backups: BackupRow[]` · `loading` · `error` · `canRestore: boolean` · `busyProgress?: number` |
| **Slots** | `empty` · `row` |
| **Events** | `soma-backup-create` · `soma-backup-download` `{ id }` · `soma-backup-restore` `{ id, confirmed: true }` · `soma-backup-delete` `{ id }` |
| **States** | loading · empty · error · creating · restoring (progress) · confirm-danger |
| **Reuse** | Settings · Advanced |
| **Gap** | FEATMATRIX U-23 / I-06 / GAP-H04 |
| **Law** | restore requires typed confirmation modal (M-005); never one-click |

### M-052 `soma-agent-profile-card` / `soma-user-profile-card` · EXISTS (refactor)

| | |
|---|---|
| **Purpose** | Identity card in sidebar/profile menus. |
| **Props** | `name` · `avatar?` · `role?` · `email?` · `tenant?` |
| **Slots** | `actions` |
| **Events** | `soma-logout` · `soma-open-profile` |
| **Skin** | `sidebar` |

### M-053 `soma-settings-models` (view) · EXISTS → compose from M-047

| | |
|---|---|
| **Purpose** | Route view `/settings/models` (UI-S-51). |
| **Composition** | `soma-settings-shell` + `soma-model-provider-config` + M-045 in modal |

---

## Dependency graph (build order)

```
L0 primitives
  M-001..M-017
        │
        ├─► L1 shell
        │     M-018 app-shell
        │     M-019 topbar ──► M-022 notifications, M-017 avatar
        │     M-020 sidebar ──► M-010 tabs? no ──► M-039 chat-search
        │     M-021 command-palette ──► M-020 routes
        │     M-023 permission-guard
        │
        ├─► L2 workspace
        │     M-024 file-manager
        │         ├─ M-024a breadcrumb
        │         ├─ M-024b tree ──► M-016 skeleton
        │         ├─ M-024c list ──► M-009 table, M-013 dropdown
        │         ├─ M-024d preview ──► M-028 code-editor | M-030 doc-viewer | img/pdf
        │         └─ M-024e upload-tray ──► M-008 toast
        │     M-025 right-panel ──► M-024, M-028, M-034, M-026*, M-027*
        │     M-029 code-block ──► M-031
        │     M-031 markdown
        │
        ├─► L3 chat
        │     M-032 message-list ──► M-033 message ──► M-031, M-029, M-034
        │     M-035 composer ──► M-036 chips, M-037 picker ──► M-024 (select mode)
        │     M-038 chat-topbar, M-039 search, M-040 branch
        │     M-041 welcome ──► M-035
        │
        └─► L4 admin
              M-042 settings-shell ──► M-043, M-044
              M-045 secret-field ──► M-046, M-047
              M-047 model-provider-config
              M-048 plugins, M-049 skills, M-050 agent profile, M-051 backup
```

\* GATED surfaces render honest disabled states until backend capability exists.

---

## Reuse matrix (which modules appear where)

| Screen / surface | Modules |
|---|---|
| Welcome (`/chat` empty) | M-018, M-019, M-020, M-041, M-035, M-008 |
| Active chat | M-018, M-019, M-020, M-032, M-033, M-034, M-035, M-038, M-025 |
| Canvas Files (UI-X-01) | M-025 → **M-024** |
| Canvas Editor (UI-X-04) | M-025 → M-028 + M-024 context |
| Canvas Tools/Debug/Capsule/Brain | M-025 + existing tools timeline / capsule / cognitive panel |
| `/memory` | M-018, M-019, M-020, M-009/M-014/M-015 (list states), existing memory view body |
| `/settings` + sections | M-042…M-051, M-001–M-012 |
| `/settings/models` | M-042, M-047, M-045, M-005 |
| Auth | M-001, M-002, M-007, M-015 (login skin) |
| File attach in chat | M-037 → M-024 select → M-036 |

---

## Skin hooks summary (module → surface)

| Surface | Modules |
|---|---|
| `chrome` | M-018, M-019, M-022, M-038, M-042 |
| `sidebar` | M-020, M-043, M-052 |
| `composer` | M-035, M-036, M-037 |
| `chat` | M-031, M-032, M-033, M-040, M-041 |
| `tool_timeline` | M-034 |
| `right_panel` | M-024 (+subparts), M-025, M-026, M-027, M-028, M-030 |
| `login` | auth views |
| *(core tokens)* | all L0 primitives |

---

## Gap coverage (FEATMATRIX → modules)

| Gap | Priority | Module(s) |
|---|---|---|
| U-03 code highlight | HIGH | M-029 |
| U-04 markdown | HIGH | M-031 |
| U-05 attachments | HIGH | M-035, M-036, M-037, M-024 |
| U-06 images in chat | MED | M-033 media path |
| U-08 branching | MED | M-032, M-040 |
| U-09 export | LOW | M-038 |
| U-10 search | MED | M-039 |
| U-11 canvas | HIGH | M-025 |
| U-12 browser | HIGH | M-026 GATED |
| U-13 desktop | MED | M-027 GATED |
| U-14 doc editor | HIGH | M-030 (viewer first; save when API real) |
| U-15 code editor | HIGH | M-028 |
| U-17 model provider UI | CRITICAL | M-047, M-045 |
| U-18 plugins | MED | M-048 |
| U-19 skills | MED | M-049 |
| U-20 secrets UI | HIGH | M-046, M-045 |
| U-22 agent profile | HIGH | M-050 |
| U-23 backup/restore | MED | M-051 |
| M-09/M-10 file ops/tree | HIGH | **M-024** |
| GAP-C03 chat md+code | CRITICAL | M-031, M-029, M-033 |

---

## Implementation rules (non-negotiable)

1. **No shims, fakes, mocks, stubs, TODOs.** A module without a real API ships GATED with reason, not empty success.
2. **Lit 3.x only.** `@customElement('soma-*')` naming. No React/Alpine.
3. **Every control has a handler.** Failure → `soma-error-state` or `toast.error`. Never silent empty.
4. **Empty ≠ error.** `_loadFailed` flag on every fetch (contrast cognitive panel pattern).
5. **Skin tokens only** via `--skin-*` / alias map. Burn hex literals during refactor.
6. **IA law:** Memory one home `/memory`; Models full-screen in Settings; left rail Memory + Settings only; no hero cards for Memory/Settings/Models on welcome.
7. **CLEF / OPA honesty** applies to any approval UI (M-034): p_safe + risk + confidence separate; override requires reason; never claim allow when denied.
8. **Gates:** `npx tsc` · `vite build` · Playwright human session when authorized.

---

## Acceptance for this catalog

- [x] Ordered by dependency (L0 → L4)
- [x] Each module: purpose, props/API, slots, events, states, reuse, skin surface
- [x] NEW vs EXISTS marked against live `webui/src/components|views`
- [x] File Manager is first-class with tree + list + preview + upload/download + breadcrumb
- [x] FEATMATRIX §2.3 / §3 gaps mapped to modules
- [x] Skin surfaces from SOMA-UI-SKINS-001 §3.3 declared per module
- [x] Real endpoints only (filesv2, ModelIn, Vault secrets, WS chat, tools catalog)
- [x] No invented domain fields

**Next:** promote to build plan tickets (one ticket per module, EXITS = tsc+build+handler proof+skin tokens only).

End of Document
