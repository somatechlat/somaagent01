"""Capsule/coordinate Django ORM models."""

from __future__ import annotations

import uuid

from django.db import models


# =============================================================================
# CAPSULE MODELS (replaces capsule_store.py)
# =============================================================================


class Capsule(models.Model):
    """Capsule definition - The Atomic Unit of Agent Identity (Rule 91).

    The Capsule acts as the "Sole Unit" of exchange, containing:
    1.  Identity (Soul)
    2.  Body (Model Configs via FK)
    3.  Hands (capabilities via M2M)
    4.  Memory (MemoryConfig via FK)

    Lifecycle: DRAFT → ACTIVE → ARCHIVED
    """

    # Status choices for lifecycle management
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=50, default="1.0.0")

    # Tenant FK for proper referential integrity
    tenant = models.ForeignKey(
        "aaas.Tenant",
        on_delete=models.CASCADE,
        related_name="capsules",
        db_index=True,
        help_text="Owning tenant",
    )

    description = models.TextField(blank=True)

    # Lifecycle Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        help_text="Lifecycle state: draft, active, archived",
    )

    # Version Lineage (for edit-spawns-new-version pattern)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent capsule this was cloned from",
    )

    # Governance & Security
    constitution = models.ForeignKey(
        "Constitution",
        on_delete=models.PROTECT,
        related_name="capsules",
        null=True,
        help_text="The binding legal framework",
    )
    constitution_ref = models.JSONField(
        default=dict, blank=True, help_text="Cross-system reference: {'checksum': str, 'url': str}"
    )
    registry_signature = models.TextField(
        null=True, blank=True, help_text="Ed25519 Signature from Registry Authority"
    )
    certified_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp of certification"
    )

    # The Soul (Identity)
    system_prompt = models.TextField(default="", help_text="Base cognitive instruction set")
    personality_traits = models.JSONField(
        default=dict, help_text="Big 5 Traits (Openness, etc.) 0.0-1.0"
    )
    neuromodulator_baseline = models.JSONField(
        default=dict, help_text="Baseline chemical state (Dopamine, etc.)"
    )
    learning_config = models.JSONField(
        default=dict,
        help_text="GMD Hyperparameters (eta, lambda, alpha) & Reward Thresholds",
    )

    # ═══════════════════════════════════════════════════════════════════
    # 2. BODY: MODEL SOVEREIGNTY (Foreign Keys Only - Rule 91)
    # ═══════════════════════════════════════════════════════════════════

    # 🧠 PRIMARY BRAIN
    chat_model = models.ForeignKey(
        "llm.LLMModelConfig",
        related_name="capabilities_chat",
        on_delete=models.PROTECT,
        null=True,  # Allowed to be null in draft
        help_text="The main cognitive engine (e.g. gpt-4-turbo)",
    )

    # 👁️ VISION & IMAGE
    image_model = models.ForeignKey(
        "llm.LLMModelConfig",
        related_name="capabilities_image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Image generation model (e.g. dall-e-3)",
    )

    # 🗣️ VOICE (TTS/STT)
    voice_model = models.ForeignKey(
        "llm.LLMModelConfig",
        related_name="capabilities_voice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Voice synthesis model (e.g. elevenlabs-v1)",
    )

    # 🌐 BROWSER
    browser_model = models.ForeignKey(
        "llm.LLMModelConfig",
        related_name="capabilities_browser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Web browsing and vision model (e.g. perplexity)",
    )

    # ═══════════════════════════════════════════════════════════════════
    # 3. HANDS: TOOLS & CAPABILITIES
    # ═══════════════════════════════════════════════════════════════════

    capabilities = models.ManyToManyField(
        "Capability",
        related_name="capsules",
        blank=True,
        help_text="Active tools/MCP servers available to this agent",
    )

    # ═══════════════════════════════════════════════════════════════════
    # 4. PERSONA & RUNTIME CONFIG (The Agent's Control Panel)
    # ═══════════════════════════════════════════════════════════════════

    persona_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Agent persona configuration: {
            "knobs": {"intelligence_level": 5, "autonomy_level": 5, "resource_budget": 0.10},
            "prompts": {"injection_prompts": [...], "tool_prompts": {...}},
            "memory": {"recall_limit": 10, "similarity_threshold": 0.7},
            "learned": {"lane_preferences": {...}}
        }
        """,
    )

    tool_policy = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Tool execution policy: {
            "auto_execute": ["echo", "timestamp"],
            "approval_required": ["code_execute"],
            "denied": ["file_delete"]
        }
        """,
    )

    memory_pointer = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Memory namespace pointer: {
            "tenant": "acme_corp",
            "namespace": "agent_xxx_chat_history",
            "recall_limit": 10,
            "similarity_threshold": 0.7
        }
        """,
    )

    neuromodulator_state = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Last-synced neuromodulator state from SomaBrain: {
            "dopamine": 0.5, "serotonin": 0.6,
            "norepinephrine": 0.4, "acetylcholine": 0.5,
            "last_synced_at": "2026-05-21T13:00:00Z"
        }
        """,
    )

    # ═══════════════════════════════════════════════════════════════════
    # 5. MEMORY & HISTORY
    # ═══════════════════════════════════════════════════════════════════

    # DISABLED: somabrain app not installed in this deployment
    # memory_config = models.ForeignKey(
    #     "somabrain.MemoryConfig",
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     help_text="Memory retention and retrieval strategy",
    # )

    resource_limits = models.JSONField(default=dict, help_text="Max wall clock, concurrency, etc.")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "capsules"
        unique_together = [["name", "version", "tenant"]]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "name", "version"]),
        ]

    def __str__(self):
        """Return string representation."""

        return f"Capsule({self.name}:{self.version}:{self.status})"

    @property
    def is_certified(self) -> bool:
        """Check if capsule has been certified."""
        return bool(self.registry_signature and self.status == self.STATUS_ACTIVE)

    @property
    def core(self) -> dict:
        """Return Core (identity) as dict.

        Renamed from 'soul' per international naming conventions.
        """
        return {
            "system_prompt": self.system_prompt,
            "personality_traits": self.personality_traits,
            "neuromodulator_baseline": self.neuromodulator_baseline,
        }

    @property
    def body(self) -> dict:
        """Return complete agent body as dict.

        This is the canonical structured view consumed by:
        - ContextBuilder (5-lane prompt assembly)
        - AgentIQ derivation (3-knob → 12 settings)
        - UnifiedGate (permission scope checks)
        - Export/Import (portable agent DNA)
        """
        capabilities = self.capabilities.filter(is_enabled=True)
        return {
            "persona": {
                "core": {
                    "system_prompt": self.system_prompt,
                    "personality_traits": self.personality_traits,
                    "neuromodulator_baseline": self.neuromodulator_baseline,
                },
                "knobs": self.persona_config.get("knobs", {}),
                "prompts": self.persona_config.get("prompts", {}),
                "tools": {
                    "enabled_capabilities": [c.name for c in capabilities],
                    "tool_registry": {
                        c.name: {
                            "name": c.name,
                            "description": c.description,
                            "schema": c.schema,
                            "config": c.config,
                            "policy": getattr(c, "policy", {}),
                            "implementation": getattr(c, "implementation", {}),
                        }
                        for c in capabilities
                    },
                    "tool_policy": self.tool_policy,
                },
                "memory": self.persona_config.get("memory", {}),
                "learned": self.persona_config.get("learned", {}),
            },
            "governance": {
                "constitution_ref": self.constitution_ref,
                "opa_policies": self.persona_config.get("governance", {}).get("opa_policies", {}),
                "spicedb_relations": self.persona_config.get("governance", {}).get("spicedb_relations", {}),
            },
            "resource_limits": self.resource_limits,
            "memory_pointer": self.memory_pointer,
            "neuromodulator_state": self.neuromodulator_state,
        }


class CapsuleInstance(models.Model):
    """Running capsule instance - replaces CapsuleInstanceStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capsule = models.ForeignKey(Capsule, on_delete=models.CASCADE, related_name="instances")
    session_id = models.CharField(max_length=255, db_index=True)
    state = models.JSONField(default=dict)
    status = models.CharField(max_length=50, default="running", db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "capsule_instances"
