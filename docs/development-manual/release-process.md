---
title: Release Process
slug: dev-release-process
version: 1.0.0
last-reviewed: 2025-10-15
audience: release-managers, maintainers
owner: release-engineering
reviewers:
  - platform-engineering
  - product
prerequisites:
  - CI green on candidate branch
verification:
  - Release checklist completed
  - Artifacts published and tagged
---

# Release Process

This process governs how SomaAgent01 versions are cut, validated, and published. Follow it for minor and patch releases; major releases require additional product approval.

## 1. Release Cadence

- Bi-weekly minor releases (odd weeks).
- Patch releases as needed for hot fixes.

## 2. Preparation

1. Ensure `soma_integration` is up to date with `main`.
2. Create a release branch: `release/v<major>.<minor>.0`.
3. Audit open issues and PRs; defer unfinished work.
4. Update [`docs/changelog.md`](../changelog.md) with highlights and links to manual updates.

## 3. Verification

Run the full validation suite:

```bash
make fmt-check
make lint
pytest
pytest tests/playwright --headed
make docs-verify
make helm-verify
```

- `make helm-verify` packages Helm charts and validates values files.
- Capture evidence (screenshots, logs) and attach to release ticket.

## 4. Release Review

- Hold release readiness review with platform, QA, docs, and product.
- Confirm documentation updates across all manuals.
- Sign off recorded in release ticket.

## 5. Tagging & Packaging

1. Bump version identifiers in `pyproject.toml`, `package.json`, and Helm charts.
2. Commit with `chore(release): v<major>.<minor>.0`.
3. Tag: `git tag v<major>.<minor>.0` and push tags.
4. Publish artifacts:
   - Python package (if applicable) via Poetry.
   - Docker images to registry (`agent0ai/agent-zero:<version>`).
   - Helm charts packaged and uploaded to artifact store.

## 6. Deployment

- Promote to staging via Argo CD or Helm release.
- Run smoke tests (`scripts/smoke_test.py --env staging`).
- Promote to production after sign-off; monitor dashboards for 24 hours.

## 7. Post-Release

- Close release ticket and associated issues.
- Update Onboarding and User manuals if workflows changed.
- Archive runbooks, logs, and metrics snapshots in release folder (`docs/releases/<version>/`).

## 8. Hotfix Process

- Branch from the latest tag (`git checkout -b hotfix/v<major>.<minor>.<patch>`).
- Apply fix, add tests, update changelog.
- Tag as `v<major>.<minor>.<patch>`.
- Notify stakeholders immediately after deployment.

## 9. Checklist

- [ ] CI & docs workflows green.
- [ ] Changelog updated.
- [ ] Manuals reviewed and signed off.
- [ ] Artifacts published.
- [ ] Deployment validated in staging and production.
- [ ] Post-release metrics captured.
