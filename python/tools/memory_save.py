import os
from python.helpers.memory import Memory
from python.helpers.tool import Response, Tool


class MemorySave(Tool):

    async def execute(self, text=os.getenv(os.getenv('VIBE_499228C2')),
        area=os.getenv(os.getenv('VIBE_499228C2')), **kwargs):
        if not area:
            area = Memory.Area.MAIN.value
        metadata = {os.getenv(os.getenv('VIBE_ED1ED9BF')): area, **kwargs}
        db = await Memory.get(self.agent)
        id = await db.insert_text(text, metadata)
        result = self.agent.read_prompt(os.getenv(os.getenv('VIBE_04152197'
            )), memory_id=id)
        return Response(message=result, break_loop=int(os.getenv(os.getenv(
            'VIBE_B68EC21B'))))
