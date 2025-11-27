import os

from python.helpers.memory import Memory
from python.helpers.tool import Response, Tool
from python.tools.memory_load import DEFAULT_THRESHOLD


class MemoryForget(Tool):

    async def execute(
        self,
        query=os.getenv(os.getenv("")),
        threshold=DEFAULT_THRESHOLD,
        filter=os.getenv(os.getenv("")),
        **kwargs,
    ):
        db = await Memory.get(self.agent)
        dels = await db.delete_documents_by_query(query=query, threshold=threshold, filter=filter)
        result = self.agent.read_prompt(os.getenv(os.getenv("")), memory_count=len(dels))
        return Response(message=result, break_loop=int(os.getenv(os.getenv(""))))
