# SRS-AGENTIQ — Capsule-Scoped Intelligence Governance

**System:** SomaStack (SomaAgent01 + SomaBrain)
**Document ID:** SRS-AGENTIQ-2026-01-16
**Version:** 3.1 (Fully Integrated with Chat Flow & RLM)
**Date:** 2026-01-16
**Status:** Final
**Parent SRS:** [SRS-CHAT-FLOW-V0.3.md](./SRS-CHAT-FLOW-V0.3.md)

**Applied Personas:** PhD Software Developer · PhD Software Analyst · PhD QA Engineer · Security Auditor · Performance Engineer · UX Consultant · ISO-style Documenter · Django Architect · Django Infra Expert · Django Evangelist

---

## 0. Executive Summary

AgentIQ is a **Governor-mediated Control Loop** integrated into the [12-Phase Chat Flow](./SRS-CHAT-FLOW-V0.3.md) between **Phase 2 (Capsule Loading)** and **Phase 3 (Context Building)**. It transforms SomaAgent01 from a linear "Prompt → Model" runtime into a **budgeted transaction system**.

### 0.1 Integration Point in Chat Flow

```
PHASE 0: Request Reception
PHASE 1: Authentication & Authorization
PHASE 2: Capsule Loading
    ↓
┌──────────────────────────────────────────────────────┐
│  AGENTIQ GOVERNOR  (NEW - This SRS)                  │
│  ├─ Phase A: Strategic Intake (AIQ_pred)             │
│  ├─ Phase B: Tool Discovery (OPA/SpiceDB scoped)     │
│  ├─ Phase C: Budget Allocation (Lane Planning)       │
│  └─ Phase D: Path Decision (Fast/Rescue)             │
└──────────────────────────────────────────────────────┘
    ↓
PHASE 3: Context Building (uses AgentIQ ContextPlan)
PHASE 4: RLM Iteration Engine (AgentIQ active per iteration)
PHASE 5-12: Execution, Learning, Response
```

### 0.2 Rule 91 Compliance: Zero Hardcoded Values

**ALL AgentIQ configuration SHALL be sourced from Django ORM:**

```python
# CORRECT: All settings from DB
weight_tool = _get_agent_setting(agent_id, "agentiq.weight_tool", default=None)
if weight_tool is None:
    raise ConfigurationError("agentiq.weight_tool not configured in DB")

# WRONG: Hardcoded defaults
weight_tool = 0.20  # ❌ FORBIDDEN
```

**Settings Priority Chain:**
1. `AgentSetting` model (agent-specific) — Primary
2. `UISetting` model (tenant/user-specific) — Secondary
3. `Capsule.config` JSONField — Tertiary
4. **NO hardcoded fallbacks** — Fail if not configured

---

## 1. Settings Schema (100% DB-Backed)

### 1.1 AgentIQ Settings Keys

All settings stored in `AgentSetting` model with key prefix `agentiq.`:

| Setting Key | Type | Description | Hot-Reloadable |
|-------------|------|-------------|----------------|
| `agentiq.weight_context` | float | ContextIQ weight in scoring | ✅ YES |
| `agentiq.weight_retrieval` | float | RetrievalIQ weight | ✅ YES |
| `agentiq.weight_tool` | float | ToolIQ weight | ✅ YES |
| `agentiq.weight_latency` | float | LatencyIQ weight | ✅ YES |
| `agentiq.weight_reliability` | float | ReliabilityIQ weight | ✅ YES |
| `agentiq.backpressure_threshold` | float | AIQ_pred below this triggers Rescue Path | ✅ YES |
| `agentiq.degrade_threshold` | float | AIQ_pred below this escalates degradation | ✅ YES |
| `agentiq.tool_top_k` | int | Max tools to return from Top-K | ✅ YES |
| `agentiq.tool_disclosure_level` | int | Default disclosure level (0-3) | ✅ YES |
| `agentiq.lane_system_policy` | float | System+Policy lane ratio | ✅ YES |
| `agentiq.lane_history` | float | History lane ratio | ✅ YES |
| `agentiq.lane_memory` | float | Memory lane ratio | ✅ YES |
| `agentiq.lane_tools` | float | Tools lane ratio | ✅ YES |
| `agentiq.lane_tool_results` | float | ToolResults lane ratio | ✅ YES |
| `agentiq.lane_buffer` | float | Buffer lane ratio | ✅ YES |
| `agentiq.buffer_min_tokens` | int | Minimum buffer tokens | ✅ YES |
| `agentiq.fast_path_latency_ms` | int | Fast Path target latency | ✅ YES |
| `agentiq.rescue_path_latency_ms` | int | Rescue Path target latency | ✅ YES |
| `agentiq.receipt_ttl_compact_hours` | int | Compact receipt TTL | ✅ YES |
| `agentiq.receipt_ttl_full_hours` | int | Full receipt TTL | ✅ YES |
| `agentiq.digest_faithfulness_threshold` | float | Min faithfulness score | ✅ YES |

