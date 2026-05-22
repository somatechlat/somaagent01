"""Capsule Export Service.

Simple. Elegant. Complete.

Exports Capsule bundles for backup, transfer, or disaster recovery.
A complete Capsule export contains everything needed to recreate an agent:
- Soul (identity, personality, prompts)
- Body (capabilities, resource limits, model constraints)
- Governance (constitution binding, cryptographic signature)
- Related data (models, prompts, settings, feature flags)

VIBE Compliance:
- Rule 82: Professional comments, zero AI slop
- Rule 84: No mocks - real Django ORM queries
- Rule 216: Django 5+ Backend Sovereignty
- Rule 245: Under 650 lines
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from admin.core.models import (
    AgentSetting,
    Capability,
    Capsule,
    CapsuleInstance,
    Constitution,
    FeatureFlag,
    Prompt,
    Session,
    UISetting,
)
from admin.llm.models import LLMModelConfig

logger = logging.getLogger(__name__)


# =============================================================================
# EXPORT DATA CLASSES
# =============================================================================


@dataclass
class CapsuleSoulExport:
    """Exported Soul (identity) data."""

    system_prompt: str
    personality_traits: dict
    neuromodulator_baseline: dict


@dataclass
class CapsuleBrainExport:
    """Exported Brain (IQ + models) data."""

    chat_model: Optional[dict]
    image_model: Optional[dict]
    voice_model: Optional[dict]
    browser_model: Optional[dict]
    iq_knobs: dict


@dataclass
class CapsuleHandsExport:
    """Exported Hands (tools) data."""

    tool_registry: dict
    tool_policy: dict


@dataclass
class CapsuleMemoryPointerExport:
    """Exported Memory pointer (reference, not payload)."""

    tenant: str
    namespace: str
    recall_limit: int
    similarity_threshold: float


@dataclass
class CapsuleBodyExport:
    """Exported Body (resource limits only — capabilities are in hands)."""

    resource_limits: dict


@dataclass
class CapsuleGovernanceExport:
    """Exported Governance data."""

    constitution_ref: dict
    registry_signature: Optional[str]
    certified_at: Optional[str]


@dataclass
class CapsuleExport:
    """Complete Capsule export structure (v2)."""

    spec_version: str
    id: str
    name: str
    version: str
    tenant: str
    description: str
    status: str
    parent_id: Optional[str]
    soul: CapsuleSoulExport
    brain: CapsuleBrainExport
    hands: CapsuleHandsExport
    memory_pointer: CapsuleMemoryPointerExport
    body: CapsuleBodyExport
    governance: CapsuleGovernanceExport
    neuromodulator_state: dict
    created_at: str
    updated_at: str


@dataclass
class ConstitutionExport:
    """Exported Constitution data."""

    id: str
    version: str
    content_hash: str
    signature: str
    content: dict
    is_active: bool


@dataclass
class CapsuleInstanceExport:
    """Exported CapsuleInstance data."""

    id: str
    session_id: str
    state: dict
    status: str
    started_at: str
    completed_at: Optional[str]


@dataclass
class RelatedDataExport:
    """Exported related data."""

    models: list
    capabilities: list
    prompts: list
    feature_flags: list
    agent_settings: list
    ui_settings: list


@dataclass
class CapsuleBundleExport:
    """Complete Capsule bundle for backup/transfer."""

    export_version: str = "1.0.0"
    exported_at: str = ""
    export_checksum: str = ""
    capsule: Optional[CapsuleExport] = None
    constitution: Optional[ConstitutionExport] = None
    instances: list = field(default_factory=list)
    related_data: Optional[RelatedDataExport] = None
    sessions: list = field(default_factory=list)


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================


def export_capsule(
    capsule_id: UUID,
    include_instances: bool = True,
    include_sessions: bool = False,
    include_related_data: bool = True,
) -> dict:
    """Export a complete Capsule bundle for backup or transfer.

    Exports all data needed to recreate the agent on another system.

    Args:
        capsule_id: UUID of the capsule to export
        include_instances: Include running CapsuleInstance records
        include_sessions: Include Session/SessionEvent data (can be large)
        include_related_data: Include models, prompts, capabilities, etc.

    Returns:
        Complete export bundle as dict (JSON-serializable)

    Raises:
        Capsule.DoesNotExist: If capsule not found
    """
    capsule = Capsule.objects.select_related("constitution", "parent").get(id=capsule_id)

    logger.info(
        "Exporting Capsule %s:%s (tenant=%s)",
        capsule.name,
        capsule.version,
        capsule.tenant,
    )

    # Build export bundle
    bundle = CapsuleBundleExport(
        export_version="1.0.0",
        exported_at=datetime.now(timezone.utc).isoformat(),
        capsule=_export_capsule_core(capsule),
        constitution=_export_constitution(capsule.constitution) if capsule.constitution else None,
    )

    # Include running instances
    if include_instances:
        bundle.instances = _export_instances(capsule)

    # Include related data (models, capabilities, prompts, etc.)
    if include_related_data:
        bundle.related_data = _export_related_data(capsule)

    # Include sessions (optional - can be very large)
    if include_sessions:
        bundle.sessions = _export_sessions(capsule)

    # Convert to dict and compute checksum
    export_dict = _bundle_to_dict(bundle)
    export_dict["export_checksum"] = _compute_checksum(export_dict)

    logger.info(
        "Capsule export complete: %s:%s, checksum=%s",
        capsule.name,
        capsule.version,
        export_dict["export_checksum"][:16],
    )

    return export_dict


def export_tenant_capsules(
    tenant: str,
    include_instances: bool = True,
    include_related_data: bool = True,
) -> dict:
    """Export ALL capsules for a tenant.

    Args:
        tenant: Tenant identifier
        include_instances: Include running instances for each capsule
        include_related_data: Include related data

    Returns:
        Complete tenant export bundle
    """
    capsules = Capsule.objects.filter(tenant=tenant)

    logger.info("Exporting %d capsules for tenant: %s", capsules.count(), tenant)

    exports = []
    for capsule in capsules:
        try:
            exports.append(
                export_capsule(
                    capsule.id,
                    include_instances=include_instances,
                    include_sessions=False,  # Too large for bulk export
                    include_related_data=False,  # Include once at tenant level
                )
            )
        except Exception as e:
            logger.error("Failed to export capsule %s: %s", capsule.id, e)

    # Get related data once for entire tenant
    related_data = None
    if include_related_data:
        related_data = {
            "models": list(LLMModelConfig.objects.filter(is_active=True).values()),
            "capabilities": list(Capability.objects.filter(is_enabled=True).values()),
            "prompts": list(Prompt.objects.filter(tenant=tenant, is_active=True).values()),
            "feature_flags": list(FeatureFlag.objects.values()),
            "ui_settings": list(UISetting.objects.filter(tenant=tenant).values()),
        }

    export = {
        "tenant_export_version": "1.0.0",
        "tenant": tenant,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "capsule_count": len(exports),
        "capsules": exports,
        "related_data": related_data,
    }

    export["export_checksum"] = _compute_checksum(export)

    logger.info(
        "Tenant export complete: %s, %d capsules, checksum=%s",
        tenant,
        len(exports),
        export["export_checksum"][:16],
    )

    return export


# =============================================================================
# INTERNAL HELPER FUNCTIONS
# =============================================================================


def _serialize_model(model) -> Optional[dict]:
    """Serialize an LLMModelConfig to dict."""
    if not model:
        return None
    return {
        "id": str(model.id) if hasattr(model, "id") else None,
        "name": getattr(model, "name", ""),
        "provider": getattr(model, "provider", ""),
        "display_name": getattr(model, "display_name", ""),
    }


def _export_capsule_core(capsule: Capsule) -> CapsuleExport:
    """Export core Capsule data (v2 format)."""
    capabilities = capsule.capabilities.filter(is_enabled=True)
    mp = capsule.memory_pointer or {}

    return CapsuleExport(
        spec_version="capsule-v2",
        id=str(capsule.id),
        name=capsule.name,
        version=capsule.version,
        tenant=str(capsule.tenant) if capsule.tenant else "",
        description=capsule.description,
        status=capsule.status,
        parent_id=str(capsule.parent.id) if capsule.parent else None,
        soul=CapsuleSoulExport(
            system_prompt=capsule.system_prompt,
            personality_traits=capsule.personality_traits,
            neuromodulator_baseline=capsule.neuromodulator_baseline,
        ),
        brain=CapsuleBrainExport(
            chat_model=_serialize_model(capsule.chat_model),
            image_model=_serialize_model(capsule.image_model),
            voice_model=_serialize_model(capsule.voice_model),
            browser_model=_serialize_model(capsule.browser_model),
            iq_knobs=capsule.persona_config.get("knobs", {}),
        ),
        hands=CapsuleHandsExport(
            tool_registry={
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
            tool_policy=capsule.tool_policy,
        ),
        memory_pointer=CapsuleMemoryPointerExport(
            tenant=mp.get("tenant", str(capsule.tenant) if capsule.tenant else "default"),
            namespace=mp.get("namespace", f"agent_{str(capsule.id)[:8]}_chat_history"),
            recall_limit=mp.get("recall_limit", 10),
            similarity_threshold=mp.get("similarity_threshold", 0.7),
        ),
        body=CapsuleBodyExport(
            resource_limits=capsule.resource_limits,
        ),
        governance=CapsuleGovernanceExport(
            constitution_ref=capsule.constitution_ref,
            registry_signature=capsule.registry_signature,
            certified_at=capsule.certified_at.isoformat() if capsule.certified_at else None,
        ),
        neuromodulator_state=capsule.neuromodulator_state,
        created_at=capsule.created_at.isoformat(),
        updated_at=capsule.updated_at.isoformat(),
    )


def _export_constitution(constitution: Constitution) -> ConstitutionExport:
    """Export Constitution data."""
    return ConstitutionExport(
        id=str(constitution.id),
        version=constitution.version,
        content_hash=constitution.content_hash,
        signature=constitution.signature,
        content=constitution.content,
        is_active=constitution.is_active,
    )


def _export_instances(capsule: Capsule) -> list:
    """Export CapsuleInstance records."""
    instances = CapsuleInstance.objects.filter(capsule=capsule)
    return [
        asdict(
            CapsuleInstanceExport(
                id=str(inst.id),
                session_id=inst.session_id,
                state=inst.state,
                status=inst.status,
                started_at=inst.started_at.isoformat(),
                completed_at=inst.completed_at.isoformat() if inst.completed_at else None,
            )
        )
        for inst in instances
    ]


def _export_related_data(capsule: Capsule) -> RelatedDataExport:
    """Export related data entities."""
    # Get capabilities from M2M (canonical) — snapshot at export time
    capabilities = list(capsule.capabilities.filter(is_enabled=True).values())

    return RelatedDataExport(
        models=list(LLMModelConfig.objects.filter(is_active=True).values()),
        capabilities=capabilities,
        prompts=list(Prompt.objects.filter(tenant=capsule.tenant, is_active=True).values()),
        feature_flags=list(FeatureFlag.objects.values()),
        agent_settings=list(AgentSetting.objects.filter(agent_id=str(capsule.id)).values()),
        ui_settings=list(UISetting.objects.filter(tenant=capsule.tenant).values()),
    )


def _export_sessions(capsule: Capsule) -> list:
    """Export Session and SessionEvent data."""
    # Get session IDs from instances
    instance_session_ids = list(
        CapsuleInstance.objects.filter(capsule=capsule).values_list("session_id", flat=True)
    )

    if not instance_session_ids:
        return []

    sessions = Session.objects.filter(session_id__in=instance_session_ids).prefetch_related(
        "events"
    )

    return [
        {
            "session_id": session.session_id,
            "persona_id": session.persona_id,
            "tenant": session.tenant,
            "metadata": session.metadata,
            "created_at": session.created_at.isoformat(),
            "events": [
                {
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "role": event.role,
                    "created_at": event.created_at.isoformat(),
                }
                for event in session.events.all()  # type: ignore[attr-defined]
            ],
        }
        for session in sessions
    ]


def _bundle_to_dict(bundle: CapsuleBundleExport) -> dict:
    """Convert export bundle to JSON-serializable dict."""

    def convert(obj: Any) -> Any:
        if hasattr(obj, "__dataclass_fields__"):
            return {k: convert(v) for k, v in asdict(obj).items()}
        if isinstance(obj, list):
            return [convert(item) for item in obj]
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj

    return convert(bundle)


def _compute_checksum(data: dict) -> str:
    """Compute SHA-256 checksum of export data."""
    # Remove existing checksum before computing
    data_copy = {k: v for k, v in data.items() if k != "export_checksum"}
    json_bytes = json.dumps(data_copy, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()


def verify_export_checksum(export_data: dict) -> bool:
    """Verify the integrity of an export bundle.

    Args:
        export_data: Export bundle dict

    Returns:
        True if checksum is valid, False otherwise
    """
    stored_checksum = export_data.get("export_checksum", "")
    computed_checksum = _compute_checksum(export_data)
    return stored_checksum == computed_checksum


# =============================================================================
# PARTIAL EXPORTS
# =============================================================================


def export_capsule_tools(capsule_id: UUID) -> dict:
    """Export just the tools from a Capsule.

    Returns a .tools.capsule fragment that can be imported into another Capsule.
    """
    capsule = Capsule.objects.prefetch_related("capabilities").get(id=capsule_id)
    capabilities = capsule.capabilities.filter(is_enabled=True)

    return {
        "spec_version": "tools-v1",
        "source_capsule": str(capsule.id),
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
        "tool_policy": capsule.tool_policy,
    }


def export_capsule_persona(capsule_id: UUID) -> dict:
    """Export just the persona from a Capsule.

    Returns a .persona.capsule fragment that can be imported into another Capsule.
    """
    capsule = Capsule.objects.get(id=capsule_id)

    return {
        "spec_version": "persona-v1",
        "source_capsule": str(capsule.id),
        "soul": {
            "system_prompt": capsule.system_prompt,
            "personality_traits": capsule.personality_traits,
            "neuromodulator_baseline": capsule.neuromodulator_baseline,
        },
        "brain": {
            "iq_knobs": capsule.persona_config.get("knobs", {}),
        },
        "memory_pointer": capsule.memory_pointer,
    }


def export_capsule_governance(capsule_id: UUID) -> dict:
    """Export just the governance from a Capsule.

    Returns a .gov.capsule fragment that can be imported into another Capsule.
    """
    capsule = Capsule.objects.get(id=capsule_id)

    return {
        "spec_version": "governance-v1",
        "source_capsule": str(capsule.id),
        "constitution_ref": capsule.constitution_ref,
        "opa_policies": capsule.body.get("governance", {}).get("opa_policies", {}),
        "spicedb_relations": capsule.body.get("governance", {}).get("spicedb_relations", {}),
    }


__all__ = [
    "export_capsule",
    "export_tenant_capsules",
    "export_capsule_tools",
    "export_capsule_persona",
    "export_capsule_governance",
    "verify_export_checksum",
    "CapsuleBundleExport",
    "CapsuleExport",
]
