from typing import Any

from python.helpers.extension import Extension
from python.helpers.session_store_adapter import record_tool_result

LEN_MIN = 500


class SaveToolCallFile(Extension):
    async def execute(self, data: dict[str, Any] | None = None, **kwargs):
        if not data:
            return

        # get tool call result
        result = data.get("tool_result") if isinstance(data, dict) else None
        if result is None:
            return

        # skip short results
        if len(str(result)) < LEN_MIN:
            return

        tool_name = data.get("tool_name") or data.get("name") or "unknown_tool"
        event_id = await record_tool_result(
            self.agent.context.id,
            tool_name=tool_name,
            result=result,
            persona_id=None,
            metadata={"source": "hist_add_tool_result"},
        )
        data["tool_result_event_id"] = event_id
