"""Canonical bootstrap seed data.

One declaration of every row bootstrap_soma writes. Nothing here invents a
host: protocol bases come from ``admin.core.helpers.vendor_api_bases`` and
deployment endpoints stay empty until the operator sets them through the
settings chain (SOMA-STD-CONFIG-001 / R-VEN-02).

LLM catalog rows are the only rows this module fully owns. Capsule, identity
and InfrastructureConfig seeds are *fill-if-absent*: an operator-edited value
is never clobbered (compare-before-write).

Model roles are the five-role contract from ``admin.llm.providers`` —
``chat_role`` / ``utility_role`` / ``embedding_role`` / ``vision_role`` /
``decision_role``. There is no second vocabulary (``slot``) and no second
binding-key table: keys come from ``ROLE_SETTING_KEYS``, the tenant-defaults
scope name from ``DEFAULTS_AGENT_ID``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from admin.core.helpers.vendor_api_bases import (
    ANTHROPIC_API_BASE,
    DEEPSEEK_API_BASE,
    GOOGLE_GENERATIVE_LANGUAGE_API_BASE,
    GROQ_API_BASE,
    HUGGINGFACE_API_BASE,
    OPENAI_API_BASE,
)
from admin.llm.providers import (
    DEFAULTS_AGENT_ID,
    MODEL_ROLES,
)
from services.common.memory_contract import DEFAULT_MEM_EMBED_DIM

__all__ = [
    "MIMO_FLASH_NAME",
    "MIMO_FLASH_ROW",
    "GROQ_MODEL_ROWS",
    "EMBEDDING_MODEL_ROWS",
    "VISION_MODEL_NAME",
    "CLEF_DECISION_ROW",
    "LLM_SEED_ROWS",
    "BIG5_TRAIT_NAMES",
    "DEFAULT_PERSONALITY_TRAITS",
    "DEFAULT_NEUROMODULATOR_BASELINE",
    "DEFAULT_LEARNING_CONFIG",
    "DEFAULT_KNOBS",
    "DEFAULT_MEMORY_POINTER_KEYS",
    "DEFAULT_RECALL_LIMIT",
    "DEFAULT_SIMILARITY_THRESHOLD",
    "DEFAULT_SYSTEM_PROMPT",
    "CAPSULE_NAME",
    "AGENT_NAME",
    "AGENT_SLUG",
    "INFRA_SEED_KEYS",
    "MODEL_ROLE_AGENT_ID",
    "MODEL_ROLE_DEFAULTS",
    "MODEL_ROLE_ORDER",
]

# ── LLM catalog ────────────────────────────────────────────────────────────

MIMO_FLASH_NAME = "mimo-v2.6-flash"

MIMO_FLASH_ROW: Dict[str, Any] = {
    "name": MIMO_FLASH_NAME,
    "display_name": "MiMo Flash",
    "model_type": "chat",
    "provider": "mimo",
    # Deployment endpoint (R-VEN-02) — operator names it on the model row /
    # InfrastructureConfig.  Never invented here.
    "api_base": "",
    "capabilities": ["text", "code", "tools", "long_context"],
    "priority": 100,
    "cost_tier": "free",
    "domains": [],
    "ctx_length": 131072,
    "limit_requests": 0,
    "limit_input": 0,
    "limit_output": 0,
    "kwargs": {},
    "is_active": True,
}

GROQ_MODEL_ROWS: List[Dict[str, Any]] = [
    {
        "name": "openai/gpt-oss-120b",
        "display_name": "GPT-OSS 120B (Groq)",
        "model_type": "chat",
        "provider": "groq",
        "api_base": GROQ_API_BASE,
        "capabilities": ["text", "code", "tools", "long_context"],
        "priority": 90,
        "cost_tier": "standard",
        "domains": [],
        "ctx_length": 131072,
        "limit_requests": 0,
        "limit_input": 65536,
        "limit_output": 65536,
        "kwargs": {"parallel_tool_calls": False},
        "is_active": True,
    },
    {
        "name": "openai/gpt-oss-20b",
        "display_name": "GPT-OSS 20B (Groq)",
        "model_type": "chat",
        "provider": "groq",
        "api_base": GROQ_API_BASE,
        "capabilities": ["text", "code", "tools", "long_context"],
        "priority": 70,
        "cost_tier": "low",
        "domains": [],
        "ctx_length": 131072,
        "limit_requests": 0,
        "limit_input": 65536,
        "limit_output": 65536,
        "kwargs": {"parallel_tool_calls": False},
        "is_active": True,
    },
]

EMBEDDING_MODEL_ROWS: List[Dict[str, Any]] = [
    {
        "name": "openai/text-embedding-3-small",
        "display_name": "text-embedding-3-small",
        "model_type": "embedding",
        "provider": "openai",
        "api_base": OPENAI_API_BASE,
        "capabilities": ["embed"],
        "priority": 50,
        "cost_tier": "low",
        "domains": [],
        "ctx_length": 8191,
        "limit_requests": 0,
        "limit_input": 8191,
        "limit_output": 0,
        "kwargs": {},
        "is_active": True,
    },
    {
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "display_name": "all-MiniLM-L6-v2",
        "model_type": "embedding",
        "provider": "huggingface",
        "api_base": HUGGINGFACE_API_BASE,
        "capabilities": ["embed"],
        "priority": 45,
        "cost_tier": "free",
        "domains": [],
        "ctx_length": 256,
        "limit_requests": 0,
        "limit_input": 256,
        "limit_output": 0,
        "kwargs": {},
        "is_active": True,
    },
]

# Vision-capable chat model. ``vision_role`` accepts ``model_type="chat"``
# (admin.llm.api._role_model_type_required); this row is the catalog's only
# vision-capable model, so it is what vision_role binds.
VISION_MODEL_NAME = "gemini-2.0-flash"

# Clef / System One decision model. api_base is filled from CLEF_API_BASE at
# write time — empty is honest when the operator has not configured it.
CLEF_DECISION_ROW: Dict[str, Any] = {
    "name": "clef-decision",
    "display_name": "Clef Decision (Workers AI)",
    "model_type": "decision",
    "provider": "cloudflare",
    "api_base": "",
    "capabilities": ["decision", "score", "noul"],
    "priority": 95,
    "cost_tier": "low",
    "domains": [],
    "ctx_length": 0,
    "limit_requests": 0,
    "limit_input": 0,
    "limit_output": 0,
    "kwargs": {},
    "is_active": True,
}

LLM_SEED_ROWS: List[Dict[str, Any]] = (
    [MIMO_FLASH_ROW]
    + GROQ_MODEL_ROWS
    + EMBEDDING_MODEL_ROWS
    + [
        {
            "name": "deepseek-chat",
            "display_name": "DeepSeek Chat",
            "model_type": "chat",
            "provider": "deepseek",
            "api_base": DEEPSEEK_API_BASE,
            "capabilities": ["text", "code", "tools", "long_context"],
            "priority": 82,
            "cost_tier": "low",
            "domains": [],
            "ctx_length": 65536,
            "limit_requests": 0,
            "limit_input": 0,
            "limit_output": 8192,
            "kwargs": {},
            "is_active": True,
        },
        {
            "name": "claude-3-5-haiku-latest",
            "display_name": "Claude 3.5 Haiku",
            "model_type": "chat",
            "provider": "anthropic",
            "api_base": ANTHROPIC_API_BASE,
            "capabilities": ["text", "code", "tools", "long_context"],
            "priority": 80,
            "cost_tier": "low",
            "domains": [],
            "ctx_length": 200000,
            "limit_requests": 0,
            "limit_input": 0,
            "limit_output": 8192,
            "kwargs": {},
            "is_active": True,
        },
        {
            "name": VISION_MODEL_NAME,
            "display_name": "Gemini 2.0 Flash",
            "model_type": "chat",
            "provider": "google",
            "api_base": GOOGLE_GENERATIVE_LANGUAGE_API_BASE,
            "capabilities": ["text", "code", "tools", "vision", "long_context"],
            "priority": 78,
            "cost_tier": "low",
            "domains": [],
            "ctx_length": 1000000,
            "limit_requests": 0,
            "limit_input": 0,
            "limit_output": 8192,
            "kwargs": {},
            "is_active": True,
        },
        CLEF_DECISION_ROW,
    ]
)

# ── Capsule-complete contract ──────────────────────────────────────────────

BIG5_TRAIT_NAMES: Tuple[str, ...] = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
)

DEFAULT_PERSONALITY_TRAITS: Dict[str, float] = {
    "openness": 0.7,
    "conscientiousness": 0.7,
    "extraversion": 0.5,
    "agreeableness": 0.6,
    "neuroticism": 0.3,
}

DEFAULT_NEUROMODULATOR_BASELINE: Dict[str, Any] = {
    "dopamine": 0.5,
    "serotonin": 0.6,
    "norepinephrine": 0.4,
    "acetylcholine": 0.5,
}

DEFAULT_LEARNING_CONFIG: Dict[str, Any] = {
    "eta": 0.1,
    "lambda": 0.9,
    "alpha": 0.05,
    "reward_threshold": 0.5,
    "negative_reward_threshold": -0.5,
}

DEFAULT_KNOBS: Dict[str, Any] = {
    "intelligence_level": 7,
    "autonomy_level": 7,
    "resource_budget": 0.5,
    "response_style": "balanced",
}

DEFAULT_MEMORY_POINTER_KEYS: Tuple[str, ...] = (
    "tenant",
    "namespace",
    "recall_limit",
    "similarity_threshold",
)

DEFAULT_RECALL_LIMIT = 10
DEFAULT_SIMILARITY_THRESHOLD = 0.7

DEFAULT_SYSTEM_PROMPT = (
    "You are Soma, the default operator agent of the Soma stack. "
    "Be direct, accurate, and honest about uncertainty. "
    "Use tools when they answer the question; never invent facts or hosts."
)

CAPSULE_NAME = "Default Agent"
AGENT_NAME = "Default Agent"
AGENT_SLUG = "default-agent"

# ── InfrastructureConfig keys (P6) ─────────────────────────────────────────
# (service_name, key, value, value_type, editable, description)
#
# ``value`` is the *seed* for the operator layer. Deployment endpoints seed
# empty — bootstrap creates the row so the settings chain has something to
# edit, never a guessed host. ``SA01_DEFAULT_TENANT_ID`` and
# ``SOMABRAIN_NAMESPACE`` are overwritten at write time with the values this
# run actually provisioned (operator's --tenant, the Capsule memory pointer);
# the empty seed is only used when that run has nothing to propagate.
# ``MEM_EMBED_DIM`` comes from the shared memory-contract constant, not a
# literal (Rule 1: a default is a hardcoded value).
INFRA_SEED_KEYS: List[Tuple[str, str, str, str, bool, str]] = [
    (
        "somabrain",
        "SOMABRAIN_URL",
        "",
        "url",
        True,
        "SomaBrain API base (deployment endpoint). Required for chat memory.",
    ),
    (
        "somabrain",
        "SOMABRAIN_NAMESPACE",
        "",
        "string",
        True,
        "SomaBrain memory namespace for this deployment.",
    ),
    (
        "platform",
        "SA01_DEFAULT_TENANT_ID",
        "",
        "string",
        True,
        "Default tenant id for this agent deployment. Must match SOMABRAIN_DEFAULT_TENANT.",
    ),
    (
        "memory",
        "MEM_EMBED_DIM",
        str(DEFAULT_MEM_EMBED_DIM),
        "integer",
        True,
        "Embedding dimension for memory vectors.",
    ),
]

# ── Model Roles (P4) ───────────────────────────────────────────────────────
# The tenant-defaults AgentSetting scope (admin.llm.providers.DEFAULTS_AGENT_ID).
MODEL_ROLE_AGENT_ID = DEFAULTS_AGENT_ID

# Declaration order for reports/asserts — the five roles of the product model.
MODEL_ROLE_ORDER: Tuple[str, ...] = MODEL_ROLES

# role -> catalog ``name`` of the LLMModelConfig it binds. The AgentSetting key
# comes from ROLE_SETTING_KEYS — this table names only the model, never a key.
MODEL_ROLE_DEFAULTS: Dict[str, str] = {
    "chat_role": MIMO_FLASH_NAME,
    "utility_role": MIMO_FLASH_NAME,
    "embedding_role": "openai/text-embedding-3-small",
    "vision_role": VISION_MODEL_NAME,
    "decision_role": CLEF_DECISION_ROW["name"],
}

# Model presets are owned by admin.llm.api (BUNDLED_PRESETS +
# POST /llm/presets/restore-bundled). bootstrap_soma binds the five Model
# Roles and deliberately does not keep a second preset catalogue here.
