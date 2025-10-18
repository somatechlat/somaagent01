# SomaAgent01 Documentation Hub

Welcome to the reorganized documentation hub. Content now lives in four curated manuals with shared resources for terminology, style, and change tracking.

## Manuals

- **[User Manual](user-manual/index.md):** Install SomaAgent01, run daily workflows, and troubleshoot issues.
- **[Technical Manual](technical-manual/index.md):** Dive into architecture, infrastructure, integrations, and data flow.
- **[Development Manual](development-manual/index.md):** Follow engineering workflows, coding standards, testing, and release processes.
- **[Onboarding Manual](onboarding-manual/index.md):** Enable new team members with orientation checklists, tool primers, and 30/60/90 planning.

## Shared Resources

- **[Documentation Style Guide](style-guide.md)** to keep writing consistent.
- **[Documentation Audit Checklist](documentation-audit-checklist.md)** enforced on every docs PR.
- **[Glossary](glossary.md)** with canonical terminology.
- **[Documentation Change Log](changelog.md)** recording updates across manuals.

## Automation & Governance

- Run `make docs-verify` locally to execute markdown lint, link checks, diagram rendering, and MkDocs build.
- Docs GitHub Action (`.github/workflows/docs-quality.yml`) enforces the same checks in CI.
- Quarterly audits follow the checklist to ensure accuracy, accessibility, and ownership.

> [!TIP]
> Legacy documents are being migrated into the new manuals. Check `_legacy/` or the change log for interim locations while the transition completes.
