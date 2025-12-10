"""Settings section builders for memory/SomaBrain configuration."""

from typing import Any

from python.helpers.settings_types import SettingsField, SettingsSection


def build_memory_section(settings: Any) -> SettingsSection:
    """Build the memory/SomaBrain settings section."""
    fields: list[SettingsField] = [
        {
            "id": "agent_memory_subdir",
            "title": "Memory Subdirectory",
            "description": "Subdirectory of /memory folder.",
            "type": "text",
            "value": settings["agent_memory_subdir"],
        },
        {
            "id": "memory_dashboard",
            "title": "Memory Dashboard",
            "description": "View stored memories.",
            "type": "button",
            "value": "Open Dashboard",
        },
        {
            "id": "memory_recall_enabled",
            "title": "Memory auto-recall enabled",
            "type": "switch",
            "value": settings["memory_recall_enabled"],
        },
        {
            "id": "memory_recall_delayed",
            "title": "Memory auto-recall delayed",
            "description": "Memories delivered one message later.",
            "type": "switch",
            "value": settings["memory_recall_delayed"],
        },
        {
            "id": "memory_recall_query_prep",
            "title": "Auto-recall AI query preparation",
            "type": "switch",
            "value": settings["memory_recall_query_prep"],
        },
        {
            "id": "memory_recall_post_filter",
            "title": "Auto-recall AI post-filtering",
            "type": "switch",
            "value": settings["memory_recall_post_filter"],
        },
        {
            "id": "memory_recall_interval",
            "title": "Memory auto-recall interval",
            "type": "range",
            "min": 1,
            "max": 10,
            "step": 1,
            "value": settings["memory_recall_interval"],
        },
        {
            "id": "memory_recall_history_len",
            "title": "Auto-recall history length",
            "type": "number",
            "value": settings["memory_recall_history_len"],
        },
        {
            "id": "memory_recall_similarity_threshold",
            "title": "Similarity threshold",
            "type": "range",
            "min": 0,
            "max": 1,
            "step": 0.01,
            "value": settings["memory_recall_similarity_threshold"],
        },
        {
            "id": "memory_recall_memories_max_search",
            "title": "Max memories to search",
            "type": "number",
            "value": settings["memory_recall_memories_max_search"],
        },
        {
            "id": "memory_recall_memories_max_result",
            "title": "Max memories to use",
            "type": "number",
            "value": settings["memory_recall_memories_max_result"],
        },
        {
            "id": "memory_recall_solutions_max_search",
            "title": "Max solutions to search",
            "type": "number",
            "value": settings["memory_recall_solutions_max_search"],
        },
        {
            "id": "memory_recall_solutions_max_result",
            "title": "Max solutions to use",
            "type": "number",
            "value": settings["memory_recall_solutions_max_result"],
        },
        {
            "id": "memory_memorize_enabled",
            "title": "Auto-memorize enabled",
            "type": "switch",
            "value": settings["memory_memorize_enabled"],
        },
        {
            "id": "memory_memorize_consolidation",
            "title": "Auto-memorize AI consolidation",
            "type": "switch",
            "value": settings["memory_memorize_consolidation"],
        },
        {
            "id": "memory_memorize_replace_threshold",
            "title": "Replacement threshold",
            "type": "range",
            "min": 0,
            "max": 1,
            "step": 0.01,
            "value": settings["memory_memorize_replace_threshold"],
        },
    ]
    return {
        "id": "memory",
        "title": "SomaBrain",
        "description": "Memory system configuration.",
        "fields": fields,
        "tab": "agent",
    }
