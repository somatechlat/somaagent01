"""
AgentIQ - Governor Control Loop Module.

This module implements the 3-knob derivation system for SomaAgent01.
ALL settings derive from capsule.body.persona.knobs.

SRS Source: SRS-AGENTIQ-2026-01-16

Applied Personas:
- PhD Developer: Pure Python, 0ms latency
- PhD Analyst: Mathematical derivation tables
- PhD QA: Bounded values, edge case handling
- Security Auditor: Fail-closed principle
- Performance: No external calls
- Django Architect: Pydantic models
"""

from admin.core.agentiq.settings import DerivedSettings
from admin.core.agentiq.derivation import derive_all_settings
from admin.core.agentiq.unified_gate import UnifiedGate

__all__ = [
    "DerivedSettings",
    "derive_all_settings",
    "UnifiedGate",
]
