⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Persona Lifecycle & Training Mode

## Purpose
Personas are portable skill capsules that let SomaAgent 01 swap expertise safely. This document describes how personas are authored, trained with human experts, sealed, and reused across deployment modes while still allowing controlled continuous learning via SomaBrain.

## Persona Components
- **Prompt core**: System instructions, tone, vocabulary, safety boundaries.
- **Tool bundle**: Whitelisted tool adapters, sandbox policies, credential scopes.
- **Knowledge snapshots**: Curated memory nodes and embeddings stored in SomaBrain/Qdrant.
- **Model preferences**: Role-specific model profiles (pre-SLM, primary, fallback) and budgets.
- **Policy hooks**: Required approvals, audit requirements, escalation channels.

## Training Mode Workflow
1. **Session Initiation**
   - Authorized trainer selects "Start Training" and chooses a base persona (empty or existing version).
   - Runtime switches to `TRAINING` mode (see runtime modes doc). All events tagged with training session ID.

2. **Human-Guided Teaching**
   - Trainer converses with the agent, runs tools, uploads artifacts, and annotates desired outcomes.
   - Agent executes tasks while logging every step (conversation, tool runs, policy decisions, attachments) immutably.
   - Trainers provide feedback (approve, correct, explain) that is stored as structured annotations.

3. **Persona Synthesis**
   - When the trainer finishes, they click "Close Training". The system:
     - Summarizes conversations into prompt updates and tool heuristics.
     - Generates knowledge snapshots linking to SomaBrain coordinates.
     - Captures recommended model overrides and policy adjustments.
     - Produces a draft persona pack (`.persona.yaml`) for review.

4. **Review & Approval**
   - Trainers and reviewers inspect the generated persona pack, adjust prompts/tool settings, and run validation tests.
   - Policy engine verifies the persona does not violate tenant or constitutional rules.
   - Once approved, the persona pack is signed and versioned (e.g., `biology_researcher.v1`).

5. **Promotion & Distribution**
   - The sealed persona is published to the persona repository / marketplace.
   - Deployment modes (DEV/PROD) reference the signed persona. Tool bundles and knowledge snapshots are mounted accordingly.
   - Previous training data remains in the training archive for audit.

## Controlled Continuous Learning
- Even after promotion, the persona may continue limited learning:
  - SomaBrain adaptation weights (λ, μ, ν, α, γ) govern updates to memories, retrieval scores, and prompts.
  - Updates are scoped to persona-owned knowledge areas and subject to policy thresholds.
  - High-risk modifications require human approval or a new training session.
- Telemetry (performance, cost, accuracy) feeds benchmark runs. If the persona drifts, operators can schedule a new training cycle or roll back to an earlier version.

## Persona Marketplace & Tool Interchange
- Personas appear in the marketplace as signed bundles containing prompt, tool suite, knowledge references, policies.
- Agents can swap personas securely: the orchestrator verifies signatures, loads tools/knowledge, and applies mode-specific policies.
- Multi-persona projects (e.g., KAMACHIQ) map tasks to personas (Biology, DevOps, QA). Each instance maintains isolated memory and tool permissions.

## Security & Governance
- Training data stored in encrypted object storage with access limited to trainers/auditors.
- Persona packs are digitally signed; only trusted signers can publish to marketplace.
- Policy engine enforces tool permissions; personas cannot access other personas' tools unless explicitly configured.
- Audit logs link persona version, session ID, trainer ID, and policy overrides.

## Implementation Checklist
1. Implement training session API (`POST /v1/persona/train/start`, `POST /v1/persona/train/close`).
2. Log all training events to Kafka (`training.conversation`, `training.tools`).
3. Build persona synthesis pipeline (prompts, tools, knowledge, policy) with human review UI.
4. Integrate persona signing, versioning, and promotion to repository/marketplace.
5. Enforce adaptation limits in runtime modes, with telemetry-driven alerts if drift detected.
