# SOMA-UI-IDREG-001 — Screen Identifier Allocation

## Document Control

| Field | Value |
|---|---|
| Document Title | Screen Identifier Allocation |
| Document Identifier | SOMA-UI-IDREG-001 |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-01-UIUX-001.md`, `SOMA-UI-MOCKUPS-001.md`, `SOMA-01-DOCS-001.md` §3.3.2 |
| Source of truth | This document; files on disk under `docs/design/mockups/` |
| Audience | Anyone allocating or renumbering a UI sub-identifier |
| Scope | UI-S-00…53, UI-X-01…08, UI-M-01…03, and the reserved UI-C / UI-A / UI-F / REQ-UIX / UIX-AT ranges |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Promoted from a working artefact to a controlled document. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | SOMA-01-DOCS-001 §3.3.2 | Sub-identifier kinds |
| N-2 | SOMA-01-UIUX-001 | Screen and feature specification |
| N-3 | SOMA-A0-PARITY-001 | Owns `UI-AT-01`…`UI-AT-08`; new tests use `UIX-AT-NN` |

---

## 1. Purpose and Scope

This is the **authoritative allocation** of every user-interface sub-identifier used by the
UI/UX documentation suite. Nothing under `docs/design/mockups/` or `docs/iso/SOMA-01-UIUX-*.md`
**SHALL** take an identifier that is not reserved here.

Identifiers are never renumbered once issued. A retired identifier is marked retired and left
in place; a new one is issued instead.

## 2. Allocation

Authoritative ID allocation for the UI/UX suite. Every document in the suite and every
mockup MUST use these identifiers exactly. Do not renumber.

## Routable screens — UI-S-01 … UI-S-53

| ID | Screen | Facet | Route (current) | Source view |
|---|---|---|---|---|
| UI-S-01 | Soul — persona & system prompt | Soul | NEW | saas-capsule-editor |
| UI-S-02 | Brain — model & IQ | Brain | /cognitive | saas-cognitive-panel |
| UI-S-03 | Hands — tools & capabilities | Hands | /tools | saas-feature-catalog |
| UI-S-04 | Memory — retention & recall | Memory | /memory | saas-memory-view |
| UI-S-05 | Body — resources & limits | Body | NEW | NEW |
| UI-S-06 | Governance — constitution & hooks | Governance | NEW | NEW |
| UI-S-07 | Chat workspace | Chat | /chat | saas-chat |
| UI-S-08 | Message detail | Chat | /chat/:id | saas-chat |
| UI-S-09 | Conversation export | Chat | NEW | NEW |
| UI-S-10 | Conversation queue | Chat | NEW | NEW |
| UI-S-11 | Capsule list | Capsule | /workspace | saas-workspace |
| UI-S-12 | Capsule editor | Capsule | /workspace/:id | saas-workspace |
| UI-S-13 | Version rail & diff | Capsule | NEW | NEW |
| UI-S-14 | Instances | Capsule | NEW | NEW |
| UI-S-15 | Module list | Module | NEW | NEW |
| UI-S-16 | Module detail & config | Module | NEW | NEW |
| UI-S-17 | Capability registry | Module | NEW | NEW |
| UI-S-18 | Capability detail & hook bindings | Module | NEW | NEW |
| UI-S-19 | Tenants | Platform | /saas/tenants | saas-tenants |
| UI-S-20 | Tenant wizard | Platform | /saas/tenants/new | saas-tenant-wizard |
| UI-S-21 | Tenant dashboard | Platform | /admin/dashboard | saas-tenant-dashboard |
| UI-S-22 | Users | Platform | /admin/users | saas-users-view |
| UI-S-23 | Roles & role matrix | Platform | /platform/roles | saas-admin-roles-list |
| UI-S-24 | Permissions | Platform | /saas/permissions | saas-permissions |
| UI-S-25 | Billing | Platform | /admin/billing | saas-tenant-billing |
| UI-S-26 | Subscriptions | Platform | /saas/subscriptions | saas-subscriptions |
| UI-S-27 | Usage analytics | Platform | /platform/usage | saas-usage-analytics |
| UI-S-28 | Tier builder | Platform | /platform/tiers | saas-tier-builder |
| UI-S-29 | Login | Auth | /login | saas-login |
| UI-S-30 | Register | Auth | /register | saas-register |
| UI-S-31 | Forgot password | Auth | /forgot-password | saas-forgot-password |
| UI-S-32 | MFA setup | Auth | /mfa/setup | saas-mfa-setup |
| UI-S-33 | Auth callback | Auth | /auth/callback | saas-auth-callback |
| UI-S-34 | Personal profile | Auth | /profile | saas-personal-profile |
| UI-S-35 | Platform profile | Auth | /admin/profile | saas-platform-profile |
| UI-S-36 | Mode selection | Auth | /mode-select | saas-mode-selection |
| UI-S-37 | Platform dashboard | Ops | /saas/dashboard | saas-platform-dashboard |
| UI-S-38 | Platform metrics | Ops | /platform/metrics | platform-metrics-dashboard |
| UI-S-39 | Infrastructure dashboard | Ops | /platform/infrastructure | saas-infrastructure-dashboard |
| UI-S-40 | Rate limits | Ops | /platform/infrastructure/redis/ratelimits | saas-rate-limits |
| UI-S-41 | Integrations dashboard | Ops | /platform/integrations | saas-integrations-dashboard |
| UI-S-42 | Marketplace | Ops | /platform/marketplace | saas-marketplace |
| UI-S-43 | Audit dashboard | Ops | /platform/audit | saas-audit-dashboard |
| UI-S-44 | Audit log | Ops | /audit | saas-audit-log |
| UI-S-45 | Agent metrics | Ops | /admin/metrics | saas-agent-metrics |
| UI-S-46 | Voice chat | Voice | /voice/chat | saas-voice-chat |
| UI-S-47 | Voice sessions | Voice | /voice/sessions | saas-voice-sessions |
| UI-S-48 | Voice personas | Voice | /voice/personas | saas-voice-personas |
| UI-S-49 | Multimodal settings | Voice | /settings/multimodal | saas-multimodal-settings |
| UI-S-50 | Settings — Agent | Settings | /settings | saas-settings |
| UI-S-51 | Settings — Models | Settings | /settings/models | saas-settings-models |
| UI-S-52 | Settings — Channels | Settings | /settings/channels | saas-settings-channels |
| UI-S-53 | Settings — External & Developer | Settings | NEW | NEW |

## Surfaces — UI-X-01 … UI-X-08 (right rail)

| ID | Surface | State | Blocking reason when gated |
|---|---|---|---|
| UI-X-01 | Files | specified | — |
| UI-X-02 | Tools | specified | — |
| UI-X-03 | Browser | specified | — |
| UI-X-04 | Editor | specified | — |
| UI-X-05 | Debug | specified | — |
| UI-X-06 | Capsule | specified | — |
| UI-X-07 | Brain | specified | — |
| UI-X-08 | Desktop | GATED | Requires a remote-desktop capability in somaAgent01. Not available today. |

## Chrome — UI-S-00

Global chrome: capsule switcher, version chip, lifecycle chip, persona knobs x3, command palette,
facet tabs x6, instance strip, neuro meters x4, surface rail x8.

## Modals & overlays — UI-M-01 … UI-M-03 (three patterns only)

| ID | Pattern | Contract |
|---|---|---|
| UI-M-01 | Drawer | right-side, 420px, ESC closes, focus trap |
| UI-M-02 | Full-screen | covers viewport, explicit dismiss only |
| UI-M-03 | Dialog | centred, destructive confirm, ESC closes |

## Sub-identifier ranges (do not collide)

| Kind | Range | Owner document |
|---|---|---|
| UI-S-* | 01-53 | SOMA-01-UIUX-001 |
| UI-X-* | 01-08 | SOMA-01-UIUX-001 |
| UI-M-* | 01-03 | SOMA-01-UIUX-002 |
| UI-C-* | 001-120 | SOMA-01-UIUX-001 (controls) |
| UI-A-* | 001-120 | SOMA-01-UIUX-001 (actions) |
| UI-F-* | 001-080 | SOMA-01-UIUX-001 (features) |
| REQ-UIX-* | 001-060 | SOMA-01-UIUX-001 |
| UIX-AT-* | 01-40 | SOMA-01-UIUX-004 |

End of Document
