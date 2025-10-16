---
title: Accessibility Statement
slug: user-accessibility
version: 1.0.0
last-reviewed: 2025-10-15
audience: compliance, product
owner: product-education
reviewers:
  - design
  - accessibility
prerequisites:
  - Knowledge of WCAG 2.1 guidelines
verification:
  - Accessibility audit passes quarterly review
---

# Accessibility Statement

SomaAgent01 commits to inclusive, accessible experiences. This statement outlines the standards we meet today, the gaps we are closing, and how to report accessibility issues.

## Compliance Baseline

- **Conformance target:** WCAG 2.1 Level AA.
- **Screen reader support:** Tested with NVDA (Windows) and VoiceOver (macOS).
- **Keyboard navigation:** All critical interactions (chat input, action buttons, settings) reachable with `Tab`/`Shift+Tab`.
- **Color contrast:** UI palette audited against AA thresholds (contrast ratio ≥ 4.5:1 for body text).

## Tested Components

| Component | Assistive Tech | Result |
| --------- | -------------- | ------ |
| Chat transcript | NVDA 2025.2 | Announces agent and user speaker labels |
| Action buttons | VoiceOver (macOS 15) | All buttons focusable and labeled |
| Settings forms | NVDA | Form fields expose labels and validation hints |
| Notification toasts | VoiceOver | Aria-live regions announce status updates |

## Known Limitations

- Diagram modals are partially accessible; keyboard trap mitigations ship in Sprint 45.
- Audio player controls rely on browser defaults. Enhanced ARIA labels are in progress.

## Reporting Issues

Email `accessibility@somaagent01.dev` or open a GitHub issue with the `accessibility` label. Include browser, assistive tech, and reproduction steps.

## Continuous Improvement

- Quarterly audits logged in [`docs/changelog.md`](../changelog.md).
- Automated tests run `axe-core` via the docs CI workflow.
- Accessibility scorecards tracked in the Documentation Audit Checklist.
