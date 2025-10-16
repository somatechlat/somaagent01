---
title: Contribution Workflow
slug: dev-contribution
version: 1.0.0
last-reviewed: 2025-10-15
audience: contributors, maintainers
owner: developer-experience
reviewers:
  - platform-engineering
  - qa
prerequisites:
  - Environment prepared per [Environment Setup](./environment.md)
verification:
  - CI green on pull request
  - Documentation checklists completed
---

# Contribution Workflow

This workflow defines how to propose, implement, and merge changes into SomaAgent01. It supplements the repository `CONTRIBUTING` guidelines with enforceable steps and automation gates.

## 1. Branching Model

- Default branch: `main`.
- Integration branch: `soma_integration`.
- Feature branches: `feature/<issue-id>-<short-description>`.
- Bugfix branches: `bugfix/<issue-id>-<short-description>`.

## 2. Preparing a Change

1. Open or reference an issue in GitHub.
2. Create a feature branch from `soma_integration`.
3. Implement changes with frequent commits. Use conventional message prefixes (`feat:`, `fix:`, `docs:`, `chore:`).
4. Update or add tests alongside code.
5. Update documentation using the manual structure (User, Technical, Development, Onboarding) and run the documentation checklist (see [`docs/documentation-audit-checklist.md`](../documentation-audit-checklist.md)).

## 3. Local Verification

```bash
make fmt-check
make lint
pytest
npm test --prefix webui
make docs-verify
```

> [!TIP]
> `make docs-verify` runs markdown linting, link checking, and MkDocs build. Configure details in `Makefile` under the `docs` namespace.

## 4. Pull Request Requirements

- Target branch: `soma_integration`.
- Labels: add `docs-only` if code unchanged, otherwise use component labels (`backend`, `frontend`, `infra`).
- Reviewers: assign at least one maintainer from each impacted area (backend, frontend, infra, docs).
- Checklist:
  - [ ] Tests added/updated.
  - [ ] Documentation updated.
  - [ ] Change logged in [`docs/changelog.md`](../changelog.md).
  - [ ] CI green (includes docs workflow).

## 5. Review Process

- Automated checks (lint, tests, docs) must pass before human review.
- Reviewers focus on correctness, security, performance, and documentation coverage.
- Address feedback via follow-up commits (avoid force-push unless squashing at the end).

## 6. Merge Strategy

- Use **Squash & Merge** for feature work.
- Use **Rebase & Merge** for large refactors coordinated with release managers.
- Post-merge: delete branch, ensure issue is closed or moved to `Done`.

## 7. Release Notes

- Every merged PR updates [`docs/changelog.md`](../changelog.md) with a short description and links to affected manuals.
- Major features annotate the Onboarding Manual if user workflows change.

## 8. Compliance

- CLA enforcement automated via GitHub Action.
- Security-sensitive changes require approval from security engineering.
- Follow SOC2 control mapping documented in the [Security Manual](../technical-manual/security.md).
