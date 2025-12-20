# Multimodal Capabilities Extension — Detailed Design

**Document ID:** MMX-DESIGN-2025-12-16  
**Version:** 1.0  
**Date:** 2025-12-16  
**Status:** PLANNING  
**Parent SRS:** SRS‑MMX‑2025‑12‑16  
**Target System:** SomaAgent01 (SomaStack)

---

## 1. Executive Summary

This document provides the detailed technical design for extending SomaAgent01 with multimodal capabilities (images, diagrams, screenshots, video). The design integrates five architectural components (A-E) into a unified system that preserves existing provider integrations and operational guarantees while enabling asset-rich SRS document generation.

### 1.1 Design Principles

1. **Clean Architecture**: All components follow Repository/Use Case/Adapter patterns
2. **VIBE Compliance**: Zero test doubles or task markers, real implementations only
3. **Deterministic Selection**: Single-provider execution per modality
4. **Learning-Enhanced**: SomaBrain feedback loop improves tool selection over time
5. **Security-First**: OPA policies, encryption, audit trails
6. **Observable**: Comprehensive metrics, traces, structured logs

### 1.2 Component Integration Map

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                     │
│                     "Generate SRS with diagrams and screenshots"             │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: INTENT &PLAN EXTRACTION (LLM)                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ContextBuilder (multimodal-aware) → LLM → Task DSL JSON              │ │
│  │  Output: {tasks: [...], assets: [...], criteria: {...}}               │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: COMPILATION (D - Task DSL Compiler)                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  JSON Plan → DAG with:                                                 │ │
│  │  - steps (dependencies, modality, constraints)                         │ │
│  │  - quality gates (rubrics, acceptance criteria)                        │ │
│  │  - failure policy                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼ (for each step in DAG)
┌──────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: CAPABILITY DISCOVERY (E - Registry)                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  CapabilityRegistry.find_candidates(modality, constraints)             │ │
│  │  → [Capability₁, Capability₂, ..., Capabilityₙ]                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: POLICY ROUTING & RANKING (A + B)                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  PolicyGraphRouter (A):                                                │ │
│  │  - Filter via OPA (allow/deny)                                         │ │
│  │  - Apply budget/quota constraints                                      │ │
│  │  - Select provider                                                     │ │
│  │  PortfolioRanker (B) - shadow/active:                                  │ │
│  │  - Query SomaBrain outcomes                                            │ │
│  │  - Rank by success/latency/cost/quality                                │ │
│  │  → Decision{chosen, rationale}                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  PHASE 5: EXECUTION (ToolExecutor extended)                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  FOR attempt IN [chosen]:                                              │ │
│  │    TRY:                                                                 │ │
│  │      provider_adapter.execute(tool, args) → asset_content              │ │
│  │      AssetStore.create(...) → asset_id                                 │ │
│  │      ProvenanceRecorder.record(...)                                    │ │
│  │      IF quality_gate_enabled:                                           │ │
│  │        AssetCritic.evaluate(asset, rubric) → (pass, score, feedback)   │ │
│  │        IF NOT pass AND attempts < MAX_REWORK:                           │ │
│  │          re-prompt with feedback, continue                             │ │
│  │      BREAK (success)                                                    │ │
│  │    EXCEPT error:                                                        │ │
│  │      record_failure(attempt)                                            │ │
│  │      FAIL                                                               │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  PHASE 6: OUTCOME FEEDBACK (SomaBrain)                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  SomaBrain.context_feedback({                                          │ │
│  │    task_name, success, latency_ms, quality_score,                      │ │
│  │    tool_id, model, provider, cost_estimate                             │ │
│  │  })                                                                     │ │
│  │  → Future ranking uses this outcome                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼ (after all steps complete)
┌──────────────────────────────────────────────────────────────────────────────┐
│  PHASE 7: SRS COMPOSITION                                                    │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  SRSComposer.compose(                                                  │ │
│  │    title, sections, asset_ids[], metadata                              │ │
│  │  ) → {markdown, asset_bundle, provenance_summary}                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
                   ┌──────────────────┐
                   │  RESPONSE        │
                   │  - SRS Document  │
                   │  - Asset URLs    │
                   │  - Provenance    │
                   └──────────────────┘
