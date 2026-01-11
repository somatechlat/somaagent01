"""Module memory_forget."""

from admin.core.helpers.memory import Memory
from admin.core.helpers.tool import Response, Tool
from admin.tools.implementations.memory_load import DEFAULT_THRESHOLD


class MemoryForget(Tool):
    """Tool for forgetting memories based on a query and threshold."""

    async def execute(self, query="", threshold=DEFAULT_THRESHOLD, filter="", **kwargs):
        """Execute execute.

        Args:
            query: The query.
            threshold: The threshold.
            filter: The filter.
        """

        db = await Memory.get(self.agent)
        dels = await db.delete_documents_by_query(query=query, threshold=threshold, filter=filter)

        result = self.agent.read_prompt("fw.memories_deleted.md", memory_count=len(dels))
        return Response(message=result, break_loop=False)