### 1.2 Settings Loading Pattern

```python
# File: admin/core/agentiq/config_resolver.py

from admin.core.helpers.settings_defaults import _get_agent_setting, _get_ui_setting

class ConfigResolver:
    """Load AgentIQ config from Django ORM. No hardcoded defaults."""

    def resolve(
        self,
        agent_id: str,
        tenant_id: str,
        persona_id: str | None = None,
        session_id: str | None = None,
    ) -> AgentIQConfig:
        """
        Cascading scope merge: agent → tenant → persona → session.
        Fails if required settings not found.
        """
        config = AgentIQConfig()

        # Load from AgentSetting (agent-specific)
        for key in AGENTIQ_REQUIRED_KEYS:
            value = _get_agent_setting(agent_id, f"agentiq.{key}")
            if value is None:
                # Try UISetting (tenant-level)
                value = _get_ui_setting(tenant_id, f"agentiq.{key}")
            if value is None:
                raise ConfigurationError(
                    f"Required AgentIQ setting 'agentiq.{key}' not found in DB. "
                    f"Configure via AgentSetting or UISetting."
                )
            setattr(config, key, value)

        return config


AGENTIQ_REQUIRED_KEYS = [
    "weight_context",
    "weight_retrieval",
    "weight_tool",
    "weight_latency",
    "weight_reliability",
    "backpressure_threshold",
    "degrade_threshold",
    "tool_top_k",
    "tool_disclosure_level",
    "lane_system_policy",
    "lane_history",
    "lane_memory",
    "lane_tools",
    "lane_tool_results",
    "lane_buffer",
    "buffer_min_tokens",
]
```

### 1.3 Hot-Reload Mechanism

AgentIQ settings are hot-reloadable via existing infrastructure:

```python
# Called on Kafka event: system.config_update
async def on_config_update(tenant_id: str):
    """Hot-reload AgentIQ config from DB."""
    # Clear Redis cache
    await cache.delete(f"agentiq:config:{tenant_id}")
    # Next request loads fresh from DB
    logger.info(f"AgentIQ config cache cleared for tenant {tenant_id}")
```

---

## 2. Integration with 12-Phase Chat Flow

### 2.1 Where AgentIQ Runs

AgentIQ integrates into [SRS-CHAT-FLOW-V0.3.md](./SRS-CHAT-FLOW-V0.3.md) as follows:

| Chat Flow Phase | AgentIQ Action |
|-----------------|----------------|
| Phase 0: Request Reception | — (no action) |
| Phase 1: Auth & Authorization | — (no action) |
| Phase 2: Capsule Loading | Load Capsule, prepare tool universe |
| **→ AgentIQ Phase A** | Strategic Intake: compute AIQ_pred |
| **→ AgentIQ Phase B** | Tool Discovery: OPA/SpiceDB scoped Top-K |
| **→ AgentIQ Phase C** | Budget Allocation: ContextPlan with lanes |
| **→ AgentIQ Phase D** | Path Decision: Fast or Rescue |
| Phase 3: Context Building | Uses AgentIQ ContextPlan for lane budgets |
| Phase 4: RLM Iteration | AgentIQ runs **per iteration** |
| Phase 5-12: Execution | — (uses context built with AgentIQ plan) |

