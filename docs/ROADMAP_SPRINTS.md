# Sprint‑Based Roadmap for Local‑Only SomaAgent01 Stack

**Purpose** – Collapse the Docker‑Compose stack to the minimal set of containers needed for a fully‑functional local development environment while keeping all required features (metrics, UI, delegation, OpenFGA, etc.).  The voice‑processing component (`whisper`) will be removed and replaced by a simple HTTP call to an external speech‑to‑text API (the API endpoint will be injected via an environment variable).  Prometheus stays because it is the canonical metrics collector.

---

## 📅 High‑Level Timeline
| Sprint | Duration | Goal | Deliverable |
|-------|----------|------|------------|
| **Sprint 1** | 1 week | **Prune & Refactor Compose** – remove Whisper, merge services, delete one‑off init containers, add API hook for voice. | Updated `docker-compose.somaagent01.yaml` (13 → 9 containers) + environment variable `VOICE_API_URL`.
| **Sprint 2** | 1 week | **Add Monitoring & Health‑Checks** – ensure Prometheus scrapes all services, add Grafana dashboard (optional). | Prometheus config updated, health‑endpoints verified.
| **Sprint 3** | 1 week | **Test End‑to‑End Flow** – UI → Delegation → Worker → SLM → Memory, with voice API stub. | Automated smoke‑test script, updated runbook.
| **Sprint 4** | 0.5 week | **Documentation & CI** – lock‑down the new stack, add CI job that builds the reduced compose file and runs the smoke test. | Updated docs (`RUNBOOK.md`, `LOCAL_ENV.md`), GitHub Actions workflow.
| **Sprint 5** (optional) | 0.5 week | **Future‑Proofing** – add optional profiles for optional services (e.g., OpenFGA, OPA) and a “full‑stack” profile for integration testing. | Profile‑aware compose file, README examples.

---

## 🏁 Sprint 1 – Prune & Refactor Compose
1. **Remove Whisper**
   - Delete the `whisper` service block.
   - Add a new environment variable `VOICE_API_URL` to the `delegation` (or `agent‑ui`) service so the UI can POST audio blobs to the external API.
2. **Merge Delegation Gateway & Worker**
   - Create a single `delegation` service using `supervisord` (or a tiny shell script) that launches both `uvicorn` and the worker.
   - Share the same `mem_limit`/`cpus` limits.
3. **Merge OpenFGA & Migration**
   - Replace `openfga` + `openfga‑migrate` with a single container that runs the migration on start‑up (see `entrypoint-openfga.sh`).
4. **Absorb Kafka‑init**
   - Move the topic‑creation logic into the `kafka` container’s start command.
   - Delete the `kafka‑init` service.
5. **Update `docker-compose.somaagent01.yaml`**
   - Resulting container count: **9** (kafka, redis, postgres, qdrant, clickhouse, prometheus, vault, opa, delegation, openfga, agent‑ui).  *Prometheus is kept.*
6. **Add a stub for the voice API**
   ```yaml
   environment:
     - VOICE_API_URL=${VOICE_API_URL:-https://example.com/voice}
   ```
   The UI will call this URL; during local dev you can point it at a mock server.

---

## 📈 Sprint 2 – Monitoring & Health‑Checks
- Verify every service exposes a `/health` endpoint (most already do).
- Extend Prometheus `prometheus.yml` to scrape:
  - `delegation` (port 8015)
  - `agent‑ui` (port 7001)
  - `openfga` (port 8080)
  - `opa` (port 8181)
- Add a Grafana dashboard (optional) that visualises:
  - Request latency
  - Worker event count
  - Kafka consumer lag (via JMX exporter if needed)
- Run `docker compose up -d` and confirm the Prometheus UI shows all targets `UP`.

---

## 🧪 Sprint 3 – End‑to‑End Validation
1. **Write a smoke‑test script** (`scripts/smoke_test.py`) that:
   - Sends a text message via the UI API.
   - Sends an audio payload to `${VOICE_API_URL}` (use a local mock that returns plain text).
   - Verifies a response appears in the UI logs and in the `delegation` logs.
2. **Run the script locally** after `docker compose up`.
3. **Update the Runbook** with the new steps (topic creation is automatic, voice API call is described).

---

## 🤖 Sprint 4 – Documentation & CI
- **Docs**
  - Add a *“Reduced‑Container Local Development”* section to `docs/LOCAL_ENV.md`.
  - Update the incident‑response table in `docs/SomaAgent01_Runbook.md` to reflect the merged services.
- **CI**
  - GitHub Actions workflow `ci.yml` that:
    1. Builds the Docker images.
    2. Spins up the reduced compose stack.
    3. Executes `scripts/smoke_test.py`.
    4. Publishes Prometheus metrics as an artifact (optional).

---

## ⚙️ Sprint 5 – Optional Profiles (Future‑Proof)
- Add Docker‑Compose profiles for:
  - `full` – all original services (including Whisper) for integration testing.
  - `metrics` – only services needed for Prometheus.
  - `api‑only` – UI + delegation (no DB) for quick UI prototyping.
- Document usage examples in the README.

---

## 📂 Where the Roadmap Lives
The roadmap is stored at **`docs/ROADMAP_SPRINTS.md`** (this file).  It is the canonical reference for the team to plan, track, and review sprint progress.

---

### Next Immediate Action
- Checkout the `V0.1.1` branch.
- Apply the Sprint 1 changes to `docker-compose.somaagent01.yaml` (remove Whisper, merge services, add `VOICE_API_URL`).
- Commit and push the updated compose file and this roadmap.

Feel free to let me know when you are ready to start Sprint 1 or if you need any of the merge scripts (supervisor config, entrypoint‑openfga.sh) generated now.
