"""Shared planning utilities to avoid duplicated helpers across planners."""

import logging
from typing import Optional, Tuple

from somabrain.memory.graph_client import GraphClient

logger = logging.getLogger(__name__)


def get_graph_client_from_memory(mem) -> Optional[GraphClient]:
    """Extract GraphClient from a memory client or its transport."""
    if mem is None:
        return None

    if hasattr(mem, "graph_client") and mem.graph_client is not None:
        return mem.graph_client

    if hasattr(mem, "_graph") and mem._graph is not None:
        return mem._graph

    if hasattr(mem, "_transport") and mem._transport is not None:
        try:
            tenant = getattr(mem, "_tenant", "default")
            return GraphClient(mem._transport, tenant=tenant)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Could not construct GraphClient from transport", error=str(exc))

    return None


def task_key_to_coord(
    task_key: str, mem, universe: Optional[str]
) -> Optional[Tuple[float, ...]]:
    """Convert a task key to a coordinate by parsing or memory lookup."""
    try:
        parts = task_key.split(",")
        if len(parts) >= 2:
            return tuple(float(p.strip()) for p in parts)
    except (ValueError, AttributeError):
        pass

    if mem is not None and hasattr(mem, "search"):
        try:
            results = mem.search(query=task_key, limit=1, universe=universe)
            if results:
                result = results[0]
                if hasattr(result, "coord"):
                    return result.coord
                if hasattr(result, "coordinate"):
                    return result.coordinate
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Memory search for task_key failed", error=str(exc))

    return None


def coord_to_str(coord: Tuple[float, ...]) -> str:
    """Convert coordinate tuple to canonical string representation."""
    return ",".join(f"{c:.6f}" for c in coord)