### 2.2 Integration in ChatService

```python
# File: services/common/chat_service.py
# Integration point: After Phase 2, before Phase 3

async def send_message(self, ...):
    # Phase 0-1: Request & Auth (existing)
    ...

    # Phase 2: Capsule Loading (existing)
    capsule = await self._load_capsule(agent_id)

    # ══════════════════════════════════════════════════════════
    # AGENTIQ INTEGRATION (NEW)
    # ══════════════════════════════════════════════════════════

    from admin.core.agentiq import ConfigResolver, AgentIQGovernor, ToolSelector, Recorder

    # Phase A: Strategic Intake
    config = ConfigResolver().resolve(
        agent_id=str(capsule.id),
        tenant_id=tenant_id,
        persona_id=persona_id,
        session_id=session_id,
    )
    governor = AgentIQGovernor(config)

    # Phase B: Tool Discovery (OPA/SpiceDB scoped)
    tool_selector = ToolSelector()
    tool_universe = await tool_selector.discover(
        user_id=user_id,
        capsule=capsule,
        query=message,
    )

    # Phase C: Budget Allocation
    context_plan = governor.plan(
        max_tokens=model_config.ctx_length,
        capsule=capsule,
        tool_universe=tool_universe,
        degradation_level=current_degradation,
    )

    # Phase D: Path Decision
    execution_path = context_plan.execution_path  # FAST or RESCUE

    # ══════════════════════════════════════════════════════════
    # END AGENTIQ - Continue to Phase 3
    # ══════════════════════════════════════════════════════════

    # Phase 3: Context Building (uses AgentIQ plan)
    context = await self.context_builder.build_context(
        lane_budget=context_plan.lane_budget,
        selected_tools=context_plan.selected_tools,
        execution_path=execution_path,
        ...
    )

    # Phase 4+: RLM Iteration (AgentIQ runs per iteration)
    ...
```

---

## 3. Tool Discovery via OPA/SpiceDB

### 3.1 The 4-Phase Tool Gate (From SRS-CHAT-FLOW §4.2)

AgentIQ tool discovery follows the existing 4-Phase Gate from the Chat Flow SRS:

```
Tool Universe (All Tools)
    ↓
PHASE 1: Global Registry Filter
    └── Is tool globally enabled?
    ↓
PHASE 2: Capsule Filter
    └── Is tool in Capsule.capabilities M2M?
    ↓
PHASE 3: SpiceDB Permission Check
    └── SpiceDB: check(user, tool, "tool:execute")
    ↓
PHASE 4: OPA Policy Check
    └── OPA: is action allowed by policy?
    ↓
DISCOVERABLE TOOLS (User's visible universe)
```

### 3.2 ToolSelector Implementation

