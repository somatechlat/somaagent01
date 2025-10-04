⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaKamachiq Agent Redesign Blueprint

## 1. Purpose
This document captures the canonical plan for transforming Agent Zero into the SomaKamachiq (SKM) agent platform. It summarizes the target architecture, persona strategy, integration points with SomaBrain, and the sprint roadmap required to deliver an OSS-first, policy-governed, voice-capable, enterprise-ready agent.

## 2. Target Architecture Overview
- **Gateway/API**: FastAPI service (behind Kong/Envoy) validates JWT, tenant, constitution hash, and OPA policy; enqueues user text/audio to Kafka and streams responses over WebSocket/SSE.
- **Conversation Worker**: Kafka consumer that rehydrates session state from Redis/Postgres, runs OSS SLM pre-processing (intent, slot filling, safety heuristics), calls primary LLM via model profiles, emits agent responses, tool requests, and audit events.
- **Tool Executor**: Stateless worker executing `python/tools` adapters inside sandbox containers or delegating to the SKM Tool Service; all calls gated by policy client; produces `tool.results` events.
- **Policy Client**: Shared wrapper around OPA/OpenFGA (`/v1/evaluate`). Every memory write, tool invocation, or provisioning step receives a verdict. Blocks are recorded in a Redis/Postgres requeue store and on Kafka `policy.blocked`.
- **Audio Experience Service**: Manages low-latency speech. Streams PCM chunks to Whisper (ASR), stores log-mel/MFCC/RMS vectors in Qdrant/SomaBrain, applies persona tone shaping, and replies with TTS audio (Kokoro/Coqui/Bark). Emits quality metrics (WER, MOS) to Kafka.
- **Analytics/Billing**: Kafka Streams or Flink writes to ClickHouse. SomaSuite dashboards show latency, refusal, cost, audio quality, policy health, and KAMACHIQ KPIs.
- **SomaBrain Integration**: `python/integrations/soma_client.py` remains the single access path. Conversation worker and tool executor emit memory events to Kafka. All coordinates/metadata, `/remember`, `/recall`, `/migrate/export` use the live SomaBrain API.

## 3. Personas as First-Class Entities
- Personas encapsulate prompts, tone, tool permissions, knowledge snapshots, and model preferences.
- Persona packages live in SomaBrain/SKM marketplace and are referenced by session state.
- Training mode captures new persona shots with lineage tracking; production/test modes use signed persona bundles.
- Session state stores persona ID, model profile override, energy/tone metrics, and governance metadata.

## 4. Open-Source SLM & LLM Strategy
- **Pre-SLM Layer**: Llama 3 8B Instruct, Mistral 7B, or Phi-3 Mini (served via vLLM or llama.cpp) handle intent, slot extraction, tool ranking, and quick heuristics before the main LLM.
- **Primary LLM**: Configurable per role; defaults to OSS (e.g., Mixtral, Codestral) with optional adapters for external providers.
- **Embeddings**: BGE-large or Instructor XL for retrieval; vectors stored in Qdrant and mirrored to SomaBrain.
- **Model Profiles Table**: Stores role → {pre-SLM, primary, fallback, temperature, max tokens}. Profiles can vary per deployment mode (developer/test/production) and per tenant.
- **Scoring Job**: Temporal/Argo workflow computes `score = w_q*quality + w_c*(1/cost) + w_l*(1/latency) + w_r*reliability` from benchmark capsules and production telemetry. Recommendations trigger `model.profile.scored` events.

## 5. Data Plane & Infrastructure
- **Kafka/KRaft**: Event backbone with topics for conversation, tools, policy, audio, analytics. Schema registry ensures contract safety.
- **Redis**: Session cache, rate limits, requeue store.
- **Postgres**: Durable session history, persona metadata, attachments, configuration, audit snapshots.
- **ClickHouse**: Analytics warehouse for latency, refusal, cost, audio quality, model scores.
- **Qdrant**: Encrypted embedding store for audio/text features; synchronized with SomaBrain knowledge graph.
- **Vault**: Secret rotation and service credentials; integrates with GitOps deployments.
- **Prometheus/Tempo/Loki**: Observability stack feeding SomaSuite dashboards.