```

---

## 2. Data Model Design

### 2.1 Entity-Relationship Diagram

```mermaid
erDiagram
    multimodal_job_plans ||--o{ multimodal_executions : contains
    multimodal_executions ||--o| multimodal_assets : produces
    multimodal_assets ||--|| asset_provenance : has
    multimodal_capabilities }o--|| multimodal_executions : uses
    
    multimodal_job_plans {
        uuid id PK
        text tenant_id
        text session_id
        jsonb plan_json
        text status
        timestamptz created_at
        timestamptz completed_at
    }
    
    multimodal_capabilities {
        serial id PK
        text tool_id
        text provider
        text_array modalities
        jsonb input_schema
        jsonb output_schema
        jsonb constraints
        text cost_tier
        text health_status
        timestamptz last_health_check
    }
    
    multimodal_executions {
        uuid id PK
        uuid plan_id FK
        int step_index
        text tool_id
        text provider
        text model
        text status
        uuid asset_id FK
        int latency_ms
        numeric cost_estimate
        numeric quality_score
        timestamptz created_at
    }
    
    multimodal_assets {
        uuid id PK
        text tenant_id
        text asset_type
        text format
        text storage_path
        bytea content
        jsonb metadata
        text checksum
        bigint size_bytes
        timestamptz created_at
    }
    
    asset_provenance {
        uuid asset_id PK_FK
        text request_id
        uuid execution_id FK
        text prompt_summary
        jsonb generation_params
        text user_id
        timestamptz created_at
    }
```

### 2.2 Key Design Decisions

**Storage Strategy**: S3-only
- **Storage**: S3-compatible object storage for assets (scalable, cost-effective)
- **PostgreSQL bytea**: Not used for multimodal assets

**Checksum Deduplication**: SHA256-based
- Prevents duplicate storage of identical assets
- Enables content-addressable retrieval
- Supports asset versioning (same content = same hash)

**Provenance Immutability**: Separate table with FK cascade
- Audit trail survives asset deletion if needed (change to CASCADE vs RESTRICT)
- Supports compliance requirements (retain provenance longer than asset)

---

## 3. Component A: Policy Graph Router (Deterministic Provider Selection)

### 3.1 Provider Ordering Specification

Explicit, versioned provider ordering per modality + task type combination:

| Order Key | Provider 1 | Provider 2 | Provider 3 | Provider 4 |
|-----------|------------|------------|------------|------------|
| `image_diagram` | `mermaid_svg` | `plantuml_png` | `matplotlib_png` | `dalle_raster` |
| `image_photo` | `dalle3` | `dalle2` | `stable_diffusion` | — |
| `image_annotated_screenshot` | `playwright_annotate` | `selenium_screenshot` + `pil_annotate` | user_upload | — |
| `video_short` | `runway_gen2` | `pika_labs` | `storyboard_frames` | — |
| `diagram_architecture` | `mermaid_svg` | `plantuml_png` | `graphviz_dot` | — |

If no eligible provider is available, the router returns a structured error.

### 3.2 OPA Integration Points

```rego
# Example policy evaluation request
{
  "action": "multimodal.tool.execute",
  "resource": "dalle3",
  "tenant": "acme-corp",
  "provider": "openai",
  "modality": "image",
  "context": {
    "cost_tier": "high",
    "tenant_budget_remaining": 5000,  # cents
    "user_override": true
  }
}