```python
# File: admin/core/agentiq/tool_selector.py

from admin.permissions.spicedb import SpiceDBClient
from admin.permissions.opa import OPAClient

class ToolSelector:
    """Capsule-scoped + Permission-scoped tool discovery."""

    async def discover(
        self,
        user_id: str,
        capsule: Capsule,
        query: str,
    ) -> list[ToolCandidate]:
        """
        Discover tools available to this user for this capsule.

        4-Phase Gate:
        1. Global enabled check
        2. Capsule M2M filter
        3. SpiceDB permission check
        4. OPA policy check
        """
        # Phase 1: Global enabled (already filtered in Capability.objects)
        all_tools = await Capability.objects.filter(is_enabled=True).avalues()

        # Phase 2: Capsule filter (M2M)
        capsule_tool_ids = set(
            await capsule.capabilities.values_list("id", flat=True).aall()
        )
        capsule_tools = [t for t in all_tools if t["id"] in capsule_tool_ids]

        # Phase 3: SpiceDB permission check (batch)
        permitted_tools = []
        for tool in capsule_tools:
            has_permission = await self.spicedb.check_permission(
                subject=f"user:{user_id}",
                permission="tool:execute",
                resource=f"tool:{tool['name']}",
            )
            if has_permission:
                permitted_tools.append(tool)

        # Phase 4: OPA policy check (batch)
        final_tools = []
        for tool in permitted_tools:
            allowed = await self.opa.check_policy(
                input={
                    "user_id": user_id,
                    "tool_name": tool["name"],
                    "action": "execute",
                }
            )
            if allowed:
                final_tools.append(tool)

        return final_tools

    async def select_top_k(
        self,
        tools: list[ToolCandidate],
        query: str,
        top_k: int,
        disclosure_level: int,
    ) -> ToolSelection:
        """After discovery, select Top-K by relevance."""
        # Semantic + lexical hybrid scoring
        scored = []
        for tool in tools:
            score = await self._compute_relevance(tool, query)
            scored.append((tool, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Top-K selection
        top_k_tools = scored[:top_k]

        # Compute margin (confidence)
        if len(scored) >= 2:
            margin = scored[0][1] - scored[1][1]
        else:
            margin = 1.0

        return ToolSelection(
            tool_ids=[t[0]["id"] for t in top_k_tools],
            scores=[t[1] for t in top_k_tools],
            margin=margin,
            disclosure_level=disclosure_level,
        )
```

---

## 4. RLM Integration

### 4.1 AgentIQ Within RLM Iterations

Per [SRS-CHAT-FLOW §4 RLM Iteration Engine](./SRS-CHAT-FLOW-V0.3.md), the RLM runs 5-10 iterations per turn. AgentIQ operates **within each iteration**:

```
RLM ITERATION LOOP:
┌─────────────────────────────────────────────────────────────┐
│  Iteration N:                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  1. ──► AGENTIQ: Recompute AIQ_pred with current state  │ │
│  │  2. ──► AGENTIQ: Adjust tool K and disclosure level     │ │
│  │  3. Build context with current weights                  │ │
│  │  4. Call LLM                                            │ │
│  │  5. Parse tool calls                                    │ │
│  │  6. Check OPA policy                                    │ │
│  │  7. Execute tools                                       │ │
│  │  8. ⭐ Call SomaBrain.apply_feedback() ⭐               │ │
│  │  9. ──► AGENTIQ: Compute AIQ_obs from iteration result  │ │
│  │  10. ──► AGENTIQ: Record AgentIQRecord                  │ │
│  │  11. Assess convergence                                 │ │
│  │  12. Loop or exit                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 AIQ Scoring Affected by RLM State

```python
def compute_aiq_pred(
    self,
    pressure: float,
    tool_tax: float,
    degradation_level: int,
    rlm_iteration: int,
    rlm_confidence: float,
) -> float:
    """
    AIQ_pred computation including RLM state.

    RLM integration:
    - Higher iteration count → lower AIQ (token pressure)
    - Higher confidence → higher AIQ (convergence bonus)
    """
    # Base computation (all weights from DB)
    base = 1.0 - (pressure * self.config.pressure_weight)
    base -= tool_tax * self.config.tool_tax_weight

    # Degradation penalty
    penalty = degradation_level * self.config.degrade_penalty_per_level

    # RLM adjustments
    iteration_penalty = rlm_iteration * self.config.rlm_iteration_penalty
    confidence_bonus = rlm_confidence * self.config.rlm_confidence_bonus

    aiq = base - penalty - iteration_penalty + confidence_bonus
    return round(max(0, min(1, aiq)) * 100, 1)
```

### 4.3 RLM-Specific Settings (Also in DB)

| Setting Key | Type | Description |
|-------------|------|-------------|
| `agentiq.rlm_iteration_penalty` | float | AIQ penalty per RLM iteration |
| `agentiq.rlm_confidence_bonus` | float | AIQ bonus from RLM confidence |
| `agentiq.rlm_max_rescue_iterations` | int | Force Rescue Path after N iterations |

---

## 5. Metrics & Observability

### 5.1 Prometheus Metrics (All from DB Config)

```python
# All metric thresholds/labels configurable via DB

