"""Core models package.

VIBE Rule 245 Compliant: Split from original 908-line models.py.

This package re-exports all models for backward compatibility.
Import paths like `from admin.core.models import Capsule` still work.
"""

# Domain models (original file, now reduced)
from admin.core.models.core import (
    # Session
    Session,
    SessionEvent,
    # Constitution & Capsule
    Constitution,
    Capsule,
    CapsuleInstance,
    # Capability
    Capability,
    # Settings
    UISetting,
    AgentSetting,
    FeatureFlag,
    # Jobs & Prompts
    Job,
    Notification,
    Prompt,
    # Memory
    MemoryReplica,
)

# Zero Data Loss Infrastructure
from admin.core.models.zdl import (
    OutboxMessage,
    DeadLetterMessage,
    IdempotencyRecord,
    PendingMemory,
)

# Sensor Outbox
from admin.core.sensors.outbox import SensorOutbox

__all__ = [
    # Session
    "Session",
    "SessionEvent",
    # Constitution & Capsule
    "Constitution",
    "Capsule",
    "CapsuleInstance",
    # Capability
    "Capability",
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
    # ZDL Infrastructure
    "OutboxMessage",
    "DeadLetterMessage",
    "IdempotencyRecord",
    "PendingMemory",
    # Sensors
    "SensorOutbox",
]