# Expected response
{
  "allow": true,
  "rationale": "User override + sufficient budget"
}
```

**Policy Enforcement Points**:
1. **Pre-Execution**: Before first attempt, filter capabilities
2. **Selection**: Before provider selection, re-check policy
3. **Budget**: Deduct estimated cost; block if exhausted
4. **Data Classification**: Block high-risk tools for sensitive tenants

---

## 4. Component B: Portfolio Selector (Learning-Enhanced Ranking)

### 4.1 Ranking Algorithm

Given candidates `C = {c₁, c₂, ..., cₙ}` for modality `M` and task type `T`:

1. **Query SomaBrain Outcomes**:
   ```python
   outcomes = soma_client.recall(
       query=f"task_type:{T} modality:{M}",
       top_k=100,
       universe="multimodal_outcomes"
   )
   ```

2. **Compute Metrics per Capability**:
   For each `cᵢ`:
   - `success_rate(cᵢ) = successes / total_attempts`
   - `avg_latency(cᵢ) = Σ latency_ms / count`
   - `avg_quality(cᵢ) = Σ quality_score / count`
   - `avg_cost(cᵢ) = Σ cost_estimate / count`

3. **Weighted Score**:
   ```
   score(cᵢ) = w₁ · success_rate(cᵢ) +
               w₂ · (1 - normalized_latency(cᵢ)) +
               w₃ · avg_quality(cᵢ) +
               w₄ · (1 - normalized_cost(cᵢ))
   
   where:
   w₁ = 0.4 (success is most important)
   w₂ = 0.2 (latency matters for UX)
   w₃ = 0.3 (quality drives rework rate)
   w₄ = 0.1 (cost is secondary if budgets set)
   ```

4. **Exploration Policy** (optional, off by default):
   With probability `ε = 0.05`, select random capability instead of top-ranked.
   - Enables discovery of better alternatives
   - Configurable per tenant (`exploration_rate`)

### 4.2 Shadow vs Active Mode

**Shadow Mode** (default):
- Ranker computes scores and rankings
- PolicyGraphRouter ignores rankings, uses cost-sorted defaults
- Logs divergence: `if shadow_rank[0] != actual_choice: log_divergence(...)`
- Metrics: `portfolio_ranker_shadow_divergence_total{modality, task_type}`

**Active Mode** (opt-in via feature flag):
- PolicyGraphRouter uses ranked order from B within allowed set from A
- A still enforces hard constraints (policy, budget, health)
- B provides soft ranking within those constraints
- Activation criteria: shadow mode divergence < 10% for 7 days

---

## 5. Component C: Producer + Critic (Quality Gating)

### 5.1 Quality Rubric Schema

```json
{
  "asset_type": "image",
  "criteria": [
    {
      "dimension": "clarity",
      "weight": 0.4,
      "threshold": 0.7,
      "description": "Text/labels are legible"
    },
    {
      "dimension": "relevance",
      "weight": 0.3,
      "threshold": 0.6,
      "description": "Content matches request intent"
    },
    {
      "dimension": "aesthetic",
      "weight": 0.3,
      "threshold": 0.5,
      "description": "Professional appearance"
    }
  ],
  "min_overall_score": 0.65
}
```

### 5.2 Evaluation Flow

```python
async def evaluate_with_rework(asset, rubric, max_attempts=2):
    for attempt in range(max_attempts):
        passes, score, feedback = await critic.evaluate(asset, rubric)
        
        if passes:
            return (asset, score)
        
        if attempt < max_attempts - 1:
            # Re-prompt with feedback
            new_prompt = f"{original_prompt}\n\nPrevious attempt failed: {feedback}\nImprove: {rubric['criteria']}"
            asset = await producer.generate(new_prompt)
        else:
            # Exhausted attempts; mark failed
            raise QualityGateFailure(f"Failed after {max_attempts} attempts: {feedback}")
```

### 5.3 Vision Model Integration

For image quality evaluation:
- **Provider**: GPT-4 Vision

**Prompt Template**:
```
Evaluate this image for:
1. Clarity: Are text/labels legible? (0-1)
2. Relevance: Does it match the description "{context}"? (0-1)
3. Aesthetic: Professional appearance? (0-1)

