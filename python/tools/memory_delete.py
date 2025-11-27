import os
from python.helpers.memory import Memory
from python.helpers.tool import Response, Tool


class MemoryDelete(Tool):

    async def execute(self, ids=os.getenv(os.getenv('VIBE_BD7707AA')), **kwargs
        ):
        db = await Memory.get(self.agent)
        ids = [id.strip() for id in ids.split(os.getenv(os.getenv(
            'VIBE_3B92A988'))) if id.strip()]
        dels = await db.delete_documents_by_ids(ids=ids)
        result = self.agent.read_prompt(os.getenv(os.getenv('VIBE_3066332F'
            )), memory_count=len(dels))
        return Response(message=result, break_loop=int(os.getenv(os.getenv(
            'VIBE_741A2879'))))
