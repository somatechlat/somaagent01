# SOMA-UI-MOCKUPS-001 — User Interface Mockups Index

## Document Control

| Field | Value |
|---|---|
| Document Title | User Interface Mockups Index |
| Document Identifier | SOMA-UI-MOCKUPS-001 |
| Version | 1.1.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-01-UIUX-001.md`, `SOMA-01-UIUX-002.md`, `SOMA-UI-IDREG-001.md`, `SOMA-UI-TEMPLATE-001.md` |
| Source of truth | This document; annexes under `docs/design/mockups/` |
| Audience | Product, design and engineering reviewers |
| Scope | Every ASCII mockup annex under `docs/design/mockups/` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Index derived from the mockups present on disk. |
| 1.1.0 | 2026-10-08 | SomaTech Engineering | Sync index with implemented settings screens UI-S-54/55; add UI-S-56 SomaBrain and UI-S-57 Agent admin (tools & permissions). |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | SOMA-01-UIUX-001 | Screen and feature specification (the master) |
| N-2 | SOMA-01-UIUX-002 | Modal and overlay specification |
| N-3 | SOMA-01-DOCS-001 §3.3.4 | Annexed design artefacts |
| N-4 | SOMA-UI-IDREG-001 | Authoritative identifier allocation |
| N-5 | SOMA-A0-PARITY-001 | Feature clone never code clone; honesty rules |

---

## 1. Purpose and Scope

This document is the **controlled index** for the ASCII wireframe mockups of the
somaAgent01 interface. Each mockup is an **annex** under `docs/design/mockups/` in the
sense of `SOMA-01-DOCS-001` §3.3.4: named by sub-identifier, inventoried here and in
`docs/iso/DOCUMENT-REGISTER.md`, but carrying no Document Control table of its own.

Mockups are **wireframes of our design**, not copies of Agent Zero screenshots.
Feature-clone-never-code-clone applies to design artefacts.

## 2. How to read a mockup

Every annex contains, in order:

1. a header line naming the screen or surface and its route;
2. an ASCII wireframe at desktop width, inside the global chrome;
3. a control map whose numbered callouts resolve to `UI-C-*` in `SOMA-01-UIUX-001`;
4. state variants — loading, empty, error, permission-denied, offline — with verbatim copy;
5. modal overlays, naming `UI-M-01` Drawer / `UI-M-02` Full-screen / `UI-M-03` Dialog.

A disabled control always shows its blocking reason. Placeholder values appear as
`<store.field>` or `‹ live value ›` rather than fabricated data. Secrets appear as a
masked placeholder with a "rotate in Vault" note, never a value.

## 3. Global chrome — UI-S-00

| ID | Title | Facet | Annex |
|---|---|---|---|
| UI-S-00 | Global chrome | — | `UI-S-00-chrome.md` |

## 4. Routable screens — UI-S-01 … UI-S-57

| ID | Title | Facet | Annex |
|---|---|---|---|
| UI-S-01 | Soul — persona & system prompt | Soul | `UI-S-01-soul.md` |
| UI-S-02 | Brain — model & IQ | Brain | `UI-S-02-brain.md` |
| UI-S-03 | Hands — tools & capabilities | Hands | `UI-S-03-hands.md` |
| UI-S-04 | Memory — retention & recall | Memory | `UI-S-04-memory.md` |
| UI-S-05 | Body — resources & limits | Body | `UI-S-05-body.md` |
| UI-S-06 | Governance — constitution & hooks | Governance | `UI-S-06-governance.md` |
| UI-S-07 | Chat workspace | Chat | `UI-S-07-chat-workspace.md` |
| UI-S-08 | Message detail | Chat | `UI-S-08-message-detail.md` |
| UI-S-09 | Conversation export | Chat | `UI-S-09-conversation-export.md` |
| UI-S-10 | Conversation queue | Chat | `UI-S-10-conversation-queue.md` |
| UI-S-11 | Capsule list | Capsule | `UI-S-11-capsule-list.md` |
| UI-S-12 | Capsule editor | Capsule | `UI-S-12-capsule-editor.md` |
| UI-S-13 | Version rail & diff | Capsule | `UI-S-13-version-rail-diff.md` |
| UI-S-14 | Instances | Capsule | `UI-S-14-instances.md` |
| UI-S-15 | Module list | Module | `UI-S-15-module-list.md` |
| UI-S-16 | Module detail & config | Module | `UI-S-16-module-detail.md` |
| UI-S-17 | Capability registry | Module | `UI-S-17-capability-registry.md` |
| UI-S-18 | Capability detail & hook bindings | Module | `UI-S-18-capability-detail.md` |
| UI-S-19 | Tenants | Platform | `UI-S-19-tenants.md` |
| UI-S-20 | Tenant wizard | Platform | `UI-S-20-tenant-wizard.md` |
| UI-S-21 | Tenant dashboard | Platform | `UI-S-21-tenant-dashboard.md` |
| UI-S-22 | Users | Platform | `UI-S-22-users.md` |
| UI-S-23 | Roles & role matrix | Platform | `UI-S-23-roles.md` |
| UI-S-24 | Permissions | Platform | `UI-S-24-permissions.md` |
| UI-S-25 | Billing | Platform | `UI-S-25-billing.md` |
| UI-S-26 | Subscriptions | Platform | `UI-S-26-subscriptions.md` |
| UI-S-27 | Usage analytics | Platform | `UI-S-27-usage-analytics.md` |
| UI-S-28 | Tier builder | Platform | `UI-S-28-tier-builder.md` |
| UI-S-29 | Login | Auth | `UI-S-29-login.md` |
| UI-S-30 | Register | Auth | `UI-S-30-register.md` |
| UI-S-31 | Forgot password | Auth | `UI-S-31-forgot-password.md` |
| UI-S-32 | MFA setup | Auth | `UI-S-32-mfa-setup.md` |
| UI-S-33 | Auth callback | Auth | `UI-S-33-auth-callback.md` |
| UI-S-34 | Personal profile | Auth | `UI-S-34-personal-profile.md` |
| UI-S-35 | Platform profile | Auth | `UI-S-35-platform-profile.md` |
| UI-S-36 | Mode selection | Auth | `UI-S-36-mode-selection.md` |
| UI-S-37 | Platform dashboard | Ops | `UI-S-37-platform-dashboard.md` |
| UI-S-38 | Platform metrics | Ops | `UI-S-38-platform-metrics.md` |
| UI-S-39 | Infrastructure dashboard | Ops | `UI-S-39-infrastructure-dashboard.md` |
| UI-S-40 | Rate limits | Ops | `UI-S-40-rate-limits.md` |
| UI-S-41 | Integrations dashboard | Ops | `UI-S-41-integrations-dashboard.md` |
| UI-S-42 | Marketplace | Ops | `UI-S-42-marketplace.md` |
| UI-S-43 | Audit dashboard | Ops | `UI-S-43-audit-dashboard.md` |
| UI-S-44 | Audit log | Ops | `UI-S-44-audit-log.md` |
| UI-S-45 | Agent metrics | Ops | `UI-S-45-agent-metrics.md` |
| UI-S-46 | Voice chat | Voice | `UI-S-46-voice-chat.md` |
| UI-S-47 | Voice sessions | Voice | `UI-S-47-voice-sessions.md` |
| UI-S-48 | Voice personas | Voice | `UI-S-48-voice-personas.md` |
| UI-S-49 | Multimodal settings | Voice | `UI-S-49-multimodal-settings.md` |
| UI-S-50 | Settings — Agent | Settings | `UI-S-50-settings-agent.md` |
| UI-S-51 | Settings — Models | Settings | `UI-S-51-settings-models.md` |
| UI-S-52 | Settings — Channels | Settings | `UI-S-52-settings-channels.md` |
| UI-S-53 | Settings — External & Developer | Settings | `UI-S-53-settings-external-dev.md` |
| UI-S-54 | Settings — Interface | Settings | `UI-S-54-settings-interface.md` |
| UI-S-55 | Settings — Tools | Settings | `UI-S-55-settings-tools.md` |
| UI-S-56 | Settings — SomaBrain | Settings | `UI-S-56-settings-somabrain.md` |
| UI-S-57 | Settings — Agent admin (tools & permissions) | Settings / Hands | `UI-S-57-settings-agent-admin.md` |

## 5. Surfaces — UI-X-01 … UI-X-08

| ID | Title | State | Annex |
|---|---|---|---|
| UI-X-01 | Files | Specified | `UI-X-01-files.md` |
| UI-X-02 | Tools | Specified | `UI-X-02-tools.md` |
| UI-X-03 | Browser | Specified | `UI-X-03-browser.md` |
| UI-X-04 | Editor | Specified | `UI-X-04-editor.md` |
| UI-X-05 | Debug | Specified | `UI-X-05-debug.md` |
| UI-X-06 | Capsule | Specified | `UI-X-06-capsule.md` |
| UI-X-07 | Brain | Specified | `UI-X-07-brain.md` |
| UI-X-08 | Desktop | GATED | `UI-X-08-desktop.md` |

`UI-X-08` (desktop) is specified complete and rendered **present but disabled** with the
blocking reason printed inline: *"Requires a remote-desktop capability in somaAgent01.
Not available today."* It is never a "coming soon" placeholder.

## 6. Inventory summary

| Metric | Count |
|---|---|
| Screen annexes (UI-S) | 58 |
| Surface annexes (UI-X) | 8 |
| **Total annexes** | **66** |

## 7. Traceability

Each annex callout resolves to a `UI-C-*` control in `SOMA-01-UIUX-001` §5, which in turn
traces `REQ-UIX-* → UI-F-* → UI-S-* → UI-C-*/UI-A-* → component → API → UIX-AT-*` in
`SOMA-01-UIUX-004`. A callout with no matching `UI-C-*` is a gap and is listed as such.

## 8. Tracked findings

| ID | Finding | Evidence | Owner |
|---|---|---|---|
| M-01 | `UI-C-*` identifiers are **not unique across annexes**. Batch 1 allocated `UI-C-029`…`UI-C-120` as per-screen callout instances; batch 2 independently allocated `UI-C-061`…`UI-C-119` as a global primitive taxonomy. 53 numeric IDs therefore carry two meanings depending on which annex is read. | `docs/design/mockups/UI-S-00-chrome.md` and its siblings (per-screen callouts) vs `docs/design/mockups/UI-X-*.md` (primitive taxonomy) | UI/UX suite owner — issue a single `UI-C-*` allocation table in `SOMA-UI-IDREG-001` and renumber the losing batch |
| M-01 is a **known defect, not a silent fix.** Renumbering 53 identifiers across 50+ annexes mid-issue would invalidate every callout already drawn, so the collision is recorded here and the annexes are issued as-is. Until it is resolved, a `UI-C-*` number is only meaningful **in the context of the annex that prints it**; `SOMA-01-UIUX-004` treats cross-annex `UI-C-*` equality as unreliable. | | |

End of Document
