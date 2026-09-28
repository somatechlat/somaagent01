# Docker, Tests, VIBE, and Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the SomaAgent01 standalone stack in Docker, run the existing test workbench, fix VIBE violations, and split files >650 lines using design patterns.

**Architecture:** Use the existing `infra/standalone/docker-compose.yml` and `webui/Dockerfile` with minimal fixes. Run tests incrementally. Address VIBE violations and file-size limits only after the runtime and test baseline are confirmed.

**Tech Stack:** Docker Compose, Python 3.12, pytest, Django, Lit 3, Vite, nginx.

---

## Phase 1: Docker Deployment

### Task 1.1: Verify environment and required secrets

**Files:**
- Read: `infra/standalone/docker-compose.yml`
- Read: `infra/standalone/.env.example` (if exists) or infer from compose

- [ ] **Step 1: Check if `.env` exists**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/.worktrees/no-mocks-agent-ui-sync/infra/standalone
ls -la .env
```

- [ ] **Step 2: Create `.env` if missing**

If `.env` does not exist, create it with safe local values:
```bash
cat > .env << 'EOF'
POSTGRES_PASSWORD=localdev123
VAULT_DEV_ROOT_TOKEN_ID=***REMOVED***
SECRET_KEY=***REMOVED***
EOF
```

- [ ] **Step 3: Verify Docker is running**

Run:
```bash
docker info
```
Expected: Docker daemon is reachable.

### Task 1.2: Build and start the standalone stack

**Files:**
- Modify if needed: `infra/standalone/docker-compose.yml`

- [ ] **Step 1: Build and start services**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/.worktrees/no-mocks-agent-ui-sync/infra/standalone
docker compose up -d --build
```

- [ ] **Step 2: Wait for health checks**

Run:
```bash
docker compose ps
```
Expected: All services show `healthy` or `running` after ~60 seconds.

- [ ] **Step 3: Test API health**

Run:
```bash
curl -s http://localhost:20020/health || curl -s http://localhost:20020/api/v2/health
```
Expected: HTTP 200 with a JSON health response.

### Task 1.3: Build and run the WebUI container

**Files:**
- Read: `webui/Dockerfile`
- Read: `webui/nginx.conf`

- [ ] **Step 1: Build WebUI image**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/.worktrees/no-mocks-agent-ui-sync/webui
docker build -t somaagent-webui .
```

- [ ] **Step 2: Run WebUI container**

Run:
```bash
docker run -d -p 2080:80 --name somaagent_webui somaagent-webui
```

- [ ] **Step 3: Verify WebUI is reachable**

Run:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:2080/
```
Expected: `200`

---

## Phase 2: Test Workbench Execution

### Task 2.1: Prepare Python test environment

**Files:**
- Read: `pyproject.toml`
- Read: `tests/conftest.py`

- [ ] **Step 1: Activate virtual environment**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/.worktrees/no-mocks-agent-ui-sync
source .venv/bin/activate
```

- [ ] **Step 2: Verify pytest is installed**

Run:
```bash
pytest --version
```
Expected: pytest 8.x installed.

### Task 2.2: Run unit tests

**Files:**
- Run: `tests/unit/`

- [ ] **Step 1: Run unit tests**

Run:
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/.worktrees/no-mocks-agent-ui-sync
pytest tests/unit/ -v
```

- [ ] **Step 2: Record results**

Note pass/fail counts and any import errors.

### Task 2.3: Run Django tests

**Files:**
- Run: `tests/django/`

- [ ] **Step 1: Run Django tests**

Run:
```bash
pytest tests/django/ -v
```

- [ ] **Step 2: Record results**

### Task 2.4: Run SaaS tests

**Files:**
- Run: `tests/saas/`

- [ ] **Step 1: Run SaaS tests**

Run:
```bash
pytest tests/saas/ -v
```

- [ ] **Step 2: Record results**

### Task 2.5: Run integration tests if infra is available