Respond with JSON:
{
  "clarity": 0.0-1.0,
  "relevance": 0.0-1.0,
  "aesthetic": 0.0-1.0,
  "passes": true/false,
  "overall_score": 0.0-1.0,
  "feedback": "concise explanation"
}
```

---

## 6. Component D: Task DSL & Compiler

### 6.1 Task DSL v1.0 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "tasks"],
  "properties": {
    "version": {"const": "1.0"},
    "metadata": {
      "type": "object",
      "properties": {
        "request_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "session_id": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"}
      }
    },
    "tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["task_id", "step_type", "modality"],
        "properties": {
          "task_id": {"type": "string"},
          "step_type": {"enum": ["generate_image", "generate_diagram", "capture_screenshot", "generate_video", "compose_srs"]},
          "modality": {"enum": ["text", "image", "video", "diagram", "screenshot"]},
          "depends_on": {"type": "array", "items": {"type": "string"}},
          "description": {"type": "string"},
          "constraints": {
            "type": "object",
            "properties": {
              "max_resolution": {"type": "integer"},
              "format": {"type": "string"},
              "duration_sec": {"type": "integer"},
              "style": {"type": "string"}
            }
          },
          "quality_gate": {
            "type": "object",
            "properties": {
              "enabled": {"type": "boolean"},
              "rubric": {"type": "object"}
            }
          },
          "user_defaults": {
            "type": "object",
            "properties": {
              "provider": {"type": "string"},
              "model": {"type": "string"}
            }
          }
        }
      }
    },
    "budget": {
      "type": "object",
      "properties": {
        "max_cost_cents": {"type": "integer"},
        "max_duration_sec": {"type": "integer"}
      }
    }
  }
}
```

### 6.2 Compiler Output: Executable DAG

```python
@dataclass
class ExecutableStep:
    step_id: str
    modality: str
    step_type: str
    dependencies: List[str]  # task_ids this step depends on
    constraints: dict
    quality_gate: Optional[dict]
    user_defaults: dict

@dataclass
class ExecutableDAG:
    steps: List[ExecutableStep]
    budget: dict
    metadata: dict
    
    def topological_order(self) -> List[ExecutableStep]:
        """Return steps in dependency-safe execution order."""
        # Implementation: Kahn's algorithm or DFS
        pass
```

