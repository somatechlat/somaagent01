---
title: Documentation Audit Checklist
slug: documentation-audit-checklist
version: 1.0.0
last-reviewed: 2025-10-15
audience: documentation authors, reviewers
owner: docs-lead
reviewers:
  - developer-experience
verification:
  - Checklist completed on every docs PR
---

# Documentation Audit Checklist

Complete this checklist for every documentation change. Attach the filled checklist to PR descriptions.

1. **Purpose stated:** Page explains why it exists and what problem it solves.
2. **Audience defined:** Target readers identified in front matter.
3. **Prerequisites listed:** Requirements documented before steps begin.
4. **Step-by-step instructions:** Procedures are ordered, actionable, and numbered where appropriate.
5. **Verification criteria:** Explicit checks confirm success at the end of each procedure.
6. **Common errors:** Troubleshooting tips or references provided for known failure modes.
7. **References & links:** Related documents linked using relative paths; links validated.
8. **Version & metadata:** `version`, `last-reviewed`, `owner`, `reviewers` updated in front matter.
9. **Accessibility:** Tables, images, and diagrams include alt text or captions; tone inclusive.
10. **Automation hooks:** `make docs-verify` (markdownlint, link checker, MkDocs) executed locally; CI workflow passes.
11. **Diagrams rendered:** Mermaid or diagram sources committed; render step succeeds.
12. **Change logged:** Entry added to [`docs/changelog.md`](./changelog.md) with summary and PR link.