AGENTIQ_PRED_SCORE = Histogram(
    'somaagent_agentiq_pred_score',
    'Predictive AIQ score distribution',
    ['agent_id', 'tenant_id', 'execution_path'],
    buckets=_get_agent_setting(agent_id, "agentiq.metrics_buckets", [0.2, 0.4, 0.6, 0.8, 1.0])
)

AGENTIQ_OBS_SCORE = Histogram(
    'somaagent_agentiq_obs_score',
    'Observed AIQ score distribution',
    ['agent_id', 'tenant_id', 'execution_path']
)

AGENTIQ_PATH_SELECTED = Counter(
    'somaagent_agentiq_path_total',
    'Execution path selections',
    ['path', 'agent_id', 'tenant_id']
)

TOOL_DISCOVERY_LATENCY = Histogram(
    'somaagent_tool_discovery_latency_ms',
    'Tool discovery latency (4-phase gate)',
    ['phase', 'agent_id']
)
```

---

## 6. Django Models

### 6.1 AgentIQRecord Model

```python
# File: admin/core/agentiq/models.py

class AgentIQRecord(models.Model):
    """Per-turn AgentIQ audit record. TTL configurable via DB."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    turn_id = models.UUIDField(db_index=True)
    conversation = models.ForeignKey("chat.Conversation", on_delete=models.CASCADE)
    rlm_iteration = models.IntegerField(default=0)  # Which RLM iteration

    # Scores (values, not weights - weights in settings)
    aiq_pred = models.FloatField()
    aiq_obs = models.FloatField(null=True)
    sub_scores = models.JSONField(default=dict)

    # Decisions
    execution_path = models.CharField(max_length=20)
    degradation_level = models.IntegerField()
    tool_top_k = models.IntegerField()
    tool_margin = models.FloatField(null=True)
    tools_discovered = models.IntegerField()  # After 4-phase gate
    tools_selected = models.JSONField(default=list)

    # Usage
    lane_usage = models.JSONField(default=dict)

    # Digest
    digest_used = models.BooleanField(default=False)
    digest_faithfulness = models.FloatField(null=True)

    # Retention (TTL loaded from DB settings)
    is_full_receipt = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "agentiq_records"
        indexes = [
            models.Index(fields=["conversation", "rlm_iteration"]),
            models.Index(fields=["expires_at"]),
        ]
```

---

## 7. Acceptance Criteria

| Criterion | Verification Method |
|-----------|---------------------|
| ✅ All weights/thresholds from DB | `grep -r "default=" admin/core/agentiq/` returns ZERO hardcoded defaults |
| ✅ Hot-reload works | Change setting in DB, verify next request uses new value |
| ✅ Tool discovery uses SpiceDB | Check SpiceDB audit logs for permission checks |
| ✅ Tool discovery uses OPA | Check OPA decision logs |
| ✅ RLM iteration affects AIQ | Verify AIQ_pred decreases across iterations |
| ✅ Fast Path ≤ target latency | Prometheus: `p95(agentiq_fast_path_latency_ms)` |
| ✅ Rescue Path ≤ target latency | Prometheus: `p95(agentiq_rescue_path_latency_ms)` |
| ✅ Receipts expire per TTL | Records deleted after configured TTL |

---

## 8. References

- [SRS-CHAT-FLOW-V0.3.md](./SRS-CHAT-FLOW-V0.3.md) — Parent specification
- [SRS-PERMISSION-MATRIX.md](./SRS-PERMISSION-MATRIX.md) — SpiceDB/OPA integration
- [SRS-SETTINGS-TREE.md](./SRS-SETTINGS-TREE.md) — Settings centralization pattern
- `admin/core/helpers/settings_defaults.py` — Settings loading implementation

---

**Document End**

*Signed off by ALL 10 PERSONAS ✅*