**Compiler Validation**:
- No circular dependencies
- All `depends_on` references exist
- Modality + step_type compatibility (e.g., can't "generate_video" with modality="image")
- Budget fields are positive integers

---

## 7. Component E: Capability Registry

### 7.1 Registration Example

```python
# At system startup or provider plugin load
await registry.register(
    tool_id="dalle3_image_gen",
    provider="openai",
    modalities=["image"],
    input_schema={
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "maxLength": 4000},
            "size": {"enum": ["1024x1024", "1792x1024", "1024x1792"]},
            "quality": {"enum": ["standard", "hd"]},
            "style": {"enum": ["vivid", "natural"]}
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "format": {"const": "png"},
            "content": {"type": "string", "format": "byte"}  # base64 or bytes
        }
    },
    constraints={
        "max_resolution": 1792,
        "supported_formats": ["png"],
        "max_prompt_length": 4000
    },
    cost_tier="high"  # $0.04-0.12 per image
)
```

### 7.2 Health Checks

```python
async def update_health_status():
    """Periodic health check for all capabilities (cron job)."""
    for capability in await registry.get_all():
        try:
            await provider_adapter.health_check(capability.provider)
            await registry.set_health_status(capability.id, "healthy")
        except Exception as e:
            await registry.set_health_status(capability.id, "unhealthy")
            logger.error(f"Health check failed for {capability.tool_id}: {e}")
```

**Health Check Triggers**:
- **Periodic**: Every 60 seconds (cron)
- **On-Demand**: Before critical tenant requests
- **Circuit Breaker**: When circuit opens, mark unhealthy; when closes, re-check

---

## 8. Provider Adapter Design

### 8.1 Adapter Interface

```python
from abc import ABC, abstractmethod

class MultimodalProviderAdapter(ABC):
    """Abstract base for provider-specific multimodal adapters."""
    
    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> dict:
        """
        Returns: {
            "format": "png",
            "content": bytes,
            "metadata": {"width": int, "height": int, ...}
        }
        """
        pass
    
    @abstractmethod
    async def generate_diagram(self, description: str, **kwargs) -> dict:
        """For diagram-specific tools (Mermaid, PlantUML, etc.)."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider availability."""
        pass
```

### 8.2 Concrete Adapters

**OpenAI DALL-E Adapter**:
```python
class OpenAIImageAdapter(MultimodalProviderAdapter):
    async def generate_image(self, prompt: str, size="1024x1024", quality="standard", **kwargs):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": "dall-e-3", "prompt": prompt, "size": size, "quality": quality}
            )
            resp.raise_for_status()
            
            data = resp.json()
            image_url = data["data"][0]["url"]
            
            # Download image
            img_resp = await client.get(image_url)
            content = img_resp.content
            
            return {
                "format": "png",
                "content": content,
                "metadata": {"revised_prompt": data["data"][0].get("revised_prompt"), "size": size}
            }
```

**Mermaid Diagram Adapter** (local rendering):
```python
class MermaidDiagramAdapter(MultimodalProviderAdapter):
    async def generate_diagram(self, description: str, **kwargs):
        # Use mermaid-cli (mmdc) to render SVG
        mermaid_code = await self._llm_generate_mermaid_code(description)
        
        proc = await asyncio.create_subprocess_exec(
            "mmdc", "-i", "/dev/stdin", "-o", "/dev/stdout", "-t", "default",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate(input=mermaid_code.encode())
        
        if proc.returncode != 0:
            raise RuntimeError(f"Mermaid rendering failed: {stderr.decode()}")
        
        return {
            "format": "svg",
            "content": stdout,
            "metadata": {"mermaid_code": mermaid_code}
        }
```

---

## 9. Security & Privacy Design

### 9.1 Asset Encryption at Rest (Optional)

For sensitive assets, support envelope encryption:

1. **Generate Data Key (DEK)**: `DEK = KMS.generate_data_key(tenant_key_id)`
2. **Encrypt Asset**: `encrypted_content = AES-256-GCM(content, DEK)`
3. **Encrypt DEK**: `encrypted_dek = KMS.encrypt(DEK, tenant_key_id)`
4. **Store**:
   ```sql
   INSERT INTO multimodal_assets (..., content, metadata)
   VALUES (..., encrypted_content, jsonb_build_object('encrypted_dek', encrypted_dek, 'algorithm', 'AES-256-GCM'))
   ```

### 9.2 Provenance Redaction

**Sensitive Fields**:
- Full prompts (may contain PII, confidential context)
- Generation params (may expose model internals)

**Redaction Policy**:
```python
async def create_provenance(asset_id: str, prompt: str, params: dict, user_id: str):
    # Redact prompt if policy says so
    if await opa.evaluate({"action": "provenance.store_full_prompt", "tenant": tenant_id}).get("deny"):
        prompt_summary = f"[REDACTED] ({len(prompt)} chars)"
    else:
        prompt_summary = prompt[:500]  # First 500 chars
    
    # Redact sensitive param keys
    safe_params = {k: v for k, v in params.items() if k not in ["api_key", "internal_model_id"]}
    
    await store_provenance(asset_id, prompt_summary, safe_params, user_id)
```

---

## 10. Observability Design

### 10.1 Prometheus Metrics

| Metric Name | Type | Labels | Purpose |
|-------------|------|--------|---------|
| `multimodal_capability_selection_total` | Counter | modality, tool_id, provider, decision_source | Track which tools selected |
| `multimodal_execution_latency_seconds` | Histogram | modality, tool_id, provider, status | Execution duration |
| `multimodal_execution_cost_estimate_cents` | Histogram | modality, tool_id, provider | Cost tracking |
| `multimodal_provider_errors_total` | Counter | modality, tool_id, error_reason | Provider error frequency |
| `multimodal_quality_score` | Histogram | modality, tool_id | Critic scores |
| `multimodal_rework_attempts_total` | Counter | modality, reason | Quality gate rework |
| `portfolio_ranker_shadow_divergence_total` | Counter | modality, task_type | Shadow mode divergence |
| `capability_health_status` | Gauge | tool_id, provider | 1=healthy, 0=unhealthy |

### 10.2 OpenTelemetry Traces

**Span Structure**:
```
multimodal_job (root span)
├── plan_extraction
│   └── llm_invoke
├── plan_compilation
├── step_00_generate_diagram
│   ├── capability_discovery
│   ├── policy_routing
│   ├── portfolio_ranking (if enabled)
│   ├── execution_attempt_0
│   │   ├── provider_api_call
│   │   └── asset_store_create
│   ├── provenance_record
│   └── quality_evaluation (if enabled)
│       └── vision_model_call
├── step_01_capture_screenshot
│   └── ...
└── srs_composition
```

**Trace Attributes**:
- `multimodal.job_id`
- `multimodal.step_id`
- `multimodal.modality`
- `multimodal.tool_id`
- `multimodal.provider`
- `multimodal.quality_score`

---

## 11. Testing Strategy

### 11.1 Test Pyramid

```
         /\
        /E2E\         Golden tests (3-5 scenarios)
       /──────\
      /Integr.\       Provider adapters, DB, SomaBrain (20-30 tests)
     /──────────\
    /   Unit     \    Registries, routers, compilers (100+ tests)
   /──────────────\
```

### 11.2 Golden E2E Scenarios

1. **"Generate SRS with Architecture Diagrams"**
   - Input: Natural language SRS request mentioning "include system architecture diagram and deployment diagram"
   - Expected: Plan with 2+ diagram tasks, execution succeeds, SRS markdown contains embedded SVGs
   - Assertions: Assets created, provenance recorded, policy enforced

2. **"Provider Failure → Explicit Error"**
   - Setup: Configure a provider endpoint to return 503
   - Input: Image generation request
   - Expected: Execution fails with a clear provider_error surfaced to the caller
   - Assertions: Error metrics incremented and failure recorded in provenance

3. **"Quality Gate Rejection → Rework → Pass"**
   - Setup: First attempt uses a deliberately low-quality diagram prompt; second attempt uses a refined prompt
   - Input: Diagram with quality gate enabled
   - Expected: First attempt rejected, second attempt passes
   - Assertions: `multimodal_rework_attempts_total` = 1, final quality_score ≥ threshold

### 11.3 Chaos Engineering Scenarios

1. **Circuit Breaker Cascade Prevention**
   - Trigger: Repeated failures on primary provider (5 failures in 10 sec)
   - Expect: Circuit opens, future requests reject the primary provider and surface a provider_unavailable error
   - Recovery: After cooldown (60s), circuit half-opens, attempts primary again

2. **Partial Job Resume**
   - Trigger: Kill process after step 3 of 5-step job
   - Expect: Job status = "partial", steps 1-3 marked complete
   - Resume: Re-submit job, steps 1-3 skipped, execution starts at step 4

---

## 12. Performance Budgets

| Operation | Target Latency (P95) | Max Latency (P99) | Notes |
|-----------|----------------------|-------------------|-------|
| Capability Discovery | 50ms | 100ms | DB query, should be fast |
| Policy Routing | 100ms | 200ms | Includes OPA call |
| Portfolio Ranking (shadow) | 200ms | 400ms | SomaBrain recall + scoring |
| Image Generation (DALL-E) | 15s | 30s | Provider-dependent |
| Diagram Rendering (Mermaid) | 2s | 5s | Local rendering |
| Quality Evaluation (vision model) | 5s | 10s | LLM call |
| SRS Composition (5 assets) | 3s | 7s | Asset retrieval + markdown generation |

**Budget Enforcement**:
- Timeouts per step (configurable in plan)
- If step exceeds timeout, mark the step failed and surface a timeout error
- Overall job timeout (sum of step budgets + 20% buffer)

---

## 13. Deployment Architecture

### 13.1 Service Topology

```
┌─────────────────────────────────────────────────────────────────┐
│  Gateway (FastAPI)                                               │
│  - /v1/multimodal/* routes                                       │
│  - Auth, rate limiting, circuit breakers                         │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  ToolExecutor (extended with multimodal_dispatch)               │
│  - PolicyGraphRouter                                             │
│  - PortfolioRanker (optional)                                    │
│  - AssetStore, ProvenanceRecorder                                │
│  - Provider adapters (OpenAI, Stability, Mermaid, ...)          │
└─────────────────────────┬────────────────────────────────────────┘
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │PostgreSQL│    │ S3/MinIO │    │SomaBrain │
    │ (Assets, │    │ (Asset   │    │(Outcomes)│
    │  Capa-   │    │  Storage)│    │          │
    │  bilities│    └──────────┘    └──────────┘
    │  Prove-  │
    │  nance)  │
    └─────────┘
```

### 13.2 Horizontal Scaling

**ToolExecutor Replicas**:
- Stateless (except transient execution state)
- Scale based on `multimodal_execution_latency_seconds` P95
- Target: Keep P95 < 20s (including provider latency)

**Bottlenecks**:
1. **Provider API Rate Limits**: Configure per-tenant quotas in OPA
2. **S3 Write Throughput**: Batch small assets, async upload
3. **SomaBrain Query Latency**: Cache recent outcomes (Redis, TTL=5min)

---

## 14. Open Questions & Future Work

### 14.1 v1.0 Scope Limitations

- **Video**: Experimental only (Runway/Pika); no editing/compositing
- **Audio**: Out of scope (defer to v2.0)
- **Real-time Streaming**: Assets generated once, not streamed
- **Multi-Asset Composition**: SRS can embed multiple assets, but no inter-asset dependencies (e.g., can't overlay screenshot on diagram)

### 14.2 Future Enhancements (v2.0+)

- **Task DSL Formalization**: Move from JSON to versioned DSL with parser/compiler
- **Active Learning**: Automated A/B testing of tools (supervised exploration)
- **Cost Optimization**: Predict cheapest path to meet quality threshold
- **Asset Templates**: Reusable diagram/screenshot templates with placeholders
- **Collaborative Editing**: Multi-user review/approval of generated assets

---

## 15. Acceptance Criteria Summary

| Category | Criterion | Status |
|----------|-----------|--------|
| **Data Model** | 5 tables created with migrations | Planned |
| **Capability Registry** | Discover tools by modality + constraints | Planned |
| **Policy Router** | Deterministic provider ordering per modality | Planned |
| **Asset Store** | S3 + PostgreSQL hybrid storage | Planned |
| **Provenance** | All assets have provenance records | Planned |
| **Provider Adapters** | 3+ adapters (OpenAI, Stability, Mermaid) | Planned |
| **Quality Critic** | Vision model evaluation for images | Planned |
| **Portfolio Ranker** | SomaBrain outcomes queried (shadow mode) | Planned |
| **SRS Composer** | Markdown with embedded assets | Planned |
| **API Endpoints** | 5+ multimodal routes functional | Planned |
| **Security** | OPA policies + encryption (optional) | Planned |
| **Observability** | Prometheus + OpenTelemetry traces | Planned |
| **Testing** | 90%+ coverage, E2E golden tests pass | Planned |
| **Deployment** | Feature flag, rollout plan | Planned |
| **VIBE Compliance** | Zero test doubles or task markers in production code | Planned |

---

**Document Status**: PLANNING — Ready for implementation upon approval

**Next Steps**:
1. Review design with all 7 personas
2. Approve implementation plan
3. Begin Phase 1: Foundation & Data Model
4. Execute tasks per `task.md` breakdown

---

*End of Design Document*
