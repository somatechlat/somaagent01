# Messaging Architecture Documentation

This directory houses living documentation for the messaging architecture overhaul tracked on the `messaging_architecture` branch.

## Contents

- `baseline.md` – Captures the current state of the docker-compose stack, environment contracts, and smoke checks (Wave 0 deliverable).
- `release.md` – Final runbook covering deployment, rollback, and validation steps (targeted for Sprint 4).
- Additional sub-documents for tooling, observability, and troubleshooting as they are produced.

## Maintenance Notes

- Keep documents versioned alongside the roadmap milestones (Wave/Sprint references).
- Update tables of contents and cross-links whenever new documents are added.
- Reference acceptance criteria from `ROADMAP_CANONICAL.md` and `ROADMAP_SPRINTS.md` when drafting new guides.
- Keep automation aligned with documentation (e.g., `scripts/check_stack.py` referenced in `baseline.md`).
