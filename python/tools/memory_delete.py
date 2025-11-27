import os

from python.helpers.memory import Memory
from python.helpers.tool import Response, Tool


class MemoryDelete(Tool):

    async def execute(self, ids=os.getenv(os.getenv("")), **kwargs):
        db = await Memory.get(self.agent)
        ids = [id.strip() for id in ids.split(os.getenv(os.getenv(""))) if id.strip()]
        dels = await db.delete_documents_by_ids(ids=ids)
        result = self.agent.read_prompt(os.getenv(os.getenv("")), memory_count=len(dels))
        return Response(message=result, break_loop=int(os.getenv(os.getenv(""))))