**Files:**
- Run: `tests/integration/`

- [ ] **Step 1: Run integration tests with infra flag**

Run:
```bash
SA01_INFRA_AVAILABLE=1 pytest tests/integration/ -v
```

- [ ] **Step 2: Record results**

If services are not reachable, mark tests as skipped and document why.

### Task 2.6: Run frontend build check

**Files:**
- Run: `webui/`

- [ ] **Step 1: Run type-check and build**

Run:
```bash
cd webui
npm run type-check
npm run build
```

- [ ] **Step 2: Record results**

---

## Phase 3: VIBE Compliance Audit

### Task 3.1: Audit frontend VIBE violations

**Files:**
- Search: `webui/src/`

- [ ] **Step 1: Search for remaining mock/demo patterns**

Run:
```bash
cd webui
grep -R -n 'getMock\|mockData\|demoData\|MOCK_DATA\|fakeData\|stubData' src/
```

- [ ] **Step 2: Search for localStorage token usage**

Run:
```bash
grep -R -n 'localStorage.*token\|localStorage\.getItem.*token\|localStorage\.setItem.*token' src/
```

- [ ] **Step 3: Fix any violations found**

Replace mock fallbacks with empty-state or error handling. Replace localStorage token usage with cookie auth via `apiClient`.

### Task 3.2: Audit backend VIBE violations

**Files:**
- Search: `services/common/`, `admin/`, `aaas/`

- [ ] **Step 1: Search for raw asyncpg/f-string SQL**

Run:
```bash
grep -R -n 'asyncpg\|execute(f"\|execute(f\x27' services/common/ admin/ aaas/ || true
```

- [ ] **Step 2: Search for stub/fake functions**

Run:
```bash
grep -R -n 'raise NotImplementedError\|return None  # TODO\|pass  # TODO\|# FIXME\|fake' services/common/ admin/ aaas/ || true
```

- [ ] **Step 3: Fix critical violations**

Focus on functions labeled "VIBE COMPLIANT" that return fake data or are stubs.

---

## Phase 4: File-Size Enforcement and Design Patterns

### Task 4.1: Identify oversized files

**Files:**
- Search: `webui/src/`

- [ ] **Step 1: Generate list of files >650 lines**

Run:
```bash
cd webui
find src -name '*.ts' -exec wc -l {} + | awk '$1 > 650 {print $0}' | sort -n
```

### Task 4.2: Refactor one oversized file at a time

**Files:**
- Varies per file

- [ ] **Step 1: Choose splitting pattern**

For each oversized file, choose one of:
- Extract sub-components (for large Lit views).
- Extract helper modules (for large service files).
- Extract hooks/mixins (for reusable logic).

- [ ] **Step 2: Refactor and verify**

After each file refactor, run:
```bash
cd webui
npm run type-check
npm run build
```

- [ ] **Step 3: Repeat until no file >650 lines**

### Task 4.3: Final verification

**Files:**
- All modified files

- [ ] **Step 1: Confirm no files exceed 650 lines**

Run:
```bash
cd webui
find src -name '*.ts' -exec wc -l {} + | awk '$1 > 650 {print $0}'
```
Expected: No output.

- [ ] **Step 2: Run full frontend verification**

Run:
```bash
cd webui
npm run type-check
npm run build
```

- [ ] **Step 3: Run Python tests**

Run:
```bash
pytest tests/unit/ tests/django/ tests/saas/ -v
```

---

## Spec Coverage Check

| Spec Requirement | Plan Task |
|---|---|
| Docker deployment | Phase 1 |
| Test workbench | Phase 2 |
| All code tested | Phase 2 + Phase 4 verification |
| VIBE compliance | Phase 3 |
| No files >650 lines | Phase 4 |
| Design pattern splitting | Phase 4 |

## Placeholder Scan

- No TBD/TODO placeholders in implementation steps.
- Each step includes exact commands or code patterns.
- Exact file paths are provided where known.
