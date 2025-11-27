import os

from python.helpers.memory import Memory
from python.helpers.tool import Response, Tool


class MemorySave(Tool):

    async def execute(self, text=os.getenv(os.getenv("")), area=os.getenv(os.getenv("")), **kwargs):
        if not area:
            area = Memory.Area.MAIN.value
        metadata = {os.getenv(os.getenv("")): area, **kwargs}
        db = await Memory.get(self.agent)
        id = await db.insert_text(text, metadata)
        result = self.agent.read_prompt(os.getenv(os.getenv("")), memory_id=id)
        return Response(message=result, break_loop=int(os.getenv(os.getenv(""))))