## 6. Audio & Conversational Experience
- Whisper (FasterWhisper) handles ASR with diarization; vectors derived (log-mel, MFCC, RMS) stored per tenant/persona.
- Persona tone shaping modifies lexical output prior to TTS.
- TTS uses Kokoro, Bark, or Coqui XTTS for low-latency responses; fallback to text if synthesis fails.
- Energy analytics (RMS, zero-crossing, spectral entropy) feed policy rules (e.g., escalation on agitation).

## 7. User Interface Requirements
- **Model Control Panel**: Simple card view per role with current model, fallback chain, usage stats, override controls, and auto mode.
- **Session Workspace**: Streaming transcript, tool execution history, policy verdicts, memory operations, interrupt/resume controls, rerun-with-larger-model option.
- **KAMACHIQ Dashboard**: Visual DAG with deliverables, budgets, persona instances, progress, blocked tasks, and override actions.
- **Tenant Admin Views**: Tenant-level model budgets, policy overrides, marketplace installer, audit log viewer.
- **Audio Console**: Mic controls, transcription feed, audio quality metrics, persona tone selector.

## 8. Sprint Roadmap (12 Weeks)
| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **0A (0-1)** | Foundations | Deploy Kafka, Redis, Postgres, Qdrant, ClickHouse, Whisper, vLLM, OPA/OpenFGA, Vault; Prometheus/Loki/Tempo; GitOps (Argo CD) and CI (Dagger + GitHub Actions); docker-compose dev stack; rename docs to SomaKamachiq. |
| **0B (2)** | Event Skeleton | Kafka client abstraction; Redis/Postgres session repository; FastAPI gateway with enqueue + SSE/WebSocket stubs; initial model profile UI layout. |
| **1A (3-4)** | Conversation Worker | Remove file persistence; conversation worker consuming `conversation.inbound`; integrate OSS SLM intent layer; streaming responses; session inspector UI. |
| **1B (5)** | Tool + Policy | Tool executor service; OPA/OpenFGA client gating memory/tool calls; requeue store + endpoints; policy dashboards; UI status indicators. |
| **2A (6)** | Audio Service | Audio WebSocket ingest; Whisper ASR; feature extraction/ storage; persona tone shaping; TTS outputs; audio metrics in ClickHouse; UI voice controls. |
| **2B (7)** | Model Profiles | Backend CRUD + scoring job; developer/test/production profile defaults; UI panel with cost/latency stats; auto suggestions. |
| **3A (8-9)** | SKM Integration | SKM MAO/provision connectors; `kamachiq.progress` events; KAMACHIQ dashboard in UI; pilot project execution. |
| **3B (10)** | Hardening | Model selection learning loop; quick-action palette; policy regression suite; Vault rotation; SOC2 evidence pack; load/chaos tests (k6, LitmusChaos); documentation updates. |

Legend: SLM runtime, DevX, Observability, Security work continue in parallel to support each sprint.

## 9. Immediate Action Items
1. Commit infrastructure manifests (Helm/Kustomize, docker-compose) and update documentation naming to SomaKamachiq.
2. Build Kafka session repository and FastAPI gateway; remove legacy `persist_chat` file storage.
3. Extract conversation worker from `agent.py` and ensure text loop works fully over Kafka.
4. Launch tool executor and policy client; implement requeue and override endpoints.
5. Integrate OSS SLM pre-processing and benchmark scoring job; stand up model profile UI view.
6. Deliver audio service and voice-enabled UI; log WER/MOS metrics.
7. Complete SKM MAO/provision connectors; run KAMACHIQ pilot; finalize dashboards and compliance docs.

## 10. References
- SomaBrain API (`python/integrations/soma_client.py`, `python/helpers/memory.py`).
- SomaStack architecture docs (`docs/somastack/`), math notes, and roadmap previously shared.
- SLM integration plan (`SomaBrain Canonical Mathematics`, `SomaBrain SLM Strategy`).

---
This blueprint should be treated as the canonical reference for engineers and operators implementing the SomaKamachiq agent.

## 11. Infrastructure Profiles
Detailed infrastructure specifications for LOCAL, DEVELOPMENT, and ENTERPRISE deployments are maintained in `docs/SomaAgent01_Infrastructure.md`. All services—Kafka, Redis, Postgres, Qdrant, ClickHouse, vLLM, Whisper, Vault, OPA/OpenFGA, Prometheus stack—are provisioned via open-source tooling (Docker Compose for LOCAL; Kubernetes + Argo CD + Helm/Terraform for shared and enterprise clusters).
