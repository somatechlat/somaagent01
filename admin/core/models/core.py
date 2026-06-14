"""Core Django ORM Models for Agent Domain.

100% Django ORM -
Replaces raw SQL stores with Django models.

This module now re-exports domain models that have been split into
separate modules for maintainability. All existing import paths continue
to work for backward compatibility.
"""

from __future__ import annotations

# Agent-related models
from admin.core.models.agent import (
    AgentSetting,
    Asset,
    DelegationTask,
    ExecutionRecord,
    FeatureFlag,
    Job,
    MemoryReplica,
    ModelProfile,
    MultimodalOutcome,
    Notification,
    Prompt,
    Provenance,
    Session,
    SessionEvent,
    UISetting,
)

# Capsule/coordinate models
from admin.core.models.capsule import Capsule, CapsuleInstance

# Governance models (Constitution & Capability)
from admin.core.models.governance import Capability, Constitution

__all__ = [
    # Session
    "Session",
    "SessionEvent",
    # Governance
    "Constitution",
    "Capability",
    # Capsule
    "Capsule",
    "CapsuleInstance",
    # Settings
    "UISetting",
    "AgentSetting",
    "FeatureFlag",
    # Jobs & Prompts
    "Job",
    "Notification",
    "Prompt",
    # Memory
    "MemoryReplica",
    # Asset
    "Asset",
    # Execution
    "ExecutionRecord",
    # Provenance
    "Provenance",
    # Model Profiles
    "ModelProfile",
    # Outcomes
    "MultimodalOutcome",
    # Delegation
    "DelegationTask",
]
