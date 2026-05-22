"""
ContextBuilder - 5-Lane Prompt Assembly Module.

Assembles prompts from capsule.body.persona using:
1. System lane (base prompt)
2. History lane (conversation)
3. Memory lane (SomaBrain recall)
4. Tools lane (available tools)
5. Buffer lane (user message)

SRS Source: SRS-CONTEXT-BUILDING-2026-01-16

Applied Personas:
- PhD Developer: Clean async design
- PhD Analyst: Lane allocation math
- Performance: Token budgeting
- Django Architect: Direct brain integration
"""

from admin.core.context.builder import build_context, ContextBuilder
from admin.core.context.lanes import get_lane_allocation, LaneAllocation
from admin.core.context.models import BuiltContext

__all__ = [
    "ContextBuilder",
    "build_context",
    "get_lane_allocation",
    "LaneAllocation",
    "BuiltContext",
]
