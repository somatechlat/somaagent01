from collections.abc import Mapping

from python.helpers.tool import Response, Tool
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError

# Backwards-compatible alias expected by tests and some callers
SomaClient = SomaBrainClient

DEFAULT_THRESHOLD = 0.7
DEFAULT_LIMIT = 10


class MemoryLoad(Tool):
    async def execute(
        self, query="", threshold=DEFAULT_THRESHOLD, limit=DEFAULT_LIMIT, filter="", **kwargs
    ):
        client = SomaBrainClient.get()
        universe = None
        if getattr(self.agent, "config", None):
            universe = getattr(self.agent.config, "memory_subdir", None)

        try:
            top_k = int(limit)
        except (TypeError, ValueError):
            top_k = DEFAULT_LIMIT
        top_k = max(1, top_k)

        try:
            numeric_threshold = float(threshold)
        except (TypeError, ValueError):
            numeric_threshold = DEFAULT_THRESHOLD
        if numeric_threshold < 0:
            numeric_threshold = 0.0

        filter_text = (filter or "").strip().lower()

        try:
            response = await client.recall(
                query,
                top_k=top_k,
                universe=universe,
            )
        except (SomaClientError, Exception):
            result = self.agent.read_prompt("fw.memories_not_found.md", query=query)
            return Response(message=result, break_loop=False)

        entries = []
        if isinstance(response, Mapping):
            wm_entries = response.get("wm", [])
            memory_entries = response.get("memory", [])
            if isinstance(wm_entries, list):
                entries.extend(wm_entries)
            if isinstance(memory_entries, list):
                entries.extend(memory_entries)

        results: list[str] = []
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            payload = entry.get("payload") if isinstance(entry.get("payload"), Mapping) else None

            score_value: float | None = None
            raw_score = entry.get("score")
            if isinstance(raw_score, (int, float)):
                score_value = float(raw_score)
            else:
                raw_score = entry.get("similarity")
                if isinstance(raw_score, (int, float)):
                    score_value = float(raw_score)

            if score_value is not None and score_value < numeric_threshold:
                continue

            message: str | None = None
            # Prefer explicit content fields in payload
            if payload:
                content = payload.get("content")
                if isinstance(content, str) and content.strip():
                    message = content.strip()
                else:
                    text = payload.get("text")
                    if isinstance(text, str) and text.strip():
                        message = text.strip()
                    else:
                        # New fallback for 'what' field in payload
                        what = payload.get("what")
                        if isinstance(what, str) and what.strip():
                            message = what.strip()
            else:
                # Fallback to top‑level content fields
                content = entry.get("content")
                if isinstance(content, str) and content.strip():
                    message = content.strip()

            # Additional fallback: use common metadata keys if no explicit content
            if not message:
                for key in ["fact", "summary", "value", "title", "text", "what"]:
                    val = entry.get(key)
                    if isinstance(val, str) and val.strip():
                        message = val.strip()
                        break

            # If still no message, serialize the entry for debugging
            if not message:
                message = str(entry)

            if message:
                if filter_text and filter_text not in message.lower():
                    continue
                results.append(message)

        if not results:
            result = self.agent.read_prompt("fw.memories_not_found.md", query=query)
        else:
            # Store raw results in conversation context for later use
            try:
                self.agent.extras_temporary["memory_load_results"] = results
            except Exception:
                pass
            result = "\n\n".join(dict.fromkeys(results))

        return Response(message=result, break_loop=False)
