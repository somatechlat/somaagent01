# Design: Docker Deployment, Test Workbench, VIBE Compliance, and File Refactoring

## Context

The `feature/no-mocks-agent-ui-sync` branch has completed the UI sync work (T1–T15 + remaining mock cleanup). There are 49 modified files and 1 new file in the worktree. The user now wants to:

1. Deploy the stack into Docker.
2. Start checking the testing workbench.
3. Ensure all code is tested.
4. Make the codebase VIBE coding compliant.
5. Enforce a 650-line limit per file.
6. Split oversized files into design-pattern-based modules.

## Scope and Priority

Because these are large, partly independent initiatives, we will proceed in phases:

| Phase | Goal | Why first |
|-------|------|-----------|
| 1 | Docker deployment | Gives a reproducible runtime to validate everything else. |
| 2 | Test workbench | Runs existing tests and identifies gaps before refactoring. |
| 3 | VIBE compliance audit + targeted fixes | Fixes the highest-impact violations (mock functions, raw SQL, stubs). |
| 4 | File-size enforcement + design-pattern splitting | Refactors files >650 lines using well-justified splits. |

Phases 1 and 2 are prerequisites for phases 3 and 4.

## Phase 1 — Docker Deployment

### Target
Build and start the standalone Docker Compose stack defined in `infra/standalone/docker-compose.yml` plus the WebUI container.

### Approach
1. Ensure `.env` exists with required variables (`POSTGRES_PASSWORD`, `VAULT_DEV_ROOT_TOKEN_ID`, `SECRET_KEY`, etc.).
2. Build the WebUI image from `webui/Dockerfile`.
3. Run `docker compose -f infra/standalone/docker-compose.yml up -d`.
4. Verify health checks pass for Postgres, Redis, Vault, and the API container.
5. Verify the WebUI is reachable and the API responds to `/api/v2/health` (or equivalent).

### Constraints
- Do not modify the existing Dockerfiles unless a real bug is found.
- Do not commit secrets.
- If build fails, fix only the minimal blocking issue.

## Phase 2 — Test Workbench

### Target
Execute the existing test suite according to `docs/requirements/SOMA-SRS-TESTBENCH-001.md` and `docs/requirements/SOMA-SRS-TESTMODULES-001.md`.

### Approach
1. Run unit tests: `pytest tests/unit/ -v`
2. Run Django tests: `pytest tests/django/ -v`
3. Run SaaS tests: `pytest tests/saas/ -v`
4. If `SA01_INFRA_AVAILABLE=1` and Docker stack is healthy, run integration tests: `pytest tests/integration/ -v`
5. Record results: which pass, which fail, and why.

### Constraints
- Do not invent new test infrastructure unless the existing one is broken.
- Mark tests that require unavailable infrastructure as skipped with a clear reason.

## Phase 3 — VIBE Compliance Audit

### Target
Address the violations documented in `docs/archive/SOMA-OLD-VIOLATIONS-001.md`, focusing on the frontend and services/common/ layers.

### Approach
1. Re-run a focused audit on:
   - `webui/src/` — no mock data, no `localStorage` token auth, real API usage.
   - `services/common/` — no stubs, no fake returns, no raw asyncpg/f-string SQL.
2. Fix confirmed violations with minimal, targeted changes.
3. Re-verify after each fix group.

### Constraints
- Follow VIBE Rule 3: do not split files unless justified.
- File splitting is justified in Phase 4 because the user explicitly requested the 650-line limit.

## Phase 4 — File-Size Enforcement and Design Patterns

### Target
No file in `webui/src/` or `services/` exceeds 650 lines. Oversized files are split using justified design patterns.

### Approach
1. Generate a list of files >650 lines.
2. For each file, choose a splitting strategy:
   - **Component decomposition** for large Lit views (extract sub-components).
   - **Service decomposition** for large service files (extract helpers/repositories).
   - **Hook/mixin pattern** for reusable UI logic.
3. Refactor one file at a time, preserving behavior and types.
4. Run build and relevant tests after each file.

### Constraints
- Only split files >650 lines.
- Each new file must have a single, clear responsibility.
- Preserve all existing tests and behavior.

## Success Criteria

- [ ] `docker compose -f infra/standalone/docker-compose.yml up -d` starts all services successfully.
- [ ] WebUI container builds and serves on the expected port.
- [ ] Unit and Django tests pass.
- [ ] No `getMock*`, `mockData`, `demoData`, or `MOCK_DATA` remains in `webui/src/`.
- [ ] No file in `webui/src/` exceeds 650 lines.
- [ ] `npm run type-check` and `npm run build` pass after all changes.

## Out of Scope

- Production deployment outside the standalone Docker stack.
- Rewriting the entire backend test suite from scratch.
- Cross-repository E2E tests requiring SomaBrain/SomaFractalMemory.
- Performance/load testing.
